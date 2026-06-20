"""
Career Tools Service Views

Implements REST API views for resume/CV builder and portfolio management.

SRS References:
- FR-22: Resume/CV Builder
- FR-23: ATS-Optimized Resume Generation
- FR-24: Portfolio Builder
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse

from apps.career_tools.models import Resume, Portfolio
from apps.career_tools.serializers import (
    ResumeSerializer,
    ResumeListSerializer,
    PortfolioSerializer,
    PortfolioListSerializer,
)
from apps.career_tools.services import ResumeService, PortfolioService


class ResumeViewSet(viewsets.ModelViewSet):
    """
    Manage resumes/CVs.

    SRS FR-22: Resume/CV Builder
    SRS FR-23: ATS-Optimized Resume Generation

    Endpoints:
    - GET /resumes/ - List user's resumes
    - GET /resumes/{id}/ - Get specific resume
    - POST /resumes/ - Create new resume
    - PUT /resumes/{id}/ - Update resume
    - DELETE /resumes/{id}/ - Delete resume
    - POST /resumes/{id}/generate/ - Generate PDF/DOCX
    - POST /resumes/{id}/optimize_ats/ - Optimize for ATS
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return resumes for current user only."""
        return Resume.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-is_primary', '-updated_at')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return ResumeListSerializer
        return ResumeSerializer

    def perform_create(self, serializer):
        """Assign the resume to the requesting user (``user`` is read-only)."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        Generate the structured resume document.

        POST /resumes/{id}/generate/

        Query Parameters:
        - file_format: pdf or docx (default: pdf)

        Returns the assembled, ordered resume content as JSON. Binary file export
        (a downloadable PDF/DOCX) is a v2 feature; ``export_format`` reports the
        requested format and ``export_available`` whether a file download exists.

        Note: ``file_format`` is used instead of ``format`` because DRF reserves
        the ``format`` query parameter for content negotiation.
        """
        resume = self.get_object()
        format_type = request.query_params.get('file_format', 'pdf').lower()

        if format_type not in ['pdf', 'docx']:
            return Response(
                {'error': 'Invalid format. Use pdf or docx'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'resume_id': str(resume.id),
            'export_format': format_type,
            'export_available': False,
            'export_note': 'Downloadable file export (PDF/DOCX) is planned for v2.',
            'document': ResumeService.build_resume_document(resume),
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def optimize_ats(self, request, pk=None):
        """
        Optimize resume for ATS (Applicant Tracking Systems).

        POST /resumes/{id}/optimize_ats/

        SRS FR-23: ATS-Optimized Resume Generation

        Scores the resume deterministically from its content and returns tailored
        suggestions. Works offline (no external service required).
        """
        resume = self.get_object()
        resume = ResumeService.optimize_for_ats(resume)

        return Response({
            'message': 'ATS optimization analysis complete',
            'ats_score': float(resume.ats_score),
            'ats_grade': resume.ats_grade_display,
            'suggestions': resume.ats_suggestions.get('improvements', []),
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Soft delete resume."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        return Response(
            {'message': 'Resume deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


class PortfolioViewSet(viewsets.ModelViewSet):
    """
    Manage portfolios.

    SRS FR-24: Portfolio Builder

    Endpoints:
    - GET /portfolios/ - List user's portfolios
    - GET /portfolios/{id}/ - Get specific portfolio
    - POST /portfolios/ - Create new portfolio
    - PUT /portfolios/{id}/ - Update portfolio
    - DELETE /portfolios/{id}/ - Delete portfolio
    - POST /portfolios/{id}/publish/ - Publish portfolio
    - GET /portfolios/public/{slug}/ - View public portfolio
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return portfolios for current user only."""
        return Portfolio.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-updated_at')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return PortfolioListSerializer
        return PortfolioSerializer

    def perform_create(self, serializer):
        """Assign the portfolio to the requesting user (``user`` is read-only)."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish portfolio (make it public).

        POST /portfolios/{id}/publish/

        Generates public URL and makes portfolio visible.
        """
        portfolio = self.get_object()
        portfolio = PortfolioService.publish_portfolio(portfolio)

        return Response({
            'message': 'Portfolio published successfully',
            'public_url': portfolio.public_url,
            'slug': portfolio.custom_url_slug,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='public/(?P<slug>[-\\w]+)')
    def public_view(self, request, slug=None):
        """
        View public portfolio by slug.

        GET /portfolios/public/{slug}/

        Anyone can access this (no authentication required).
        """
        try:
            portfolio = Portfolio.objects.get(
                custom_url_slug=slug,
                is_public=True,
                is_deleted=False
            )

            # Increment view count
            portfolio.view_count += 1
            portfolio.save(update_fields=['view_count'])

            serializer = PortfolioSerializer(portfolio)
            return Response(serializer.data)

        except Portfolio.DoesNotExist:
            return Response(
                {'error': 'Portfolio not found or not public'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, *args, **kwargs):
        """Soft delete portfolio."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        return Response(
            {'message': 'Portfolio deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
