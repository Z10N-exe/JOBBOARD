from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('role') != 'admin':
            raise ValueError('Superuser must have role=admin.')
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model that uses email as the unique identifier
    and adds a role field to distinguish between job seekers, employers, and administrators.
    """
    username = None
    email = models.EmailField(_('email address'), unique=True)

    ROLE_CHOICES = [
        ('seeker', 'Job Seeker'),
        ('employer', 'Employer'),
        ('admin', 'Administrator'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='seeker')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)  # Added for email verification

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.email


class JobSeekerProfile(models.Model):
    """
    Profile for job seekers, linked one-to-one with CustomUser.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    skills_text = models.TextField(blank=True, null=True)
    experience_years = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Resume(models.Model):
    """
    Resume uploaded by a job seeker.
    """
    job_seeker = models.OneToOneField(JobSeekerProfile, on_delete=models.CASCADE, primary_key=True)
    uploaded_file = models.FileField(upload_to='resumes/%Y/%m/%d/', blank=True, null=True)
    extracted_text = models.TextField(help_text="Text extracted from the uploaded resume file")
    uploaded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uploaded_file.name if self.uploaded_file else f"Resume for {self.job_seeker}"


class EmployerProfile(models.Model):
    """
    Profile for employers, linked one-to-one with CustomUser.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    company_name = models.CharField(max_length=100)
    company_description = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.company_name


class Job(models.Model):
    """
    Job posting by an employer.
    """
    EMPLOYMENT_TYPE_CHOICES = [
        ('full', 'Full-time'),
        ('part', 'Part-time'),
        ('contract', 'Contract'),
    ]

    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    required_skills_text = models.TextField(blank=True, null=True)
    min_experience = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    employment_type = models.CharField(max_length=10, choices=EMPLOYMENT_TYPE_CHOICES, default='full')
    date_posted = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Application(models.Model):
    """
    Application of a job seeker to a job.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('interviewed', 'Interviewed'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    job_seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE)
    match_score = models.FloatField(help_text="Score between 0 and 1 indicating match quality")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'job_seeker')  # Prevent duplicate applications

    def __str__(self):
        return f"{self.job_seeker} applied to {self.job}"


class MatchScore(models.Model):
    """
    Cached match scores between jobs and job seekers (optional, for performance).
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    job_seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE)
    score = models.FloatField(help_text="Match score between 0 and 1")
    top_keywords = models.CharField(max_length=255, help_text="Comma-separated list of top contributing keywords")
    computed_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'job_seeker')

    def __str__(self):
        return f"Match score for {self.job_seeker} on {self.job}: {self.score}"