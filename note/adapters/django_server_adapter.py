from urllib.parse import quote

from django.conf import settings
from django.db.models import Q
from django.shortcuts import resolve_url

from note.adapters.base_adapter import BaseAdapter


class DjangoServerAdapter(BaseAdapter):
    verbose_name = 'Микросервис заметок'
    MAX_PORTION_SIZE = 400
    portion = []

    def __init__(self, storage_uuid):
        from note.models import Note
        self.storage_uuid = storage_uuid
        self.queryset = Note.objects.filter(storage_uuid=storage_uuid)

    def clear(self):
        self.queryset.delete()

    def add_to_portion(self, file_name, file_content):
        from note.models import Note
        fields = Note(
            title=file_name,
            content=file_content,
            storage_uuid=self.storage_uuid,
        )
        fields.fetch_search_fields()
        self.portion.append(fields)

    def commit(self):
        from note.models import Note
        Note.objects.bulk_create(self.portion, self.MAX_PORTION_SIZE)
        self.portion.clear()

    def search(
        self,
        operator,
        count_on_page,
        page_number,
        fields,
        file_name=None,
        file_content=None,
    ):
        from django.core.paginator import Paginator
        from note.models import prepare_to_search
        filter = {}
        if file_name:
            file_name = prepare_to_search(file_name)
            filter['search_title__contains'] = file_name

        if file_content:
            file_content = prepare_to_search(file_content)
            filter['search_content__contains'] = file_content

        notes = self.queryset
        if len(filter) == 2 and operator == 'or':
            notes = notes.filter(Q(search_title__contains=file_name) | Q(search_content__contains=file_content))
        else:
            notes = notes.filter(**filter)

        paginator = Paginator(notes, count_on_page)
        page = paginator.page(page_number)

        notes = list(page.object_list.values(*fields))
        for note in notes:
            note['url'] = self.get_note_url(note['title'])

        return notes, {'num_pages': paginator.num_pages, 'count': paginator.count}

    def get_note_url(self, title):
        return '{}/{}'.format(settings.SITE_URL, resolve_url('note_editor', quoted_title=quote(title)))

    def get(self, title):
        notes = self.queryset.filter(title=title)
        note = notes.first()
        return {'title': note.title, 'content': note.content} if note else None

    def add(self, title, content):
        from note.models import Note
        note = Note(title=title, content=content, storage_uuid=self.storage_uuid)
        note.fetch_search_fields()
        note.save()
        return {'title': note.title, 'content': note.content}

    def edit(self, title, new_title=None, new_content=None):
        note = self.queryset.get(title=title)
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

        return updated_fields

    def delete(self, title):
        note = self.queryset.get(title=title)
        note.delete()

    def get_list(self, page_number, count_on_page):
        from django.core.paginator import Paginator
        notes = self.queryset.order_by('title')
        paginator = Paginator(notes, count_on_page)
        page = paginator.page(page_number)
        return (
            [
                {'title': note.title, 'content': note.content, 'url': self.get_note_url(note.title)}
                for note in page.object_list
            ],
            {'num_pages': paginator.num_pages},
        )
