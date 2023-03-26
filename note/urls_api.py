from django.urls import path

from note.views import note_search, note_hook
from note.views_api import NoteView

urlpatterns = [
    path('search/<str:query>/', note_search, name='api_note_search'),
    path('<str:title>/', NoteView.as_view(), name='api_note'),
    path('hook/', note_hook, name='api_note_hook'),
]
