from rest_framework import serializers


class NoteEditViewSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, help_text='Текущее имя заметки')
    new_title = serializers.CharField(max_length=255, required=False, help_text='Новое имя заметки')
    new_content = serializers.CharField(max_length=20000, required=False, help_text='Новое содержимое заметки')

    def validate(self, data):
        if not data.get('new_title') and not data.get('new_content'):
            raise serializers.ValidationError("required new_title or new_content, or both")

        return data
