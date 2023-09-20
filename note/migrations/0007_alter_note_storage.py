# Generated by Django 4.2.1 on 2023-09-20 18:04

from django.db import migrations, models
import django.db.models.deletion


def populate_storage_field(apps, schema_editor):
    NoteStorageServiceModel = apps.get_model("note", "NoteStorageServiceModel")
    Note = apps.get_model("note", "Note")
    for note in Note.objects.all():
        note.storage = NoteStorageServiceModel.objects.get(uuid=note.storage_uuid)
        note.save()


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0006_note_storage_alter_notestorageservicemodel_service_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_storage_field, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='note',
            name='storage',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='note.notestorageservicemodel'),
        ),
    ]
