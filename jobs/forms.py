from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Job, JobCategory, Skill, JobReport


class JobForm(forms.ModelForm):
    deadline = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Last date for candidates to submit applications"
    )

    class Meta:
        model = Job
        fields = [
            'title', 'category', 'job_type', 'work_mode', 'experience_level',
            'location', 'salary_min', 'salary_max', 'salary_negotiable',
            'skills_required', 'description', 'responsibilities', 'requirements',
            'vacancies', 'deadline', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Django Backend Engineer'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'work_mode': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Pune, Maharashtra / Remote'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Salary (e.g. 600000)'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Salary (e.g. 1200000)'}),
            'salary_negotiable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'skills_required': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Comprehensive job overview and role details...'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '- Build high performance REST APIs\n- Write unit & integration tests\n- Collaborate with frontend engineers'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '- 2+ years of experience in Python & Django\n- Solid SQL and database design knowledge\n- Familiarity with Git & CI/CD'}),
            'vacancies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now().date():
            raise ValidationError("Job deadline cannot be in the past.")
        return deadline

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        salary_negotiable = cleaned_data.get('salary_negotiable')

        if not salary_negotiable and salary_min and salary_max and salary_min > salary_max:
            self.add_error('salary_max', "Maximum salary cannot be lower than minimum salary.")

        return cleaned_data


class JobReportForm(forms.ModelForm):
    class Meta:
        model = JobReport
        fields = ['reason', 'details']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide specific details regarding this report...'}),
        }
