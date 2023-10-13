from django.urls import path

from note.views import (
    NoteEditView,
    NoteListView,
    NoteStorageServiceListView,
    NoteImportExportView,
    NoteView,
)

urlpatterns = [
    path('<str:source>/<str:quoted_title>.md/edit', NoteEditView.as_view(), name='note_editor_post2'),
    path('<str:source>/new/edit', NoteEditView.as_view(), name='note_create_post'),
    path('<str:source>/<str:quoted_title>.md', NoteView.as_view(), name='note_editor2'),
    path('<str:source>/new', NoteView.as_view(), name='note_create'),
    path('import_export', NoteImportExportView.as_view(), name='note_import_export'),
    path('storage_services/<str:pk>', NoteStorageServiceListView.as_view(), name='note_service_storage_edit'),
    path('storage_services/', NoteStorageServiceListView.as_view(), name='note_service_storage_add'),
    path('storage_services', NoteStorageServiceListView.as_view(), name='note_service_storage_list'),
    path('', NoteListView.as_view(), name='note_list'),
]
