import json
import io
import os.path
import zipfile

import firebase_admin
import requests
from django.conf import settings
from django.db.models import Q
from firebase_admin import credentials, firestore
from typesense import Client

from note.serializers_uploader import UploaderFirestoreSerializer, UploaderTypesenseSerializer


def get_root_url(
    directory: str = '',
    owner: str = settings.GITHUB_OWNER,
    repo: str = settings.GITHUB_REPO,
    raw: bool = False,
):
    url_raw = f'https://raw.githubusercontent.com/{owner}/{repo}/main{directory}'
    url_page = f'https://github.com/{owner}/{repo}/blob/main{directory}'
    return url_raw if raw else url_page


def download_from_github_archive(owner, repo, directory):
    print('start downloading the archive')
    response = requests.get('https://github.com/{}/{}/archive/refs/heads/main.zip'.format(owner, repo))
    archive = io.BytesIO(response.content)
    print('the archive is downloaded')
    with zipfile.ZipFile(archive) as archive_object:
        for member_name in archive_object.namelist():
            if not member_name.startswith('{}-main{}'.format(repo, directory)):
                continue

            member_info = archive_object.getinfo(member_name)
            if not member_info.is_dir():
                with archive_object.open(member_info) as member_file:
                    file_name, _ = os.path.splitext(os.path.basename(member_name))
                    file_content = str(member_file.read(), 'utf-8')
                    yield file_name, file_content


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
    pass


class UploaderFirestore(BaseUploader):
    verbose_name = 'Firestore'
    serializer = UploaderFirestoreSerializer
    MAX_PORTION_SIZE = 500

    def __init__(self, certificate):
        cred = credentials.Certificate(certificate)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.batch = self.db.batch()

    def clear(self):
        ...

    def add_to_portion(self, file_name, file_content):
        ref = self.db.collection('knowledge').document(file_name)
        self.batch.set(ref, {'text': file_content})

    def commit(self):
        self.batch.commit()


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

    def __init__(self, server, port, protocol, api_key):
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

    def __init__(self):
        pass

    def clear(self):
        from note.models import Note
        Note.objects.all().delete()

    def add_to_portion(self, file_name, file_content):
        from note.models import Note
        fields = Note(
            title=file_name,
            content=file_content,
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
        limit,
        offset,
        fields,
        file_name=None,
        file_content=None,
    ):
        from note.models import Note, prepare_to_search
        filter = {}
        if file_name:
            file_name = prepare_to_search(file_name)
            filter['search_title__contains'] = file_name

        if file_content:
            file_content = prepare_to_search(file_content)
            filter['search_content__contains'] = file_content

        notes = Note.objects
        if len(filter) == 2 and operator == 'or':
            notes = notes.filter(Q(search_title__contains=file_name) | Q(search_content__contains=file_content))
        else:
            notes = notes.filter(**filter)

        count = notes.count()

        results = list(notes[offset:limit+offset].values(*fields))
        return dict(results=results, count=count)

    def get(self, title):
        from note.models import Note
        notes = Note.objects.filter(title=title)
        if notes.exists():
            note = notes[0]
            return {'title': note.title, 'content': note.content}

        return None

    def add(self, title, content):
        from note.models import Note
        note = Note(title=title, content=content)
        note.fetch_search_fields()
        note.save()
        return {'title': note.title, 'content': note.content}

    def edit(self, title, new_title=None, new_content=None):
        from note.models import Note
        note = Note.objects.get(title=title)
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
        from note.models import Note
        note = Note.objects.get(title=title)
        note.delete()


def run_initiator(downloader, args_downloader, uploader, args_uploader):
    downloader = globals()['download_from_{}'.format(downloader)]
    uploader = get_uploader(uploader, args_uploader)
    uploader.clear()
    portion_size = 0
    total_size = 0
    for file_name, file_content in downloader(*args_downloader):
        uploader.add_to_portion(file_name, file_content)
        portion_size += 1
        if portion_size == uploader.MAX_PORTION_SIZE:
            uploader.commit()
            total_size += portion_size
            portion_size = 0
            print('uploaded files into database:', total_size)

    if portion_size:
        uploader.commit()

    print('uploading is finished. Totally uploaded:', total_size + portion_size)


def get_uploader(uploader_name, args_uploader):
    class_uploader = 'Uploader{}'.format(uploader_name.title().replace('_', ''))
    return globals()[class_uploader](*args_uploader)


def get_service_names():
    service_names = []
    for subclass in BaseUploader.__subclasses__():
        service_names.append(
            (subclass.__name__[8:], subclass.verbose_name),
        )

    return service_names


def get_storage_service(source=None, user=None):
    """Функция получения объекта хранилища заметок"""
    from note.models import NoteStorageServiceModel

    storage = None
    if user and user.is_authenticated and source:
        storage = NoteStorageServiceModel.objects.filter(user=user, source=source)
    elif user and user.is_authenticated:
        storage = NoteStorageServiceModel.objects.filter(user=user, is_default=True)
    elif source:
        storage = NoteStorageServiceModel.objects.filter(source=source)

    if storage:
        service_name = storage.service
        service_credentials = json.loads(storage.credentials)
        source = storage.source
    else:
        service_name = settings.DEFAULT_UPLOADER
        service_credentials = {}
        source = 'django_server'

    return get_uploader(service_name, service_credentials), source
