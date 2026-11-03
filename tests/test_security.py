import os
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from companies.models import Company
from jobs.models import Job
from accounts.models import CandidateProfile, RecruiterProfile
from applications.models import Application


class SecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.company1 = Company.objects.create(name="Alpha Corp", industry="Tech", location="Delhi")
        self.company2 = Company.objects.create(name="Beta Corp", industry="Finance", location="Pune")

        # Recruiter 1 (Company 1)
        self.recruiter1 = User.objects.create_user(username="recruiter1", password="Password123!")
        RecruiterProfile.objects.create(user=self.recruiter1, company=self.company1, is_verified=True)

        # Recruiter 2 (Company 2 - unrelated)
        self.recruiter2 = User.objects.create_user(username="recruiter2", password="Password123!")
        RecruiterProfile.objects.create(user=self.recruiter2, company=self.company2, is_verified=True)

        # Candidate
        self.candidate = User.objects.create_user(username="candidate_secure", password="Password123!")
        dummy_file = SimpleUploadedFile("resume.pdf", b"Dummy resume content", content_type="application/pdf")
        self.candidate_prof = CandidateProfile.objects.create(
            user=self.candidate,
            resume=dummy_file
        )

        # Job posted by Recruiter 1
        self.job1 = Job.objects.create(
            recruiter=self.recruiter1,
            company=self.company1,
            title="Security Engineer",
            deadline=timezone.now().date() + datetime.timedelta(days=10),
            description="Security role",
            is_active=True
        )

    def tearDown(self):
        # Clean up created file
        if self.candidate_prof.resume and os.path.exists(self.candidate_prof.resume.path):
            try:
                os.remove(self.candidate_prof.resume.path)
            except Exception:
                pass

    def test_anonymous_user_cannot_download_resume(self):
        # Anonymous user must be redirected to login
        url = reverse('accounts:download_resume', kwargs={'user_id': self.candidate.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_unrelated_recruiter_gets_403_forbidden_on_resume(self):
        # Recruiter 2 has NOT received any application from Candidate
        self.client.login(username="recruiter2", password="Password123!")
        url = reverse('accounts:download_resume', kwargs={'user_id': self.candidate.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_recruiter_can_download_resume(self):
        # Candidate applies to Job 1 (owned by Recruiter 1)
        Application.objects.create(job=self.job1, candidate=self.candidate, status="Applied")

        # Now Recruiter 1 is authorized to view resume
        self.client.login(username="recruiter1", password="Password123!")
        url = reverse('accounts:download_resume', kwargs={'user_id': self.candidate.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_candidate_can_download_own_resume(self):
        self.client.login(username="candidate_secure", password="Password123!")
        url = reverse('accounts:download_resume', kwargs={'user_id': self.candidate.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_prevent_applying_to_expired_job(self):
        expired_job = Job.objects.create(
            recruiter=self.recruiter1,
            company=self.company1,
            title="Expired Position",
            deadline=timezone.now().date() - datetime.timedelta(days=2),
            description="Old job",
            is_active=True
        )
        self.client.login(username="candidate_secure", password="Password123!")
        url = reverse('applications:apply_job', kwargs={'job_id': expired_job.id})
        response = self.client.get(url)
        # Should redirect back with error message
        self.assertEqual(response.status_code, 302)
