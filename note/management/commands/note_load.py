from django.core.management.base import BaseCommand

from note.adapters import run_initiator


class Command(BaseCommand):
    help = 'Load knowledge from GitHub repository into some database for fast searching'

    def add_arguments(self, parser):
        parser.add_argument('--source-from', type=str)
        parser.add_argument('--source-to', type=str, default=None)

    def handle(self, *args, **options):
        for total_count in run_initiator(options['source-from'], options['source-to']):
            print('uploaded files into database:', total_count)

        print('uploading is finished.')
