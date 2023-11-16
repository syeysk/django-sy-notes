from django.conf import settings
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('note/', include('note.urls')),
    path('api/', include('server.urls_api')),
    path('auth/', include('django_sy_framework.custom_auth.urls')),
    path('token/', include('django_sy_framework.token.urls')),
    path('', include('django_sy_framework.base.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
