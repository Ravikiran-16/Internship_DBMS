from flask import Blueprint, request, jsonify
import bcrypt
import jwt
from datetime import datetime, timedelta
from utils.db import execute_query
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_student():
    """
    Register a new student
    
    Request Body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "phone": "1234567890",
        "department": "Computer Science",
        "cgpa": 8.5,
        "backlogs": 0
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'department', 'cgpa']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(
            data['password'].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Insert student
        query = """
            INSERT INTO student (name, email, phone, department, cgpa, backlogs, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        student_id = execute_query(query, (
            data['name'],
            data['email'],
            data.get('phone'),
            data['department'],
            data['cgpa'],
            data.get('backlogs', 0),
            hashed_password
        ))
        
        return jsonify({
            'message': 'Registration successful',
            'student_id': student_id
        }), 201
        
    except Exception as e:
        error_msg = str(e)
        if 'Duplicate entry' in error_msg:
            if 'email' in error_msg:
                return jsonify({'error': 'Email already registered'}), 400
            elif 'phone' in error_msg:
                return jsonify({'error': 'Phone number already registered'}), 400
        return jsonify({'error': 'Registration failed', 'details': error_msg}), 500

@auth_bp.route('/login', methods=['POST'])
def login_student():
    """
    Student login
    
    Request Body:
    {
        "email": "john@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.json
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Get student from database
        query = "SELECT * FROM student WHERE email = %s"
        student = execute_query(query, (data['email'],), fetch_one=True)
        
        if not student:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if bcrypt.checkpw(data['password'].encode('utf-8'), student['password'].encode('utf-8')):
            # Generate JWT token
            token_data = {
                'user_id': student['student_id'],
                'email': student['email'],
                'user_type': 'Student',
                'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
            }
            
            token = jwt.encode(token_data, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
            
            # Remove password from response
            student.pop('password', None)
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': student['student_id'],
                    'name': student['name'],
                    'email': student['email'],
                    'department': student['department'],
                    'cgpa': float(student['cgpa'])
                }
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/admin/login', methods=['POST'])
def login_admin():
    """
    Admin/TPO login
    
    Request Body:
    {
        "email": "tpo@university.edu",
        "password": "admin123"
    }
    """
    try:
        data = request.json
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Get admin from database
        query = "SELECT * FROM admin_user WHERE email = %s"
        admin = execute_query(query, (data['email'],), fetch_one=True)
        
        if not admin:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if bcrypt.checkpw(data['password'].encode('utf-8'), admin['password'].encode('utf-8')):
            # Generate JWT token
            token_data = {
                'user_id': admin['admin_id'],
                'email': admin['email'],
                'role': admin['role'],
                'user_type': 'Admin',
                'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
            }
            
            token = jwt.encode(token_data, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
            
            # Remove password from response
            admin.pop('password', None)
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': admin['admin_id'],
                    'name': admin['name'],
                    'email': admin['email'],
                    'role': admin['role']
                }
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify JWT token validity
    
    Headers:
        Authorization: Bearer <token>
    """
    token = None
    
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(" ")[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify({'error': 'Invalid token format'}), 401
    
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    try:
        data = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        return jsonify({
            'valid': True,
            'user': {
                'id': data.get('user_id'),
                'email': data.get('email'),
                'type': data.get('user_type')
            }
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 401