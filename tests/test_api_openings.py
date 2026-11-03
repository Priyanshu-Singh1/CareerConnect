from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from companies.models import Company
from companies.services import CompanyOpeningsAPIService
from jobs.models import Job
from accounts.models import CandidateProfile
from applications.models import Application


class CompanyOpeningsAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate_user = User.objects.create_user(
            username="candidate_api_test",
            password="TestPassword123!"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            headline="Python & Cloud Developer"
        )

    def test_fetch_and_sync_known_company(self):
        result = CompanyOpeningsAPIService.fetch_and_sync_company_openings('Amazon')
        self.assertIsNotNone(result)
        self.assertEqual(result['company'].name, 'Amazon')
        self.assertTrue(result['count'] > 0)

        # Check in DB
        company = Company.objects.get(name='Amazon')
        self.assertEqual(company.industry, 'E-Commerce & Cloud (AWS)')
        jobs = Job.objects.filter(company=company)
        self.assertEqual(jobs.count(), result['count'])

        # Recruiter check
        recruiter = jobs.first().recruiter
        self.assertTrue(hasattr(recruiter, 'recruiter_profile'))
        self.assertTrue(recruiter.recruiter_profile.is_verified)

    def test_fetch_and_sync_arbitrary_dynamic_company(self):
        # Test arbitrary company not in static catalog (e.g. OpenAI)
        result = CompanyOpeningsAPIService.fetch_and_sync_company_openings('OpenAI')
        self.assertIsNotNone(result)
        self.assertEqual(result['company'].name, 'Openai')
        self.assertTrue(result['count'] >= 2)

        company = Company.objects.get(slug='openai')
        self.assertTrue(Job.objects.filter(company=company).exists())

    def test_company_api_search_view(self):
        # Test searching via fetch-api view
        response = self.client.get(reverse('companies:fetch_api'), {'company': 'Netflix'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Netflix')
        self.assertContains(response, 'Available Openings at Netflix')

    def test_json_rest_api_endpoint(self):
        # Test GET /companies/api/fetch/?company=Spotify
        response = self.client.get(reverse('companies:api_fetch_openings'), {'company': 'Spotify'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['company']['name'], 'Spotify')
        self.assertTrue(len(data['openings']) > 0)

    def test_candidate_can_apply_to_fetched_job(self):
        # 1. Fetch openings for Google
        result = CompanyOpeningsAPIService.fetch_and_sync_company_openings('Google')
        google_job = result['jobs'][0]

        # 2. Candidate logs in
        self.client.login(username="candidate_api_test", password="TestPassword123!")

        # 3. View job detail page
        detail_url = reverse('jobs:job_detail', kwargs={'pk': google_job.pk, 'slug': google_job.slug})
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, google_job.title)

        # 4. Candidate submits application
        from django.core.files.uploadedfile import SimpleUploadedFile
        resume_file = SimpleUploadedFile("my_resume.pdf", b"Candidate Resume PDF content", content_type="application/pdf")

        apply_url = reverse('applications:apply_job', kwargs={'job_id': google_job.id})
        apply_resp = self.client.post(apply_url, {
            'resume': resume_file,
            'cover_letter': 'Excited to apply for this Google opening through CareerConnect!',
        })
        # Should redirect to candidate applications tracking page
        self.assertEqual(apply_resp.status_code, 302)
        self.assertRedirects(apply_resp, reverse('applications:candidate_applications'))

        # 5. Verify application exists in DB
        app = Application.objects.get(job=google_job, candidate=self.candidate_user)
        self.assertEqual(app.status, 'Applied')
        self.assertEqual(app.cover_letter, 'Excited to apply for this Google opening through CareerConnect!')
