"""
PlacementHub Frontend - Flask + Jinja2
Connects to the existing backend API
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'frontend-secret-key')

# ============================================================
# CONFIG — point this to your backend
# ============================================================
API_BASE = os.getenv('API_BASE', 'http://localhost:5000/api')

# ============================================================
# HELPERS
# ============================================================

def api(method, path, data=None, token=None, files=None):
    """Make a request to the backend API."""
    url = f"{API_BASE}{path}"
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, params=data, timeout=10)
        elif method == 'POST':
            if files:
                r = requests.post(url, headers=headers, data=data, files=files, timeout=10)
            else:
                headers['Content-Type'] = 'application/json'
                r = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PUT':
            headers['Content-Type'] = 'application/json'
            r = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == 'DELETE':
            r = requests.delete(url, headers=headers, timeout=10)
        else:
            return None, 'Invalid method'

        # ✅ FIX: Check HTTP status BEFORE returning JSON.
        # Previously, error responses like 401 {"error": "..."} were returned
        # as successful data, causing KeyError when code tried to slice a dict.
        if r.ok:
            try:
                return r.json(), None
            except Exception:
                return None, f"Server returned status {r.status_code}"
        else:
            try:
                error_data = r.json()
                msg = error_data.get('error') or error_data.get('message') or f"Request failed ({r.status_code})"
            except Exception:
                msg = f"Request failed with status {r.status_code}"
            # If 401, clear the session token so the user gets redirected to login
            if r.status_code == 401:
                from flask import session as _session
                _session.pop('token', None)
            return None, msg

    except requests.exceptions.ConnectionError:
        return None, 'Cannot connect to backend. Make sure the API server is running.'
    except requests.exceptions.Timeout:
        return None, 'Request timed out.'
    except Exception as e:
        return None, str(e)


def get_token():
    return session.get('token')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('token'):
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('token'):
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        if session.get('user_type') != 'Admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# AUTH ROUTES
# ============================================================

@app.route('/')
def index():
    if session.get('token'):
        if session.get('user_type') == 'Admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('token'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'student')

        endpoint = '/auth/admin/login' if user_type == 'admin' else '/auth/login'
        data, err = api('POST', endpoint, {'email': email, 'password': password})

        if err:
            return render_template('auth/login.html', error=err)

        if data and 'token' in data:
            session['token'] = data['token']
            session['user_type'] = data['user']['type'] if 'type' in data['user'] else ('Admin' if user_type == 'admin' else 'Student')
            session['user_name'] = data['user'].get('name', '')
            session['user_id'] = data['user'].get('id')
            session['user_role'] = data['user'].get('role', 'TPO')

            flash(f"Welcome back, {data['user'].get('name', '')}!", 'success')

            if session['user_type'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))

        error = data.get('error', 'Login failed') if data else 'Login failed'
        return render_template('auth/login.html', error=error)

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        payload = {
            'name': form_data.get('name'),
            'email': form_data.get('email'),
            'password': form_data.get('password'),
            'phone': form_data.get('phone'),
            'department': form_data.get('department'),
            'cgpa': float(form_data.get('cgpa', 0)),
            'backlogs': int(form_data.get('backlogs', 0))
        }

        data, err = api('POST', '/auth/register', payload)

        if err:
            return render_template('auth/register.html', error=err, form_data=form_data)

        if data and 'student_id' in data:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        error = data.get('error', 'Registration failed') if data else 'Registration failed'
        return render_template('auth/register.html', error=error, form_data=form_data)

    return render_template('auth/register.html', form_data={})


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ============================================================
# STUDENT ROUTES
# ============================================================

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    token = get_token()
    stats, _ = api('GET', '/students/dashboard/stats', token=token)
    drives, _ = api('GET', '/applications/drives', token=token)

    # Guard: drives must be a list before slicing (a dict response would crash)
    drives_list = drives if isinstance(drives, list) else []
    return render_template('student/dashboard.html',
                           stats=stats or {},
                           upcoming_drives=drives_list[:5])


@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    token = get_token()

    if request.method == 'POST':
        payload = {}
        if request.form.get('phone'):
            payload['phone'] = request.form.get('phone')
        if request.form.get('cgpa'):
            payload['cgpa'] = float(request.form.get('cgpa'))
        if request.form.get('backlogs') is not None:
            payload['backlogs'] = int(request.form.get('backlogs', 0))

        data, err = api('PUT', '/students/profile', payload, token=token)
        if err:
            student, _ = api('GET', '/students/profile', token=token)
            skills, _ = api('GET', '/students/skills', token=token)
            return render_template('student/profile.html', student=student or {}, skills=skills or [], error=err)

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))

    student, _ = api('GET', '/students/profile', token=token)
    skills, _ = api('GET', '/students/skills', token=token)
    return render_template('student/profile.html', student=student or {}, skills=skills or [])


@app.route('/student/skills', methods=['GET', 'POST'])
@login_required
def student_skills():
    token = get_token()

    if request.method == 'POST':
        payload = {
            'skill_name': request.form.get('skill_name'),
            'category': request.form.get('category'),
            'proficiency_level': request.form.get('proficiency_level', 'Intermediate')
        }
        data, err = api('POST', '/students/skills', payload, token=token)
        if err:
            skills, _ = api('GET', '/students/skills', token=token)
            return render_template('student/skills.html', skills=skills or [], error=err)

        if data and 'error' in data:
            skills, _ = api('GET', '/students/skills', token=token)
            return render_template('student/skills.html', skills=skills or [], error=data['error'])

        flash('Skill added!', 'success')
        return redirect(url_for('student_skills'))

    skills, _ = api('GET', '/students/skills', token=token)
    return render_template('student/skills.html', skills=skills or [])


@app.route('/student/skills/<int:skill_id>/delete', methods=['POST'])
@login_required
def delete_skill(skill_id):
    token = get_token()
    api('DELETE', f'/students/skills/{skill_id}', token=token)
    flash('Skill removed.', 'info')
    return redirect(url_for('student_skills'))


@app.route('/student/drives')
@login_required
def student_drives():
    token = get_token()
    params = {}
    if request.args.get('search'):
        params['search'] = request.args.get('search')
    if request.args.get('mode'):
        params['mode'] = request.args.get('mode')

    drives, err = api('GET', '/applications/drives', token=token)

    # Filter client-side (since backend may not support all filters)
    if drives:
        search = request.args.get('search', '').lower()
        mode = request.args.get('mode', '')
        if search:
            drives = [d for d in drives if search in (d.get('company_name') or '').lower()]
        if mode:
            drives = [d for d in drives if d.get('mode') == mode]

    return render_template('student/drives.html', drives=drives or [])


@app.route('/student/drives/<int:drive_id>')
@login_required
def student_drive_detail(drive_id):
    token = get_token()
    drive, _ = api('GET', f'/applications/drives/{drive_id}', token=token)
    eligibility, _ = api('GET', f'/applications/check-eligibility/{drive_id}', token=token)
    return render_template('student/drive_detail.html', drive=drive or {}, eligibility=eligibility or {})


@app.route('/student/apply/<int:drive_id>')
@login_required
def student_apply(drive_id):
    token = get_token()
    data, err = api('POST', '/applications/apply', {'drive_id': drive_id}, token=token)

    if err:
        flash(f'Error: {err}', 'danger')
    elif data and 'error' in data:
        flash(data['error'], 'danger')
    else:
        flash('Application submitted successfully!', 'success')

    return redirect(url_for('student_applications'))


@app.route('/student/applications')
@login_required
def student_applications():
    token = get_token()
    applications, _ = api('GET', '/applications/my-applications', token=token)
    return render_template('student/applications.html', applications=applications or [])


@app.route('/student/applications/<int:application_id>')
@login_required
def student_application_detail(application_id):
    token = get_token()
    application, _ = api('GET', f'/applications/applications/{application_id}', token=token)
    return render_template('student/application_detail.html', application=application or {})


@app.route('/student/offers')
@login_required
def student_offers():
    token = get_token()
    applications, _ = api('GET', '/applications/my-applications', token=token)
    return render_template('student/offers.html', applications=applications or [])


@app.route('/student/offers/<int:offer_id>/accept', methods=['POST'])
@login_required
def accept_offer(offer_id):
    token = get_token()
    data, err = api('POST', f'/applications/offers/{offer_id}/accept', token=token)
    if err or (data and 'error' in data):
        flash((data or {}).get('error', err or 'Failed to accept offer'), 'danger')
    else:
        flash('Offer accepted! Congratulations! 🎉', 'success')
    return redirect(url_for('student_offers'))


@app.route('/student/offers/<int:offer_id>/reject', methods=['POST'])
@login_required
def reject_offer(offer_id):
    token = get_token()
    data, err = api('POST', f'/applications/offers/{offer_id}/reject', token=token)
    if err or (data and 'error' in data):
        flash((data or {}).get('error', err or 'Failed to reject offer'), 'danger')
    else:
        flash('Offer declined.', 'info')
    return redirect(url_for('student_offers'))


@app.route('/student/resume', methods=['GET', 'POST'])
@login_required
def student_resume():
    token = get_token()
    student, _ = api('GET', '/students/profile', token=token)

    if request.method == 'POST':
        if 'resume' not in request.files:
            return render_template('student/resume.html',
                                   current_resume=(student or {}).get('resume'),
                                   error='No file selected')

        file = request.files['resume']
        files = {'resume': (file.filename, file.stream, file.content_type)}
        data, err = api('POST', '/students/upload-resume', files=files, token=token)

        if err:
            return render_template('student/resume.html',
                                   current_resume=(student or {}).get('resume'), error=err)
        if data and 'error' in data:
            return render_template('student/resume.html',
                                   current_resume=(student or {}).get('resume'), error=data['error'])

        flash('Resume uploaded successfully!', 'success')
        return redirect(url_for('student_resume'))

    return render_template('student/resume.html', current_resume=(student or {}).get('resume'))


# ============================================================
# ADMIN ROUTES
# ============================================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    token = get_token()
    stats, _ = api('GET', '/admin/dashboard/stats', token=token)
    return render_template('admin/dashboard.html', stats=stats or {})


@app.route('/admin/students')
@admin_required
def admin_students():
    token = get_token()
    students, _ = api('GET', '/admin/students', token=token)

    # Client-side filtering
    search = request.args.get('search', '').lower()
    dept = request.args.get('dept', '')
    if students:
        if search:
            students = [s for s in students if search in (s.get('name') or '').lower()
                        or search in (s.get('email') or '').lower()]
        if dept:
            students = [s for s in students if s.get('department') == dept]

    return render_template('admin/students.html', students=students or [])


@app.route('/admin/companies')
@admin_required
def admin_companies():
    token = get_token()
    companies, _ = api('GET', '/admin/companies', token=token)
    return render_template('admin/companies.html', companies=companies or [])


@app.route('/admin/companies/add', methods=['GET', 'POST'])
@admin_required
def admin_add_company():
    token = get_token()

    if request.method == 'POST':
        payload = {
            'name': request.form.get('name'),
            'location': request.form.get('location'),
            'industry': request.form.get('industry'),
            'website': request.form.get('website'),
            'hr_contact': request.form.get('hr_contact')
        }
        data, err = api('POST', '/admin/companies', payload, token=token)
        if err:
            return render_template('admin/add_company.html', error=err)
        if data and 'error' in data:
            return render_template('admin/add_company.html', error=data['error'])
        flash('Company added successfully!', 'success')
        return redirect(url_for('admin_companies'))

    return render_template('admin/add_company.html')


@app.route('/admin/companies/<int:company_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_company(company_id):
    token = get_token()

    if request.method == 'POST':
        payload = {}
        for field in ['name', 'location', 'industry', 'website', 'hr_contact']:
            if request.form.get(field):
                payload[field] = request.form.get(field)
        api('PUT', f'/admin/companies/{company_id}', payload, token=token)
        flash('Company updated!', 'success')
        return redirect(url_for('admin_companies'))

    companies, _ = api('GET', '/admin/companies', token=token)
    company = next((c for c in (companies or []) if c['company_id'] == company_id), {})
    return render_template('admin/edit_company.html', company=company)


@app.route('/admin/companies/<int:company_id>/job-roles', methods=['GET', 'POST'])
@admin_required
def admin_job_roles(company_id):
    token = get_token()

    if request.method == 'POST':
        payload = {
            'company_id': company_id,
            'role_name': request.form.get('role_name'),
            'min_cgpa': float(request.form.get('min_cgpa', 0)),
            'job_type': request.form.get('job_type'),
            'salary_range': request.form.get('salary_range'),
            'description': request.form.get('description')
        }
        data, err = api('POST', '/admin/job-roles', payload, token=token)
        if err:
            flash(err, 'danger')
        elif data and 'error' in data:
            flash(data['error'], 'danger')
        else:
            flash('Job role added!', 'success')
        return redirect(url_for('admin_job_roles', company_id=company_id))

    companies, _ = api('GET', '/admin/companies', token=token)
    company = next((c for c in (companies or []) if c['company_id'] == company_id), {})
    return render_template('admin/job_roles.html', company=company)


@app.route('/admin/drives')
@admin_required
def admin_drives():
    token = get_token()
    # Get all drives by fetching from student endpoint too
    drives, _ = api('GET', '/applications/drives', token=token)
    return render_template('admin/drives.html', drives=drives or [])


@app.route('/admin/drives/add', methods=['GET', 'POST'])
@admin_required
def admin_add_drive():
    token = get_token()
    companies, _ = api('GET', '/admin/companies', token=token)

    if request.method == 'POST':
        payload = {
            'company_id': int(request.form.get('company_id')),
            'drive_date': request.form.get('drive_date'),
            'mode': request.form.get('mode'),
            'deadline': request.form.get('deadline'),
            'venue': request.form.get('venue')
        }
        data, err = api('POST', '/admin/drives', payload, token=token)
        if err:
            return render_template('admin/add_drive.html', companies=companies or [], error=err)
        if data and 'error' in data:
            return render_template('admin/add_drive.html', companies=companies or [], error=data['error'])
        flash('Placement drive created!', 'success')
        return redirect(url_for('admin_drives'))

    return render_template('admin/add_drive.html', companies=companies or [])


@app.route('/admin/drives/<int:drive_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_drive(drive_id):
    token = get_token()

    if request.method == 'POST':
        payload = {}
        for field in ['drive_date', 'mode', 'deadline', 'venue']:
            if request.form.get(field):
                payload[field] = request.form.get(field)
        api('PUT', f'/admin/drives/{drive_id}', payload, token=token)
        flash('Drive updated!', 'success')
        return redirect(url_for('admin_drives'))

    drives, _ = api('GET', '/applications/drives', token=token)
    drive = next((d for d in (drives or []) if d['drive_id'] == drive_id), {})
    return render_template('admin/edit_drive.html', drive=drive)


@app.route('/admin/applications')
@admin_required
def admin_applications():
    token = get_token()
    params = {}
    if request.args.get('status'):
        params['status'] = request.args.get('status')
    if request.args.get('drive_id'):
        params['drive_id'] = request.args.get('drive_id')

    applications, _ = api('GET', '/admin/applications', params, token=token)
    drives, _ = api('GET', '/applications/drives', token=token)
    return render_template('admin/applications.html',
                           applications=applications or [],
                           drives=drives or [])


@app.route('/admin/applications/<int:application_id>/status', methods=['POST'])
@admin_required
def admin_update_status(application_id):
    token = get_token()
    payload = {
        'status': request.form.get('status'),
        'round_number': int(request.form.get('round_number')) if request.form.get('round_number') else None,
        'result': request.form.get('result') or None,
        'feedback': request.form.get('feedback') or None
    }
    data, err = api('PUT', f'/admin/applications/{application_id}/status', payload, token=token)
    if err:
        flash(err, 'danger')
    elif data and 'error' in data:
        flash(data['error'], 'danger')
    else:
        flash('Application status updated!', 'success')
    return redirect(url_for('admin_applications'))


@app.route('/admin/offers')
@admin_required
def admin_offers():
    token = get_token()
    # Get selected applications for offer creation
    all_apps, _ = api('GET', '/admin/applications', {'status': 'Selected'}, token=token)

    # Get existing offers via placement summary
    summary, _ = api('GET', '/admin/reports/placement-summary', token=token)

    return render_template('admin/offers.html',
                           offers=summary or [],
                           selected_applications=all_apps or [])


@app.route('/admin/offers/add', methods=['POST'])
@admin_required
def admin_add_offer():
    token = get_token()
    payload = {
        'application_id': int(request.form.get('application_id')),
        'salary': float(request.form.get('salary')) if request.form.get('salary') else None,
        'joining_date': request.form.get('joining_date') or None,
        'response_deadline': request.form.get('response_deadline') or None
    }
    data, err = api('POST', '/admin/offers', payload, token=token)
    if err:
        flash(err, 'danger')
    elif data and 'error' in data:
        flash(data['error'], 'danger')
    else:
        flash('Offer created successfully!', 'success')
    return redirect(url_for('admin_offers'))


@app.route('/admin/reports')
@admin_required
def admin_reports():
    token = get_token()
    placement_summary, _ = api('GET', '/admin/reports/placement-summary', token=token)
    drive_stats, _ = api('GET', '/admin/reports/drive-stats', token=token)
    student_skills, _ = api('GET', '/admin/reports/student-skills', token=token)

    return render_template('admin/reports.html',
                           placement_summary=placement_summary or [],
                           drive_stats=drive_stats or [],
                           student_skills=student_skills or [])


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500, message='Internal server error'), 500


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    print("=" * 55)
    print("🚀  PlacementHub Frontend")
    print("=" * 55)
    print(f"🌐  Frontend:  http://localhost:8000")
    print(f"🔌  Backend:   {API_BASE}")
    print("=" * 55)
    app.run(host='0.0.0.0', port=8000, debug=True)