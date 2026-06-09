from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .forms import (
    ApplicationStatusForm,
    CustomUserCreationForm,
    EmployerProfileForm,
    JobForm,
    JobSeekerProfileForm,
    ResumeUploadForm,
)
from .models import (
    Application,
    CustomUser,
    EmployerProfile,
    Job,
    JobSeekerProfile,
    Resume,
)
from .utils import compute_relevance, extract_text_from_file


def home(request):
    return render(request, 'core/home.html')


def account_choice(request):
    return render(request, 'core/register_choice.html')


def register_seeker(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = JobSeekerProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'seeker'
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('dashboard')
    else:
        user_form = CustomUserCreationForm(initial={'role': 'seeker'})
        profile_form = JobSeekerProfileForm()

    return render(
        request,
        'core/register_seeker.html',
        {'user_form': user_form, 'profile_form': profile_form},
    )


def register_employer(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = EmployerProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'employer'
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            messages.success(request, 'Employer account created successfully.')
            return redirect('dashboard')
    else:
        user_form = CustomUserCreationForm(initial={'role': 'employer'})
        profile_form = EmployerProfileForm()

    return render(
        request,
        'core/register_employer.html',
        {'user_form': user_form, 'profile_form': profile_form},
    )


@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    if request.user.role == 'employer':
        return redirect('employer_dashboard')
    return redirect('seeker_dashboard')


@login_required
def seeker_dashboard(request):
    if request.user.role != 'seeker':
        messages.error(request, 'Access restricted to job seekers. Please login with a job seeker account.')
        return redirect('login')

    seeker_profile = get_object_or_404(JobSeekerProfile, user=request.user)
    resume = getattr(seeker_profile, 'resume', None)
    
    # Calculate profile completeness
    completeness_fields = {
        'first_name': bool(seeker_profile.first_name),
        'last_name': bool(seeker_profile.last_name),
        'phone': bool(seeker_profile.phone),
        'location': bool(seeker_profile.location),
        'skills_text': bool(seeker_profile.skills_text),
        'resume': bool(resume and resume.extracted_text.strip()),
    }
    completeness_score = sum(completeness_fields.values()) / len(completeness_fields) * 100
    
    recommendations = []
    if resume and resume.extracted_text.strip():
        active_jobs = Job.objects.filter(is_active=True)
        for job in active_jobs:
            score, keywords = compute_relevance(job.description, resume.extracted_text)
            recommendations.append({'job': job, 'score': score, 'keywords': keywords})
        recommendations.sort(key=lambda item: item['score'], reverse=True)

    applications = Application.objects.filter(job_seeker=seeker_profile).select_related('job')

    return render(request, 'core/seeker_dashboard.html', {
        'seeker_profile': seeker_profile,
        'resume': resume,
        'recommendations': recommendations[:10],
        'applications': applications,
        'completeness_score': completeness_score,
        'completeness_fields': completeness_fields,
    })


@login_required
def employer_dashboard(request):
    if request.user.role != 'employer':
        return HttpResponseForbidden('Access restricted to employers.')

    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    jobs = Job.objects.filter(employer=employer_profile).annotate(applicant_count=Count('application'))
    total_jobs = jobs.count()
    active_jobs = jobs.filter(is_active=True).count()
    total_applicants = Application.objects.filter(job__employer=employer_profile).count()
    top_jobs = jobs.order_by('-applicant_count')[:3]

    return render(request, 'core/employer_dashboard.html', {
        'employer_profile': employer_profile,
        'jobs': jobs,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applicants': total_applicants,
        'top_jobs': top_jobs,
    })


@login_required
def upload_resume(request):
    if request.user.role != 'seeker':
        return HttpResponseForbidden('Access restricted to job seekers.')

    seeker_profile = get_object_or_404(JobSeekerProfile, user=request.user)
    resume = getattr(seeker_profile, 'resume', None)

    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES, instance=resume)
        if form.is_valid():
            # Extract text from uploaded file before saving
            if form.cleaned_data.get('uploaded_file'):
                extracted = extract_text_from_file(form.cleaned_data['uploaded_file'])
            else:
                extracted = ''
            
            # Save with job_seeker parameter only when creating new resume
            # When updating, the instance already has the job_seeker set
            if resume is None:
                resume_obj = form.save(commit=False, job_seeker=seeker_profile)
            else:
                resume_obj = form.save(commit=False)
            resume_obj.extracted_text = extracted
            resume_obj.save()
            messages.success(request, 'Resume uploaded and parsed successfully.')
            return redirect('seeker_dashboard')
    else:
        form = ResumeUploadForm(instance=resume)

    return render(request, 'core/resume_upload.html', {'form': form, 'resume': resume})


@login_required
def job_list(request):
    if request.user.role != 'seeker':
        return HttpResponseForbidden('Access restricted to job seekers.')

    query = request.GET.get('q', '')
    jobs = Job.objects.filter(is_active=True)
    if query:
        jobs = jobs.filter(title__icontains=query) | jobs.filter(description__icontains=query)
    return render(request, 'core/job_list.html', {'jobs': jobs, 'query': query})


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    return render(request, 'core/job_detail.html', {'job': job})


@login_required
def apply_job(request, job_id):
    if request.user.role != 'seeker':
        return HttpResponseForbidden('Access restricted to job seekers.')

    job = get_object_or_404(Job, id=job_id, is_active=True)
    seeker_profile = get_object_or_404(JobSeekerProfile, user=request.user)
    resume = getattr(seeker_profile, 'resume', None)
    if not resume or not resume.extracted_text.strip():
        messages.error(request, 'Please upload a resume before applying.')
        return redirect('upload_resume')

    score, keywords = compute_relevance(job.description, resume.extracted_text)
    application, created = Application.objects.get_or_create(
        job=job,
        job_seeker=seeker_profile,
        defaults={'match_score': score},
    )

    if not created:
        messages.warning(request, 'You have already applied to this job.')
    else:
        messages.success(request, 'Application submitted successfully.')

    return redirect('seeker_dashboard')


@login_required
def create_job(request):
    if request.user.role != 'employer':
        return HttpResponseForbidden('Access restricted to employers.')

    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = employer_profile
            job.save()
            messages.success(request, 'Job created successfully.')
            return redirect('employer_dashboard')
    else:
        form = JobForm()
    return render(request, 'core/job_form.html', {'form': form, 'title': 'Post New Job'})


@login_required
def edit_job(request, job_id):
    if request.user.role != 'employer':
        return HttpResponseForbidden('Access restricted to employers.')

    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    job = get_object_or_404(Job, id=job_id, employer=employer_profile)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully.')
            return redirect('employer_dashboard')
    else:
        form = JobForm(instance=job)

    return render(request, 'core/job_form.html', {'form': form, 'title': 'Edit Job'})


@login_required
def delete_job(request, job_id):
    if request.user.role != 'employer':
        return HttpResponseForbidden('Access restricted to employers.')

    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    job = get_object_or_404(Job, id=job_id, employer=employer_profile)
    job.delete()
    messages.success(request, 'Job deleted successfully.')
    return redirect('employer_dashboard')


@login_required
def job_applicants(request, job_id):
    if request.user.role != 'employer':
        return HttpResponseForbidden('Access restricted to employers.')

    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    job = get_object_or_404(Job, id=job_id, employer=employer_profile)
    applications = Application.objects.filter(job=job).select_related('job_seeker__user')
    status_counts = applications.values('status').annotate(count=Count('id'))
    
    # Add top keywords to each application
    for application in applications:
        try:
            if application.job_seeker.resume and application.job_seeker.resume.extracted_text:
                _, keywords = compute_relevance(job.description, application.job_seeker.resume.extracted_text)
                application.top_keywords = keywords
            else:
                application.top_keywords = []
        except JobSeekerProfile.resume.RelatedObjectDoesNotExist:
            application.top_keywords = []
    
    return render(request, 'core/applicants.html', {
        'job': job,
        'applications': applications,
        'status_counts': status_counts,
    })


@login_required
def update_application_status(request, application_id):
    if request.user.role != 'employer':
        return HttpResponseForbidden('Access restricted to employers.')

    application = get_object_or_404(Application, id=application_id)
    job = application.job
    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    if job.employer != employer_profile:
        return HttpResponseForbidden('Access restricted to the owning employer.')

    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application status updated.')
            return redirect('job_applicants', job_id=job.id)
    else:
        form = ApplicationStatusForm(instance=application)

    return render(request, 'core/update_application_status.html', {'form': form, 'application': application})


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden('You do not have permission to access this page.')

    total_users = CustomUser.objects.exclude(role='admin').count()
    seekers_count = CustomUser.objects.filter(role='seeker').count()
    employers_count = CustomUser.objects.filter(role='employer').count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    
    # Get all users for management
    all_users = CustomUser.objects.exclude(role='admin').order_by('-date_joined')
    
    # Get recent jobs for moderation
    recent_jobs = Job.objects.order_by('-date_posted')[:10]

    context = {
        'total_users': total_users,
        'seekers_count': seekers_count,
        'employers_count': employers_count,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'all_users': all_users,
        'recent_jobs': recent_jobs,
        'data_breaches': 0,
        'alerts': 5,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def admin_deactivate_user(request, user_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden('Access restricted to administrators.')
    
    user = get_object_or_404(CustomUser, id=user_id)
    if user.role == 'admin':
        messages.error(request, 'Cannot deactivate another administrator.')
        return redirect('admin_dashboard')
    
    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.email} has been {status}.')
    return redirect('admin_dashboard')


@login_required
def admin_delete_user(request, user_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden('Access restricted to administrators.')
    
    user = get_object_or_404(CustomUser, id=user_id)
    if user.role == 'admin':
        messages.error(request, 'Cannot delete another administrator.')
        return redirect('admin_dashboard')
    
    email = user.email
    user.delete()
    messages.success(request, f'User {email} has been deleted.')
    return redirect('admin_dashboard')


@login_required
def admin_delete_job(request, job_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden('Access restricted to administrators.')
    
    job = get_object_or_404(Job, id=job_id)
    job_title = job.title
    job.delete()
    messages.success(request, f'Job "{job_title}" has been deleted by admin.')
    return redirect('admin_dashboard')
