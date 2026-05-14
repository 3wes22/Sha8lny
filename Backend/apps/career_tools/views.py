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

    def perform_create(self, serializer):
        """Assign current user when creating resume."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        Generate resume as PDF or DOCX.

        POST /resumes/{id}/generate/?format=pdf
        """
        resume = self.get_object()
        format_type = request.query_params.get('format') or request.data.get('format', 'pdf')
        format_type = format_type.lower()

        if format_type not in ['pdf', 'docx']:
            return Response(
                {'error': 'Invalid format. Use pdf or docx'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.career_tools.services import ResumeService

        try:
            if format_type == 'pdf':
                resume = ResumeService.generate_pdf(resume)
                file_url = request.build_absolute_uri(resume.pdf_file.url) if resume.pdf_file else None
            else:
                resume = ResumeService.generate_docx(resume)
                file_url = request.build_absolute_uri(resume.docx_file.url) if resume.docx_file else None

            return Response({
                'message': f'{format_type.upper()} generated successfully',
                'resume_id': str(resume.id),
                'format': format_type,
                'file_url': file_url,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Failed to generate {format_type.upper()}: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def optimize_ats(self, request, pk=None):
        """
        Optimize resume for ATS (Applicant Tracking Systems).

        POST /resumes/{id}/optimize_ats/
        """
        resume = self.get_object()

        from apps.career_tools.services import ResumeService

        try:
            resume = ResumeService.optimize_for_ats(resume)

            return Response({
                'message': 'ATS optimization analysis complete',
                'ats_score': float(resume.ats_score),
                'ats_grade': resume.ats_grade_display,
                'suggestions': resume.ats_suggestions,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'ATS optimization failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
