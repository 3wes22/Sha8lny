"""
User Service Views

Implements REST API views as specified in SRS Appendix B.

SRS References:
- FR-1: User Registration
- FR-2: User Login (returns JWT access token)
- FR-3: Profile Management
- FR-4: User Preferences
- FR-5: Skill Tracking
- Appendix B: API Endpoint Summary
"""

from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from django.utils import timezone

from apps.users.models import User, Skill, UserSkill, UserPreferences
from apps.users.serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    SkillSerializer,
    SkillListSerializer,
    SkillSearchSerializer,
    UserSkillSerializer,
    UserSkillCreateSerializer,
    UserSkillUpdateSerializer,
    UserPreferencesSerializer,
)
from apps.users.services import SkillService


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint.

    SRS Reference: FR-1 (User Registration)
    SRS Note: Specifies Auth0, but using Django auth for MVP
    Endpoint: POST /auth/register/

    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "username": "johndoe",
        "full_name": "John Doe",
        "date_of_birth": "1995-05-15",
        "phone_number": "+201234567890",
        "preferred_language": "en"
    }

    Response: User profile + JWT tokens
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """Create user and return JWT tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens (SRS FR-2: return JWT access token)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Registration successful'
            },
            status=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    """
    User login endpoint.

    SRS Reference: FR-2 (User Login)
    SRS: "The system shall authenticate users using Auth0 and return a JWT access token"
    Endpoint: POST /auth/login (SRS Appendix B)

    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }

    Response: User profile + JWT tokens
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Update last login timestamp
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])

        # Generate JWT tokens (SRS FR-2 requirement)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'user': UserDetailSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'message': 'Login successful'
            },
            status=status.HTTP_200_OK
        )


class UserLogoutView(APIView):
    """
    User logout endpoint.

    Blacklists the refresh token to prevent reuse.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Logout user by blacklisting refresh token."""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response(
                {'message': 'Logout successful'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TokenRefreshView(BaseTokenRefreshView):
    """
    Refresh JWT access token.

    Standard JWT token refresh endpoint.
    """
    pass


# ============================================================================
# USER PROFILE VIEWS
# ============================================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update current user profile.

    SRS References:
    - FR-3 (Profile Management)
    - Appendix B: GET /users/me, PUT /users/me

    GET /users/me - Get current user profile
    PUT /users/me - Update profile

    SRS FR-3: Users shall be able to:
    - Edit personal information
    - Set career goals
    - Upload/pre-fill skills
    - Add experience summary
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return current authenticated user."""
        return self.request.user

    def get_serializer_class(self):
        """Use different serializers for GET vs PUT."""
        if self.request.method == 'GET':
            return UserDetailSerializer
        return UserUpdateSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get current user profile.

        SRS Endpoint: GET /users/me (Appendix B)
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Update user profile.

        SRS Endpoint: PUT /users/me (Appendix B)
        SRS FR-3: Edit personal information
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return updated profile using detail serializer
        return Response(
            UserDetailSerializer(instance).data,
            status=status.HTTP_200_OK
        )


class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """
    Get and update user preferences.

    SRS Reference: FR-4 (User Preferences)
    SRS: The system shall store:
    - Preferred learning format
    - Target job role
    - Interests
    - Language preference

    GET /users/me/preferences/ - Get preferences
    PUT /users/me/preferences/ - Update preferences
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get or create preferences for current user."""
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.request.user
        )
        return preferences


# ============================================================================
# SKILL VIEWS
# ============================================================================

class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and search available skills.

    SRS Reference: FR-5 (Skill Tracking)

    GET /skills/ - List all skills
    GET /skills/{id}/ - Get skill details
    GET /skills/search/ - Search skills by name
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Skill.objects.filter(is_active=True, is_deleted=False)

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return SkillListSerializer
        return SkillSerializer

    def get_queryset(self):
        """Filter skills with optional query parameters."""
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Order by popularity
        queryset = queryset.order_by('-popularity_score', 'name')

        return queryset

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search skills by name.

        SRS Reference: FR-5 (Skill Tracking)
        Query Parameters:
        - query: Search term (required)
        - category: Filter by category (optional)
        - limit: Max results (default: 20)
        """
        serializer = SkillSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        category = serializer.validated_data.get('category')
        limit = serializer.validated_data.get('limit', 20)

        # Search using service
        skills = SkillService.search_skills(query)

        # Filter by category if specified
        if category:
            skills = [s for s in skills if s.category == category]

        # Limit results
        skills = skills[:limit]

        return Response(
            SkillSerializer(skills, many=True).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        List all skill categories.

        Returns available skill categories for filtering.
        """
        categories = [
            {'value': 'technical', 'label': 'Technical'},
            {'value': 'soft', 'label': 'Soft Skills'},
            {'value': 'business', 'label': 'Business'},
            {'value': 'design', 'label': 'Design'},
            {'value': 'data', 'label': 'Data & Analytics'},
            {'value': 'marketing', 'label': 'Marketing'},
            {'value': 'other', 'label': 'Other'},
        ]
        return Response(categories)


class UserSkillViewSet(viewsets.ModelViewSet):
    """
    Manage user skills.

    SRS Reference: FR-5 (Skill Tracking)
    SRS Endpoints (Appendix B):
    - GET /users/skills - List user skills
    - POST /users/skills - Add skill

    Additional endpoints:
    - GET /user-skills/{id}/ - Get specific user skill
    - PUT /user-skills/{id}/ - Update skill proficiency
    - DELETE /user-skills/{id}/ - Remove skill
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return skills for current user only."""
        return UserSkill.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('skill').order_by('-created_at')

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return UserSkillCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserSkillUpdateSerializer
        return UserSkillSerializer

    def create(self, request, *args, **kwargs):
        """
        Add skill to user profile.

        SRS Endpoint: POST /users/skills (Appendix B)
        SRS FR-5: System shall allow adding and modifying user skills
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_skill = serializer.save()

        return Response(
            UserSkillSerializer(user_skill).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        Update skill proficiency level.

        SRS FR-5: System shall update skill levels after roadmap progress
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_skill = serializer.save()

        return Response(
            UserSkillSerializer(updated_skill).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """
        Remove skill from user profile (soft delete).

        Uses SkillService for consistency with business logic.
        """
        instance = self.get_object()
        SkillService.remove_user_skill(
            user=request.user,
            skill=instance.skill
        )

        return Response(
            {'message': 'Skill removed successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'])
    def gap_analysis(self, request):
        """
        Analyze skill gaps against target skills.

        Query Parameters:
        - target_skills: Comma-separated list of skill names

        Returns:
        - current_skills: User's current skills
        - missing_skills: Skills user doesn't have
        - skills_to_improve: Skills below expert level
        """
        target_skills_param = request.query_params.get('target_skills', '')
        if not target_skills_param:
            return Response(
                {'error': 'target_skills parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_skills = [s.strip() for s in target_skills_param.split(',')]

        analysis = SkillService.get_skill_gap_analysis(
            user=request.user,
            target_skills=target_skills
        )

        return Response(analysis, status=status.HTTP_200_OK)
