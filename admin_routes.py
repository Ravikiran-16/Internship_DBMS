from flask import Blueprint, request, jsonify
from utils.db import execute_query, get_db_connection
from utils.auth_middleware import admin_required
import bcrypt

admin_bp = Blueprint('admin', __name__)

# ============================================================================
# COMPANY MANAGEMENT
# ============================================================================

@admin_bp.route('/companies', methods=['GET'])
@admin_required
def get_all_companies(current_user):
    """Get all companies"""
    try:
        query = "SELECT * FROM company ORDER BY name"
        companies = execute_query(query, fetch_all=True)
        
        for company in companies:
            if company.get('created_at'):
                company['created_at'] = company['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(companies), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch companies', 'details': str(e)}), 500

@admin_bp.route('/companies', methods=['POST'])
@admin_required
def add_company(current_user):
    """
    Add a new company
    
    Request Body:
    {
        "name": "Google",
        "location": "Bangalore",
        "industry": "Technology",
        "website": "www.google.com",
        "hr_contact": "hr@google.com"
    }
    """
    try:
        data = request.json
        
        if not data.get('name'):
            return jsonify({'error': 'Company name is required'}), 400
        
        query = """
            INSERT INTO company (name, location, industry, website, hr_contact)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        company_id = execute_query(query, (
            data['name'],
            data.get('location'),
            data.get('industry'),
            data.get('website'),
            data.get('hr_contact')
        ))
        
        return jsonify({
            'message': 'Company added successfully',
            'company_id': company_id
        }), 201
        
    except Exception as e:
        if 'Duplicate entry' in str(e):
            return jsonify({'error': 'Company already exists'}), 400
        return jsonify({'error': 'Failed to add company', 'details': str(e)}), 500

@admin_bp.route('/companies/<int:company_id>', methods=['PUT'])
@admin_required
def update_company(current_user, company_id):
    """Update company details"""
    try:
        data = request.json
        
        update_fields = []
        params = []
        
        for field in ['name', 'location', 'industry', 'website', 'hr_contact']:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(company_id)
        query = f"UPDATE company SET {', '.join(update_fields)} WHERE company_id = %s"
        execute_query(query, tuple(params))
        
        return jsonify({'message': 'Company updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update company', 'details': str(e)}), 500

# ============================================================================
# JOB ROLE MANAGEMENT
# ============================================================================

@admin_bp.route('/job-roles', methods=['POST'])
@admin_required
def add_job_role(current_user):
    """
    Add job role for a company
    
    Request Body:
    {
        "company_id": 1,
        "role_name": "Software Engineer",
        "min_cgpa": 7.5,
        "job_type": "Full-time",
        "salary_range": "10-15 LPA",
        "description": "Full stack development role"
    }
    """
    try:
        data = request.json
        
        required = ['company_id', 'role_name', 'min_cgpa', 'job_type']
        for field in required:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        query = """
            INSERT INTO job_role (company_id, role_name, min_cgpa, job_type, salary_range, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        job_id = execute_query(query, (
            data['company_id'],
            data['role_name'],
            data['min_cgpa'],
            data['job_type'],
            data.get('salary_range'),
            data.get('description')
        ))
        
        return jsonify({
            'message': 'Job role added successfully',
            'job_id': job_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to add job role', 'details': str(e)}), 500

# ============================================================================
# PLACEMENT DRIVE MANAGEMENT
# ============================================================================

@admin_bp.route('/drives', methods=['POST'])
@admin_required
def create_drive(current_user):
    """
    Create a new placement drive
    
    Request Body:
    {
        "company_id": 1,
        "drive_date": "2026-05-15",
        "mode": "Online",
        "deadline": "2026-05-10",
        "venue": "Main Campus"
    }
    """
    try:
        data = request.json
        
        required = ['company_id', 'drive_date', 'mode', 'deadline']
        for field in required:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        query = """
            INSERT INTO placement_drive (company_id, drive_date, mode, deadline, venue)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        drive_id = execute_query(query, (
            data['company_id'],
            data['drive_date'],
            data['mode'],
            data['deadline'],
            data.get('venue')
        ))
        
        return jsonify({
            'message': 'Placement drive created successfully',
            'drive_id': drive_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create drive', 'details': str(e)}), 500

@admin_bp.route('/drives/<int:drive_id>', methods=['PUT'])
@admin_required
def update_drive(current_user, drive_id):
    """Update placement drive details"""
    try:
        data = request.json
        
        update_fields = []
        params = []
        
        for field in ['drive_date', 'mode', 'deadline', 'venue']:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(drive_id)
        query = f"UPDATE placement_drive SET {', '.join(update_fields)} WHERE drive_id = %s"
        execute_query(query, tuple(params))
        
        return jsonify({'message': 'Drive updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update drive', 'details': str(e)}), 500

# ============================================================================
# APPLICATION MANAGEMENT
# ============================================================================

@admin_bp.route('/applications', methods=['GET'])
@admin_required
def get_all_applications(current_user):
    """Get all applications with filters"""
    try:
        # Query parameters
        drive_id = request.args.get('drive_id')
        status = request.args.get('status')
        
        query = """
            SELECT 
                a.*,
                s.name as student_name,
                s.email,
                s.department,
                s.cgpa,
                c.name as company_name,
                pd.drive_date
            FROM application a
            JOIN student s ON a.student_id = s.student_id
            JOIN placement_drive pd ON a.drive_id = pd.drive_id
            JOIN company c ON pd.company_id = c.company_id
            WHERE 1=1
        """
        
        params = []
        
        if drive_id:
            query += " AND a.drive_id = %s"
            params.append(drive_id)
        
        if status:
            query += " AND a.status = %s"
            params.append(status)
        
        query += " ORDER BY a.applied_at DESC"
        
        applications = execute_query(query, tuple(params) if params else None, fetch_all=True)
        
        for app in applications:
            if app.get('applied_at'):
                app['applied_at'] = app['applied_at'].strftime('%Y-%m-%d %H:%M:%S')
            if app.get('drive_date'):
                app['drive_date'] = app['drive_date'].strftime('%Y-%m-%d')
            if app.get('cgpa'):
                app['cgpa'] = float(app['cgpa'])
        
        return jsonify(applications), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch applications', 'details': str(e)}), 500

@admin_bp.route('/applications/<int:application_id>/status', methods=['PUT'])
@admin_required
def update_application_status(current_user, application_id):
    """
    Update application status and optionally add interview round
    
    Request Body:
    {
        "status": "Shortlisted",
        "round_number": 1,
        "round_type": "Technical",
        "result": "Pass",
        "feedback": "Good technical skills"
    }
    """
    try:
        data = request.json
        
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.callproc('UpdateApplicationStatus', (
                    application_id,
                    data['status'],
                    data.get('round_number'),
                    data.get('result'),
                    data.get('feedback')
                ))
                connection.commit()
            
            return jsonify({'message': 'Application status updated successfully'}), 200
        finally:
            connection.close()
        
    except Exception as e:
        return jsonify({'error': 'Failed to update status', 'details': str(e)}), 500

# ============================================================================
# OFFER MANAGEMENT
# ============================================================================

@admin_bp.route('/offers', methods=['POST'])
@admin_required
def create_offer(current_user):
    """
    Create job offer
    
    Request Body:
    {
        "application_id": 1,
        "salary": 1200000.00,
        "joining_date": "2026-07-01",
        "response_deadline": "2026-06-01"
    }
    """
    try:
        data = request.json
        
        if not data.get('application_id'):
            return jsonify({'error': 'application_id is required'}), 400
        
        query = """
            INSERT INTO offer (application_id, salary, joining_date, response_deadline, status)
            VALUES (%s, %s, %s, %s, 'Pending')
        """
        
        offer_id = execute_query(query, (
            data['application_id'],
            data.get('salary'),
            data.get('joining_date'),
            data.get('response_deadline')
        ))
        
        return jsonify({
            'message': 'Offer created successfully',
            'offer_id': offer_id
        }), 201
        
    except Exception as e:
        if 'Duplicate entry' in str(e):
            return jsonify({'error': 'Offer already exists for this application'}), 400
        return jsonify({'error': 'Failed to create offer', 'details': str(e)}), 500

# ============================================================================
# REPORTS & ANALYTICS
# ============================================================================

@admin_bp.route('/reports/placement-summary', methods=['GET'])
@admin_required
def get_placement_summary(current_user):
    """Get placement summary from view"""
    try:
        query = "SELECT * FROM vw_placement_summary"
        summary = execute_query(query, fetch_all=True)
        
        for row in summary:
            if row.get('cgpa'):
                row['cgpa'] = float(row['cgpa'])
            if row.get('Offered_Salary'):
                row['Offered_Salary'] = float(row['Offered_Salary'])
        
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': 'Failed to generate report', 'details': str(e)}), 500

@admin_bp.route('/reports/drive-stats', methods=['GET'])
@admin_required
def get_drive_stats(current_user):
    """Get drive statistics from view"""
    try:
        query = "SELECT * FROM vw_drive_stats"
        stats = execute_query(query, fetch_all=True)
        
        for row in stats:
            if row.get('drive_date'):
                row['drive_date'] = row['drive_date'].strftime('%Y-%m-%d')
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': 'Failed to generate stats', 'details': str(e)}), 500

@admin_bp.route('/reports/student-skills', methods=['GET'])
@admin_required
def get_student_skills_report(current_user):
    """Get student skills report from view"""
    try:
        query = "SELECT * FROM vw_student_skills"
        skills = execute_query(query, fetch_all=True)
        return jsonify(skills), 200
    except Exception as e:
        return jsonify({'error': 'Failed to generate report', 'details': str(e)}), 500

@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_admin_dashboard_stats(current_user):
    """Get comprehensive dashboard statistics"""
    try:
        stats = {}
        
        # Total students
        stats['total_students'] = execute_query(
            "SELECT COUNT(*) as count FROM student", fetch_one=True
        )['count']
        
        # Total companies
        stats['total_companies'] = execute_query(
            "SELECT COUNT(*) as count FROM company", fetch_one=True
        )['count']
        
        # Total drives
        stats['total_drives'] = execute_query(
            "SELECT COUNT(*) as count FROM placement_drive", fetch_one=True
        )['count']
        
        # Total applications
        stats['total_applications'] = execute_query(
            "SELECT COUNT(*) as count FROM application", fetch_one=True
        )['count']
        
        # Students placed
        stats['students_placed'] = execute_query(
            """SELECT COUNT(DISTINCT a.student_id) as count 
               FROM application a 
               JOIN offer o ON a.application_id = o.application_id 
               WHERE o.status = 'Accepted'""",
            fetch_one=True
        )['count']
        
        # Applications by status
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM application 
            GROUP BY status
        """
        status_results = execute_query(status_query, fetch_all=True)
        stats['applications_by_status'] = {item['status']: item['count'] for item in status_results}
        
        # Department-wise placement
        dept_query = """
            SELECT s.department, COUNT(DISTINCT s.student_id) as placed_count
            FROM student s
            JOIN application a ON s.student_id = a.student_id
            JOIN offer o ON a.application_id = o.application_id
            WHERE o.status = 'Accepted'
            GROUP BY s.department
        """
        dept_results = execute_query(dept_query, fetch_all=True)
        stats['department_wise_placement'] = dept_results
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats', 'details': str(e)}), 500

# ============================================================================
# STUDENT MANAGEMENT
# ============================================================================

@admin_bp.route('/students', methods=['GET'])
@admin_required
def get_all_students(current_user):
    """Get all students"""
    try:
        query = """
            SELECT student_id, name, email, phone, department, cgpa, backlogs, created_at
            FROM student
            ORDER BY name
        """
        students = execute_query(query, fetch_all=True)
        
        for student in students:
            if student.get('cgpa'):
                student['cgpa'] = float(student['cgpa'])
            if student.get('created_at'):
                student['created_at'] = student['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(students), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch students', 'details': str(e)}), 500