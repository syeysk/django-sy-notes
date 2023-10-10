class NoteBackuperMixin:
    storage = None
    queryset = None

    def b_clear(self):
        self.queryset.delete()

    def b_add(self, title, content):
        from note.models import Note
        note = self.queryset.filter(title=title).first()
        if not note:
            note = Note(title=title, content=content, storage=self.storage)
            note.fetch_search_fields()
            note.save()

    def b_delete(self, title):
        note = self.queryset.filter(title=title).first()
        if note:
            note.delete()

    def b_edit(self, title, new_title=None, new_content=None):
        from note.models import Note
        note = self.queryset.filter(title=title).first()
        if not note:
            note = self.queryset.filter(title=new_title).first()
            if not note:
                note = Note(title=new_title, content=new_content, storage=self.storage)
                note.fetch_search_fields()
                note.save()

        updated_fields = []
        if new_title and note.title != new_title:
            note.title = new_title
            updated_fields.append('title')

        if new_content and note.content != new_content:
            note.content = new_content
            updated_fields.append('content')

        if updated_fields:
            note.fetch_search_fields()
            note.save()
