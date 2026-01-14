"""
Users Service Layer

Handles all user-related business logic including user creation, authentication,
profile management, and skill tracking.
"""

from typing import Optional, List, Dict, Any
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import User, Skill, UserSkill


User = get_user_model()


class UserService:
    """Service for user management operations"""

    @staticmethod
    def create_user(
        email: str,
        password: str,
        **extra_fields
    ) -> User:
        """
        Create a new user with validation.

        Args:
            email: User email address
            password: User password (will be hashed)
            **extra_fields: Additional user fields (username, full_name, date_of_birth, etc.)

        Returns:
            User: Created user instance

        Raises:
            ValidationError: If email already exists or validation fails
        """
        if User.objects.filter(email=email).exists():
            raise ValidationError(f"User with email {email} already exists")

        user = User.objects.create_user(
            email=email,
            password=password,
            **extra_fields
        )

        return user

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return User.objects.get(email=email, is_deleted=False)
        except User.DoesNotExist:
            return None

    @staticmethod
    def update_user_profile(
        user: User,
        **fields
    ) -> User:
        """
        Update user profile fields.

        Args:
            user: User instance to update
            **fields: Fields to update

        Returns:
            User: Updated user instance
        """
        allowed_fields = [
            'username', 'full_name', 'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'location', 'bio', 'linkedin_url', 'github_url',
            'portfolio_url', 'current_job_title', 'years_of_experience',
            'education_level', 'preferred_learning_style', 'preferred_language',
            'timezone', 'onboarding_completed', 'onboarding_step'
        ]

        for field, value in fields.items():
            if field in allowed_fields:
                setattr(user, field, value)

        user.save()
        return user

    @staticmethod
    def deactivate_user(user: User) -> None:
        """Soft delete user account"""
        user.is_active = False
        user.save(update_fields=['is_active', 'updated_at'])

    @staticmethod
    def reactivate_user(user: User) -> None:
        """Reactivate user account"""
        user.is_active = True
        user.save(update_fields=['is_active', 'updated_at'])


class SkillService:
    """Service for skill management operations"""

    @staticmethod
    def get_or_create_skill(name: str, category: str = 'general') -> Skill:
        """
        Get existing skill or create new one.

        Args:
            name: Skill name
            category: Skill category

        Returns:
            Skill: Skill instance
        """
        skill, created = Skill.objects.get_or_create(
            name=name,
            defaults={'category': category}
        )
        return skill

    @staticmethod
    def get_skills_by_category(category: str) -> List[Skill]:
        """Get all skills in a category"""
        return list(Skill.objects.filter(
            category=category,
            is_deleted=False
        ))

    @staticmethod
    def search_skills(query: str) -> List[Skill]:
        """Search skills by name"""
        return list(Skill.objects.filter(
            name__icontains=query,
            is_deleted=False
        ))

    @staticmethod
    @transaction.atomic
    def add_user_skill(
        user: User,
        skill: Skill,
        proficiency_level: str = 'beginner',
        years_of_experience: int = 0
    ) -> UserSkill:
        """
        Add skill to user profile.

        Args:
            user: User instance
            skill: Skill instance
            proficiency_level: Proficiency level (beginner, intermediate, advanced, expert)
            years_of_experience: Years of experience with this skill

        Returns:
            UserSkill: Created user skill association
        """
        user_skill, created = UserSkill.objects.update_or_create(
            user=user,
            skill=skill,
            defaults={
                'proficiency_level': proficiency_level,
                'years_of_experience': years_of_experience
            }
        )
        return user_skill

    @staticmethod
    def get_user_skills(user: User) -> List[UserSkill]:
        """Get all skills for a user"""
        return list(UserSkill.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('skill'))

    @staticmethod
    def remove_user_skill(user: User, skill: Skill) -> None:
        """Remove skill from user profile (soft delete)"""
        try:
            user_skill = UserSkill.objects.get(user=user, skill=skill)
            user_skill.is_deleted = True
            user_skill.save(update_fields=['is_deleted', 'updated_at'])
        except UserSkill.DoesNotExist:
            pass

    @staticmethod
    def update_skill_proficiency(
        user: User,
        skill: Skill,
        proficiency_level: str,
        years_of_experience: Optional[int] = None
    ) -> UserSkill:
        """Update user's proficiency level for a skill"""
        try:
            user_skill = UserSkill.objects.get(user=user, skill=skill)
            user_skill.proficiency_level = proficiency_level

            if years_of_experience is not None:
                user_skill.years_of_experience = years_of_experience

            user_skill.save()
            return user_skill
        except UserSkill.DoesNotExist:
            raise ValidationError(f"User does not have skill: {skill.name}")

    @staticmethod
    def get_skill_gap_analysis(user: User, target_skills: List[str]) -> Dict[str, Any]:
        """
        Analyze skill gaps between user's current skills and target skills.

        Args:
            user: User instance
            target_skills: List of target skill names

        Returns:
            dict: {
                'current_skills': [...],
                'missing_skills': [...],
                'skills_to_improve': [...]
            }
        """
        user_skills = UserSkill.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('skill')

        current_skill_names = {us.skill.name for us in user_skills}
        target_skill_set = set(target_skills)

        missing_skills = target_skill_set - current_skill_names

        skills_to_improve = [
            {
                'skill': us.skill.name,
                'current_level': us.proficiency_level,
                'target_level': 'expert'
            }
            for us in user_skills
            if us.skill.name in target_skill_set and us.proficiency_level != 'expert'
        ]

        return {
            'current_skills': list(current_skill_names),
            'missing_skills': list(missing_skills),
            'skills_to_improve': skills_to_improve
        }
