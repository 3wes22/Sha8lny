"""
Jobs Service Views

Implements REST API views for job market data, search, and insights.

SRS References:
- FR-18: Job Scraping and Normalization
- FR-19: Job-Skill Matching
- FR-20: Market Insights
- FR-21: Skill Demand Analysis
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from apps.jobs.models import Job, SavedJob
from apps.jobs.services import JobService
from apps.jobs.serializers import (
    JobSerializer,
    JobListSerializer,
    JobSearchSerializer,
    SavedJobSerializer,
    SavedJobCreateSerializer,
)


# ============================================================================
# EXTRA ENDPOINT - NOT IN SRS APPENDIX B
# Uncomment if needed in future
# ============================================================================

# class JobPlatformViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     View job platforms.
#
#     Endpoints:
#     - GET /platforms/ - List active job platforms
#     - GET /platforms/{id}/ - Get specific platform
#     """
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = JobPlatformSerializer
#
#     def get_queryset(self):
#         return JobPlatform.objects.filter(
#             is_active=True,
#             is_deleted=False
#         ).order_by('name')


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Job listing views.

    SRS Appendix B Endpoints:
    - GET /jobs/search - Search jobs (FR-19)
    - GET /jobs/{id} - Get job details
    - GET /jobs/recent/ - Recent job postings
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return active jobs within cache period."""
        return Job.objects.filter(
            is_deleted=False,
            is_active=True,
            platform__is_active=True
        ).select_related('platform').prefetch_related('job_skills__skill')

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'search':
            return JobListSerializer
        elif self.action == 'search_params':
            return JobSearchSerializer
        return JobSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search jobs with filters.

        SRS FR-19: Job-Skill Matching
        SRS Appendix B: GET /jobs/search

        Query Parameters:
        - query: Search in title, company, description
        - location: Filter by location
        - job_type: Filter by job type
        - experience_level: Filter by experience
        - is_remote: Boolean for remote jobs
        - min_salary: Minimum salary
        - skills: Comma-separated skill names
        """
        queryset = self.get_queryset()

        # Search query
        query = request.query_params.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(company_name__icontains=query) |
                Q(description__icontains=query)
            )

        # Location filter
        location = request.query_params.get('location')
        if location:
            queryset = queryset.filter(
                Q(location_city__icontains=location) |
                Q(location_country__icontains=location)
            )

        # Job type filter
        job_type = request.query_params.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)

        # Experience level filter
        experience_level = request.query_params.get('experience_level')
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        # Remote filter
        is_remote = request.query_params.get('is_remote')
        if is_remote:
            queryset = queryset.filter(is_remote=is_remote.lower() == 'true')

        # Salary filter
        min_salary = request.query_params.get('min_salary')
        if min_salary:
            queryset = queryset.filter(salary_min__gte=int(min_salary))

        # Skills filter (FR-19: Job-Skill Matching)
        skills = request.query_params.get('skills')
        if skills:
            skill_list = [s.strip() for s in skills.split(',')]
            for skill in skill_list:
                queryset = queryset.filter(
                    job_skills__skill__name__icontains=skill
                ).distinct()

        # Order by posted date (newest first)
        queryset = queryset.order_by('-posted_date')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def match(self, request):
        """Return jobs ranked by skill overlap against the authenticated user."""
        limit = int(request.query_params.get("limit", 20))
        matches = JobService.match_jobs_for_user(request.user, limit=limit)
        user_level = matches[0].get("user_career_level") if matches else None
        payload = []
        for item in matches:
            job = item["job"]
            payload.append(
                {
                    **JobListSerializer(job, context={"request": request}).data,
                    "match_score": item["match_score"],
                    "matching_skills": item.get("matching_skills", []),
                    "missing_skills": item.get("missing_skills", []),
                    "explanation": item.get("explanation", {}),
                    "user_career_level": item.get("user_career_level"),
                    "job_experience_level": item.get("job_experience_level"),
                }
            )
        return Response(
            {
                "user_career_level": user_level,
                "results": payload,
            }
        )

    # ============================================================================
    # EXTRA ENDPOINTS - NOT IN SRS APPENDIX B
    # Commented out to match SRS. Uncomment if needed in future.
    # ============================================================================

    # @action(detail=False, methods=['get'])
    # def recent(self, request):
    #     """
    #     Get recent job postings (last 7 days).
    #
    #     GET /jobs/recent/
    #     """
    #     week_ago = timezone.now().date() - timedelta(days=7)
    #     jobs = self.get_queryset().filter(
    #         posted_date__gte=week_ago
    #     ).order_by('-posted_date')[:50]
    #
    #     serializer = JobListSerializer(jobs, many=True)
    #     return Response(serializer.data)


class SavedJobViewSet(viewsets.ModelViewSet):
    """
    User saved jobs management.

    Endpoints:
    - GET /saved-jobs/ - List user's saved jobs
    - POST /saved-jobs/ - Save a job
    - DELETE /saved-jobs/{id}/ - Unsave a job
    - POST /saved-jobs/toggle/{job_id}/ - Toggle save status
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for saved jobs

    def get_queryset(self):
        """Return current user's saved jobs."""
        return SavedJob.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('job__platform').order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'toggle':
            return SavedJobCreateSerializer
        return SavedJobSerializer

    def create(self, request, *args, **kwargs):
        """Save a job."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Check if already saved
        job_id = serializer.validated_data['job'].id
        if SavedJob.objects.filter(user=request.user, job_id=job_id, is_deleted=False).exists():
            return Response(
                {'detail': 'Job already saved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            SavedJobSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['post'], url_path='toggle/(?P<job_id>[^/.]+)')
    def toggle(self, request, job_id=None):
        """
        Toggle save status for a job.
        
        POST /saved-jobs/toggle/{job_id}/
        
        Returns:
        - 201: Job saved
        - 200: Job unsaved
        """
        # Check if job exists (including soft-deleted)
        try:
            saved_job = SavedJob.objects.get(
                user=request.user,
                job_id=job_id
            )
            
            if saved_job.is_deleted:
                # Restore soft-deleted job
                saved_job.is_deleted = False
                saved_job.save()
                return Response(
                    {
                        'detail': 'Job saved',
                        'is_saved': True,
                        'saved_job': SavedJobSerializer(saved_job).data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                # Soft delete the job
                saved_job.is_deleted = True
                saved_job.save()
                return Response(
                    {'detail': 'Job unsaved', 'is_saved': False},
                    status=status.HTTP_200_OK
                )
                
        except SavedJob.DoesNotExist:
            # Job not saved, create new
            try:
                job = Job.objects.get(id=job_id, is_deleted=False)
                saved_job = SavedJob.objects.create(user=request.user, job=job)
                return Response(
                    {
                        'detail': 'Job saved',
                        'is_saved': True,
                        'saved_job': SavedJobSerializer(saved_job).data
                    },
                    status=status.HTTP_201_CREATED
                )
            except Job.DoesNotExist:
                return Response(
                    {'detail': 'Job not found'},
                    status=status.HTTP_404_NOT_FOUND
                )


# ============================================================================
# EXTRA ENDPOINT - NOT IN SRS APPENDIX B
# Uncomment if needed in future
# ============================================================================

# class SkillDemandViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     View skill demand insights.
#
#     SRS FR-20: Market Insights
#     SRS FR-21: Skill Demand Analysis
#
#     Endpoints:
#     - GET /demand/ - List skill demand data
#     - GET /demand/{id}/ - Get specific skill demand
#     - GET /demand/trending/ - Get trending skills
#     """
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = SkillDemandSerializer
#
#     def get_queryset(self):
#         """Return recent skill demand data (last 6 months)."""
#         six_months_ago = timezone.now().date() - timedelta(days=180)
#         return SkillDemand.objects.filter(
#             is_deleted=False,
#             month__gte=six_months_ago
#         ).select_related('skill').order_by('-demand_count')
#
#     @action(detail=False, methods=['get'])
#     def trending(self, request):
#         """
#         Get trending skills (rising trend).
#
#         GET /demand/trending/
#
#         Returns skills with rising trend ordered by growth.
#         """
#         skills = self.get_queryset().filter(
#             trend_direction='rising',
#             growth_percentage__gt=0
#         ).order_by('-growth_percentage')[:20]
#
#         serializer = self.get_serializer(skills, many=True)
#         return Response(serializer.data)
