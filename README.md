# CareerConnect — Job & Internship Portal

**CareerConnect** is a full-featured, production-ready web portal built with **Django 6.1**, **Bootstrap 5**, and **SQLite** that bridges students, job seekers, and industry recruiters. Candidates can discover verified opportunities, track real-time hiring stages, receive skill match percentages, and manage their profiles, while recruiters can post listings, review applicants, move candidates through a structured hiring pipeline, and schedule interviews.

---

## 🎯 Six Django Syllabus Units — Implementation Mapping

CareerConnect was purpose-built to demonstrate all 6 curriculum units cleanly and thoroughly:

| Unit | Syllabus Topics Covered | Implementation in CareerConnect | Key Source Files |
| :--- | :--- | :--- | :--- |
| **Unit I: Introduction to Django** | Architecture, `startproject`, `startapp`, settings configuration, `manage.py`, environment variables | Modular structure with 4 decoupled apps (`accounts`, `companies`, `jobs`, `applications`), `.env` support via `python-dotenv`. | `careerconnect/settings.py`, `manage.py`, `.env` |
| **Unit II: Views and URLs** | Function-Based Views (FBVs), URL routing, parameterized paths (`<int:pk>`, `<slug:slug>`), GET/POST dispatch, custom 403/404/500 error handlers | Multi-criteria search, parameterized job detail URLs, secure file access views with 403 Forbidden checks, custom error templates. | `jobs/views.py`, `jobs/urls.py`, `careerconnect/views.py`, `templates/errors/` |
| **Unit III: Templates, Debugging & Testing** | Django Template Language (DTL), template inheritance (`base.html`), loops, conditionals, custom filters, automated unit & integration testing | Responsive layout using Bootstrap 5, pipeline kanban, custom templatetag `get_item`, 23 automated unit, API and security tests. | `templates/base.html`, `applications/templatetags/app_tags.py`, `tests/` |
| **Unit IV: Forms in Django** | `forms.ModelForm`, CSRF token protection, form validation, error rendering, POST-Redirect-GET design pattern | Validated registration forms, deadline checks, past date prevention, resume MIME/extension validations, file upload handling. | `accounts/forms.py`, `jobs/forms.py`, `applications/forms.py`, `companies/forms.py` |
| **Unit V: Models, Migrations & Admin** | Models, fields, `ForeignKey`, `OneToOneField`, `ManyToManyField`, `UniqueConstraint`, ORM CRUD, Admin custom actions & inlines | `CandidateProfile`, `RecruiterProfile`, `Company`, `Job`, `Application`, `Interview`, `Notification`, composite unique constraints, admin actions. | `accounts/models.py`, `jobs/models.py`, `applications/models.py`, `*/admin.py` |
| **Unit VI: Cookies, Sessions & Authentication** | User authentication, password hashing (PBKDF2), role decorators, session tracking, cookie inspection | Built-in Auth, custom decorators (`@candidate_required`, `@recruiter_required`, `@verified_recruiter_required`), session-based "Recently Viewed Jobs", console password reset. | `accounts/decorators.py`, `accounts/views.py`, `accounts/context_processors.py` |

---

## 👥 User Roles & Access Control

1. **Candidate / Student**
   - Register, login, and customize personal candidate profile.
   - Profile completeness indicator (% score) encouraging full information.
   - Upload resume (PDF/DOCX, 5MB max), specify skills, education, past internships, and portfolio/GitHub links.
   - Search and filter jobs by keyword, category, job type, work mode, location, and sort by newest or deadline.
   - Smart Skill Matching score showing compatibility with each listing.
   - Apply for jobs using existing profile resume or uploading a custom one.
   - Real-time application tracking across 7 stages: *Applied, Under Review, Shortlisted, Interview Scheduled, Selected, Rejected, Withdrawn*.
   - View scheduled interview date, time, meeting link, and instructions.
   - Save / bookmark jobs to wishlist.
   - Report inappropriate or fraudulent listings.

2. **Recruiter / Employer**
   - Create and update company profile (logo, size, industry, location, description).
   - Post, edit, publish, close, or delete job listings.
   - Specify salary ranges, vacancies, deadlines, and required skills.
   - View all applicants filtered by job and stage.
   - **Visual Kanban Hiring Pipeline** with one-click stage moves.
   - Access candidate profiles and download authorized applicant resumes.
   - Schedule interviews with candidate instructions and meeting link/location.
   - View recruitment analytics: total listings, application count, shortlisted count, and hiring conversion rate (%).

3. **Portal Administrator (Django Admin)**
   - Moderate and verify recruiter accounts and company records.
   - Review reported job posts and toggle active statuses.
   - Manage job categories, predefined skills, and user permissions.
   - Direct access at `/admin/`.

---

## 🔒 Security & Privacy Enforcement

- **Database-Level Unique Constraint**: Enforces one application per candidate per job (`unique_job_candidate_application`), preventing duplicate applications.
- **Deadline Enforcement**: Candidates cannot submit applications to expired or closed jobs.
- **Strict Resume Access Control (`/accounts/resume/download/<id>/`)**: Resumes are protected by role-checking logic. Only the candidate owner, recruiters whose jobs the candidate has applied to, or administrators can view/download candidate resumes. Unauthorized requests receive an HTTP `403 Forbidden`.
- **Role Guard Decorators**: `@candidate_required`, `@recruiter_required`, and `@verified_recruiter_required` enforce view-level permissions.
- **CSRF Protection**: All POST requests enforce `{% csrf_token %}`.
- **Password Security**: Uses Django's built-in PBKDF2 with SHA256 password hashing.

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone or navigate to the repository directory
cd Django_Project

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Run Migrations & Populate Demo Data
```bash
# Apply database migrations
python manage.py migrate

# Seed database with realistic demo accounts, jobs, and applications
python manage.py seed_data
```

### 4. Start the Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000** in your browser.

---

## 🔑 Pre-Configured Demo Credentials

For quick evaluation, the `seed_data` command creates ready-to-test accounts:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Superuser / Admin** | `admin` | `Admin@123` | Access to `/admin/` |
| **Recruiter (TechNova)** | `recruiter_alex` | `Recruiter@123` | Has 2 active job listings & applicants |
| **Recruiter (CloudScale)**| `recruiter_priya` | `Recruiter@123` | Has 1 active cloud intern opening |
| **Candidate (Python/Django)** | `candidate_rahul` | `Candidate@123` | High skill match, has scheduled interview |
| **Candidate (React/Fullstack)** | `candidate_ananya` | `Candidate@123` | Applied to Full Stack role |

---

## 🧪 Automated Test Suite

CareerConnect comes with **23 automated tests** covering models, views, forms, constraints, API opening sync, and security permissions.

Run the test suite anytime:
```bash
python manage.py test
```

**Test Output:**
```text
Creating test database for alias 'default'...
.......................
----------------------------------------------------------------------
Ran 23 tests in 22.346s

OK
Destroying test database for alias 'default'...
```

---

## 📁 Project Directory Structure

```text
Django_Project/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── careerconnect/            # Project configuration
│   ├── settings.py           # Database, middleware, templates, auth config
│   ├── urls.py               # Main routing & error handler registration
│   ├── views.py              # Custom 403, 404, 500 error views
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # User authentication & profiles
│   ├── models.py             # CandidateProfile, RecruiterProfile
│   ├── forms.py              # Candidate/Recruiter registration & profile forms
│   ├── views.py              # Login, register, dashboards, secure resume download
│   ├── urls.py               # Account routes & password reset endpoints
│   ├── decorators.py         # @candidate_required, @recruiter_required
│   └── context_processors.py # Global user_role_context for navbar
├── companies/                # Company profiles & directory
│   ├── models.py             # Company model with auto-slug
│   ├── forms.py              # Company edit form
│   ├── views.py              # Company directory, detail & edit views
│   └── urls.py
├── jobs/                     # Job listings, search & wishlist
│   ├── models.py             # Job, JobCategory, Skill, SavedJob, JobReport
│   ├── forms.py              # JobForm, JobReportForm
│   ├── views.py              # Home, search/filter list, detail, CRUD
│   ├── urls.py
│   └── management/commands/
│       └── seed_data.py      # Automated database populator
├── applications/             # Job applications, pipeline & interviews
│   ├── models.py             # Application, Interview, Notification
│   ├── forms.py              # ApplicationForm, InterviewScheduleForm
│   ├── views.py              # Apply, candidate tracker, recruiter pipeline
│   ├── urls.py
│   └── templatetags/
│       └── app_tags.py       # Custom template filters
├── templates/                # Server-rendered HTML templates
│   ├── base.html             # Master layout with responsive navbar & footer
│   ├── accounts/             # Login, register, profiles, password reset
│   ├── companies/            # Company directory & detail
│   ├── jobs/                 # Job listings, detail, post/edit, wishlist
│   ├── applications/         # Apply form, tracker, pipeline kanban, interview
│   ├── dashboards/           # Candidate & Recruiter dashboards
│   └── errors/               # 403, 404, 500 error pages
├── static/                   # Static assets
│   ├── css/custom.css        # Custom styling, badges, and kanban board
│   └── js/main.js            # Tooltip activation, alert auto-dismiss
└── tests/                    # Automated test suite
    ├── test_models.py        # Model constraints & skill match tests
    ├── test_views.py         # Views, registration & permission tests
    └── test_security.py      # 403 Forbidden resume download tests
```

---

## 🌟 Standout Features

1. **Live Company Openings API Integration**: Candidates can search for ANY company (e.g., *Google, Amazon, Microsoft, Meta, Netflix, Apple, TCS, Infosys, Zomato, Swiggy, Spotify, Adobe* or any custom organization). The API discovers company profiles, active job and internship openings, imports them into CareerConnect with appropriate categories and skills, and allows candidates to apply immediately. Available via interactive view (`/companies/fetch-api/`), search auto-sync, and REST JSON endpoint (`/companies/api/fetch/?company=<name>`).
2. **Visual Kanban Pipeline**: Recruiters can review candidates arranged by stage (*Applied* &rarr; *Under Review* &rarr; *Shortlisted* &rarr; *Interview* &rarr; *Selected* &rarr; *Rejected*) with quick-action status transition forms.
3. **Smart Skill Matching Algorithm**: Compares candidate's selected skills against job requirements in pure Python, calculating a live compatibility percentage ($0-100\%$) displayed with matched/missing skill badges.
4. **Recruitment Analytics**: Real-time conversion rate calculations ($(\text{Hired} / \text{Total Applications}) \times 100$), job counts, and pipeline distribution metrics.
5. **Session-Based Recently Viewed Jobs**: Tracks job IDs in `request.session['recently_viewed_jobs']`, demonstrating cookie & session management on candidate dashboards.
