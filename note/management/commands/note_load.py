from django.core.management.base import BaseCommand

from note.load_from_github import run_initiator


class Command(BaseCommand):
    help = 'Load knowledge from GitHub repository into some database for fast searching'

    def add_arguments(self, parser):
        parser.add_argument('--source-from', type=str)
        parser.add_argument('--source-to', type=str, default=None)

    def handle(self, *args, **options):
        run_initiator(options['source-from'], options['source-to'])
