from django.urls import path

from note.views import note_hook
from note.views_api import NoteView, NoteSearchView

urlpatterns = [
    path('search/<str:query>/', NoteSearchView.as_view(), name='api_note_search'),
    path('<str:title>/', NoteView.as_view(), name='api_note'),
    path('hook/', note_hook, name='api_note_hook'),
]
