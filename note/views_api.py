from urllib.parse import unquote

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django_sy_framework.custom_auth.authentication import TokenAuthentication
from django_sy_framework.custom_auth.permissions import CheckIsUsernNotAnonymousUser
from note.adapters import get_storage_service
from note.serializers import ERROR_NAME_MESSAGE
from note.serializers_api import (
    NoteAddViewSerializer,
    NoteEditViewSerializer,
    ErroResponseSerializer,
    NoteResponseSerializer,
    NoteSearchViewSerializer,
    NoteSearchResponseSerializer,
)

source_parametr = OpenApiParameter(
    name='source',
    description='Название базы',
    required=False,
    type=str,
    default=settings.DEFAULT_SOURCE_CODE,
    location=OpenApiParameter.QUERY,
    examples=[
        OpenApiExample('База по-умолчанию', value='default'),
        OpenApiExample('База заметок проекта Платформы', value='.project2'),
        OpenApiExample('База сообщества TVP', value='tvp-github'),
    ]
)

query_parametr = OpenApiParameter(
    name='query',
    description='URL-кодированая (уникальная) строка',
    required=False,
    type=str,
    location=OpenApiParameter.PATH,
    examples=[
        OpenApiExample('пример', value='page name')
    ]
)


class Auth(OpenApiAuthenticationExtension):
    name = 'Token authentication'
    target_class = TokenAuthentication

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'name': 'AUTHORIZATION',
            'in': 'header',
            'scheme': 'Bearer',
        }


class NoteSearchView(APIView):
    """Класс метода поиска заметок"""

    @extend_schema(
        tags=['Заметки'],
        parameters=[
            source_parametr,
            NoteSearchViewSerializer,
            query_parametr,
        ],
        responses={200: NoteSearchResponseSerializer},
        summary='Найти заметку',
    )
    def get(self, request, query):
        """Метод для поиска заметок"""
        serializer = NoteSearchViewSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        count_on_page = data['count_on_page']
        page_number = data['page_number']
        query = unquote(query)
        search_by = data['search-by']
        fields = data['fields']
        file_name = query if search_by in ('title', 'all') else None
        file_content = query if search_by in ('content', 'all') else None
        fields = ('title', 'content') if fields == 'all' else (fields,)

        with get_storage_service(request.GET.get('source')) as (uploader, source):
            notes, meta = uploader.search(
                operator=data['operator'],
                count_on_page=count_on_page,
                page_number=page_number,
                fields=fields,
                file_name=file_name,
                file_content=file_content,
            )
            response_data = {
                'results': notes,
                'source': source,
                'count_on_page': count_on_page,
                'page_number': page_number,
                'pages': meta['num_pages'],
                'count': meta['count']
            }

        return Response(status=status.HTTP_200_OK, data=response_data)


class NoteView(APIView):
    """Класс методов для работы с заметками"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [CheckIsUsernNotAnonymousUser]

    @extend_schema(
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя запрашиваемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={200: NoteResponseSerializer, 404: ErroResponseSerializer},
        tags=['Заметки'],
        summary='Получить заметку',
    )
    def get(self, request, title):
        """Метод получения заметки"""
        with get_storage_service(request.GET.get('source')) as (uploader, source):
            note_data = uploader.get(title=unquote(title))

            if not note_data:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'detail': 'Заметка не найдена'})

            note_data['source'] = source

        return Response(status=status.HTTP_200_OK, data=note_data)

    @extend_schema(
        request=NoteAddViewSerializer,
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя создаваемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={204: None, 422: ErroResponseSerializer, 400: 'Ошибка в значениях полей'},
        tags=['Заметки'],
        summary='Создать заметку',
    )
    def post(self, request, title):
        """Метод создания новой заметки"""
        serializer = NoteAddViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(title)
        if title.startswith('.'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'title': [ERROR_NAME_MESSAGE]})

        with get_storage_service(request.GET.get('source')) as (uploader, source):
            if uploader.get(title=title):
                data = {'detail': 'Заметка с таким названием уже существует'}
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data=data)

            uploader.add(title, data['content'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=NoteEditViewSerializer,
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя редактируемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={204: None, 400: 'Ошибка полей', 404: ErroResponseSerializer, 422: ErroResponseSerializer},
        tags=['Заметки'],
        summary='Отредактировать заметку',
    )
    def put(self, request, title):
        """
        Метод редактирования существующей заметки.

        Обязателен как минимум один из параметров в теле: `new_content` или `new_title`.
        """
        serializer = NoteEditViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(title)
        new_title = data.get('new_title')
        if title.startswith('.'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'title': [ERROR_NAME_MESSAGE]})
        elif new_title and new_title.startswith('.'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'new_title': [ERROR_NAME_MESSAGE]})

        with get_storage_service(request.GET.get('source')) as (uploader, _):
            if not uploader.get(title=title):
                return Response(status=status.HTTP_404_NOT_FOUND, data={'detail': 'Заметка не найдена'})

            if new_title and new_title != title and uploader.get(title=new_title):
                response_data = {'detail': 'Заметка с таким названием уже существует'}
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY, data=response_data)

            uploader.edit(title, new_title, data.get('new_content'))

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя удаляемой заметки', location=OpenApiParameter.PATH),
        ],
        responses={204: None, 404: ErroResponseSerializer},
        tags=['Заметки'],
        summary='Удалить заметку',
    )
    def delete(self, request, title):
        """Метод удаления заметки"""
        title = unquote(title)
        if title.startswith('.'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'title': [ERROR_NAME_MESSAGE]})

        with get_storage_service(request.GET.get('source')) as (uploader, _):
            note_data = uploader.get(title=title)
            if not note_data:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'detail': 'Заметка не найдена'})

            uploader.delete(title)

        return Response(status=status.HTTP_204_NO_CONTENT)
