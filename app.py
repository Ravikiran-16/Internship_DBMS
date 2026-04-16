from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from utils.db import test_connection
import os

# Import blueprints
from routes.auth import auth_bp
from routes.student import student_bp
from routes.application_routes import application_bp
from routes.admin_routes import admin_bp
# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Create upload directory if it doesn't exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(student_bp, url_prefix='/api/students')
app.register_blueprint(application_bp, url_prefix='/api/applications')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# ============================================================================
# ROOT ROUTES
# ============================================================================

@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'message': 'Placement Management System API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth',
            'students': '/api/students',
            'applications': '/api/applications',
            'admin': '/api/admin'
        }
    }), 200

@app.route('/health')
def health_check():
    """Health check endpoint"""
    db_status, db_message = test_connection()
    
    return jsonify({
        'status': 'healthy' if db_status else 'unhealthy',
        'database': db_message,
        'api': 'running'
    }), 200 if db_status else 500

@app.route('/api')
def api_info():
    """API information"""
    return jsonify({
        'api': 'Placement Management System',
        'version': '1.0.0',
        'available_endpoints': {
            'Authentication': {
                'POST /api/auth/register': 'Register new student',
                'POST /api/auth/login': 'Student login',
                'POST /api/auth/admin/login': 'Admin/TPO login',
                'GET /api/auth/verify': 'Verify token'
            },
            'Student': {
                'GET /api/students/profile': 'Get student profile',
                'PUT /api/students/profile': 'Update profile',
                'GET /api/students/skills': 'Get skills',
                'POST /api/students/skills': 'Add skill',
                'DELETE /api/students/skills/<id>': 'Remove skill',
                'GET /api/students/report': 'Get student report',
                'GET /api/students/dashboard/stats': 'Get dashboard stats',
                'POST /api/students/upload-resume': 'Upload resume'
            },
            'Applications': {
                'GET /api/applications/drives': 'Get all drives',
                'GET /api/applications/drives/<id>': 'Get drive details',
                'POST /api/applications/apply': 'Apply to drive',
                'GET /api/applications/my-applications': 'Get my applications',
                'GET /api/applications/applications/<id>': 'Get application details',
                'POST /api/applications/offers/<id>/accept': 'Accept offer',
                'POST /api/applications/offers/<id>/reject': 'Reject offer',
                'GET /api/applications/check-eligibility/<drive_id>': 'Check eligibility'
            },
            'Admin': {
                'GET /api/admin/companies': 'Get companies',
                'POST /api/admin/companies': 'Add company',
                'PUT /api/admin/companies/<id>': 'Update company',
                'POST /api/admin/job-roles': 'Add job role',
                'POST /api/admin/drives': 'Create drive',
                'PUT /api/admin/drives/<id>': 'Update drive',
                'GET /api/admin/applications': 'Get all applications',
                'PUT /api/admin/applications/<id>/status': 'Update application status',
                'POST /api/admin/offers': 'Create offer',
                'GET /api/admin/reports/placement-summary': 'Placement summary',
                'GET /api/admin/reports/drive-stats': 'Drive statistics',
                'GET /api/admin/reports/student-skills': 'Student skills report',
                'GET /api/admin/dashboard/stats': 'Admin dashboard stats',
                'GET /api/admin/students': 'Get all students'
            }
        }
    }), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return jsonify({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource'
    }), 403

@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 errors"""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Placement Management System API")
    print("=" * 60)
    
    # Test database connection
    db_status, db_message = test_connection()
    if db_status:
        print(f"✅ {db_message}")
    else:
        print(f"❌ {db_message}")
        print("⚠️  Please check your database configuration in .env file")
    
    print(f"📍 Server running on: http://{Config.HOST}:{Config.PORT}")
    print(f"🔧 Debug mode: {Config.DEBUG}")
    print(f"📚 API Documentation: http://{Config.HOST}:{Config.PORT}/api")
    print("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )