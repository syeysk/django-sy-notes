from urllib.parse import unquote

from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from note.load_from_github import prepare_to_search, get_uploader, get_root_url
from note.credentials import args_uploader
from note.serializers import NoteAddViewSerializer, NoteEditViewSerializer


source_parametr = OpenApiParameter(
    name='source',
    description='источник заметок',
    required=False,
    type=str,
    default=settings.DEFAULT_UPLOADER,
    location=OpenApiParameter.QUERY
)


class NoteView(APIView):
    """Класс методов для работы с заметками"""

    @extend_schema(
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя запрашиваемой заметки', location=OpenApiParameter.PATH),
        ],
    )
    def get(self, request, title):
        """Метод получения заметки"""
        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        note_data = uploader.get(title=unquote(title))
        if not note_data:
            return Response(status=status.HTTP_404_NOT_FOUND)

        note_data['source'] = uploader_name
        return Response(status=status.HTTP_200_OK, data=note_data)

    @extend_schema(
        request=NoteAddViewSerializer,
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя создаваемой заметки', location=OpenApiParameter.PATH),
        ],
    )
    def post(self, request, title):
        """Метод создания новой заметки"""
        serializer = NoteAddViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = unquote(title)

        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        note_data = uploader.get(title=title)
        if note_data:
            data = {'detail': 'Заметка с таким названием уже существует'}
            return Response(status=status.HTTP_200_OK, data=data)

        note_data = uploader.add(title, data['content'])
        note_data['source'] = uploader_name
        return Response(status=status.HTTP_200_OK, data=note_data)

    @extend_schema(
        request=NoteEditViewSerializer,
        parameters=[
            source_parametr,
            OpenApiParameter(name='title', description='имя редактируемой заметки', location=OpenApiParameter.PATH),
        ],
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

        uploader_name = request.GET.get('source', settings.DEFAULT_UPLOADER)
        uploader = get_uploader(uploader_name, args_uploader[uploader_name])
        if not uploader.get(title=title):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if new_title and new_title != title and uploader.get(title=new_title):
            response_data = {'detail': 'Заметка с таким названием уже существует'}
            return Response(status=status.HTTP_200_OK, data=response_data)

        note_data = uploader.edit(title, new_title, data.get('new_content'))
        note_data['source'] = uploader_name
        return Response(status=status.HTTP_200_OK, data=note_data)
