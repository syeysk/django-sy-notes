from django.conf import settings
from django.core.management.base import BaseCommand
from django.shortcuts import resolve_url

from note.adapters import get_storage_service
from note.models import NoteStorageServiceModel


class Command(BaseCommand):
    help = 'Generate note, containing list of storages'

    def handle(self, *args, **options):
        storages = (
            NoteStorageServiceModel.objects
            .filter(service=settings.DEFAULT_SOURCE_SERVICE_NAME)
            .values_list('source', 'description')
        )
        md_lines = ['Список баз знаний:', '']
        for storage in storages:
            source, description = storage
            url = resolve_url('note_list_db', source)
            md_lines.append(f'- [{description}]({url})')

        with get_storage_service() as (adapter, _):
            title = '.Список баз знаний'
            content = '\n'.join(md_lines)
            if adapter.get(title):
                adapter.edit(title, new_content=content)
            else:
                adapter.add(title, content)

        print('generating is finished. {} storages were listed.'.format(len(md_lines) - 2))
