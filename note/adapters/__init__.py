import os.path
from contextlib import contextmanager

import requests
from django.conf import settings

from note.adapters.base_adapter import BaseAdapter
from note.adapters.django_server_adapter import DjangoServerAdapter
from note.adapters.firestore_adapter import FirestoreAdapter
from note.adapters.github_adapter import GithubAdapter
from note.adapters.typesense_adapter import TypesenseAdapter


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
    for subclass in BaseAdapter.__subclasses__():
        service_names.append(
            (subclass.__name__[:-7], subclass if add_class else subclass.verbose_name),
        )

    return service_names


def service_name_to_class(service_name):
    return globals()['{}Adapter'.format(service_name)]


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
