import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from companies.models import Company
from jobs.models import Job, Skill, JobCategory
from accounts.models import CandidateProfile, RecruiterProfile
from applications.models import Application


class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name="Innovate Ltd", industry="IT", location="Mumbai")
        
        # Recruiter
        self.recruiter_user = User.objects.create_user(
            username="recruiter_jane",
            email="jane@innovate.com",
            password="RecruiterPassword123!"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company=self.company,
            is_verified=True
        )

        # Candidate
        self.candidate_user = User.objects.create_user(
            username="candidate_john",
            email="john@example.com",
            password="CandidatePassword123!"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            headline="Web Developer"
        )

        # Job
        self.job = Job.objects.create(
            recruiter=self.recruiter_user,
            company=self.company,
            title="Django Developer",
            job_type="Full-time",
            work_mode="Remote",
            location="Mumbai",
            deadline=timezone.now().date() + datetime.timedelta(days=20),
            description="Django role description",
            is_active=True
        )

    def test_home_page_loads(self):
        response = self.client.get(reverse('jobs:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CareerConnect")

    def test_job_list_search(self):
        response = self.client.get(reverse('jobs:job_list'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Developer")

        response_empty = self.client.get(reverse('jobs:job_list'), {'q': 'NonExistentTitle'})
        self.assertEqual(response_empty.status_code, 200)
        self.assertContains(response_empty, "No matching opportunities found")

    def test_candidate_registration(self):
        response = self.client.post(reverse('accounts:register_candidate'), {
            'username': 'new_candidate',
            'first_name': 'New',
            'last_name': 'Candidate',
            'email': 'new_candidate@test.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='new_candidate')
        self.assertTrue(hasattr(new_user, 'candidate_profile'))

    def test_recruiter_registration(self):
        response = self.client.post(reverse('accounts:register_recruiter'), {
            'username': 'new_recruiter',
            'first_name': 'New',
            'last_name': 'Recruiter',
            'email': 'recruiter@newcompany.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'designation': 'HR Manager',
            'new_company_name': 'NextGen AI',
            'new_company_industry': 'AI',
            'new_company_location': 'Bengaluru',
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='new_recruiter')
        self.assertTrue(hasattr(new_user, 'recruiter_profile'))
        self.assertEqual(new_user.recruiter_profile.company.name, 'NextGen AI')

    def test_candidate_dashboard_access_control(self):
        # Anonymous user redirected to login
        response = self.client.get(reverse('accounts:candidate_dashboard'))
        self.assertEqual(response.status_code, 302)

        # Candidate user allowed
        self.client.login(username="candidate_john", password="CandidatePassword123!")
        response = self.client.get(reverse('accounts:candidate_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_recruiter_dashboard_access_control(self):
        # Candidate denied access to recruiter dashboard
        self.client.login(username="candidate_john", password="CandidatePassword123!")
        response = self.client.get(reverse('accounts:recruiter_dashboard'))
        self.assertEqual(response.status_code, 302)

        # Recruiter allowed
        self.client.login(username="recruiter_jane", password="RecruiterPassword123!")
        response = self.client.get(reverse('accounts:recruiter_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_recruiter_updates_status(self):
        app = Application.objects.create(
            job=self.job,
            candidate=self.candidate_user,
            status="Applied"
        )
        self.client.login(username="recruiter_jane", password="RecruiterPassword123!")
        response = self.client.post(reverse('applications:update_status', kwargs={'application_id': app.id}), {
            'status': 'Shortlisted',
            'recruiter_notes': 'Good profile',
        })
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, 'Shortlisted')
