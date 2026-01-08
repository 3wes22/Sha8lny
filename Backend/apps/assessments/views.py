"""
Assessments Service Views

Implements REST API views for AI-powered skill assessments.

SRS References:
- FR-6: Generate Skill Assessment
- FR-7: Assessment Versioning
- FR-8: AI Processing
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg
from django.db import models

from apps.assessments.models import Assessment, AssessmentResult
from apps.assessments.serializers import (
    AssessmentSerializer,
    AssessmentCreateSerializer,
    AssessmentResponseSerializer,
    AssessmentResultSerializer,
    AssessmentListSerializer,
)
from apps.assessments.services import AssessmentService


# ============================================================================
# ASSESSMENT VIEWS
# ============================================================================

class AssessmentViewSet(viewsets.ModelViewSet):
    """
    Manage user skill assessments.

    SRS Appendix B Endpoints:
    - POST /assessment/ - Generate assessment (FR-6)
    - GET /assessment/latest - Latest assessment
    - GET /assessment/history - All assessments (FR-7)
    - POST /assessment/{id}/submit/ - Submit responses
    - GET /assessment/{id}/result/ - Get AI-processed result (FR-8)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return assessments for current user only."""
        return Assessment.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

    def get_serializer_class(self):
        """Use appropriate serializer per action."""
        if self.action == 'create':
            return AssessmentCreateSerializer
        elif self.action == 'list' or self.action == 'history':
            return AssessmentListSerializer
        elif self.action == 'submit':
            return AssessmentResponseSerializer
        return AssessmentSerializer

    def create(self, request, *args, **kwargs):
        """
        Generate new skill assessment.

        SRS FR-6: System shall accept user input (CV text, Career goals, Skills)
        SRS Appendix B: POST /assessment/

        Request Body:
        {
            "assessment_type": "skills",  # or career_interests, personality, learning_style, comprehensive
            "cv_text": "...",  # optional
            "career_goals": "...",  # optional
            "current_skills": ["Python", "Django"]  # optional
        }

        Returns:
        {
            "id": "uuid",
            "assessment_type": "skills",
            "status": "draft",
            "questions": [...],  # AI-generated questions (TODO: integrate LLM)
            ...
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create assessment using service
        assessment = serializer.save()

        return Response(
            AssessmentSerializer(assessment).data,
            status=status.HTTP_201_CREATED
        )

    def list(self, request, *args, **kwargs):
        """
        List user's assessments with optional filtering.

        Query Parameters:
        - assessment_type: Filter by type (skills, career_interests, etc.)
        - status: Filter by status (draft, in_progress, completed)
        """
        queryset = self.get_queryset()

        # Filter by assessment type
        assessment_type = request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)

        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get user's latest assessment.

        SRS Appendix B: GET /assessment/latest

        Query Parameters:
        - assessment_type: Filter by type (optional)

        Returns: Single assessment object or 404
        """
        queryset = self.get_queryset()

        # Filter by type if provided
        assessment_type = request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)

        latest_assessment = queryset.first()

        if not latest_assessment:
            return Response(
                {'error': 'No assessments found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AssessmentSerializer(latest_assessment)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get assessment history for user.

        SRS FR-7: Assessment Versioning
        SRS Appendix B: GET /assessment/history

        Query Parameters:
        - assessment_type: Filter by type
        - status: Filter by status
        - limit: Number of results (default: 20, max: 100)

        Returns: List of assessments ordered by creation date
        """
        queryset = self.get_queryset()

        # Apply filters (same as list)
        assessment_type = request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Apply limit
        limit = request.query_params.get('limit', '20')
        try:
            limit = min(int(limit), 100)  # Max 100 results
            queryset = queryset[:limit]
        except ValueError:
            pass

        serializer = AssessmentListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit assessment responses.

        POST /assessment/{id}/submit/

        Request Body:
        {
            "responses": [
                {
                    "question_id": "q1",
                    "answer": "Python, Django, REST APIs",
                    "confidence_level": 4
                },
                ...
            ]
        }

        Actions:
        1. Validate responses against assessment questions
        2. Save responses to assessment.responses field
        3. Update assessment status to 'completed'
        4. Trigger AI processing (async via Celery - TODO)
        5. Return updated assessment

        SRS FR-6: User submits responses
        """
        assessment = self.get_object()

        # Check if assessment is already completed
        if assessment.status == 'completed':
            return Response(
                {'error': 'Assessment already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AssessmentResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        responses = serializer.validated_data['responses']

        # Update assessment with responses
        assessment.responses = responses
        assessment.status = 'completed'
        assessment.answered_questions = len(responses)
        assessment.save()

        # TODO: Trigger AI processing task
        # from apps.assessments.tasks import process_assessment_results
        # process_assessment_results.delay(str(assessment.id))

        return Response(
            {
                'message': 'Assessment submitted successfully',
                'assessment': AssessmentSerializer(assessment).data,
                'note': 'AI processing will complete shortly'
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """
        Get AI-processed assessment result.

        GET /assessment/{id}/result/

        SRS FR-8: Parse AI response into Skills, Levels, Notes, Recommendations

        Returns:
        - AssessmentResult object with skill scores, insights, recommendations
        - 404 if result not yet processed
        - 202 if processing is in progress
        """
        assessment = self.get_object()

        # Check if assessment is completed
        if assessment.status != 'completed':
            return Response(
                {'error': 'Assessment not yet completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check AI processing status
        if assessment.ai_processing_status == 'pending':
            return Response(
                {
                    'message': 'Assessment is queued for AI processing',
                    'status': 'pending'
                },
                status=status.HTTP_202_ACCEPTED
            )
        elif assessment.ai_processing_status == 'processing':
            return Response(
                {
                    'message': 'AI is currently processing your assessment',
                    'status': 'processing'
                },
                status=status.HTTP_202_ACCEPTED
            )
        elif assessment.ai_processing_status == 'failed':
            return Response(
                {
                    'error': 'AI processing failed. Please try resubmitting.',
                    'status': 'failed'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Get result
        try:
            result = AssessmentResult.objects.get(
                assessment=assessment,
                is_deleted=False
            )
            serializer = AssessmentResultSerializer(result)
            return Response(serializer.data)

        except AssessmentResult.DoesNotExist:
            return Response(
                {'error': 'Assessment result not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'])
    def cancel(self, request, pk=None):
        """
        Cancel in-progress assessment.

        DELETE /assessment/{id}/cancel/

        Only allows canceling draft or in_progress assessments.
        """
        assessment = self.get_object()

        if assessment.status == 'completed':
            return Response(
                {'error': 'Cannot cancel completed assessment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete
        assessment.is_deleted = True
        assessment.save()

        return Response(
            {'message': 'Assessment cancelled successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


# ============================================================================
# ASSESSMENT RESULT VIEWS
# ============================================================================

class AssessmentResultView(APIView):
    """
    View assessment results.

    GET /assessment/results/ - List all user's assessment results
    GET /assessment/results/{id}/ - Get specific result
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, result_id=None):
        """Get assessment result(s)."""
        if result_id:
            # Get specific result
            try:
                result = AssessmentResult.objects.get(
                    id=result_id,
                    assessment__user=request.user,
                    is_deleted=False
                )
                serializer = AssessmentResultSerializer(result)
                return Response(serializer.data)

            except AssessmentResult.DoesNotExist:
                return Response(
                    {'error': 'Result not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # List all results
            results = AssessmentResult.objects.filter(
                assessment__user=request.user,
                is_deleted=False
            ).select_related('assessment').order_by('-created_at')

            # Filter by assessment type
            assessment_type = request.query_params.get('assessment_type')
            if assessment_type:
                results = results.filter(assessment__assessment_type=assessment_type)

            # Pagination
            from rest_framework.pagination import PageNumberPagination
            paginator = PageNumberPagination()
            paginator.page_size = 20
            page = paginator.paginate_queryset(results, request)

            if page is not None:
                serializer = AssessmentResultSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = AssessmentResultSerializer(results, many=True)
            return Response(serializer.data)


# ============================================================================
# STATISTICS VIEWS
# ============================================================================

class AssessmentStatsView(APIView):
    """
    Get user's assessment statistics.

    GET /assessment/stats/

    Returns:
    - total_assessments: Total completed assessments
    - assessments_by_type: Count by assessment type
    - average_completion_time: Average time to complete
    - latest_result: Most recent assessment result summary
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get assessment statistics for user."""
        user = request.user

        # Get all user assessments
        assessments = Assessment.objects.filter(
            user=user,
            is_deleted=False
        )

        total_assessments = assessments.count()
        completed_assessments = assessments.filter(status='completed').count()

        # Count by type
        by_type = dict(
            assessments.values('assessment_type')
            .annotate(count=Count('id'))
            .values_list('assessment_type', 'count')
        )

        # Average completion time
        completed = assessments.filter(
            status='completed',
            time_spent_seconds__gt=0
        )
        avg_time = completed.aggregate(
            avg=Avg('time_spent_seconds')
        )['avg'] or 0

        # Latest result
        latest_result = AssessmentResult.objects.filter(
            assessment__user=user,
            is_deleted=False
        ).select_related('assessment').order_by('-created_at').first()

        stats = {
            'total_assessments': total_assessments,
            'completed_assessments': completed_assessments,
            'in_progress_assessments': assessments.filter(status='in_progress').count(),
            'assessments_by_type': by_type,
            'average_completion_time_seconds': int(avg_time),
            'latest_result': AssessmentResultSerializer(latest_result).data if latest_result else None
        }

        return Response(stats, status=status.HTTP_200_OK)
