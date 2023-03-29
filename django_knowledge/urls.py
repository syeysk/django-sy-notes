from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('note/', include('note.urls')),
    path('faci/', include('faci.urls')),
    path('auth/', include('custom_auth.urls')),
    path('', include('pages.urls')),
    path('api/', include('django_knowledge.urls_api')),
]
