"""
Career Tools API Tests

Tests for Resume CRUD, PDF/DOCX generation, and ATS optimization.
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User
from apps.career_tools.models import Resume


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='testuser@example.com',
        password='testpass123',
        username='testuser',
        full_name='Test User',
        auth0_id='auth0|test12345',
        date_of_birth='1990-01-01',
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def sample_resume_data():
    return {
        'title': 'Software Engineer Resume',
        'template_name': 'modern',
        'personal_info': {
            'name': 'Ahmed Mohamed',
            'email': 'ahmed@example.com',
            'phone': '+20 123 456 7890',
            'location': 'Cairo, Egypt',
            'summary': 'Full-stack developer with 3 years of experience.',
        },
        'work_experience': {
            'items': [
                {
                    'role': 'Backend Developer',
                    'company': 'Tech Corp',
                    'start_date': 'Jan 2022',
                    'end_date': 'Present',
                    'achievements': [
                        'Built REST APIs serving 10k users',
                        'Reduced query time by 40%',
                    ],
                }
            ]
        },
        'education': {
            'items': [
                {
                    'degree': 'B.Sc. Computer Science',
                    'institution': 'Cairo University',
                    'graduation_date': '2021',
                }
            ]
        },
        'skills': {'items': ['Python', 'Django', 'React', 'PostgreSQL', 'Docker']},
    }


@pytest.fixture
def resume(user, sample_resume_data):
    return Resume.objects.create(user=user, **sample_resume_data)


class TestResumeListCreate:
    """Test resume list and create endpoints."""

    def test_list_resumes_empty(self, auth_client):
        url = reverse('career_tools:resume-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_resume(self, auth_client, sample_resume_data):
        url = reverse('career_tools:resume-list')
        response = auth_client.post(url, sample_resume_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Software Engineer Resume'

    def test_create_resume_unauthenticated(self, api_client, sample_resume_data):
        url = reverse('career_tools:resume-list')
        response = api_client.post(url, sample_resume_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestResumeDetailUpdateDelete:
    """Test resume detail, update, and delete endpoints."""

    def test_get_resume_detail(self, auth_client, resume):
        url = reverse('career_tools:resume-detail', kwargs={'pk': resume.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == resume.title

    def test_update_resume(self, auth_client, resume):
        url = reverse('career_tools:resume-detail', kwargs={'pk': resume.id})
        response = auth_client.patch(url, {'title': 'Updated Title'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        resume.refresh_from_db()
        assert resume.title == 'Updated Title'

    def test_delete_resume(self, auth_client, resume):
        url = reverse('career_tools:resume-detail', kwargs={'pk': resume.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        resume.refresh_from_db()
        assert resume.is_deleted is True


class TestResumeGeneration:
    """Test PDF and DOCX generation."""

    def test_generate_pdf(self, auth_client, resume):
        url = reverse('career_tools:resume-generate', kwargs={'pk': resume.id})
        response = auth_client.post(url, {'format': 'pdf'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'file_url' in response.data
        resume.refresh_from_db()
        assert resume.pdf_file

    def test_generate_docx(self, auth_client, resume):
        url = reverse('career_tools:resume-generate', kwargs={'pk': resume.id})
        response = auth_client.post(url, {'format': 'docx'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        resume.refresh_from_db()
        assert resume.docx_file

    def test_generate_invalid_format(self, auth_client, resume):
        url = reverse('career_tools:resume-generate', kwargs={'pk': resume.id})
        response = auth_client.post(url, {'format': 'txt'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestATSOptimization:
    """Test ATS optimization (will use rule-based fallback if Ollama is down)."""

    def test_optimize_ats(self, auth_client, resume):
        url = reverse('career_tools:resume-optimize-ats', kwargs={'pk': resume.id})
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'ats_score' in response.data
        assert 'suggestions' in response.data
        resume.refresh_from_db()
        assert resume.is_ats_optimized is True
        assert resume.ats_score > 0
