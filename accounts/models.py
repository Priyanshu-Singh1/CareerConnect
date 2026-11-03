from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    headline = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="e.g., Computer Science Graduate | Aspiring Python & Django Developer"
    )
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True, help_text="Brief professional summary about yourself")
    education = models.TextField(
        blank=True, 
        help_text="Education details (Degree, College/University, Year, CGPA/Percentage)"
    )
    experience = models.TextField(
        blank=True, 
        help_text="Past experience or internships (Role, Company, Duration, Responsibilities)"
    )
    projects = models.TextField(
        blank=True, 
        help_text="Key projects (Title, Tech stack, Description, Live/GitHub link)"
    )
    skills = models.ManyToManyField('jobs.Skill', blank=True, related_name='candidates')
    resume = models.FileField(
        upload_to='resumes/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc'])],
        help_text="Upload your resume in PDF or DOCX format (Max 5MB)"
    )
    portfolio_url = models.URLField(blank=True, help_text="Personal website or portfolio URL")
    github_url = models.URLField(blank=True, help_text="GitHub profile URL")
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def completeness_percentage(self):
        """
        Calculates profile completeness percentage (0 to 100).
        """
        score = 0
        if self.user.first_name and self.user.last_name:
            score += 10
        if self.headline:
            score += 10
        if self.phone:
            score += 10
        if self.location:
            score += 10
        if self.bio:
            score += 10
        if self.education:
            score += 15
        if self.skills.exists():
            score += 15
        if self.resume:
            score += 10
        if self.projects or self.experience:
            score += 5
        if self.portfolio_url or self.github_url or self.linkedin_url:
            score += 5
        return min(score, 100)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Candidate)"


class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recruiters'
    )
    designation = models.CharField(
        max_length=120, 
        blank=True, 
        help_text="e.g., Lead Tech Recruiter, HR Manager"
    )
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(
        default=True, 
        help_text="Admin verification allows recruiter to post jobs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        comp_name = self.company.name if self.company else "Independent"
        return f"{self.user.get_full_name() or self.user.username} - {comp_name} (Recruiter)"
