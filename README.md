# PlacementHub Frontend

Flask + Jinja2 frontend for the Placement Management System.

## Project Structure

```
placement_frontend/
├── frontend_app.py              ← Main Flask app (run this)
├── requirements_frontend.txt    ← Dependencies
├── templates/
│   ├── base.html                ← Base layout (styles, navbar)
│   ├── error.html               ← Error pages
│   ├── auth/
│   │   ├── login.html           ← Login (Student + Admin tabs)
│   │   └── register.html        ← Student registration
│   ├── student/
│   │   ├── layout.html          ← Student layout with sidebar
│   │   ├── dashboard.html       ← Student dashboard
│   │   ├── profile.html         ← View/edit profile
│   │   ├── skills.html          ← Manage skills
│   │   ├── drives.html          ← Browse placement drives
│   │   ├── drive_detail.html    ← Drive details + apply
│   │   ├── applications.html    ← My applications list
│   │   ├── application_detail.html ← Application + interview rounds
│   │   ├── offers.html          ← Job offers (accept/reject)
│   │   └── resume.html          ← Upload resume
│   └── admin/
│       ├── layout.html          ← Admin layout with sidebar
│       ├── dashboard.html       ← Admin dashboard + stats
│       ├── students.html        ← All students list
│       ├── companies.html       ← Companies list
│       ├── add_company.html     ← Add company form
│       ├── edit_company.html    ← Edit company form
│       ├── job_roles.html       ← Manage job roles
│       ├── drives.html          ← Drives list
│       ├── add_drive.html       ← Create drive form
│       ├── edit_drive.html      ← Edit drive form
│       ├── applications.html    ← All applications + status update
│       ├── offers.html          ← Create/view offers
│       └── reports.html         ← Analytics (3 tabs)
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements_frontend.txt
```

### 2. Create .env file (optional)
```
SECRET_KEY=your-frontend-secret-key
API_BASE=http://localhost:5000/api
```

### 3. Make sure your backend is running first
```bash
# In your backend folder:
python app.py
# Backend runs on port 5000
```

### 4. Run the frontend
```bash
python frontend_app.py
# Frontend runs on port 8000
```

### 5. Open in browser
```
http://localhost:8000
```

## How It Works

- The frontend is a **separate Flask app** running on port **8000**
- It talks to your existing backend API on port **5000** via HTTP
- All authentication uses **JWT tokens stored in Flask session**
- No database access from the frontend — everything goes through your API

## Pages

### Public
| Page | URL |
|------|-----|
| Login | `/login` |
| Register | `/register` |

### Student (requires login)
| Page | URL |
|------|-----|
| Dashboard | `/student/dashboard` |
| Profile | `/student/profile` |
| Skills | `/student/skills` |
| Browse Drives | `/student/drives` |
| My Applications | `/student/applications` |
| My Offers | `/student/offers` |
| Upload Resume | `/student/resume` |

### Admin (requires admin login)
| Page | URL |
|------|-----|
| Dashboard | `/admin/dashboard` |
| Students | `/admin/students` |
| Companies | `/admin/companies` |
| Drives | `/admin/drives` |
| Applications | `/admin/applications` |
| Offers | `/admin/offers` |
| Reports | `/admin/reports` |
