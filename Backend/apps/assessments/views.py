"""
Assessment API views with staged-skills rollout and legacy compatibility.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from django.conf import settings
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.models import Assessment, AssessmentResult
from apps.assessments.role_graph import load_role_graph, resolve_role_key
from apps.assessments.serializers import (
    AssessmentCreateSerializer,
    AssessmentListSerializer,
    AssessmentResponseSerializer,
    AssessmentResultSerializer,
    AssessmentSerializer,
)
from apps.assessments.services import AssessmentService
from apps.assessments.tasks import (
    evaluate_assessment_answers_task,
    generate_assessment_questions_task,
    generate_stage_one_task,
    process_final_evaluation_task,
    process_stage_one_submission_task,
    run_evaluate_assessment_answers,
    run_generate_assessment_questions,
    run_generate_stage_one,
    run_process_final_evaluation,
    run_process_stage_one_submission,
)
from apps.core.ai_throttles import AIBurstThrottle, AISustainedThrottle
from apps.core.health_checks import get_ai_runtime_health


def dispatch_assessment_task(task, eager_runner, assessment_id: str):
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        task_id = uuid4().hex
        eager_runner(assessment_id, task_id=task_id)
        return SimpleNamespace(id=task_id)
    return task.delay(assessment_id)


class AssessmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    _AI_ACTIONS = {'create', 'submit'}

    def get_throttles(self):
        if self.action in self._AI_ACTIONS:
            return [AIBurstThrottle(), AISustainedThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return Assessment.objects.filter(
            user=self.request.user,
            is_deleted=False,
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return AssessmentCreateSerializer
        if self.action in {'list', 'history'}:
            return AssessmentListSerializer
        if self.action == 'submit':
            return AssessmentResponseSerializer
        return AssessmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assessment = serializer.save()
        if assessment.is_staged:
            task = dispatch_assessment_task(
                generate_stage_one_task,
                run_generate_stage_one,
                str(assessment.id),
            )
        else:
            task = dispatch_assessment_task(
                generate_assessment_questions_task,
                run_generate_assessment_questions,
                str(assessment.id),
            )
        assessment.ai_task_id = getattr(task, "id", "") or ""
        assessment.save(update_fields=["ai_task_id", "updated_at"])

        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        assessment_type = request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='runtime/health')
    def runtime_health(self, request):
        return Response(get_ai_runtime_health())

    @action(detail=False, methods=['post'], url_path='preview-questions')
    def preview_questions(self, request):
        target_career = str(request.data.get('target_career') or '').strip()
        if not target_career:
            return Response(
                {'error': 'target_career is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        require_live_llm = request.data.get('require_live_llm', False)
        if isinstance(require_live_llm, str):
            require_live_llm = require_live_llm.strip().lower() in {'1', 'true', 'yes', 'on'}
        else:
            require_live_llm = bool(require_live_llm)

        role_graph = load_role_graph(resolve_role_key(target_career))
        questions, metadata, retrieval_info = AssessmentAIService.generate_stage_one(role_graph.role_key, role_graph)
        client_questions = AssessmentService._normalize_staged_questions(questions)
        runtime_health = get_ai_runtime_health()

        response_payload = {
            'target_career': target_career,
            'role_key': role_graph.role_key,
            'role_label': role_graph.role_label,
            'question_count': len(client_questions),
            'questions': client_questions,
            'metadata': metadata.to_dict(),
            'runtime_health': runtime_health,
        }

        if require_live_llm and metadata.fallback_used:
            return Response(
                {
                    'error': 'Live Gemini generation is unavailable',
                    **response_payload,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(response_payload, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        queryset = self.get_queryset()
        assessment_type = request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)
        latest_assessment = queryset.first()
        if not latest_assessment:
            return Response({'error': 'No assessments found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AssessmentSerializer(latest_assessment).data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        queryset = self.get_queryset()
        assessment_type = request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        limit = request.query_params.get('limit', '20')
        try:
            queryset = queryset[: min(int(limit), 100)]
        except ValueError:
            pass
        return Response(AssessmentListSerializer(queryset, many=True).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        assessment = self.get_object()
        serializer = AssessmentResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        responses = serializer.validated_data['responses']

        if assessment.is_staged:
            active_questions = AssessmentService.get_active_questions(assessment)
            if not active_questions:
                return Response(
                    {'error': 'Assessment questions are still being prepared'},
                    status=status.HTTP_409_CONFLICT,
                )

            if assessment.stage == 'stage_1':
                assessment = AssessmentService.submit_stage_one(str(assessment.id), request.user, responses)
                task = dispatch_assessment_task(
                    process_stage_one_submission_task,
                    run_process_stage_one_submission,
                    str(assessment.id),
                )
                assessment.ai_task_id = getattr(task, "id", "") or ""
                assessment.save(update_fields=['ai_task_id', 'updated_at'])
                return Response(
                    {
                        'message': 'Stage one submitted successfully and stage two is being prepared',
                        'assessment': AssessmentSerializer(assessment).data,
                        'result_id': None,
                        'submission_state': 'stage_1_analyzing',
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

            if assessment.stage == 'stage_2':
                assessment = AssessmentService.submit_stage_two(str(assessment.id), request.user, responses)
                task = dispatch_assessment_task(
                    process_final_evaluation_task,
                    run_process_final_evaluation,
                    str(assessment.id),
                )
                assessment.ai_task_id = getattr(task, "id", "") or ""
                assessment.save(update_fields=['ai_task_id', 'updated_at'])
                return Response(
                    {
                        'message': 'Assessment submitted successfully and queued for final analysis',
                        'assessment': AssessmentSerializer(assessment).data,
                        'result_id': None,
                        'submission_state': 'stage_2_analyzing',
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

            return Response(
                {'error': 'Assessment already completed'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if assessment.status == 'completed':
            return Response({'error': 'Assessment already completed'}, status=status.HTTP_400_BAD_REQUEST)
        if not assessment.questions:
            return Response(
                {'error': 'Assessment questions are still being generated'},
                status=status.HTTP_409_CONFLICT,
            )

        assessment = AssessmentService.complete_assessment(str(assessment.id), request.user, responses)
        task = dispatch_assessment_task(
            evaluate_assessment_answers_task,
            run_evaluate_assessment_answers,
            str(assessment.id),
        )
        assessment.ai_task_id = getattr(task, "id", "") or ""
        assessment.save(update_fields=['ai_task_id', 'updated_at'])
        return Response(
            {
                'message': 'Assessment submitted successfully and queued for analysis',
                'assessment': AssessmentSerializer(assessment).data,
                'result_id': None,
                'submission_state': 'processing',
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        assessment = self.get_object()

        if assessment.is_staged:
            if assessment.ai_processing_status == 'failed':
                return Response(
                    {'error': 'AI processing failed. Please try resubmitting.', 'status': 'failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if assessment.stage != 'completed' or assessment.ai_processing_status in {'pending', 'processing'}:
                submission_state = 'stage_1_analyzing'
                status_message = 'We are analyzing your initial responses to create targeted questions for you.'
                if assessment.stage == 'stage_2':
                    submission_state = 'stage_2_analyzing'
                    status_message = 'We are finalizing your staged assessment result.'

                return Response(
                    {
                        'message': 'Assessment is still processing',
                        'status': assessment.ai_processing_status,
                        'submission_state': submission_state,
                        'status_message': status_message,
                        'next_actions': [
                            {'label': 'Return to dashboard', 'route': '/dashboard', 'kind': 'assessment'}
                        ],
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

        else:
            if assessment.status != 'completed':
                return Response({'error': 'Assessment not yet completed'}, status=status.HTTP_400_BAD_REQUEST)
            if assessment.ai_processing_status == 'pending':
                return Response(
                    {
                        'message': 'Assessment is queued for AI processing',
                        'status': 'pending',
                        'submission_state': 'processing',
                        'status_message': 'Your answers are saved and waiting for analysis.',
                        'next_actions': [
                            {'label': 'Return to dashboard', 'route': '/dashboard', 'kind': 'assessment'}
                        ],
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            if assessment.ai_processing_status == 'processing':
                return Response(
                    {
                        'message': 'AI is currently processing your assessment',
                        'status': 'processing',
                        'submission_state': 'processing',
                        'status_message': 'We are building your strengths, gaps, and recommended next steps.',
                        'next_actions': [
                            {'label': 'Return to dashboard', 'route': '/dashboard', 'kind': 'assessment'}
                        ],
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            if assessment.ai_processing_status == 'failed':
                return Response(
                    {'error': 'AI processing failed. Please try resubmitting.', 'status': 'failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        try:
            result = AssessmentResult.objects.get(assessment=assessment, is_deleted=False)
        except AssessmentResult.DoesNotExist:
            return Response({'error': 'Assessment result not found'}, status=status.HTTP_404_NOT_FOUND)

        data = AssessmentResultSerializer(result).data
        data['submission_state'] = 'completed'
        data['status_message'] = 'Your assessment is ready. Review the outcome and continue to roadmap or jobs.'
        data['next_actions'] = [
            {'label': 'View roadmap', 'route': '/roadmap', 'kind': 'roadmap'},
            {'label': 'Explore jobs', 'route': '/jobs', 'kind': 'jobs'},
        ]
        return Response(data)
