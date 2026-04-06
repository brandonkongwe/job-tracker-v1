import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
class UserManager(BaseUserManager):
    """Custom manager: email is the unique identifier, not username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required."))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", User.Role.JOB_SEEKER)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model.

    Fields
    ------
    id          : UUID primary key — safer to expose in APIs than auto-increment int
    email       : unique login identifier
    first_name  : required
    last_name   : required
    role        : JobSeeker (default) or Admin
    bio         : optional short profile bio
    location    : optional current location (city / country)
    website     : optional personal or portfolio URL
    avatar      : optional profile picture
    is_active   : soft-disable accounts without deleting data
    is_staff    : grants Django admin access
    date_joined : set automatically on creation
    last_login  : updated by JWT on token issue (SIMPLE_JWT['UPDATE_LAST_LOGIN'])
    """

    class Role(models.TextChoices):
        JOB_SEEKER = "job_seeker", _("Job Seeker")
        ADMIN = "admin", _("Admin")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=100)
    last_name = models.CharField(_("last name"), max_length=100)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.JOB_SEEKER,
        db_index=True,
    )

    bio = models.TextField(_("bio"), blank=True, default="")
    location = models.CharField(_("location"), max_length=150, blank=True, default="")
    website = models.URLField(_("website"), blank=True, default="")
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_job_seeker(self):
        return self.role == self.Role.JOB_SEEKER