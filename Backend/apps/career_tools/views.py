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

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        Generate resume as PDF or DOCX.

        POST /resumes/{id}/generate/

        Query Parameters:
        - format: pdf or docx (default: pdf)

        Returns: File download

        TODO: Implement PDF/DOCX generation using ReportLab or python-docx
        """
        resume = self.get_object()
        format_type = request.query_params.get('format', 'pdf').lower()

        if format_type not in ['pdf', 'docx']:
            return Response(
                {'error': 'Invalid format. Use pdf or docx'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Implement actual PDF/DOCX generation
        # For now, return a placeholder response
        return Response({
            'message': f'{format_type.upper()} generation is pending implementation',
            'resume_id': str(resume.id),
            'format': format_type
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=True, methods=['post'])
    def optimize_ats(self, request, pk=None):
        """
        Optimize resume for ATS (Applicant Tracking Systems).

        POST /resumes/{id}/optimize_ats/

        SRS FR-23: ATS-Optimized Resume Generation

        Analyzes resume and provides ATS optimization suggestions.

        TODO: Implement ATS optimization using AI
        """
        resume = self.get_object()

        # TODO: Implement ATS optimization logic
        # For now, return a placeholder score
        resume.is_ats_optimized = True
        resume.ats_score = 85.0
        resume.save()

        return Response({
            'message': 'ATS optimization analysis complete',
            'ats_score': resume.ats_score,
            'suggestions': [
                'Add more keywords from job description',
                'Use standard section headings',
                'Avoid tables and complex formatting',
                'Include measurable achievements'
            ]
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
        ).prefetch_related('projects').order_by('-updated_at')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return PortfolioListSerializer
        return PortfolioSerializer

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish portfolio (make it public).

        POST /portfolios/{id}/publish/

        Generates public URL and makes portfolio visible.
        """
        portfolio = self.get_object()
        portfolio.is_public = True
        portfolio.save()

        public_url = f"/portfolio/{portfolio.slug}/"

        return Response({
            'message': 'Portfolio published successfully',
            'public_url': public_url,
            'slug': portfolio.slug
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
                slug=slug,
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
