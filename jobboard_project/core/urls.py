from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.account_choice, name='account_choice'),
    path('register/seeker/', views.register_seeker, name='register_seeker'),
    path('register/employer/', views.register_employer, name='register_employer'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('seeker-dashboard/', views.seeker_dashboard, name='seeker_dashboard'),
    path('employer-dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('resume/upload/', views.upload_resume, name='upload_resume'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('jobs/create/', views.create_job, name='create_job'),
    path('jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('jobs/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
]
