"""
Roadmaps Service Views

Implements REST API views for AI-powered personalized learning roadmaps.

SRS References:
- FR-9: Generate Personalized Roadmap
- FR-10: Assessment-Based Roadmap Generation
- FR-11: Course Association with Roadmaps
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone

from apps.roadmaps.models import (
    RoadmapTemplate,
    Roadmap,
    RoadmapPhase,
    RoadmapMilestone
)
from apps.roadmaps.serializers import (
    RoadmapTemplateSerializer,
    RoadmapTemplateListSerializer,
    RoadmapSerializer,
    RoadmapListSerializer,
    RoadmapDetailSerializer,
    RoadmapCreateFromTemplateSerializer,
    RoadmapCreateAISerializer,
    RoadmapUpdateSerializer,
    RoadmapProgressUpdateSerializer,
    RoadmapStatsSerializer,
)
from apps.roadmaps.services import (
    RoadmapTemplateService,
    RoadmapService,
)
from apps.assessments.models import AssessmentResult


# ============================================================================
# EXTRA ENDPOINT - Needed for MVP
# ============================================================================

class RoadmapTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View roadmap templates.

    Endpoints:
    - GET /templates/ - List all published templates
    - GET /templates/{id}/ - Get specific template
    - GET /templates/by_career/?career=Backend - Filter by career
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only published templates."""
        return RoadmapTemplate.objects.filter(
            is_published=True,
            is_deleted=False
        ).order_by('-usage_count')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return RoadmapTemplateListSerializer
        return RoadmapTemplateSerializer

    @action(detail=False, methods=['get'])
    def by_career(self, request):
        """
        Get templates filtered by career.

        Query Parameters:
        - career: Career name to search for (required)
        """
        career = request.query_params.get('career')
        if not career:
            return Response(
                {'error': 'career parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        templates = RoadmapTemplateService.get_template_by_career(career)
        serializer = RoadmapTemplateListSerializer(templates, many=True)
        return Response(serializer.data)


# ============================================================================
# ROADMAP VIEWS
# ============================================================================

class RoadmapViewSet(viewsets.ModelViewSet):
    """
    Manage user learning roadmaps.

    SRS Appendix B Endpoints:
    - POST /roadmap/ - Generate roadmap (FR-9, FR-10)
    - GET /roadmap/ - Get user's roadmap
    - GET /roadmap/{id}/ - Get specific roadmap
    - PUT /roadmap/{id}/ - Update roadmap
    - DELETE /roadmap/{id}/ - Delete roadmap
    - PUT /roadmap/{id}/progress/ - Update progress
    - POST /roadmap/{id}/activate/ - Activate roadmap
    - GET /roadmap/{id}/stats/ - Get roadmap statistics
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return roadmaps for current user only."""
        return Roadmap.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('template', 'assessment').order_by('-created_at')

    def get_serializer_class(self):
        """Use appropriate serializer per action."""
        if self.action == 'list':
            return RoadmapListSerializer
        elif self.action == 'retrieve':
            return RoadmapDetailSerializer
        elif self.action == 'create':
            # Determine which creation method based on request data
            if 'template_id' in self.request.data:
                return RoadmapCreateFromTemplateSerializer
            else:
                return RoadmapCreateAISerializer
        elif self.action in ['update', 'partial_update']:
            return RoadmapUpdateSerializer
        elif self.action == 'progress':
            return RoadmapProgressUpdateSerializer
        return RoadmapSerializer

    def list(self, request, *args, **kwargs):
        """
        List user's roadmaps with optional filtering.

        Query Parameters:
        - status: Filter by status (draft, active, in_progress, completed, etc.)
        - target_career: Filter by target career
        """
        queryset = self.get_queryset()

        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by career
        career = request.query_params.get('target_career')
        if career:
            queryset = queryset.filter(target_career__icontains=career)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Generate new roadmap.

        SRS FR-9: Generate Personalized Roadmap
        SRS FR-10: Assessment-Based Roadmap Generation
        SRS Appendix B: POST /roadmap/

        Two creation methods:
        1. From Template:
           {
               "template_id": "uuid",
               "weekly_hours_commitment": 10,
               "customizations": {}
           }

        2. AI-Generated:
           {
               "assessment_id": "uuid",  // optional
               "target_career": "Backend Developer",
               "current_level": "beginner",
               "target_level": "senior",
               "weekly_hours_commitment": 10
           }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create roadmap based on method
        if 'template_id' in request.data:
            # Create from template
            template = RoadmapTemplateService.get_template_by_id(
                str(serializer.validated_data['template_id'])
            )
            roadmap = RoadmapService.create_roadmap_from_template(
                user=request.user,
                template=template,
                customizations={
                    'weekly_hours': serializer.validated_data.get('weekly_hours_commitment', 10),
                    **serializer.validated_data.get('customizations', {})
                }
            )
        else:
            # AI-generated roadmap
            assessment = serializer.validated_data.get('assessment')

            roadmap = RoadmapService.generate_ai_roadmap(
                user=request.user,
                assessment=assessment,
                target_career=serializer.validated_data['target_career'],
                current_level=serializer.validated_data['current_level'],
                target_level=serializer.validated_data['target_level'],
                weekly_hours=serializer.validated_data.get('weekly_hours_commitment', 10)
            )

        return Response(
            RoadmapSerializer(roadmap).data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Get specific roadmap with full hierarchy.

        SRS Appendix B: GET /roadmap/{id}/

        Returns complete roadmap with phases, milestones, and courses.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update roadmap details."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(RoadmapSerializer(instance).data)

    @action(detail=True, methods=['put', 'patch'])
    def progress(self, request, pk=None):
        """
        Update roadmap progress.

        SRS Appendix B: PUT /roadmap/{id}/progress/

        Request Body:
        {
            "phase_id": "uuid",  // OR
            "milestone_id": "uuid",
            "status": "completed"  // not_started, in_progress, completed, skipped
        }

        Updates:
        - Phase/milestone status
        - Completion timestamps
        - Parent roadmap completion percentage
        """
        roadmap = self.get_object()
        serializer = RoadmapProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phase_id = serializer.validated_data.get('phase_id')
        milestone_id = serializer.validated_data.get('milestone_id')
        new_status = serializer.validated_data['status']

        if phase_id:
            # Update phase status
            try:
                phase = RoadmapPhase.objects.get(id=phase_id, roadmap=roadmap)
                phase.status = new_status

                if new_status == 'in_progress' and not phase.started_at:
                    phase.started_at = timezone.now()
                elif new_status == 'completed' and not phase.completed_at:
                    phase.completed_at = timezone.now()
                    phase.completion_percentage = 100.00

                phase.save()

                # Update roadmap status if needed
                if new_status == 'in_progress' and roadmap.status == 'draft':
                    roadmap.status = 'in_progress'
                    roadmap.started_at = timezone.now()
                    roadmap.save()

                return Response(
                    {'message': 'Phase progress updated successfully'},
                    status=status.HTTP_200_OK
                )

            except RoadmapPhase.DoesNotExist:
                return Response(
                    {'error': 'Phase not found in this roadmap'},
                    status=status.HTTP_404_NOT_FOUND
                )

        elif milestone_id:
            # Update milestone status
            try:
                milestone = RoadmapMilestone.objects.get(
                    id=milestone_id,
                    phase__roadmap=roadmap
                )
                milestone.status = new_status

                if new_status == 'completed' and not milestone.completed_at:
                    milestone.completed_at = timezone.now()

                milestone.save()

                # Update phase if all milestones completed
                phase = milestone.phase
                total = phase.milestones.count()
                completed = phase.milestones.filter(status='completed').count()

                if completed == total:
                    phase.status = 'completed'
                    phase.completion_percentage = 100.00
                    phase.completed_at = timezone.now()
                    phase.save()

                # Update roadmap status
                if milestone.status == 'in_progress' and roadmap.status == 'draft':
                    roadmap.status = 'in_progress'
                    roadmap.started_at = timezone.now()
                    roadmap.save()

                return Response(
                    {'message': 'Milestone progress updated successfully'},
                    status=status.HTTP_200_OK
                )

            except RoadmapMilestone.DoesNotExist:
                return Response(
                    {'error': 'Milestone not found in this roadmap'},
                    status=status.HTTP_404_NOT_FOUND
                )

    # ============================================================================
    # EXTRA ENDPOINTS - NOT IN SRS APPENDIX B
    # Commented out to match SRS. Uncomment if needed in future.
    # ============================================================================

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a roadmap.

        POST /roadmap/{id}/activate/

        Sets roadmap status to 'active' and marks started_at timestamp.
        """
        roadmap = self.get_object()

        if roadmap.status in ['active', 'in_progress']:
            return Response(
                {'error': 'Roadmap is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        roadmap = RoadmapService.update_roadmap_status(roadmap, 'active')

        return Response(
            RoadmapSerializer(roadmap).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get roadmap statistics.

        GET /roadmap/{id}/stats/

        Returns:
        - total_phases, completed_phases
        - total_milestones, completed_milestones
        - total_courses
        - estimated_total_hours
        - completion_percentage
        """
        roadmap = self.get_object()
        stats = RoadmapService.get_roadmap_statistics(roadmap)
        serializer = RoadmapSerializer(roadmap)
        summary = serializer.data.get('journey_summary', {})

        stats.update(
            {
                'current_focus_node_id': serializer.data.get('current_focus_node_id'),
                'next_action': {
                    'type': summary.get('next_action_type', 'roadmap'),
                    'id': summary.get('next_action_id'),
                    'title': summary.get('next_action_title', roadmap.title),
                    'summary': summary.get('next_action_summary', roadmap.description or ''),
                },
            }
        )

        return Response(stats, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Soft delete roadmap."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        return Response(
            {'message': 'Roadmap deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
