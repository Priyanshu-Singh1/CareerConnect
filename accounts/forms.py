from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import CandidateProfile, RecruiterProfile
from companies.models import Company
from jobs.models import Skill


class CandidateRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}), min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            CandidateProfile.objects.create(user=user)
        return user


class RecruiterRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Work Email Address', 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}), min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}))
    
    # Recruiter specific fields
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        empty_label="-- Select an existing company or leave blank to create new --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    new_company_name = forms.CharField(
        max_length=200, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Or enter new company name', 'class': 'form-control'})
    )
    new_company_industry = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Company industry (e.g. IT, FinTech)', 'class': 'form-control'})
    )
    new_company_location = forms.CharField(
        max_length=150, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Company headquarters location', 'class': 'form-control'})
    )
    designation = forms.CharField(
        max_length=120, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'Your designation (e.g. HR Lead, Tech Recruiter)', 'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20, 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Phone number', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        company = cleaned_data.get('company')
        new_company_name = cleaned_data.get('new_company_name')

        if not company and not new_company_name:
            self.add_error('company', "Please select an existing company or provide a new company name.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            company = self.cleaned_data.get('company')
            if not company and self.cleaned_data.get('new_company_name'):
                company, _ = Company.objects.get_or_create(
                    name=self.cleaned_data['new_company_name'].strip(),
                    defaults={
                        'industry': self.cleaned_data.get('new_company_industry', 'Technology'),
                        'location': self.cleaned_data.get('new_company_location', 'Remote / Global'),
                        'description': f"Official profile for {self.cleaned_data['new_company_name'].strip()}.",
                    }
                )

            RecruiterProfile.objects.create(
                user=user,
                company=company,
                designation=self.cleaned_data.get('designation', ''),
                phone=self.cleaned_data.get('phone', ''),
                is_verified=True # Initial auto-approval for development, can be toggled by Admin
            )
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = [
            'headline', 'phone', 'location', 'avatar',
            'bio', 'education', 'experience', 'projects',
            'skills', 'resume', 'portfolio_url', 'github_url', 'linkedin_url'
        ]
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Backend Developer | Django & Python Enthusiast'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bengaluru, India'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell recruiters about yourself, your career ambitions, and strengths...'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'B.Tech in Computer Science, XYZ University (2022-2026) - CGPA: 8.5/10'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Software Intern at ABC Technologies (Summer 2025) - Built REST APIs and dashboard features.'}),
            'projects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '1. CareerConnect Portal: Job portal built with Django, SQLite, Bootstrap.\n2. E-commerce API: FastAPI backend with JWT auth.'}),
            'skills': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourportfolio.dev'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/yourhandle'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume and hasattr(resume, 'size'):
            max_size = 5 * 1024 * 1024  # 5MB
            if resume.size > max_size:
                raise ValidationError("Resume file size cannot exceed 5MB.")
            ext = resume.name.split('.')[-1].lower()
            if ext not in ['pdf', 'docx', 'doc']:
                raise ValidationError("Allowed file types are PDF, DOCX, or DOC.")
        return resume


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ['company', 'designation', 'phone']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
        }
