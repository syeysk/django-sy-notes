from django.contrib import admin
from note.models import ImageNote, Note, NoteStorageServiceModel


class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'storage', 'user', 'title', 'search_title')


admin.site.register(Note, NoteAdmin)


class ImageNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'image')


admin.site.register(ImageNote, ImageNoteAdmin)


class NoteStorageServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'source', 'description', 'is_default')


admin.site.register(NoteStorageServiceModel, NoteStorageServiceAdmin)
