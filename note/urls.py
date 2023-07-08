from django.urls import path, re_path

from note.views import (
    NoteEditorView,
    NoteListView,
)

urlpatterns = [
    path('<str:quoted_title>.md', NoteEditorView.as_view(), name='note_editor'),
    path('', NoteListView.as_view(), name='note_list'),
]
