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
        return HttpResponseForbidden('Access restricted to job seekers.')

    seeker_profile = get_object_or_404(JobSeekerProfile, user=request.user)
    resume = getattr(seeker_profile, 'resume', None)
    recommendations = []
    if resume and resume.extracted_text.strip():
        active_jobs = Job.objects.filter(is_active=True)
        for job in active_jobs:
            score = compute_relevance(job.description, resume.extracted_text)
            recommendations.append({'job': job, 'score': score})
        recommendations.sort(key=lambda item: item['score'], reverse=True)

    applications = Application.objects.filter(job_seeker=seeker_profile).select_related('job')

    return render(request, 'core/seeker_dashboard.html', {
        'seeker_profile': seeker_profile,
        'resume': resume,
        'recommendations': recommendations[:10],
        'applications': applications,
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
            resume_obj = form.save(commit=False)
            resume_obj.job_seeker = seeker_profile
            if resume_obj.uploaded_file:
                extracted = extract_text_from_file(resume_obj.uploaded_file)
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

    application, created = Application.objects.get_or_create(
        job=job,
        job_seeker=seeker_profile,
        defaults={'match_score': compute_relevance(job.description, resume.extracted_text)},
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

    recent_logs = [
        {'user': 'John Doe', 'access_time': '12:00 PM', 'status': 'Successful'},
        {'user': 'Jane Smith', 'access_time': '12:15 PM', 'status': 'Failed'},
    ]

    context = {
        'total_users': total_users,
        'seekers_count': seekers_count,
        'employers_count': employers_count,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'data_breaches': 0,
        'alerts': 5,
        'recent_logs': recent_logs,
    }
    return render(request, 'core/admin_dashboard.html', context)
