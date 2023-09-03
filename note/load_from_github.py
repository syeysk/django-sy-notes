import os.path
import zipfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote

import requests
from django.conf import settings
from django.db.models import Q
from django.shortcuts import resolve_url
from firebase_admin import credentials, delete_app, firestore, initialize_app
from typesense import Client

from note.serializers_uploader import (
    UploaderFirestoreSerializer,
    UploaderGithubSerializer,
    UploaderTypesenseSerializer,
)


def download_from_github_directory(owner, repo, directory, token):
    graphql = """query getStartAndEndPoints {{
  repository(owner: "{}", name: "{}") {{
    object(expression: "HEAD:{}") {{
      ... on Tree {{
        entries {{
          name
          object {{
            ... on Blob {{
              text
            }}
          }}
        }}
      }}
    }}
  }}
}}""".format(owner, repo, directory)
    response = requests.post('https://api.github.com/graphql', json={'query': graphql}, headers={
        'Content-Type': 'application/json',
        'Authorization': 'bearer {}'.format(token),
        'User-Agent': 'test',
    })
    content = response.json()
    if 'message' in content:
        print(content['message'])

    errors = content.get('errors')
    if errors:
        for error in errors:
            print(error['message'])

    data = content.get('data')
    if data:
        files = data['repository']['object']['entries']
        for file in files:
            file_name = file['name']
            file_name, _ = os.path.splitext(file_name)
            file_content = file['object']['text']
            yield file_name, file_content


class BaseUploader:

    def close(self):
        pass

    @staticmethod
    def total_count_objects_to_count_pages(count_objects, count_on_page):
        return (count_objects // count_on_page) + 1 if count_objects % count_on_page > 0 else 0

    def get(self, title: str) -> dict | None:
        """Return a note from a storage by `title`.

        :param title: title of a note
        :return: `dict` like `{'title': '', 'content': ''}` if a note exists, else - `None`
        """
        raise NotImplementedError()

    def add(self, title: str, content: str) -> dict:
        """Create a note into a storage.

        :param title: title of a note. Must be unique value
        :param content: content of a note
        :return: `dict` like `{'title': '', 'content': ''}`
        """
        raise NotImplementedError()

    def edit(self, title: str, new_title: str = None, new_content: str = None):
        """Change an existing note. Minimum one of `new_title`, `new_content` must be not None"""
        raise NotImplementedError()

    def delete(self, title: str):
        """Delete a note from a storage by `title`"""
        raise NotImplementedError()

    def get_list(self, page_number: int, count_on_page: int) -> tuple[dict, dict]:
        """Return a list of notes from a storage by """
        raise NotImplementedError()

    def get_note_url(self, title: str):
        """Return a note URL by `title`"""
        raise NotImplementedError()


class UploaderFirestore(BaseUploader):
    verbose_name = 'Firestore'
    serializer = UploaderFirestoreSerializer
    MAX_PORTION_SIZE = 500

    def __init__(self, _, certificate):
        cred = credentials.Certificate(certificate)
        self.app = initialize_app(cred)
        self.db = firestore.client()
        self.batch = None
        self.collection = self.db.collection('knowledge')
        self.field = 'text'

    def close(self):
        delete_app(self.app)

    def clear(self):
        ...

    def add_to_portion(self, file_name, file_content):
        ref = self.collection.document(file_name)
        if self.batch is None:
            self.batch = self.db.batch()

        self.batch.set(ref, {self.field: file_content})

    def commit(self):
        if self.batch is not None:
            self.batch.commit()

    def get(self, title):
        ref_document = self.collection.document(title)
        document = ref_document.get()
        return {'title': ref_document.id, 'content': document.get(self.field)} if document.exists else None

    def add(self, title, content):
        self.collection.document(title).set({self.field: content})
        return {'title': title, 'content': content}

    def edit(self, title, new_title=None, new_content=None):
        ref_document = self.collection.document(title)
        document = ref_document.get()
        updated_fields = []
        if new_title and title != new_title:
            ref_document = self.collection.document(new_title)
            ref_document.set({self.field: new_content})
            updated_fields.append('title')
            # TODO: удалить старый документ либо изменить id у существующего

        if new_content and document.get(self.field) != new_content:
            if new_title and title != new_title:
                ref_document.set({self.field: new_content})

            updated_fields.append('content')

        return updated_fields

    def get_list(self, page_number, count_on_page):
        notes = []
        offset = (page_number - 1) * count_on_page
        for ref_document in self.collection.limit(count_on_page).offset(offset).get():
            notes.append({'title': ref_document.id, 'content': ref_document.get(self.field)})

        num_pages = self.total_count_objects_to_count_pages(self.collection.count().get()[0][0].value, count_on_page)
        return (
            notes,
            {'num_pages': num_pages},
        )


class UploaderTypesense(BaseUploader):
    verbose_name = 'Typesense'
    serializer = UploaderTypesenseSerializer
    MAX_PORTION_SIZE = 500
    portion = []
    knowledge_schema = {
        'name': 'knowledge',
        'fields': [
            {'name': 'filename', 'type': 'string'},
            {'name': 'text', 'type': 'string', 'facet': True},
            {'name': 'index', 'type': 'float'}
        ],
        'default_sorting_field': 'index'
    }
    index = 0

    def __init__(self, _, server, port, protocol, api_key):
        self.client = Client({
            'nodes': [{
                'host': server,
                'port': port,
                'protocol': protocol,
            }],
            'api_key': api_key,
            'connection_timeout_seconds': 2
        })

    def clear(self):
        try:
            name = self.knowledge_schema['name']
            self.client.collections[name].delete()
        except Exception as e:
            pass

        self.client.collections.create(self.knowledge_schema)

    def add_to_portion(self, file_name, file_content):
        fields = {'filename': file_name, 'text': file_content, 'index': self.index}
        self.portion.append(fields)
        self.index += 1

    def commit(self):
        name = self.knowledge_schema['name']
        self.client.collections[name].documents.import_(self.portion)
        self.portion.clear()

    def search(self, file_name=None, file_content=None, page_number=1):
        name = self.knowledge_schema['name']
        res = self.client.collections[name].documents.search({
            'q': file_name,
            'query_by': 'filename',
            'sort_by': 'index:desc'
        })
        results = []
        for hit in res['hits']:
            document = hit['document']
            results.append(dict(title=document['filename'], content=document['text']))

        return dict(results=results, count=res['found'])


class UploaderDjangoServer(BaseUploader):
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

        return notes, {'num_pages': paginator.num_pages}

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


class UploaderGithub(BaseUploader):
    verbose_name = 'Github'
    serializer = UploaderGithubSerializer
    URL_ARCHIVE = 'https://github.com/{}/{}/archive/refs/heads/{}.zip'
    URL_NOTE = 'https://raw.githubusercontent.com/{}/{}/{}{}/{}.md'

    def __init__(self, _, owner, repo, branch, directory):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.directory = directory

    def get_note_url(self, title):
        return f'https://github.com/{self.owner}/{self.repo}/blob/main{self.directory}/{quote(title)}.md'

    def get(self, title):
        response = requests.get(self.URL_NOTE.format(self.owner, self.repo, self.branch, self.directory, quote(title)))
        return None if response.status_code == 404 else {'title': title, 'content': response.text}

    def get_list(self, page_number, count_on_page):
        archive_dir = Path(__file__).resolve().parent.parent / 'cache_archives'
        archive_path = archive_dir / '{}.zip'.format('__'.join((self.owner, self.repo, self.branch)))
        if not os.path.exists(archive_dir):
            os.mkdir(archive_dir)

        if not os.path.exists(archive_path):
            response = requests.get(self.URL_ARCHIVE.format(self.owner, self.repo, self.branch))
            with open(archive_path, 'wb') as archive_file:
                archive_file.write(response.content)

        notes = []
        path_to_notes = '{}-{}{}'.format(self.repo, self.branch, self.directory)
        total_count = 0
        with zipfile.ZipFile(archive_path) as archive_object:
            for member_info in archive_object.infolist():
                filename = member_info.filename
                if not filename.startswith(path_to_notes) or not filename.endswith('.md') or member_info.is_dir():
                    continue

                total_count += 1
                if len(notes) >= count_on_page:
                    continue

                current_page = (total_count // count_on_page) + 1 if total_count % count_on_page > 0 else 0
                if current_page != page_number:
                    continue

                with archive_object.open(member_info) as member_file:
                    file_name, _ = os.path.splitext(os.path.basename(filename))
                    file_content = str(member_file.read(), 'utf-8')
                    notes.append({'title': file_name, 'content': file_content})

        return notes, {'num_pages': self.total_count_objects_to_count_pages(total_count, count_on_page)}


def run_initiator(source_from, source_to):
    portion_size = 0
    total_size = 0
    count_on_page = 100
    with get_storage_service(source_from) as (downloader, _), get_storage_service(source_to) as (uploader, _):
        uploader.clear()

        notes, meta = downloader.get_list(1, count_on_page)
        for num_page in range(1, meta['num_pages'] + 1):
            for note in downloader.get_list(num_page, count_on_page)[0] if num_page > 1 else notes:
                file_name, file_content = note['title'], note['content']
                uploader.add_to_portion(file_name, file_content)
                portion_size += 1
                if portion_size == uploader.MAX_PORTION_SIZE:
                    uploader.commit()
                    total_size += portion_size
                    portion_size = 0
                    yield total_size

        if portion_size:
            uploader.commit()

    yield total_size + portion_size


def get_service_names(add_class=False):
    service_names = []
    for subclass in BaseUploader.__subclasses__():
        service_names.append(
            (subclass.__name__[8:], subclass if add_class else subclass.verbose_name),
        )

    return service_names


def service_name_to_class(service_name):
    return globals()['Uploader{}'.format(service_name)]


@contextmanager
def get_storage_service(source=None, user=None):
    """Функция получения объекта базы заметок"""
    from note.models import NoteStorageServiceModel

    storage = None
    if user and user.is_authenticated and source:
        storage = NoteStorageServiceModel.objects.filter(user=user, source=source).first()
    elif user and user.is_authenticated:
        storage = NoteStorageServiceModel.objects.filter(user=user, is_default=True).first()
    elif source:
        storage = NoteStorageServiceModel.objects.filter(source=source).first()

    if not storage:
        storage = NoteStorageServiceModel.objects.filter(source=settings.DEFAULT_SOURCE_CODE).first()
        if not storage:
            raise Exception(f'not found default knowledge base "{settings.DEFAULT_SOURCE_CODE}"')

    service_name = storage.service
    service_credentials = storage.credentials
    source = storage.source
    storage_uuid = storage.uuid

    uploader_class = service_name_to_class(service_name)
    uploader = uploader_class(storage_uuid, **service_credentials)
    try:
        yield uploader, source
    finally:
        uploader.close()
