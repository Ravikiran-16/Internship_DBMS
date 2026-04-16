from flask import Blueprint, request, jsonify
from utils.db import execute_query, call_procedure
from utils.auth_middleware import token_required
import os
from werkzeug.utils import secure_filename
from config import Config

student_bp = Blueprint('student', __name__)

@student_bp.route('/profile', methods=['GET'])
@token_required
def get_my_profile(current_user):
    """Get current student's profile"""
    try:
        student_id = current_user['user_id']
        
        query = """
            SELECT student_id, name, email, phone, department, cgpa, backlogs, resume, created_at
            FROM student WHERE student_id = %s
        """
        student = execute_query(query, (student_id,), fetch_one=True)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Get skills
        skills_query = """
            SELECT s.skill_id, s.skill_name, s.category, ss.proficiency_level
            FROM student_skill ss
            JOIN skill s ON ss.skill_id = s.skill_id
            WHERE ss.student_id = %s
        """
        skills = execute_query(skills_query, (student_id,), fetch_all=True)
        
        # Get placement status
        status_query = "SELECT GetPlacementStatus(%s) as status"
        status_result = execute_query(status_query, (student_id,), fetch_one=True)
        
        student['skills'] = skills or []
        student['placement_status'] = status_result['status'] if status_result else 'Not Applied'
        student['cgpa'] = float(student['cgpa'])
        
        return jsonify(student), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch profile', 'details': str(e)}), 500

@student_bp.route('/profile/<int:student_id>', methods=['GET'])
@token_required
def get_student_profile(current_user, student_id):
    """Get any student's profile (for admin)"""
    try:
        query = """
            SELECT student_id, name, email, phone, department, cgpa, backlogs, resume, created_at
            FROM student WHERE student_id = %s
        """
        student = execute_query(query, (student_id,), fetch_one=True)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        student['cgpa'] = float(student['cgpa'])
        return jsonify(student), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch profile', 'details': str(e)}), 500

@student_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """
    Update student profile
    
    Request Body:
    {
        "phone": "9876543210",
        "cgpa": 8.7,
        "backlogs": 0
    }
    """
    try:
        student_id = current_user['user_id']
        data = request.json
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if 'phone' in data:
            update_fields.append("phone = %s")
            params.append(data['phone'])
        
        if 'cgpa' in data:
            update_fields.append("cgpa = %s")
            params.append(data['cgpa'])
        
        if 'backlogs' in data:
            update_fields.append("backlogs = %s")
            params.append(data['backlogs'])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(student_id)
        
        query = f"UPDATE student SET {', '.join(update_fields)} WHERE student_id = %s"
        execute_query(query, tuple(params))
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@student_bp.route('/skills', methods=['GET'])
@token_required
def get_my_skills(current_user):
    """Get current student's skills"""
    try:
        student_id = current_user['user_id']
        
        query = """
            SELECT s.skill_id, s.skill_name, s.category, ss.proficiency_level
            FROM student_skill ss
            JOIN skill s ON ss.skill_id = s.skill_id
            WHERE ss.student_id = %s
            ORDER BY s.skill_name
        """
        skills = execute_query(query, (student_id,), fetch_all=True)
        
        return jsonify(skills or []), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch skills', 'details': str(e)}), 500

@student_bp.route('/skills', methods=['POST'])
@token_required
def add_skill(current_user):
    """
    Add skill to student
    
    Request Body:
    {
        "skill_name": "Python",
        "category": "Programming",
        "proficiency_level": "Advanced"
    }
    """
    try:
        student_id = current_user['user_id']
        data = request.json
        
        if not data.get('skill_name'):
            return jsonify({'error': 'Skill name is required'}), 400
        
        # First, ensure skill exists in skill table
        skill_query = "INSERT IGNORE INTO skill (skill_name, category) VALUES (%s, %s)"
        execute_query(skill_query, (data['skill_name'], data.get('category')))
        
        # Get skill_id
        get_skill = "SELECT skill_id FROM skill WHERE skill_name = %s"
        skill = execute_query(get_skill, (data['skill_name'],), fetch_one=True)
        
        if not skill:
            return jsonify({'error': 'Failed to create skill'}), 500
        
        # Link skill to student
        link_query = """
            INSERT INTO student_skill (student_id, skill_id, proficiency_level) 
            VALUES (%s, %s, %s)
        """
        
        execute_query(link_query, (
            student_id, 
            skill['skill_id'],
            data.get('proficiency_level', 'Intermediate')
        ))
        
        return jsonify({'message': 'Skill added successfully'}), 201
        
    except Exception as e:
        error_msg = str(e)
        if 'Duplicate entry' in error_msg:
            return jsonify({'error': 'Skill already exists for this student'}), 400
        return jsonify({'error': 'Failed to add skill', 'details': error_msg}), 500

@student_bp.route('/skills/<int:skill_id>', methods=['DELETE'])
@token_required
def remove_skill(current_user, skill_id):
    """Remove skill from student"""
    try:
        student_id = current_user['user_id']
        
        query = "DELETE FROM student_skill WHERE student_id = %s AND skill_id = %s"
        execute_query(query, (student_id, skill_id))
        
        return jsonify({'message': 'Skill removed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to remove skill', 'details': str(e)}), 500

@student_bp.route('/report', methods=['GET'])
@token_required
def get_student_report(current_user):
    """
    Get comprehensive student report using stored procedure
    """
    try:
        student_id = current_user['user_id']
        
        # Call stored procedure
        results = call_procedure('GetStudentReport', [student_id])
        
        if not results:
            return jsonify({'error': 'No data found'}), 404
        
        # Parse results (procedure returns 3 result sets)
        report = {}
        
        if len(results) >= 1 and results[0]:
            # Basic info
            report['student'] = results[0][0]
            if 'cgpa' in report['student']:
                report['student']['cgpa'] = float(report['student']['cgpa'])
        
        if len(results) >= 2:
            # Skills
            report['skills'] = results[1] if results[1] else []
        
        if len(results) >= 3:
            # Applications
            report['applications'] = results[2] if results[2] else []
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate report', 'details': str(e)}), 500

@student_bp.route('/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """Get statistics for student dashboard"""
    try:
        student_id = current_user['user_id']
        
        stats = {}
        
        # Total applications
        app_query = "SELECT COUNT(*) as count FROM application WHERE student_id = %s"
        app_result = execute_query(app_query, (student_id,), fetch_one=True)
        stats['total_applications'] = app_result['count']
        
        # Applications by status
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM application 
            WHERE student_id = %s 
            GROUP BY status
        """
        status_results = execute_query(status_query, (student_id,), fetch_all=True)
        stats['applications_by_status'] = {item['status']: item['count'] for item in status_results}
        
        # Total skills
        skill_query = "SELECT COUNT(*) as count FROM student_skill WHERE student_id = %s"
        skill_result = execute_query(skill_query, (student_id,), fetch_one=True)
        stats['total_skills'] = skill_result['count']
        
        # Offers
        offer_query = """
            SELECT COUNT(*) as count 
            FROM offer o
            JOIN application a ON o.application_id = a.application_id
            WHERE a.student_id = %s
        """
        offer_result = execute_query(offer_query, (student_id,), fetch_one=True)
        stats['total_offers'] = offer_result['count']
        
        # Placement status
        status = execute_query(
            "SELECT GetPlacementStatus(%s) as status", 
            (student_id,), 
            fetch_one=True
        )
        stats['placement_status'] = status['status'] if status else 'Not Applied'
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats', 'details': str(e)}), 500

@student_bp.route('/upload-resume', methods=['POST'])
@token_required
def upload_resume(current_user):
    """Upload student resume"""
    try:
        student_id = current_user['user_id']
        
        if 'resume' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        if '.' not in file.filename:
            return jsonify({'error': 'Invalid file'}), 400
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in Config.ALLOWED_EXTENSIONS:
            return jsonify({'error': f'Only {", ".join(Config.ALLOWED_EXTENSIONS)} files allowed'}), 400
        
        # Create upload directory if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Save file with secure filename
        filename = secure_filename(f"student_{student_id}_resume.{ext}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Update database
        query = "UPDATE student SET resume = %s WHERE student_id = %s"
        execute_query(query, (filename, student_id))
        
        return jsonify({
            'message': 'Resume uploaded successfully',
            'filename': filename
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to upload resume', 'details': str(e)}), 500