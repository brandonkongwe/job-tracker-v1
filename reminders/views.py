"""
Views for the reminders app.

Endpoints (all under /api/v1/reminders/)
-----------------------------------------
GET    /           List own reminders
POST   /           Create a reminder
GET    /<id>/      Retrieve a reminder
PATCH  /<id>/      Update (e.g. reschedule remind_at, cancel via is_active=false)
DELETE /<id>/      Delete a reminder
POST   /<id>/cancel/  Convenience: set is_active=False without deleting
"""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrAdmin

from .models import Reminder
from .serializers import ReminderDetailSerializer, ReminderListSerializer, ReminderWriteSerializer



@extend_schema_view(
    list=extend_schema(tags=["reminders"],           summary="List reminders"),
    create=extend_schema(tags=["reminders"],         summary="Create a reminder"),
    retrieve=extend_schema(tags=["reminders"],       summary="Retrieve a reminder"),
    update=extend_schema(tags=["reminders"],         summary="Full update"),
    partial_update=extend_schema(tags=["reminders"], summary="Partial update (reschedule, cancel)"),
    destroy=extend_schema(tags=["reminders"],        summary="Delete a reminder"),
)
class ReminderViewSet(viewsets.ModelViewSet):
    """
    CRUD for reminders.
    Scoped to the authenticated user's own reminders.
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ["is_sent", "is_active", "reminder_type", "application"]
    ordering_fields    = ["remind_at", "created_at"]
    ordering           = ["remind_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Reminder.objects.select_related("user", "application")
        if user.is_admin:
            return qs.all()
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ReminderWriteSerializer
        if self.action == "retrieve":
            return ReminderDetailSerializer
        return ReminderListSerializer

    @extend_schema(
        tags=["reminders"],
        summary="Cancel a reminder (sets is_active=False)",
        responses={200: ReminderDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Convenience endpoint to deactivate a reminder without deleting it.
        Useful for frontend 'Cancel reminder' buttons — no request body needed.
        """
        reminder = self.get_object()
        if reminder.is_sent:
            return Response(
                {"detail": "Cannot cancel a reminder that has already been sent."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reminder.is_active = False
        reminder.save(update_fields=["is_active", "updated_at"])
        serializer = ReminderDetailSerializer(reminder, context={"request": request})
        return Response(serializer.data)