"""
Tests for Jobs API endpoints.

Test Coverage:
- Job search with filters
- Job retrieval
- Job listings
- Skill matching
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User, Skill, UserSkill
from apps.jobs.models import JobPlatform, Job, JobSkill
from apps.jobs.services import JobService


@pytest.fixture
def api_client():
    """API client fixture."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        auth0_id='test_auth0_123',
        email='testuser@example.com',
        username='testuser',
        full_name='Test User',
        date_of_birth='1990-01-01'
    )


@pytest.fixture
def job_platform(db):
    """Create a job platform."""
    return JobPlatform.objects.create(
        name='Test Platform',
        slug='test-platform',
        website_url='https://testplatform.com',
        is_active=True,
        scraping_enabled=True,
        target_countries=['Egypt']
    )


@pytest.fixture
def python_skill(db):
    """Create Python skill."""
    return Skill.objects.create(
        name='Python',
        slug='python',
        category='technical'
    )


@pytest.fixture
def django_skill(db):
    """Create Django skill."""
    return Skill.objects.create(
        name='Django',
        slug='django',
        category='technical'
    )


@pytest.fixture
def backend_job(db, job_platform, python_skill, django_skill):
    """Create a backend developer job."""
    job = Job.objects.create(
        platform=job_platform,
        external_id='backend_123',
        external_url='https://testplatform.com/jobs/backend_123',
        title='Backend Developer',
        company_name='Tech Company',
        description='Build scalable backend systems',
        requirements='Python, Django, PostgreSQL',
        location_city='Cairo',
        location_country='Egypt',
        is_remote=False,
        remote_type='on_site',
        job_type='full_time',
        experience_level='mid',
        experience_years_min=2,
        experience_years_max=5,
        salary_min=Decimal('15000.00'),
        salary_max=Decimal('25000.00'),
        salary_currency='EGP',
        salary_period='monthly',
        salary_disclosed=True,
        posted_date=timezone.now().date(),
        is_active=True
    )

    # Add skills
    JobSkill.objects.create(job=job, skill=python_skill, is_required=True)
    JobSkill.objects.create(job=job, skill=django_skill, is_required=True)

    return job


@pytest.fixture
def frontend_job(db, job_platform):
    """Create a frontend developer job."""
    return Job.objects.create(
        platform=job_platform,
        external_id='frontend_456',
        external_url='https://testplatform.com/jobs/frontend_456',
        title='Frontend Developer',
        company_name='Startup Inc',
        description='Build beautiful user interfaces',
        requirements='React, TypeScript, CSS',
        location_city='Alexandria',
        location_country='Egypt',
        is_remote=True,
        remote_type='fully_remote',
        job_type='full_time',
        experience_level='entry',
        experience_years_min=0,
        experience_years_max=2,
        salary_min=Decimal('8000.00'),
        salary_max=Decimal('15000.00'),
        salary_currency='EGP',
        salary_period='monthly',
        salary_disclosed=True,
        posted_date=timezone.now().date(),
        is_active=True
    )


@pytest.mark.django_db
class TestJobSearchAPI:
    """Tests for job search endpoint."""

    def test_search_all_jobs(self, api_client, test_user, backend_job, frontend_job):
        """Test listing all jobs without filters."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 2

    def test_search_by_title(self, api_client, test_user, backend_job, frontend_job):
        """Test searching jobs by title."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'query': 'Backend'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Backend Developer'

    def test_search_by_company(self, api_client, test_user, backend_job, frontend_job):
        """Test searching jobs by company name."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'query': 'Startup'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['company_name'] == 'Startup Inc'

    def test_filter_by_location(self, api_client, test_user, backend_job, frontend_job):
        """Test filtering jobs by location."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'location': 'Cairo'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['location_city'] == 'Cairo'

    def test_filter_by_job_type(self, api_client, test_user, backend_job, job_platform):
        """Test filtering by job type."""
        # Create internship job
        Job.objects.create(
            platform=job_platform,
            external_id='intern_789',
            external_url='https://testplatform.com/jobs/intern_789',
            title='Software Engineering Intern',
            company_name='Big Corp',
            location_city='Cairo',
            location_country='Egypt',
            job_type='internship',
            experience_level='entry',
            posted_date=timezone.now().date(),
            is_active=True
        )

        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'job_type': 'internship'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['job_type'] == 'internship'

    def test_filter_by_experience_level(self, api_client, test_user, backend_job, frontend_job):
        """Test filtering by experience level."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'experience_level': 'mid'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['experience_level'] == 'mid'

    def test_filter_remote_jobs(self, api_client, test_user, backend_job, frontend_job):
        """Test filtering remote jobs."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'is_remote': 'true'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['is_remote'] is True

    def test_filter_by_min_salary(self, api_client, test_user, backend_job, frontend_job):
        """Test filtering by minimum salary."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'min_salary': '12000'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert Decimal(response.data['results'][0]['salary_min']) >= Decimal('12000')

    def test_filter_by_skills(self, api_client, test_user, backend_job, python_skill):
        """Test filtering by required skills."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {'skills': 'Python'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Backend Developer'

    def test_combined_filters(self, api_client, test_user, backend_job, frontend_job):
        """Test combining multiple filters."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-search')
        response = api_client.get(url, {
            'location': 'Cairo',
            'job_type': 'full_time',
            'experience_level': 'mid'
        })

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Backend Developer'


@pytest.mark.django_db
class TestJobRetrievalAPI:
    """Tests for job retrieval endpoints."""

    def test_retrieve_job_by_id(self, api_client, test_user, backend_job):
        """Test retrieving a specific job."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-detail', args=[backend_job.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Backend Developer'
        assert response.data['company_name'] == 'Tech Company'
        assert 'skills' in response.data
        assert len(response.data['skills']) == 2  # Python and Django

    def test_retrieve_nonexistent_job(self, api_client, test_user):
        """Test retrieving a job that doesn't exist."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-detail', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestJobListAPI:
    """Tests for job listing endpoint."""

    def test_list_jobs(self, api_client, test_user, backend_job, frontend_job):
        """Test listing jobs with pagination."""
        api_client.force_authenticate(user=test_user)

        url = reverse('jobs:job-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 2

    def test_unauthenticated_access(self, api_client, backend_job):
        """Test that unauthenticated users cannot access jobs."""
        url = reverse('jobs:job-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestJobServiceSkillMatching:
    """Tests for job-skill matching service."""

    def test_match_jobs_with_user_skills(
        self, db, test_user, backend_job, python_skill, django_skill
    ):
        """Test matching jobs based on user skills."""
        # Add Python skill to user
        UserSkill.objects.create(
            user=test_user,
            skill=python_skill,
            proficiency_level='intermediate'
        )

        # Match jobs
        matches = JobService.match_jobs_for_user(test_user, limit=10)

        assert len(matches) > 0
        assert matches[0]['job'].id == backend_job.id
        assert matches[0]['match_score'] == 50  # Has 1 of 2 required skills
        assert 'Python' in matches[0]['matching_skills']
        assert 'Django' in matches[0]['missing_skills']

    def test_match_all_skills(
        self, db, test_user, backend_job, python_skill, django_skill
    ):
        """Test 100% match when user has all required skills."""
        # Add both skills to user
        UserSkill.objects.create(
            user=test_user,
            skill=python_skill,
            proficiency_level='advanced'
        )
        UserSkill.objects.create(
            user=test_user,
            skill=django_skill,
            proficiency_level='intermediate'
        )

        matches = JobService.match_jobs_for_user(test_user, limit=10)

        assert len(matches) > 0
        assert matches[0]['match_score'] == 100
        assert len(matches[0]['matching_skills']) == 2
        assert len(matches[0]['missing_skills']) == 0

    def test_no_user_skills(self, db, test_user, backend_job):
        """Test matching when user has no skills."""
        matches = JobService.match_jobs_for_user(test_user, limit=10)

        # Should return recent jobs with 0 match score
        assert len(matches) > 0
        assert all(match['match_score'] == 0 for match in matches)


@pytest.mark.django_db
class TestJobServiceMethods:
    """Tests for JobService methods."""

    def test_get_recent_jobs(self, db, backend_job, frontend_job, job_platform):
        """Test getting recently posted jobs."""
        # Create old job (posted 10 days ago)
        old_date = (timezone.now() - timedelta(days=10)).date()
        Job.objects.create(
            platform=job_platform,
            external_id='old_job',
            external_url='https://testplatform.com/jobs/old_job',
            title='Old Job',
            company_name='Old Company',
            location_city='Cairo',
            location_country='Egypt',
            job_type='full_time',
            posted_date=old_date,
            is_active=True
        )

        # Get recent jobs (last 7 days)
        recent_jobs = JobService.get_recent_jobs(days=7, limit=50)

        assert len(recent_jobs) == 2  # Only backend_job and frontend_job
        job_titles = [job.title for job in recent_jobs]
        assert 'Old Job' not in job_titles

    def test_get_remote_jobs(self, db, backend_job, frontend_job):
        """Test getting only remote jobs."""
        remote_jobs = JobService.get_remote_jobs(limit=50)

        assert len(remote_jobs) == 1
        assert remote_jobs[0].is_remote is True
        assert remote_jobs[0].title == 'Frontend Developer'

    def test_create_job(self, db, job_platform):
        """Test creating a job via service."""
        job = JobService.create_job(
            platform=job_platform,
            external_id='new_job_123',
            title='Data Scientist',
            company_name='AI Startup',
            location_city='Cairo',
            location_country='Egypt',
            job_type='full_time',
            experience_level='senior',
            description='Build ML models',
            external_url='https://testplatform.com/jobs/new_job_123'
        )

        assert job.id is not None
        assert job.title == 'Data Scientist'
        assert job.platform == job_platform
        assert job.is_active is True

    def test_create_job_prevents_duplicates(self, db, job_platform):
        """Test that creating same job twice updates instead of duplicating."""
        # Create job first time
        job1 = JobService.create_job(
            platform=job_platform,
            external_id='duplicate_123',
            title='First Title',
            company_name='Company A',
            location_city='Cairo',
            location_country='Egypt',
            external_url='https://testplatform.com/jobs/duplicate_123'
        )

        # Create same job again with different title
        job2 = JobService.create_job(
            platform=job_platform,
            external_id='duplicate_123',  # Same external_id
            title='Updated Title',
            company_name='Company A',
            location_city='Cairo',
            location_country='Egypt',
            external_url='https://testplatform.com/jobs/duplicate_123'
        )

        # Should be same job, updated
        assert job1.id == job2.id
        assert job2.title == 'Updated Title'
        assert Job.objects.filter(external_id='duplicate_123').count() == 1
