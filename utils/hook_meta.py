from dataclasses import dataclass, field

from django.contrib.auth import get_user_model


@dataclass
class CreatedNote:
    source: str
    title: str
    content: str
    request: 'django.http.HttpRequest' = None
    adapter: 'note.adapters.base_adapter.BaseAdapter' = None
    errors: dict = field(default_factory=dict)


@dataclass
class UpdatedNote:
    source: str
    title: str
    new_title: str
    new_content: str
    request: 'django.http.HttpRequest' = None
    adapter: 'note.adapters.base_adapter.BaseAdapter' = None
    user: get_user_model() = None
    errors: dict = field(default_factory=dict)


@dataclass
class DeletedNote:
    source: str
    title: str
    request: 'django.http.HttpRequest' = None
    adapter: 'note.adapters.base_adapter.BaseAdapter' = None
    user: get_user_model() = None


@dataclass
class CreatePageNote:
    source: str
    request: 'django.http.HttpRequest' = None


@dataclass
class ViewPageNote:
    source: str
    title: str
    content: str
    request: 'django.http.HttpRequest' = None
    has_access_to_edit: bool = True
    user: get_user_model() = None
