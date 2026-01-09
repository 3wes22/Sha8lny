"""
Jobs Service Layer

Handles job aggregation, matching, applications, and AI-powered job recommendations.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import JobListing, JobApplication, SavedJob
from apps.users.models import User, UserSkill
from apps.notifications.signals import job_match_found, job_application_submitted


class JobService:
    """Service for job listing management and search"""

    @staticmethod
    def search_jobs(
        query: str = "",
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        min_salary: Optional[Decimal] = None,
        is_remote: Optional[bool] = None,
        limit: int = 50
    ) -> List[JobListing]:
        """
        Search jobs with filters.

        Args:
            query: Search query
            location: Filter by location
            job_type: Filter by job type (full_time, part_time, etc.)
            experience_level: Filter by experience level
            min_salary: Minimum salary
            is_remote: Filter remote jobs
            limit: Maximum results

        Returns:
            List[JobListing]: Matching jobs
        """
        queryset = JobListing.objects.filter(
            is_active=True,
            is_deleted=False
        )

        # Text search
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(company_name__icontains=query) |
                Q(description__icontains=query) |
                Q(required_skills__icontains=query)
            )

        # Location filter
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Job type filter
        if job_type:
            queryset = queryset.filter(job_type=job_type)

        # Experience level filter
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        # Salary filter
        if min_salary:
            queryset = queryset.filter(
                salary_min__gte=min_salary
            )

        # Remote filter
        if is_remote is not None:
            queryset = queryset.filter(is_remote=is_remote)

        return list(queryset.order_by('-posted_date')[:limit])

    @staticmethod
    def get_job_by_id(job_id: str) -> Optional[JobListing]:
        """Get job by ID"""
        try:
            job = JobListing.objects.get(id=job_id, is_deleted=False)
            # Increment view count
            job.view_count += 1
            job.save(update_fields=['view_count', 'updated_at'])
            return job
        except JobListing.DoesNotExist:
            return None

    @staticmethod
    def get_recent_jobs(limit: int = 20) -> List[JobListing]:
        """Get recently posted jobs"""
        return list(JobListing.objects.filter(
            is_active=True,
            is_deleted=False
        ).order_by('-posted_date')[:limit])

    @staticmethod
    def get_remote_jobs(limit: int = 50) -> List[JobListing]:
        """Get remote job listings"""
        return list(JobListing.objects.filter(
            is_remote=True,
            is_active=True,
            is_deleted=False
        ).order_by('-posted_date')[:limit])

    @staticmethod
    def match_jobs_for_user(
        user: User,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find jobs matching user's skills and experience.

        Args:
            user: User instance
            limit: Maximum matches

        Returns:
            List of dicts with job and match_score
        """
        # Get user's skills
        user_skills = set(
            UserSkill.objects.filter(
                user=user,
                is_deleted=False
            ).values_list('skill__name', flat=True)
        )

        if not user_skills:
            # No skills - return recent jobs
            jobs = JobService.get_recent_jobs(limit)
            return [{'job': job, 'match_score': 0} for job in jobs]

        # Get all active jobs
        jobs = JobListing.objects.filter(
            is_active=True,
            is_deleted=False
        )

        # Calculate match scores
        matches = []
        for job in jobs[:100]:  # Limit to first 100 for performance
            # Parse required skills from job
            required_skills = set()
            if job.required_skills:
                if isinstance(job.required_skills, list):
                    required_skills = set(job.required_skills)
                elif isinstance(job.required_skills, str):
                    required_skills = {
                        s.strip().lower()
                        for s in job.required_skills.split(',')
                    }

            # Calculate match percentage
            if required_skills:
                user_skills_lower = {s.lower() for s in user_skills}
                required_skills_lower = {s.lower() for s in required_skills}

                matching_skills = user_skills_lower & required_skills_lower
                match_score = int((len(matching_skills) / len(required_skills_lower)) * 100)
            else:
                match_score = 0

            if match_score > 0:
                matches.append({
                    'job': job,
                    'match_score': match_score,
                    'matching_skills': list(user_skills & required_skills)
                })

        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        # Emit signals for high matches (>70%)
        for match in matches[:5]:
            if match['match_score'] >= 70:
                job_match_found.send(
                    sender=JobListing,
                    instance=match['job'],
                    user=user,
                    match_score=match['match_score']
                )

        return matches[:limit]

    @staticmethod
    @transaction.atomic
    def create_job_listing(
        title: str,
        company_name: str,
        description: str,
        location: str,
        job_type: str,
        experience_level: str,
        **kwargs
    ) -> JobListing:
        """Create a new job listing (from external API sync)"""
        job = JobListing.objects.create(
            title=title,
            company_name=company_name,
            description=description,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
            is_active=True,
            posted_date=timezone.now(),
            **kwargs
        )
        return job


class JobApplicationService:
    """Service for job application management"""

    @staticmethod
    @transaction.atomic
    def apply_to_job(
        user: User,
        job: JobListing,
        cover_letter: str = "",
        resume_id: Optional[str] = None
    ) -> JobApplication:
        """
        Submit job application.

        Args:
            user: User applying
            job: Job listing
            cover_letter: Optional cover letter
            resume_id: Optional resume ID to attach

        Returns:
            JobApplication: Created application
        """
        # Check for existing application
        existing = JobApplication.objects.filter(
            user=user,
            job=job,
            is_deleted=False
        ).first()

        if existing:
            return existing

        application = JobApplication.objects.create(
            user=user,
            job=job,
            status='applied',
            applied_at=timezone.now(),
            cover_letter=cover_letter,
            resume_snapshot={
                'resume_id': resume_id
            } if resume_id else {}
        )

        # Increment application count on job
        job.application_count += 1
        job.save(update_fields=['application_count', 'updated_at'])

        # Emit signal
        job_application_submitted.send(
            sender=JobApplication,
            instance=application,
            user=user,
            job=job
        )

        return application

    @staticmethod
    def get_user_applications(user: User) -> List[JobApplication]:
        """Get all applications for user"""
        return list(JobApplication.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('job').order_by('-applied_at'))

    @staticmethod
    def update_application_status(
        application_id: str,
        status: str,
        notes: str = ""
    ) -> Optional[JobApplication]:
        """Update application status"""
        try:
            application = JobApplication.objects.get(id=application_id)
            application.status = status

            if notes:
                application.notes = notes

            if status == 'rejected':
                application.rejected_at = timezone.now()
            elif status == 'accepted':
                application.interview_scheduled_at = timezone.now()

            application.save()
            return application
        except JobApplication.DoesNotExist:
            return None


class SavedJobService:
    """Service for saved job management"""

    @staticmethod
    def save_job(user: User, job: JobListing, notes: str = "") -> SavedJob:
        """Save a job for later"""
        saved_job, created = SavedJob.objects.get_or_create(
            user=user,
            job=job,
            defaults={'notes': notes}
        )

        if not created and notes:
            saved_job.notes = notes
            saved_job.save()

        return saved_job

    @staticmethod
    def unsave_job(user: User, job: JobListing) -> bool:
        """Remove saved job"""
        try:
            saved_job = SavedJob.objects.get(user=user, job=job)
            saved_job.is_deleted = True
            saved_job.save(update_fields=['is_deleted', 'updated_at'])
            return True
        except SavedJob.DoesNotExist:
            return False

    @staticmethod
    def get_saved_jobs(user: User) -> List[SavedJob]:
        """Get all saved jobs for user"""
        return list(SavedJob.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('job').order_by('-created_at'))

    @staticmethod
    def is_job_saved(user: User, job: JobListing) -> bool:
        """Check if job is saved by user"""
        return SavedJob.objects.filter(
            user=user,
            job=job,
            is_deleted=False
        ).exists()
