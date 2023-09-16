from django.urls import path, include


urlpatterns = [
    path('v1/note/', include('note.urls_api')),
    path('v1/linker/', include('django_sy_framework.linker.urls_api')),
    path('', include('django_sy_framework.base.urls_api')),
]
