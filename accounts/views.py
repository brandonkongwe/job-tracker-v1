"""
Views for the accounts app.

Endpoints
---------
POST   /api/v1/auth/register/         Register a new user
POST   /api/v1/auth/login/            Obtain JWT access + refresh tokens
POST   /api/v1/auth/token/refresh/    Refresh the access token
POST   /api/v1/auth/logout/           Blacklist the refresh token
GET    /api/v1/auth/me/               Retrieve own profile
PATCH  /api/v1/auth/me/               Update own profile
POST   /api/v1/auth/me/password/      Change own password
GET    /api/v1/auth/users/            List all users (admin only)
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .permissions import IsAdminRole
from .serializers import (
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserPublicSerializer,
)

User = get_user_model()


@extend_schema(tags=["auth"])
class RegisterView(generics.CreateAPIView):
    """
    Register a new Job Seeker account.
    No authentication required.
    Returns the created user profile (no tokens — user must login separately).
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Account created successfully. Please log in.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["auth"])
class LoginView(TokenObtainPairView):
    """
    Authenticate with email + password.
    Returns access token, refresh token, and basic user info.
    """

    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=["auth"])
class TokenRefreshView(TokenRefreshView):
    """Refresh an expired access token using a valid refresh token."""
    pass


@extend_schema(
    tags=["auth"],
    request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}}},
    responses={
        205: OpenApiResponse(description="Logout successful — refresh token blacklisted."),
        400: OpenApiResponse(description="Invalid or missing refresh token."),
    },
)
class LogoutView(APIView):
    """
    Invalidate the provided refresh token by adding it to the blacklist.
    The access token will expire naturally (short-lived by design).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Token is invalid or already expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_205_RESET_CONTENT,
        )


@extend_schema_view(
    get=extend_schema(tags=["auth"], summary="Get own profile"),
    patch=extend_schema(tags=["auth"], summary="Update own profile"),
    put=extend_schema(tags=["auth"], summary="Replace own profile"),
)
class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  — return the authenticated user's full profile.
    PATCH — partial update (preferred for frontend).
    PUT  — full update.
    Avatar upload via multipart/form-data.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["auth"], summary="Change own password")
class PasswordChangeView(APIView):
    """
    Change the authenticated user's password.
    Requires the current password for verification.
    After a successful change, all existing tokens remain valid until they expire
    — consider logging the user out on the frontend after this call.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["auth"], summary="List all users (admin only)")
class UserListView(generics.ListAPIView):
    """
    Returns a paginated list of all users.
    Restricted to Admin role only.
    """

    serializer_class = UserPublicSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    queryset = User.objects.filter(is_active=True).order_by("-date_joined")
    filterset_fields = ["role"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["date_joined", "last_login"]