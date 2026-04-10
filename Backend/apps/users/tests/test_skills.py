"""
Skills API Tests

Tests for skill management endpoints.
SRS Reference: FR-5 (Skill Tracking)
"""

import pytest
from decimal import Decimal
from rest_framework import status


def get_results(response_data):
    """Helper to get results from paginated or non-paginated response."""
    if isinstance(response_data, dict) and 'results' in response_data:
        return response_data['results']
    return response_data


@pytest.mark.django_db
class TestSkillList:
    """Tests for GET /api/v1/users/skills/"""

    def test_list_skills(self, authenticated_client, skill_set):
        """Test listing all skills."""
        url = '/api/v1/users/skills/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = get_results(response.data)
        assert len(results) == len(skill_set)

    def test_list_skills_by_category(self, authenticated_client, skill_set):
        """Test filtering skills by category."""
        url = '/api/v1/users/skills/?category=technical'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = get_results(response.data)
        # Should only return technical skills
        for skill in results:
            assert skill['category'] == 'technical'

    def test_list_skills_unauthenticated(self, api_client, skill_set):
        """Test skills list requires authentication."""
        url = '/api/v1/users/skills/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestSkillSearch:
    """Tests for GET /api/v1/users/skills/search/"""

    def test_search_skills_by_name(self, authenticated_client, skill_set):
        """Test searching skills by name."""
        url = '/api/v1/users/skills/search/?query=python'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any('python' in skill['name'].lower() for skill in response.data)

    def test_search_skills_with_limit(self, authenticated_client, skill_set):
        """Test searching skills with result limit."""
        # Query must be at least 2 characters
        url = '/api/v1/users/skills/search/?query=py&limit=2'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 2

    def test_search_skills_no_results(self, authenticated_client, skill_set):
        """Test search with no matching results."""
        url = '/api/v1/users/skills/search/?query=xyznonexistent'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_search_skills_missing_query(self, authenticated_client):
        """Test search without query parameter fails."""
        url = '/api/v1/users/skills/search/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSkillCategories:
    """Tests for GET /api/v1/users/skills/categories/"""

    def test_get_categories(self, authenticated_client):
        """Test getting skill categories."""
        url = '/api/v1/users/skills/categories/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        # Check structure
        for category in response.data:
            assert 'value' in category
            assert 'label' in category


@pytest.mark.django_db
class TestUserSkillList:
    """Tests for GET /api/v1/users/user-skills/"""

    def test_list_user_skills(self, authenticated_client, user_skill):
        """Test listing user's skills."""
        url = '/api/v1/users/user-skills/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = get_results(response.data)
        assert len(results) >= 1
        assert results[0]['skill']['name'] == user_skill.skill.name

    def test_list_user_skills_empty(self, authenticated_client, user):
        """Test listing skills for user with no skills."""
        url = '/api/v1/users/user-skills/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = get_results(response.data)
        assert len(results) == 0


@pytest.mark.django_db
class TestUserSkillCreate:
    """Tests for POST /api/v1/users/user-skills/"""

    def test_add_skill_success(self, authenticated_client, skill):
        """Test adding a skill to user profile."""
        url = '/api/v1/users/user-skills/'
        response = authenticated_client.post(url, {
            'skill_id': str(skill.id),
            'proficiency_level': 'intermediate',
            'years_of_experience': '2.5',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['skill']['name'] == skill.name
        assert response.data['proficiency_level'] == 'intermediate'

    def test_add_skill_with_type(self, authenticated_client, skill):
        """Test adding a skill with skill type specified."""
        url = '/api/v1/users/user-skills/'
        response = authenticated_client.post(url, {
            'skill_id': str(skill.id),
            'proficiency_level': 'expert',
            'skill_type': 'hard',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['proficiency_level'] == 'expert'

    def test_add_skill_invalid_id(self, authenticated_client):
        """Test adding skill with invalid ID fails."""
        url = '/api/v1/users/user-skills/'
        response = authenticated_client.post(url, {
            'skill_id': '00000000-0000-0000-0000-000000000000',
            'proficiency_level': 'beginner',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_skill_invalid_proficiency(self, authenticated_client, skill):
        """Test adding skill with invalid proficiency fails."""
        url = '/api/v1/users/user-skills/'
        response = authenticated_client.post(url, {
            'skill_id': str(skill.id),
            'proficiency_level': 'super-expert',  # Invalid
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_skill_does_not_emit_decimal_field_warnings(self, authenticated_client, skill, recwarn):
        """Adding a skill should not emit serializer validation warnings."""
        url = '/api/v1/users/user-skills/'
        response = authenticated_client.post(url, {
            'skill_id': str(skill.id),
            'proficiency_level': 'intermediate',
            'years_of_experience': '2.5',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert all(
            "max_value should be an integer or Decimal instance." not in str(warning.message)
            for warning in recwarn.list
        )


@pytest.mark.django_db
class TestUserSkillUpdate:
    """Tests for PUT/PATCH /api/v1/users/user-skills/{id}/"""

    def test_update_skill_proficiency(self, authenticated_client, user_skill):
        """Test updating skill proficiency level."""
        url = f'/api/v1/users/user-skills/{user_skill.id}/'
        response = authenticated_client.patch(url, {
            'proficiency_level': 'expert',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['proficiency_level'] == 'expert'

    def test_update_skill_experience(self, authenticated_client, user_skill):
        """Test updating years of experience."""
        url = f'/api/v1/users/user-skills/{user_skill.id}/'
        response = authenticated_client.patch(url, {
            'proficiency_level': 'advanced',
            'years_of_experience': '5.0',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['proficiency_level'] == 'advanced'

    def test_update_skill_does_not_emit_decimal_field_warnings(self, authenticated_client, user_skill, recwarn):
        """Updating a skill should not emit serializer validation warnings."""
        url = f'/api/v1/users/user-skills/{user_skill.id}/'
        response = authenticated_client.patch(url, {
            'proficiency_level': 'advanced',
            'years_of_experience': '5.0',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert all(
            "max_value should be an integer or Decimal instance." not in str(warning.message)
            for warning in recwarn.list
        )


@pytest.mark.django_db
class TestUserSkillDelete:
    """Tests for DELETE /api/v1/users/user-skills/{id}/"""

    def test_delete_skill_success(self, authenticated_client, user_skill):
        """Test removing a skill from user profile."""
        url = f'/api/v1/users/user-skills/{user_skill.id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's removed (soft deleted)
        list_response = authenticated_client.get('/api/v1/users/user-skills/')
        results = get_results(list_response.data)
        assert all(s['id'] != str(user_skill.id) for s in results)

    def test_delete_other_user_skill(self, authenticated_client, another_user, skill, db):
        """Test cannot delete another user's skill."""
        from apps.users.models import UserSkill

        # Create skill for another user
        other_skill = UserSkill.objects.create(
            user=another_user,
            skill=skill,
            proficiency_level='beginner',
        )

        url = f'/api/v1/users/user-skills/{other_skill.id}/'
        response = authenticated_client.delete(url)

        # Should fail - either 404 or 403
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
class TestSkillGapAnalysis:
    """Tests for GET /api/v1/users/user-skills/gap_analysis/"""

    def test_gap_analysis_success(self, authenticated_client, user_skill, skill_set):
        """Test skill gap analysis."""
        target_skills = ','.join([s.name for s in skill_set[:3]])
        url = f'/api/v1/users/user-skills/gap_analysis/?target_skills={target_skills}'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'current_skills' in response.data or 'missing_skills' in response.data

    def test_gap_analysis_missing_param(self, authenticated_client):
        """Test gap analysis without target_skills fails."""
        url = '/api/v1/users/user-skills/gap_analysis/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
