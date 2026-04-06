from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new user sign-up.
    Requires password + password_confirm that must match.
    Returns the created user (without exposing the password hash).
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        label=_("Confirm password"),
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match.")})
        # Run Django's built-in password validators
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Minimal read-only representation — safe for admin user listings.
    Does not expose email or personal details of other users.
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "role", "avatar", "date_joined"]
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Full profile for the authenticated user's own account.
    Readable + writable (except id, email, role, date_joined).
    Email changes are handled separately to allow re-verification in future.
    """

    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.CharField(read_only=True)
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "bio",
            "location",
            "website",
            "avatar",
            "application_count",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "email", "role", "full_name", "date_joined", "last_login"]

    def get_application_count(self, obj):
        return obj.applications.count()

    def validate_avatar(self, value):
        if value and value.size > 2 * 1024 * 1024:  # 2 MB limit for avatars
            raise serializers.ValidationError(_("Avatar must be smaller than 2 MB."))
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    Authenticated endpoint to change own password.
    Requires current password for verification before accepting the new one.
    """

    current_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password_confirm": _("New passwords do not match.")}
            )
        validate_password(attrs["new_password"])
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT login response to include basic user info,
    so the frontend doesn't need an extra /me call right after login.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "full_name": self.user.full_name,
            "role": self.user.role,
        }
        return data