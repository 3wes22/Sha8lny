"""
Django admin configuration for User Service models.

Provides customized admin interfaces for User, Skill, UserSkill, and UserPreferences.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.users.models import User, Skill, UserSkill, UserPreferences


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = [
        'email',
        'username',
        'full_name',
        'is_active',
        'is_premium',
        'is_staff',
        'account_status',
        'onboarding_completed',
        'created_at',
    ]

    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'is_premium',
        'account_status',
        'onboarding_completed',
        'email_verified',
        'preferred_language',
        'created_at',
    ]

    search_fields = [
        'email',
        'username',
        'full_name',
        'auth0_id',
    ]

    ordering = ['-created_at']

    readonly_fields = [
        'id',
        'auth0_id',
        'created_at',
        'updated_at',
        'last_login_at',
        'deleted_at',
        'age',
    ]

    fieldsets = (
        (_('Authentication'), {
            'fields': (
                'id',
                'auth0_id',
                'email',
                'email_verified',
                'username',
                'password',
            )
        }),
        (_('Profile Information'), {
            'fields': (
                'full_name',
                'date_of_birth',
                'age',
                'phone_number',
            )
        }),
        (_('Account Status'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_premium',
                'account_status',
            )
        }),
        (_('Onboarding'), {
            'fields': (
                'onboarding_completed',
                'onboarding_step',
            )
        }),
        (_('Preferences'), {
            'fields': (
                'preferred_language',
                'timezone',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'groups',
                'user_permissions',
            ),
            'classes': ('collapse',),
        }),
        (_('Audit Information'), {
            'fields': (
                'created_at',
                'updated_at',
                'last_login_at',
                'is_deleted',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'full_name',
                'date_of_birth',
                'password1',
                'password2',
            ),
        }),
    )

    def age(self, obj):
        """Display calculated age."""
        return obj.age
    age.short_description = _('Age')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin interface for Skill model."""

    list_display = [
        'name',
        'slug',
        'category',
        'parent_skill',
        'skill_level',
        'popularity_score',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'category',
        'skill_level',
        'is_active',
        'created_at',
    ]

    search_fields = [
        'name',
        'slug',
        'description',
    ]

    ordering = ['-popularity_score', 'name']

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
    ]

    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (_('Skill Information'), {
            'fields': (
                'id',
                'name',
                'slug',
                'description',
                'category',
            )
        }),
        (_('Hierarchy'), {
            'fields': (
                'parent_skill',
                'skill_level',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'is_active',
                'popularity_score',
            )
        }),
        (_('Audit Information'), {
            'fields': (
                'created_at',
                'updated_at',
                'is_deleted',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    """Admin interface for UserSkill model."""

    list_display = [
        'user',
        'skill',
        'skill_type',
        'proficiency_level',
        'years_of_experience',
        'source',
        'is_verified',
        'created_at',
    ]

    list_filter = [
        'skill_type',
        'proficiency_level',
        'source',
        'is_verified',
        'created_at',
    ]

    search_fields = [
        'user__email',
        'user__username',
        'skill__name',
    ]

    ordering = ['-created_at']

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
    ]

    autocomplete_fields = ['user', 'skill']

    fieldsets = (
        (_('User & Skill'), {
            'fields': (
                'id',
                'user',
                'skill',
            )
        }),
        (_('Proficiency'), {
            'fields': (
                'skill_type',
                'proficiency_level',
                'years_of_experience',
            )
        }),
        (_('Source & Verification'), {
            'fields': (
                'source',
                'is_verified',
                'verified_at',
                'verified_by',
            )
        }),
        (_('Audit Information'), {
            'fields': (
                'created_at',
                'updated_at',
                'is_deleted',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """Admin interface for UserPreferences model."""

    list_display = [
        'user',
        'email_notifications',
        'push_notifications',
        'profile_visibility',
        'daily_learning_goal_minutes',
        'created_at',
    ]

    list_filter = [
        'email_notifications',
        'push_notifications',
        'weekly_digest',
        'profile_visibility',
        'show_progress',
        'preferred_learning_style',
        'created_at',
    ]

    search_fields = [
        'user__email',
        'user__username',
    ]

    ordering = ['-created_at']

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
    ]

    autocomplete_fields = ['user']

    fieldsets = (
        (_('User'), {
            'fields': (
                'id',
                'user',
            )
        }),
        (_('Notification Preferences'), {
            'fields': (
                'email_notifications',
                'push_notifications',
                'weekly_digest',
            )
        }),
        (_('Privacy Settings'), {
            'fields': (
                'profile_visibility',
                'show_progress',
            )
        }),
        (_('Learning Preferences'), {
            'fields': (
                'preferred_learning_style',
                'daily_learning_goal_minutes',
                'reminder_time',
            )
        }),
        (_('Audit Information'), {
            'fields': (
                'created_at',
                'updated_at',
                'is_deleted',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )
