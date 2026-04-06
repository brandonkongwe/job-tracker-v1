from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import JobApplicationViewSet

app_name = "applications"

router = DefaultRouter()
router.register(r"", JobApplicationViewSet, basename="application")

urlpatterns = [
    path("", include(router.urls)),
]