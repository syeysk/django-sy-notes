from django.urls import path, re_path

from note.views import (
    NoteEditorView,
    NoteListView,
)

urlpatterns = [
    re_path('(?P<note_id>[0-9]+)', NoteEditorView.as_view(), name='note_editor'),
    path('', NoteListView.as_view(), name='note_list'),
]
