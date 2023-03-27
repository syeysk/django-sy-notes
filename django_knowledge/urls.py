from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('note/', include('note.urls')),
    path('faci/', include('faci.urls')),
    path('auth/', include('custom_auth.urls')),
    path('', include('pages.urls')),
    path('api/v1/', include('django_knowledge.urls_api')),
]
