from django.contrib import admin
from note.models import ImageNote, Note, NoteStorageServiceModel


class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'storage', 'title', 'search_title')


admin.site.register(Note, NoteAdmin)


class ImageNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'image')


admin.site.register(ImageNote, ImageNoteAdmin)


class NoteStorageServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'source', 'description', 'is_default')


admin.site.register(NoteStorageServiceModel, NoteStorageServiceAdmin)
