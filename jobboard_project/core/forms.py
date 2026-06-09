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

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            if len(password) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
            if not any(c.isupper() for c in password):
                raise ValidationError('Password must contain at least one uppercase letter.')
            if not any(c.islower() for c in password):
                raise ValidationError('Password must contain at least one lowercase letter.')
            if not any(c.isdigit() for c in password):
                raise ValidationError('Password must contain at least one digit.')
            if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
                raise ValidationError('Password must contain at least one special character.')
        return password


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
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.doc'}
    
    class Meta:
        model = Resume
        fields = ['uploaded_file']
    
    def clean_uploaded_file(self):
        uploaded_file = self.cleaned_data.get('uploaded_file')
        if not uploaded_file:
            raise ValidationError('Please upload a file.')
        
        # Check file extension
        filename = uploaded_file.name.lower()
        file_ext = None
        for ext in self.ALLOWED_EXTENSIONS:
            if filename.endswith(ext):
                file_ext = ext
                break
        
        if not file_ext:
            allowed = ', '.join(self.ALLOWED_EXTENSIONS)
            raise ValidationError(f'Invalid file type. Allowed types: {allowed}')
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if uploaded_file.size > max_size:
            raise ValidationError('File size must not exceed 5MB.')
        
        return uploaded_file
    
    def save(self, commit=True, job_seeker=None):
        """
        Override save to handle OneToOneField primary key properly.
        When creating a new Resume, we need to explicitly set the job_seeker.
        """
        instance = super().save(commit=False)
        
        # Set the job_seeker if provided
        if job_seeker is not None:
            instance.job_seeker = job_seeker
        
        if commit:
            instance.save()
        
        return instance


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']
