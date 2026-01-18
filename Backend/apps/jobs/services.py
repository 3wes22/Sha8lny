"""
Jobs Service Layer

Handles job search, filtering, skill matching, and market insights.

SRS References:
- FR-18: Job Scraping and Normalization
- FR-19: Job-Skill Matching
- FR-20: Market Insights
- FR-21: Skill Demand Analysis
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from apps.jobs.models import JobPlatform, Job, JobSkill, MarketInsight, SkillDemand
from apps.users.models import User, Skill, UserSkill


class JobService:
    """Service for job management and search."""

    @staticmethod
    def search_jobs(
        query: str = "",
        location_city: Optional[str] = None,
        location_country: str = "Egypt",
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        min_salary: Optional[Decimal] = None,
        is_remote: Optional[bool] = None,
        skills: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Job]:
        """
        Search jobs with comprehensive filters.

        Args:
            query: Search in title, company, description
            location_city: Filter by city
            location_country: Filter by country (default: Egypt)
            job_type: full_time, part_time, contract, internship, freelance
            experience_level: entry, mid, senior, lead, executive
            min_salary: Minimum salary filter
            is_remote: Filter remote jobs
            skills: List of skill names to match
            limit: Maximum results

        Returns:
            List[Job]: Matching jobs ordered by posted_date
        """
        queryset = Job.objects.filter(
            is_active=True,
            is_deleted=False,
            platform__is_active=True
        ).select_related('platform').prefetch_related('job_skills__skill')

        # Text search
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(company_name__icontains=query) |
                Q(description__icontains=query) |
                Q(requirements__icontains=query)
            )

        # Location filters
        if location_city:
            queryset = queryset.filter(location_city__icontains=location_city)

        if location_country:
            queryset = queryset.filter(location_country=location_country)

        # Job type filter
        if job_type:
            queryset = queryset.filter(job_type=job_type)

        # Experience level filter
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        # Salary filter
        if min_salary:
            queryset = queryset.filter(salary_min__gte=min_salary)

        # Remote filter
        if is_remote is not None:
            queryset = queryset.filter(is_remote=is_remote)

        # Skills filter (Job-Skill Matching - FR-19)
        if skills:
            for skill_name in skills:
                queryset = queryset.filter(
                    job_skills__skill__name__iexact=skill_name
                ).distinct()

        return list(queryset.order_by('-posted_date')[:limit])

    @staticmethod
    def get_job_by_id(job_id: str) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job UUID

        Returns:
            Job instance or None
        """
        try:
            return Job.objects.select_related('platform').prefetch_related(
                'job_skills__skill'
            ).get(id=job_id, is_deleted=False)
        except Job.DoesNotExist:
            return None

    @staticmethod
    def get_recent_jobs(days: int = 7, limit: int = 50) -> List[Job]:
        """
        Get recently posted jobs.

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List[Job]: Recent jobs
        """
        cutoff_date = (timezone.now() - timedelta(days=days)).date()

        return list(Job.objects.filter(
            is_active=True,
            is_deleted=False,
            posted_date__gte=cutoff_date,
            platform__is_active=True
        ).select_related('platform').order_by('-posted_date')[:limit])

    @staticmethod
    def get_remote_jobs(limit: int = 50) -> List[Job]:
        """
        Get remote job listings.

        Args:
            limit: Maximum results

        Returns:
            List[Job]: Remote jobs
        """
        return list(Job.objects.filter(
            is_remote=True,
            is_active=True,
            is_deleted=False,
            platform__is_active=True
        ).select_related('platform').order_by('-posted_date')[:limit])

    @staticmethod
    def match_jobs_for_user(user: User, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find jobs matching user's skills.

        SRS FR-19: Job-Skill Matching

        Args:
            user: User instance
            limit: Maximum matches

        Returns:
            List of dicts with:
            - job: Job instance
            - match_score: Percentage match (0-100)
            - matching_skills: List of matched skill names
        """
        # Get user's skills
        user_skills = set(
            UserSkill.objects.filter(
                user=user,
                is_deleted=False
            ).values_list('skill__name', flat=True)
        )

        if not user_skills:
            # No skills - return recent jobs with 0 match score
            jobs = JobService.get_recent_jobs(limit=limit)
            return [{'job': job, 'match_score': 0, 'matching_skills': []} for job in jobs]

        # Get active jobs with their required skills
        jobs = Job.objects.filter(
            is_active=True,
            is_deleted=False,
            platform__is_active=True
        ).select_related('platform').prefetch_related('job_skills__skill')

        matches = []
        for job in jobs[:200]:  # Limit to 200 for performance
            # Get required skills for this job
            job_required_skills = set(
                job.job_skills.filter(
                    is_required=True
                ).values_list('skill__name', flat=True)
            )

            if not job_required_skills:
                continue

            # Calculate match
            matching_skills = user_skills & job_required_skills
            match_score = int((len(matching_skills) / len(job_required_skills)) * 100)

            if match_score > 0:
                matches.append({
                    'job': job,
                    'match_score': match_score,
                    'matching_skills': list(matching_skills),
                    'missing_skills': list(job_required_skills - user_skills)
                })

        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        return matches[:limit]

    @staticmethod
    @transaction.atomic
    def create_job(
        platform: JobPlatform,
        external_id: str,
        title: str,
        company_name: str,
        location_city: str = "",
        location_country: str = "Egypt",
        **kwargs
    ) -> Job:
        """
        Create or update job listing (for scraping/API sync).

        Args:
            platform: JobPlatform instance
            external_id: Platform's unique job ID
            title: Job title
            company_name: Company name
            location_city: City
            location_country: Country
            **kwargs: Additional Job model fields

        Returns:
            Job instance
        """
        # Check if job already exists (prevent duplicates)
        job, created = Job.objects.update_or_create(
            platform=platform,
            external_id=external_id,
            defaults={
                'title': title,
                'company_name': company_name,
                'location_city': location_city,
                'location_country': location_country,
                'is_active': True,
                **kwargs
            }
        )

        return job

    @staticmethod
    def get_jobs_by_platform(platform_slug: str, limit: int = 50) -> List[Job]:
        """
        Get jobs from specific platform.

        Args:
            platform_slug: Platform slug (e.g., 'wuzzuf', 'linkedin')
            limit: Maximum results

        Returns:
            List[Job]: Jobs from platform
        """
        try:
            platform = JobPlatform.objects.get(slug=platform_slug, is_active=True)
            return list(Job.objects.filter(
                platform=platform,
                is_active=True,
                is_deleted=False
            ).order_by('-posted_date')[:limit])
        except JobPlatform.DoesNotExist:
            return []

    @staticmethod
    def add_skills_to_job(job: Job, skill_names: List[str], is_required: bool = True) -> None:
        """
        Add skills to a job.

        Args:
            job: Job instance
            skill_names: List of skill names
            is_required: Whether skills are required or nice-to-have
        """
        from django.utils.text import slugify

        for skill_name in skill_names:
            skill_name = skill_name.strip()

            # Try to get existing skill by name (case-insensitive)
            try:
                skill = Skill.objects.get(name__iexact=skill_name)
            except Skill.DoesNotExist:
                # Create new skill
                skill = Skill.objects.create(
                    name=skill_name,
                    slug=slugify(skill_name),
                    category='technical'
                )

            # Create JobSkill relationship
            JobSkill.objects.get_or_create(
                job=job,
                skill=skill,
                defaults={'is_required': is_required}
            )


class MarketInsightService:
    """Service for market insights and analytics."""

    @staticmethod
    def get_insights_by_career(
        career_field: str,
        country: str = "Egypt"
    ) -> List[MarketInsight]:
        """
        Get market insights for a career field.

        SRS FR-20: Market Insights

        Args:
            career_field: Career field name
            country: Country filter

        Returns:
            List[MarketInsight]: Recent insights
        """
        return list(MarketInsight.objects.filter(
            career_field__icontains=career_field,
            country=country,
            is_deleted=False
        ).order_by('-generated_at')[:10])

    @staticmethod
    @transaction.atomic
    def generate_job_demand_insight(
        career_field: str,
        country: str = "Egypt",
        period_days: int = 30
    ) -> MarketInsight:
        """
        Generate job demand insight for a career field.

        Args:
            career_field: Career field to analyze
            country: Country to analyze
            period_days: Analysis period in days

        Returns:
            MarketInsight: Generated insight
        """
        period_start = (timezone.now() - timedelta(days=period_days)).date()
        period_end = timezone.now().date()

        # Query jobs in this field
        jobs = Job.objects.filter(
            title__icontains=career_field,
            location_country=country,
            posted_date__gte=period_start,
            posted_date__lte=period_end,
            is_deleted=False
        )

        # Calculate statistics
        total_jobs = jobs.count()
        avg_salary = jobs.aggregate(
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max')
        )

        # Get top skills
        top_skills = JobSkill.objects.filter(
            job__in=jobs,
            is_required=True
        ).values('skill__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Get top companies
        top_companies = jobs.values('company_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Create insight
        insight = MarketInsight.objects.create(
            insight_type='job_demand',
            career_field=career_field,
            country=country,
            data_period_start=period_start,
            data_period_end=period_end,
            total_jobs_analyzed=total_jobs,
            insights_data={
                'total_jobs': total_jobs,
                'average_salary_min': float(avg_salary['avg_min'] or 0),
                'average_salary_max': float(avg_salary['avg_max'] or 0),
                'top_skills': [
                    {'skill': s['skill__name'], 'count': s['count']}
                    for s in top_skills
                ],
                'top_companies': [
                    {'company': c['company_name'], 'count': c['count']}
                    for c in top_companies
                ],
                'trend_direction': 'stable',  # TODO: Calculate actual trend
                'trend_percentage': 0.0
            }
        )

        return insight


class SkillDemandService:
    """Service for skill demand analytics."""

    @staticmethod
    def get_trending_skills(
        country: str = "Egypt",
        limit: int = 20
    ) -> List[SkillDemand]:
        """
        Get trending skills (rising demand).

        SRS FR-21: Skill Demand Analysis

        Args:
            country: Country filter
            limit: Maximum results

        Returns:
            List[SkillDemand]: Trending skills ordered by growth
        """
        return list(SkillDemand.objects.filter(
            country=country,
            trend_direction='rising',
            is_deleted=False
        ).select_related('skill').order_by('-trend_percentage')[:limit])

    @staticmethod
    def get_skill_demand_history(
        skill: Skill,
        country: str = "Egypt",
        months: int = 6
    ) -> List[SkillDemand]:
        """
        Get historical demand data for a skill.

        Args:
            skill: Skill instance
            country: Country filter
            months: Number of months to retrieve

        Returns:
            List[SkillDemand]: Historical demand data
        """
        cutoff_date = (timezone.now() - timedelta(days=months * 30)).date()

        return list(SkillDemand.objects.filter(
            skill=skill,
            country=country,
            month__gte=cutoff_date,
            is_deleted=False
        ).order_by('month'))

    @staticmethod
    @transaction.atomic
    def calculate_skill_demand(
        skill: Skill,
        country: str = "Egypt",
        month_date: Optional[timezone.datetime] = None
    ) -> SkillDemand:
        """
        Calculate demand metrics for a skill in a given month.

        Args:
            skill: Skill to analyze
            country: Country to analyze
            month_date: Month to analyze (defaults to current month)

        Returns:
            SkillDemand: Calculated demand data
        """
        if not month_date:
            month_date = timezone.now().date().replace(day=1)

        # Get jobs requiring this skill in this month
        jobs_with_skill = JobSkill.objects.filter(
            skill=skill,
            job__location_country=country,
            job__posted_date__year=month_date.year,
            job__posted_date__month=month_date.month,
            job__is_deleted=False
        ).select_related('job')

        demand_count = jobs_with_skill.count()

        # Calculate average salaries
        salary_stats = jobs_with_skill.aggregate(
            avg_min=Avg('job__salary_min'),
            avg_max=Avg('job__salary_max')
        )

        # Get top job titles
        top_titles = jobs_with_skill.values('job__title').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        # Calculate trend (compare to previous month)
        prev_month = (month_date - timedelta(days=30)).replace(day=1)
        prev_demand = SkillDemand.objects.filter(
            skill=skill,
            country=country,
            month=prev_month
        ).first()

        if prev_demand and prev_demand.demand_count > 0:
            trend_percentage = ((demand_count - prev_demand.demand_count) / prev_demand.demand_count) * 100
            if trend_percentage > 5:
                trend_direction = 'rising'
            elif trend_percentage < -5:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_percentage = Decimal('0.00')
            trend_direction = 'stable'

        # Create or update demand record
        demand, _ = SkillDemand.objects.update_or_create(
            skill=skill,
            country=country,
            month=month_date,
            defaults={
                'demand_count': demand_count,
                'trend_direction': trend_direction,
                'trend_percentage': Decimal(str(round(trend_percentage, 2))),
                'average_salary_min': salary_stats['avg_min'],
                'average_salary_max': salary_stats['avg_max'],
                'top_job_titles': [t['job__title'] for t in top_titles]
            }
        )

        return demand
