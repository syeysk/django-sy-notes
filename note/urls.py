from django.urls import path, re_path

from note.views import (
    NoteEditorView,
    NoteListView,
    NoteStorageServiceListView,
    NoteImportExportView,
)

urlpatterns = [
    path('import_export', NoteImportExportView.as_view(), name='note_import_export'),
    path('storage_services/<str:pk>', NoteStorageServiceListView.as_view(), name='note_service_storage_edit'),
    path('storage_services/', NoteStorageServiceListView.as_view(), name='note_service_storage_add'),
    path('storage_services', NoteStorageServiceListView.as_view(), name='note_service_storage_list'),
    path('<str:quoted_title>.md', NoteEditorView.as_view(), name='note_editor'),
    path('', NoteListView.as_view(), name='note_list'),
]
