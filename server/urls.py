from django.contrib import admin
from django.urls import path, include

from django_sy_framework.base import urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('note/', include('note.urls')),
    path('auth/', include('custom_auth.urls')),
    path('api/', include('server.urls_api')),
] + urls.urlpatterns
