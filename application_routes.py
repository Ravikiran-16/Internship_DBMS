from flask import Blueprint, request, jsonify
from utils.db import execute_query, get_db_connection
from utils.auth_middleware import token_required
from datetime import datetime

application_bp = Blueprint('application', __name__)

@application_bp.route('/drives', methods=['GET'])
@token_required
def get_all_drives(current_user):
    """
    Get all available placement drives
    Query params: ?upcoming=true (optional)
    """
    try:
        upcoming_only = request.args.get('upcoming', 'false').lower() == 'true'
        
        query = """
            SELECT 
                pd.drive_id,
                pd.drive_date,
                pd.mode,
                pd.deadline,
                pd.venue,
                c.company_id,
                c.name as company_name,
                c.location as company_location,
                c.industry,
                GROUP_CONCAT(DISTINCT jr.role_name SEPARATOR ', ') as roles,
                MIN(jr.min_cgpa) as min_cgpa_required
            FROM placement_drive pd
            JOIN company c ON pd.company_id = c.company_id
            LEFT JOIN job_role jr ON c.company_id = jr.company_id
            WHERE pd.deadline >= CURDATE()
            GROUP BY pd.drive_id, pd.drive_date, pd.mode, pd.deadline, pd.venue,
                     c.company_id, c.name, c.location, c.industry
            ORDER BY pd.drive_date ASC
        """
        
        drives = execute_query(query, fetch_all=True)
        
        # Convert dates to strings and decimals to floats
        for drive in drives:
            if drive.get('drive_date'):
                drive['drive_date'] = drive['drive_date'].strftime('%Y-%m-%d')
            if drive.get('deadline'):
                drive['deadline'] = drive['deadline'].strftime('%Y-%m-%d')
            if drive.get('min_cgpa_required'):
                drive['min_cgpa_required'] = float(drive['min_cgpa_required'])
        
        return jsonify(drives), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch drives', 'details': str(e)}), 500

@application_bp.route('/drives/<int:drive_id>', methods=['GET'])
@token_required
def get_drive_details(current_user, drive_id):
    """Get detailed information about a specific drive"""
    try:
        query = """
            SELECT 
                pd.*,
                c.name as company_name,
                c.location as company_location,
                c.industry,
                c.website,
                c.hr_contact
            FROM placement_drive pd
            JOIN company c ON pd.company_id = c.company_id
            WHERE pd.drive_id = %s
        """
        drive = execute_query(query, (drive_id,), fetch_one=True)
        
        if not drive:
            return jsonify({'error': 'Drive not found'}), 404
        
        # Get job roles for this company
        roles_query = """
            SELECT job_id, role_name, min_cgpa, job_type, salary_range, description
            FROM job_role
            WHERE company_id = %s
        """
        roles = execute_query(roles_query, (drive['company_id'],), fetch_all=True)
        
        # Convert dates and decimals
        if drive.get('drive_date'):
            drive['drive_date'] = drive['drive_date'].strftime('%Y-%m-%d')
        if drive.get('deadline'):
            drive['deadline'] = drive['deadline'].strftime('%Y-%m-%d')
        
        for role in roles:
            if role.get('min_cgpa'):
                role['min_cgpa'] = float(role['min_cgpa'])
        
        drive['job_roles'] = roles
        
        return jsonify(drive), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch drive details', 'details': str(e)}), 500

@application_bp.route('/apply', methods=['POST'])
@token_required
def apply_to_drive(current_user):
    """
    Apply to a placement drive using stored procedure
    
    Request Body:
    {
        "drive_id": 1
    }
    """
    try:
        student_id = current_user['user_id']
        data = request.json
        
        if not data.get('drive_id'):
            return jsonify({'error': 'drive_id is required'}), 400
        
        drive_id = data['drive_id']
        
        # Check eligibility first
        check_query = "SELECT IsEligible(%s, %s) as eligible"
        result = execute_query(check_query, (student_id, drive_id), fetch_one=True)
        
        if not result['eligible']:
            return jsonify({'error': 'You are not eligible for this drive (CGPA requirement not met)'}), 400
        
        # Call stored procedure to enroll
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Prepare OUT parameter
                cursor.execute("SET @message = ''")
                
                # Call procedure
                cursor.callproc('EnrollStudent', (student_id, drive_id, 0))
                
                # Get OUT parameter value
                cursor.execute("SELECT @_EnrollStudent_2 as message")
                result = cursor.fetchone()
                message = result['message']
                
                connection.commit()
                
                if 'SUCCESS' in message:
                    return jsonify({'message': message}), 201
                else:
                    return jsonify({'error': message}), 400
                    
        finally:
            connection.close()
        
    except Exception as e:
        return jsonify({'error': 'Failed to apply', 'details': str(e)}), 500

@application_bp.route('/my-applications', methods=['GET'])
@token_required
def get_my_applications(current_user):
    """Get all applications for current student"""
    try:
        student_id = current_user['user_id']
        
        query = """
            SELECT 
                a.application_id,
                a.drive_id,
                a.status,
                a.applied_at,
                pd.drive_date,
                pd.mode,
                pd.deadline,
                c.company_id,
                c.name as company_name,
                c.industry,
                o.offer_id,
                o.salary,
                o.status as offer_status,
                o.joining_date
            FROM application a
            JOIN placement_drive pd ON a.drive_id = pd.drive_id
            JOIN company c ON pd.company_id = c.company_id
            LEFT JOIN offer o ON a.application_id = o.application_id
            WHERE a.student_id = %s
            ORDER BY a.applied_at DESC
        """
        
        applications = execute_query(query, (student_id,), fetch_all=True)
        
        # Convert dates and decimals
        for app in applications:
            if app.get('applied_at'):
                app['applied_at'] = app['applied_at'].strftime('%Y-%m-%d %H:%M:%S')
            if app.get('drive_date'):
                app['drive_date'] = app['drive_date'].strftime('%Y-%m-%d')
            if app.get('deadline'):
                app['deadline'] = app['deadline'].strftime('%Y-%m-%d')
            if app.get('joining_date'):
                app['joining_date'] = app['joining_date'].strftime('%Y-%m-%d')
            if app.get('salary'):
                app['salary'] = float(app['salary'])
        
        return jsonify(applications), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch applications', 'details': str(e)}), 500

@application_bp.route('/applications/<int:application_id>', methods=['GET'])
@token_required
def get_application_details(current_user, application_id):
    """Get detailed information about an application including interview rounds"""
    try:
        # Get application details
        app_query = """
            SELECT 
                a.*,
                pd.drive_date,
                pd.mode,
                c.name as company_name,
                c.industry,
                s.name as student_name,
                s.email,
                s.department,
                s.cgpa,
                o.salary,
                o.status as offer_status,
                o.joining_date
            FROM application a
            JOIN placement_drive pd ON a.drive_id = pd.drive_id
            JOIN company c ON pd.company_id = c.company_id
            JOIN student s ON a.student_id = s.student_id
            LEFT JOIN offer o ON a.application_id = o.application_id
            WHERE a.application_id = %s
        """
        
        application = execute_query(app_query, (application_id,), fetch_one=True)
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check if user has access
        if current_user['user_type'] == 'Student' and application['student_id'] != current_user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get interview rounds
        rounds_query = """
            SELECT round_id, round_number, round_type, result, feedback, interview_date
            FROM interview_round
            WHERE application_id = %s
            ORDER BY round_number
        """
        rounds = execute_query(rounds_query, (application_id,), fetch_all=True)
        
        # Convert dates and decimals
        if application.get('applied_at'):
            application['applied_at'] = application['applied_at'].strftime('%Y-%m-%d %H:%M:%S')
        if application.get('drive_date'):
            application['drive_date'] = application['drive_date'].strftime('%Y-%m-%d')
        if application.get('joining_date'):
            application['joining_date'] = application['joining_date'].strftime('%Y-%m-%d')
        if application.get('cgpa'):
            application['cgpa'] = float(application['cgpa'])
        if application.get('salary'):
            application['salary'] = float(application['salary'])
        
        for round in rounds:
            if round.get('interview_date'):
                round['interview_date'] = round['interview_date'].strftime('%Y-%m-%d')
        
        application['interview_rounds'] = rounds
        
        return jsonify(application), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch application details', 'details': str(e)}), 500

@application_bp.route('/offers/<int:offer_id>/accept', methods=['POST'])
@token_required
def accept_offer(current_user, offer_id):
    """Accept a job offer"""
    try:
        student_id = current_user['user_id']
        
        # Verify offer belongs to student
        verify_query = """
            SELECT o.* 
            FROM offer o
            JOIN application a ON o.application_id = a.application_id
            WHERE o.offer_id = %s AND a.student_id = %s
        """
        offer = execute_query(verify_query, (offer_id, student_id), fetch_one=True)
        
        if not offer:
            return jsonify({'error': 'Offer not found or access denied'}), 404
        
        if offer['status'] == 'Accepted':
            return jsonify({'error': 'Offer already accepted'}), 400
        
        # Update offer status
        update_query = "UPDATE offer SET status = 'Accepted' WHERE offer_id = %s"
        execute_query(update_query, (offer_id,))
        
        return jsonify({'message': 'Offer accepted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to accept offer', 'details': str(e)}), 500

@application_bp.route('/offers/<int:offer_id>/reject', methods=['POST'])
@token_required
def reject_offer(current_user, offer_id):
    """Reject a job offer"""
    try:
        student_id = current_user['user_id']
        
        # Verify offer belongs to student
        verify_query = """
            SELECT o.* 
            FROM offer o
            JOIN application a ON o.application_id = a.application_id
            WHERE o.offer_id = %s AND a.student_id = %s
        """
        offer = execute_query(verify_query, (offer_id, student_id), fetch_one=True)
        
        if not offer:
            return jsonify({'error': 'Offer not found or access denied'}), 404
        
        if offer['status'] == 'Rejected':
            return jsonify({'error': 'Offer already rejected'}), 400
        
        # Update offer status
        update_query = "UPDATE offer SET status = 'Rejected' WHERE offer_id = %s"
        execute_query(update_query, (offer_id,))
        
        return jsonify({'message': 'Offer rejected successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to reject offer', 'details': str(e)}), 500

@application_bp.route('/check-eligibility/<int:drive_id>', methods=['GET'])
@token_required
def check_eligibility(current_user, drive_id):
    """Check if student is eligible for a drive"""
    try:
        student_id = current_user['user_id']
        
        query = "SELECT IsEligible(%s, %s) as eligible"
        result = execute_query(query, (student_id, drive_id), fetch_one=True)
        
        # Get student CGPA
        cgpa_query = "SELECT cgpa FROM student WHERE student_id = %s"
        student = execute_query(cgpa_query, (student_id,), fetch_one=True)
        
        # Get required CGPA
        req_query = """
            SELECT MIN(jr.min_cgpa) as required_cgpa
            FROM job_role jr
            JOIN placement_drive pd ON jr.company_id = pd.company_id
            WHERE pd.drive_id = %s
        """
        requirement = execute_query(req_query, (drive_id,), fetch_one=True)
        
        return jsonify({
            'eligible': bool(result['eligible']),
            'student_cgpa': float(student['cgpa']) if student else None,
            'required_cgpa': float(requirement['required_cgpa']) if requirement and requirement['required_cgpa'] else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to check eligibility', 'details': str(e)}), 500