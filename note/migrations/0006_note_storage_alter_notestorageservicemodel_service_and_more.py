# Generated by Django 4.2.1 on 2023-09-20 17:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0005_remove_note_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='storage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='note.notestorageservicemodel'),
        ),
        migrations.AlterField(
            model_name='notestorageservicemodel',
            name='service',
            field=models.CharField(choices=[('DjangoServer', 'Микросервис заметок'), ('Firestore', 'Firestore'), ('Github', 'Github'), ('Typesense', 'Typesense')], max_length=30, verbose_name='Внешний сервис базы'),
        ),
        migrations.CreateModel(
            name='ImageNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='note-images')),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='note.note')),
            ],
        ),
    ]