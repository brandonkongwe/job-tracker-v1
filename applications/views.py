"""
Views for the applications app.

Endpoints (all under /api/v1/applications/)
-------------------------------------------
GET    /                               List own applications (paginated)
POST   /                               Create a new application
GET    /<id>/                          Retrieve application detail
PATCH  /<id>/                          Partial update (e.g. status change)
PUT    /<id>/                          Full update
DELETE /<id>/                          Delete application
POST   /<id>/documents/                Upload a document
DELETE /<id>/documents/<doc_id>/       Delete a document
GET    /<id>/history/                  Status change audit trail
"""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOwnerOrAdmin

from .filters import JobApplicationFilter
from .models import Document, JobApplication, StatusHistory
from .pagination import ApplicationPagination
from .serializers import (
    DocumentSerializer,
    JobApplicationDetailSerializer,
    JobApplicationListSerializer,
    JobApplicationWriteSerializer,
    StatusHistorySerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["applications"],
        summary="List job applications",
        parameters=[
            OpenApiParameter("search",        description="Search company, title, location, notes"),
            OpenApiParameter("status",        description="Filter by status (repeatable)"),
            OpenApiParameter("work_mode",     description="Filter by work mode"),
            OpenApiParameter("is_active",     description="true = active only, false = terminal only"),
            OpenApiParameter("applied_after", description="Applied on or after (YYYY-MM-DD)"),
            OpenApiParameter("ordering",      description="Order by: created_at, applied_date, company_name, -created_at …"),
            OpenApiParameter("page",          description="Page number"),
            OpenApiParameter("page_size",     description="Results per page (max 100)"),
        ],
    ),
    create=extend_schema(tags=["applications"],  summary="Create a new application"),
    retrieve=extend_schema(tags=["applications"], summary="Retrieve application detail"),
    update=extend_schema(tags=["applications"],   summary="Full update"),
    partial_update=extend_schema(tags=["applications"], summary="Partial update (status change, notes, etc.)"),
    destroy=extend_schema(tags=["applications"],  summary="Delete an application"),
)
class JobApplicationViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for job applications.
    Users only ever see and modify their own applications.
    Admins can see all (scoped in get_queryset).
    """

    permission_classes    = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    pagination_class      = ApplicationPagination
    filterset_class       = JobApplicationFilter
    search_fields         = ["company_name", "job_title", "location", "notes", "source_detail"]
    ordering_fields       = ["created_at", "updated_at", "applied_date", "company_name", "job_title", "status"]
    ordering              = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        base_qs = JobApplication.objects.select_related("user").prefetch_related(
            Prefetch("documents", queryset=Document.objects.order_by("-uploaded_at")),
            Prefetch("status_history", queryset=StatusHistory.objects.order_by("changed_at")),
        )
        if user.is_admin:
            return base_qs.all()
        return base_qs.filter(user=user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return JobApplicationWriteSerializer
        if self.action == "retrieve":
            return JobApplicationDetailSerializer
        return JobApplicationListSerializer


    @extend_schema(
        tags=["applications"],
        summary="Upload a document (CV, cover letter) to an application",
        request={"multipart/form-data": DocumentSerializer},
        responses={201: DocumentSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="documents",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_document(self, request, pk=None):
        application = self.get_object()
        serializer = DocumentSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(application=application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["applications"],
        summary="Delete a document from an application",
        responses={204: None},
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"documents/(?P<doc_id>[0-9a-f-]+)",
    )
    def delete_document(self, request, pk=None, doc_id=None):
        application = self.get_object()
        document = get_object_or_404(Document, id=doc_id, application=application)
        document.file.delete(save=False)   # remove file from storage
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @extend_schema(
        tags=["applications"],
        summary="Get status change history for an application",
        responses={200: StatusHistorySerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        application = self.get_object()
        history_qs  = application.status_history.order_by("changed_at")
        serializer  = StatusHistorySerializer(history_qs, many=True)
        return Response(serializer.data)