from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import Application, CustomUser, Job, JobSeekerProfile, EmployerProfile, Resume


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email Address')

    class Meta:
        model = CustomUser
        fields = ('email', 'role')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'role', 'is_active', 'is_staff')


class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            'first_name',
            'last_name',
            'phone',
            'location',
            'skills_text',
            'experience_years',
        ]
        widgets = {
            'skills_text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'List key skills separated by commas'}),
        }


class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = [
            'company_name',
            'company_description',
            'contact_phone',
        ]
        widgets = {
            'company_description': forms.Textarea(attrs={'rows': 3}),
        }


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title',
            'description',
            'required_skills_text',
            'min_experience',
            'location',
            'employment_type',
            'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'required_skills_text': forms.Textarea(attrs={'rows': 3}),
        }


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['uploaded_file']


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']
