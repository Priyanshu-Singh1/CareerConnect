import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.utils import IntegrityError
from companies.models import Company
from jobs.models import JobCategory, Skill, Job, SavedJob
from accounts.models import CandidateProfile, RecruiterProfile
from applications.models import Application, Interview


class ModelTestCase(TestCase):
    def setUp(self):
        # Company
        self.company = Company.objects.create(
            name="Apex Innovations",
            industry="IT",
            location="Pune"
        )
        # Recruiter
        self.recruiter_user = User.objects.create_user(
            username="recruiter_test",
            password="Password123!"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company=self.company,
            designation="Talent Lead"
        )
        # Skills
        self.skill_python = Skill.objects.create(name="Python")
        self.skill_django = Skill.objects.create(name="Django")
        self.skill_react = Skill.objects.create(name="React")

        # Job
        self.job = Job.objects.create(
            recruiter=self.recruiter_user,
            company=self.company,
            title="Backend Engineer",
            job_type="Full-time",
            work_mode="Remote",
            location="Pune",
            deadline=timezone.now().date() + datetime.timedelta(days=10),
            description="Build great software"
        )
        self.job.skills_required.add(self.skill_python, self.skill_django)

        # Candidate
        self.candidate_user = User.objects.create_user(
            username="candidate_test",
            password="Password123!"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            headline="Python Developer"
        )
        self.candidate_profile.skills.add(self.skill_python)

    def test_company_slug_generation(self):
        self.assertEqual(self.company.slug, "apex-innovations")

    def test_job_slug_and_status(self):
        self.assertEqual(self.job.slug, "backend-engineer")
        self.assertTrue(self.job.can_apply)
        self.assertFalse(self.job.is_expired)

    def test_smart_skill_match_algorithm(self):
        # Candidate has 1 out of 2 required skills (50%)
        score, matched = self.job.skill_match_score(self.candidate_user)
        self.assertEqual(score, 50)
        self.assertIn(self.skill_python, matched)

        # Add second skill -> 100%
        self.candidate_profile.skills.add(self.skill_django)
        score, matched = self.job.skill_match_score(self.candidate_user)
        self.assertEqual(score, 100)

    def test_unique_application_constraint(self):
        Application.objects.create(
            job=self.job,
            candidate=self.candidate_user,
            status="Applied"
        )
        # Attempting duplicate application must raise IntegrityError
        with self.assertRaises(IntegrityError):
            Application.objects.create(
                job=self.job,
                candidate=self.candidate_user,
                status="Applied"
            )

    def test_can_withdraw_logic(self):
        app = Application.objects.create(
            job=self.job,
            candidate=self.candidate_user,
            status="Applied"
        )
        self.assertTrue(app.can_withdraw)

        app.status = "Under Review"
        app.save()
        self.assertTrue(app.can_withdraw)

        app.status = "Shortlisted"
        app.save()
        self.assertFalse(app.can_withdraw)

    def test_saved_job_unique_constraint(self):
        SavedJob.objects.create(candidate=self.candidate_user, job=self.job)
        with self.assertRaises(IntegrityError):
            SavedJob.objects.create(candidate=self.candidate_user, job=self.job)
