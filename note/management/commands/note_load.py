from django.conf import settings
from django.core.management.base import BaseCommand

from note.load_from_github import run_initiator
from note.credentials import args_downloader


class Command(BaseCommand):
    help = 'Load knowledge from GitHub repository into some database for fast searching'

    def add_arguments(self, parser):
        parser.add_argument('--downloader', type=str, default=settings.DEFAULT_DOWNLOADER)
        parser.add_argument('--source-to', type=str, default=None)

    def handle(self, *args, **options):
        downloader = options['downloader']
        source_to = options['source-to']
        run_initiator(downloader, args_downloader[downloader], source_to)
