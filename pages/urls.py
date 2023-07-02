from django.urls import path

from pages.views import (
    IntroView,
    ServiceServerView,
    ProfileView,
)


urlpatterns = [
    path('service_server', ServiceServerView.as_view(), name='service_server'),
    path('profile', ProfileView.as_view(), name='custom_profile'),
    path('', IntroView.as_view(), name='index'),
]
