from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Application(models.Model):
    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Under Review', 'Under Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview Scheduled', 'Interview Scheduled'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
        ('Withdrawn', 'Withdrawn'),
    ]

    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(
        upload_to='resumes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc'])],
        help_text="Resume file submitted for this specific application"
    )
    cover_letter = models.TextField(blank=True, help_text="Optional statement of purpose or cover note")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Applied')
    recruiter_notes = models.TextField(blank=True, help_text="Internal recruiter evaluation notes")
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['job', 'candidate'], name='unique_job_candidate_application')
        ]
        ordering = ['-applied_at']

    @property
    def can_withdraw(self):
        """Candidates can withdraw only while application is Applied or Under Review."""
        return self.status in ['Applied', 'Under Review']

    @property
    def status_badge_class(self):
        mapping = {
            'Applied': 'bg-primary',
            'Under Review': 'bg-info text-dark',
            'Shortlisted': 'bg-warning text-dark',
            'Interview Scheduled': 'bg-purple text-white',
            'Selected': 'bg-success',
            'Rejected': 'bg-danger',
            'Withdrawn': 'bg-secondary',
        }
        return mapping.get(self.status, 'bg-secondary')

    def __str__(self):
        return f"{self.candidate.username} -> {self.job.title} ({self.status})"


class Interview(models.Model):
    MODE_CHOICES = [
        ('Online Video Call', 'Online Video Call'),
        ('In-person / Office', 'In-person / Office'),
        ('Phone Screening', 'Phone Screening'),
    ]

    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='interview')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    mode = models.CharField(max_length=30, choices=MODE_CHOICES, default='Online Video Call')
    location_or_link = models.CharField(
        max_length=500, 
        help_text="Google Meet / Zoom link or company physical office address"
    )
    instructions = models.TextField(
        blank=True, 
        help_text="Candidate instructions (e.g., topics covered, coding setup required)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"Interview for {self.application.candidate.username} at {self.application.job.title}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.title}"
