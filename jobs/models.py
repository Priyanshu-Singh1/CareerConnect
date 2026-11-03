from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone


class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-briefcase', help_text="Bootstrap icon class name, e.g. bi-code-slash")

    class Meta:
        verbose_name_plural = 'Job Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def active_jobs_count(self):
        return self.jobs.filter(is_active=True, deadline__gte=timezone.now().date()).count()

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
    ]

    WORK_MODE_CHOICES = [
        ('On-site', 'On-site'),
        ('Hybrid', 'Hybrid'),
        ('Remote', 'Remote'),
    ]

    EXPERIENCE_CHOICES = [
        ('Fresher', 'Fresher / Entry Level'),
        ('Junior', 'Junior (1-3 yrs)'),
        ('Mid-level', 'Mid-level (3-5 yrs)'),
        ('Senior', 'Senior (5+ yrs)'),
    ]

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='Full-time')
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='On-site')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='Fresher')
    location = models.CharField(max_length=150)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_negotiable = models.BooleanField(default=False)
    skills_required = models.ManyToManyField(Skill, blank=True, related_name='jobs')
    description = models.TextField()
    responsibilities = models.TextField(blank=True, help_text="Key responsibilities (bullet points or paragraphs)")
    requirements = models.TextField(blank=True, help_text="Candidate requirements and qualifications")
    vacancies = models.PositiveIntegerField(default=1)
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.deadline < timezone.now().date()

    @property
    def can_apply(self):
        return self.is_active and not self.is_expired

    @property
    def salary_display(self):
        if self.salary_negotiable:
            return "Negotiable"
        if self.salary_min and self.salary_max:
            return f"₹{int(self.salary_min):,} - ₹{int(self.salary_max):,}"
        elif self.salary_min:
            return f"From ₹{int(self.salary_min):,}"
        elif self.salary_max:
            return f"Up to ₹{int(self.salary_max):,}"
        return "Not Disclosed"

    def skill_match_score(self, user):
        """
        Smart job matching: returns match percentage (0-100) and matched skills list.
        """
        if not user or not user.is_authenticated:
            return 0, []
        if not hasattr(user, 'candidate_profile'):
            return 0, []
        
        required_skills = set(self.skills_required.all())
        if not required_skills:
            return 100, []
        
        candidate_skills = set(user.candidate_profile.skills.all())
        matched = required_skills.intersection(candidate_skills)
        score = int(round((len(matched) / len(required_skills)) * 100))
        return score, list(matched)

    def __str__(self):
        return f"{self.title} at {self.company.name}"


class SavedJob(models.Model):
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['candidate', 'job'], name='unique_candidate_saved_job')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.candidate.username} saved {self.job.title}"


class JobReport(models.Model):
    REASON_CHOICES = [
        ('Fraudulent / Scam', 'Fraudulent / Scam'),
        ('Incorrect Details', 'Incorrect Details'),
        ('Expired Listing', 'Expired Listing'),
        ('Discriminatory / Offensive', 'Discriminatory / Offensive'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Dismissed', 'Dismissed'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_reports')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on {self.job.title} by {self.reported_by.username} ({self.status})"
