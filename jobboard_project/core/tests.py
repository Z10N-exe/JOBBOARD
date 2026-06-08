from django.test import TestCase
from django.urls import reverse

from .models import Application, CustomUser, EmployerProfile, Job, JobSeekerProfile


class CoreTests(TestCase):
    def test_create_superuser_assigns_admin_role(self):
        admin = CustomUser.objects.create_superuser(email='admin2@example.com', password='AdminPass123')
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, 'admin')

    def test_employer_dashboard_requires_login(self):
        response = self.client.get(reverse('employer_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_employer_dashboard_access(self):
        user = CustomUser.objects.create_user(email='employer@test.com', password='Secret123', role='employer')
        EmployerProfile.objects.create(user=user, company_name='Acme Inc')
        self.client.login(username='employer@test.com', password='Secret123')
        response = self.client.get(reverse('employer_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employer Dashboard')

    def test_register_seeker_redirects_after_success(self):
        response = self.client.post(
            reverse('register_seeker'),
            data={
                'email': 'seeker@test.com',
                'password1': 'TestPass123',
                'password2': 'TestPass123',
                'role': 'seeker',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'phone': '1234567890',
                'location': 'Remote',
                'skills_text': 'Python,Django',
                'experience_years': 2,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(email='seeker@test.com', role='seeker').exists())
        self.assertRedirects(response, reverse('seeker_dashboard'))

    def test_register_employer_redirects_after_success(self):
        response = self.client.post(
            reverse('register_employer'),
            data={
                'email': 'employer2@test.com',
                'password1': 'TestPass123',
                'password2': 'TestPass123',
                'role': 'employer',
                'company_name': 'Test Corp',
                'company_description': 'We build test products.',
                'contact_phone': '1112223333',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(email='employer2@test.com', role='employer').exists())
        self.assertRedirects(response, reverse('employer_dashboard'))

    def test_employer_can_create_job(self):
        user = CustomUser.objects.create_user(email='employer2@test.com', password='Secret123', role='employer')
        EmployerProfile.objects.create(user=user, company_name='Acme Inc')
        self.client.login(username='employer2@test.com', password='Secret123')
        response = self.client.post(
            reverse('create_job'),
            data={
                'title': 'Software Engineer',
                'description': 'Build software solutions',
                'required_skills_text': 'Python,Django',
                'min_experience': 2,
                'location': 'Remote',
                'employment_type': 'full',
                'is_active': True,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Job.objects.filter(title='Software Engineer', employer__user=user).exists())
        self.assertRedirects(response, reverse('employer_dashboard'))

    def test_application_status_breakdown_available(self):
        seeker = CustomUser.objects.create_user(email='seeker2@test.com', password='Secret123', role='seeker')
        seeker_profile = JobSeekerProfile.objects.create(user=seeker, first_name='Jane', last_name='Doe')
        employer = CustomUser.objects.create_user(email='employer3@test.com', password='Secret123', role='employer')
        employer_profile = EmployerProfile.objects.create(user=employer, company_name='Acme Inc')
        job = Job.objects.create(
            employer=employer_profile,
            title='Test Job',
            description='Test description',
            required_skills_text='Python',
            min_experience=1,
            location='Remote',
            employment_type='full',
            is_active=True,
        )
        Application.objects.create(job=job, job_seeker=seeker_profile, match_score=0.8, status='pending')
        self.client.login(username='employer3@test.com', password='Secret123')
        response = self.client.get(reverse('job_applicants', args=[job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Applicants')
        self.assertContains(response, 'Pending')
