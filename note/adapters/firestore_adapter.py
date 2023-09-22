from firebase_admin import credentials, delete_app, firestore, initialize_app

from note.adapters.base_adapter import BaseAdapter
from note.serializers_uploader import UploaderFirestoreSerializer


class FirestoreAdapter(BaseAdapter):
    verbose_name = 'Firestore'
    serializer = UploaderFirestoreSerializer
    MAX_PORTION_SIZE = 500

    def __init__(self, storage, certificate):
        self.storage = storage
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
