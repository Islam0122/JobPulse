from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    StackViewSet,
    WorkFormatViewSet,
    EmploymentTypeViewSet
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('stacks', StackViewSet, basename='stack')
router.register('work-formats', WorkFormatViewSet, basename='workformat')
router.register('employment-types', EmploymentTypeViewSet, basename='employmenttype')

urlpatterns = [
    path('', include(router.urls)),
]