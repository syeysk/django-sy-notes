from django.conf import settings
from django.shortcuts import resolve_url


class BaseAdapter:

    def close(self):
        pass

    @staticmethod
    def total_count_objects_to_count_pages(count_objects, count_on_page):
        return (count_objects // count_on_page) + 1 if count_objects % count_on_page > 0 else 0

    def get_note_url(self, title):
        """Return a note URL by `title`"""
        return '{}{}'.format(settings.SITE_URL, resolve_url('note_editor', quoted_title=title))

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
