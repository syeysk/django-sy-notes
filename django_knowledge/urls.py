from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('admin/', admin.site.urls),
    path('api/v1/note/', include('note.urls_api')),
    path('api/v1/faci/', include('faci.urls_api')),
    path('note/', include('note.urls')),
    path('faci/', include('faci.urls')),
    path('auth/', include('custom_auth.urls')),
    path('', include('pages.urls')),
]
