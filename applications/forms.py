from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Application, Interview


class ApplicationForm(forms.ModelForm):
    use_profile_resume = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'use_profile_resume'})
    )

    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']
        widgets = {
            'resume': forms.FileInput(attrs={'class': 'form-control', 'id': 'custom_resume_input'}),
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write a compelling note explaining why you are the best fit for this role...'}),
        }

    def __init__(self, *args, candidate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate = candidate
        if self.candidate and hasattr(self.candidate, 'candidate_profile') and self.candidate.candidate_profile.resume:
            self.fields['resume'].required = False
        else:
            self.fields['resume'].required = True
            self.fields['use_profile_resume'].widget.attrs['disabled'] = 'disabled'
            self.fields['use_profile_resume'].initial = False

    def clean(self):
        cleaned_data = super().clean()
        use_profile = cleaned_data.get('use_profile_resume')
        uploaded_resume = cleaned_data.get('resume')

        if not uploaded_resume:
            if use_profile and self.candidate and hasattr(self.candidate, 'candidate_profile') and self.candidate.candidate_profile.resume:
                cleaned_data['resume'] = self.candidate.candidate_profile.resume
            else:
                self.add_error('resume', "Please upload a resume file (PDF or DOCX).")
        return cleaned_data


class ApplicationStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status', 'recruiter_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'recruiter_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional internal recruiter notes...'}),
        }


class InterviewScheduleForm(forms.ModelForm):
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    scheduled_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Interview
        fields = ['scheduled_date', 'scheduled_time', 'mode', 'location_or_link', 'instructions']
        widgets = {
            'mode': forms.Select(attrs={'class': 'form-select'}),
            'location_or_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/xyz-abc or Office Room 402'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. Please bring an ID proof and prepare to discuss your Django project architecture.'}),
        }

    def clean_scheduled_date(self):
        date = self.cleaned_data.get('scheduled_date')
        if date and date < timezone.now().date():
            raise ValidationError("Interview date cannot be in the past.")
        return date
