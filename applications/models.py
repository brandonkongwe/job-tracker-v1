import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
def validate_cv_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    allowed = getattr(settings, "ALLOWED_CV_EXTENSIONS", [".pdf", ".doc", ".docx"])
    if ext not in allowed:
        raise ValidationError(
            _("Unsupported file type '%(ext)s'. Allowed: %(allowed)s.")
            % {"ext": ext, "allowed": ", ".join(allowed)}
        )


def validate_cv_size(value):
    max_size = getattr(settings, "MAX_UPLOAD_SIZE", 5 * 1024 * 1024)
    if value.size > max_size:
        raise ValidationError(
            _("File size %(size)s MB exceeds the %(max)s MB limit.")
            % {
                "size": round(value.size / 1024 / 1024, 1),
                "max": round(max_size / 1024 / 1024),
            }
        )


def cv_upload_path(instance, filename):
    """Store CVs under: cvs/<user_id>/<application_id>/<filename>"""
    return f"cvs/{instance.application.user_id}/{instance.application_id}/{filename}"


class JobApplication(models.Model):
    """
    Represents a single job application made by a user.

    The status field drives the pipeline (Saved => Applied => … => Offer).
    Salary fields are optional — not all job postings disclose compensation.
    source tracks where the user found the role (LinkedIn, Referral, etc.).
    """

    class Status(models.TextChoices):
        SAVED       = "saved",       _("Saved")
        APPLIED     = "applied",     _("Applied")
        SCREENING   = "screening",   _("Screening")
        INTERVIEW   = "interview",   _("Interview")
        OFFER       = "offer",       _("Offer")
        ACCEPTED    = "accepted",    _("Accepted")
        REJECTED    = "rejected",    _("Rejected")
        WITHDRAWN   = "withdrawn",   _("Withdrawn")

    class WorkMode(models.TextChoices):
        REMOTE   = "remote",   _("Remote")
        HYBRID   = "hybrid",   _("Hybrid")
        ON_SITE  = "on_site",  _("On-site")

    class Source(models.TextChoices):
        LINKEDIN    = "linkedin",    _("LinkedIn")
        INDEED      = "indeed",      _("Indeed")
        COMPANY     = "company",     _("Company Website")
        REFERRAL    = "referral",    _("Referral")
        RECRUITER   = "recruiter",   _("Recruiter")
        JOB_BOARD   = "job_board",   _("Job Board")
        OTHER       = "other",       _("Other")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        db_index=True,
    )

    company_name = models.CharField(_("company name"), max_length=200, db_index=True)
    job_title    = models.CharField(_("job title"), max_length=200, db_index=True)
    job_url      = models.URLField(_("job posting URL"), blank=True, default="")
    location     = models.CharField(_("location"), max_length=200, blank=True, default="")
    work_mode    = models.CharField(
        _("work mode"),
        max_length=10,
        choices=WorkMode.choices,
        blank=True,
        default="",
    )

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.SAVED,
        db_index=True,
    )

    salary_min    = models.PositiveIntegerField(_("salary min (annual)"), null=True, blank=True)
    salary_max    = models.PositiveIntegerField(_("salary max (annual)"), null=True, blank=True)
    salary_currency = models.CharField(_("currency"), max_length=3, default="USD")

    source = models.CharField(
        _("source"),
        max_length=20,
        choices=Source.choices,
        default=Source.OTHER,
    )
    source_detail = models.CharField(
        _("source detail"),
        max_length=200,
        blank=True,
        default="",
        help_text=_("E.g. referrer name, recruiter company, specific job board."),
    )

    applied_date       = models.DateField(_("date applied"), null=True, blank=True)
    interview_date     = models.DateTimeField(_("interview date/time"), null=True, blank=True)
    offer_deadline     = models.DateField(_("offer deadline"), null=True, blank=True)

    notes = models.TextField(_("notes"), blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("job application")
        verbose_name_plural = _("job applications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "applied_date"]),
        ]

    def __str__(self):
        return f"{self.job_title} at {self.company_name} [{self.get_status_display()}]"

    def clean(self):
        if self.salary_min and self.salary_max and self.salary_min > self.salary_max:
            raise ValidationError({"salary_min": _("Minimum salary cannot exceed maximum salary.")})

    @property
    def is_active(self):
        """True if the application is still in-flight (not a terminal state)."""
        return self.status not in {
            self.Status.ACCEPTED,
            self.Status.REJECTED,
            self.Status.WITHDRAWN,
        }

    @property
    def salary_range_display(self):
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,} – {self.salary_max:,}"
        if self.salary_min:
            return f"{self.salary_currency} {self.salary_min:,}+"
        return "Not disclosed"


class Document(models.Model):
    """
    A file (CV or cover letter) attached to a specific job application.
    Multiple documents per application are supported.
    """

    class DocumentType(models.TextChoices):
        CV           = "cv",           _("CV / Resume")
        COVER_LETTER = "cover_letter", _("Cover Letter")
        OTHER        = "other",        _("Other")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(
        _("document type"),
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.CV,
    )
    file = models.FileField(
        _("file"),
        upload_to=cv_upload_path,
        validators=[validate_cv_extension, validate_cv_size],
    )
    original_filename = models.CharField(_("original filename"), max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("document")
        verbose_name_plural = _("documents")
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.original_filename}"

    def save(self, *args, **kwargs):
        # Preserve original filename before storage renames it
        if not self.original_filename and self.file:
            self.original_filename = self.file.name
        super().save(*args, **kwargs)

    @property
    def file_size_display(self):
        size = self.file.size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / 1024 / 1024:.1f} MB"


class StatusHistory(models.Model):
    """
    Immutable log of every status change on a JobApplication.
    Written automatically via the serializer's update() method.
    Used by the analytics app to compute time-between-stages metrics.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    from_status = models.CharField(
        _("from status"),
        max_length=20,
        choices=JobApplication.Status.choices,
        blank=True,  # blank on initial creation
        default="",
    )
    to_status = models.CharField(
        _("to status"),
        max_length=20,
        choices=JobApplication.Status.choices,
    )
    changed_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(
        _("note"),
        max_length=500,
        blank=True,
        default="",
        help_text=_("Optional note about why the status changed."),
    )

    class Meta:
        verbose_name = _("status history")
        verbose_name_plural = _("status histories")
        ordering = ["changed_at"]

    def __str__(self):
        return f"{self.from_status} → {self.to_status} ({self.changed_at:%Y-%m-%d})"