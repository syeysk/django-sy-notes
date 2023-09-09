import zipfile
from pathlib import Path
from urllib.parse import quote

from note.adapters.base_adapter import BaseAdapter
from note.serializers_uploader import UploaderGithubSerializer


class GithubAdapter(BaseAdapter):
    verbose_name = 'Github'
    serializer = UploaderGithubSerializer
    URL_ARCHIVE = 'https://github.com/{}/{}/archive/refs/heads/{}.zip'
    URL_NOTE = 'https://raw.githubusercontent.com/{}/{}/{}{}/{}.md'

    def __init__(self, _, owner, repo, branch, directory):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.directory = directory

    def get_note_url(self, title):
        return f'https://github.com/{self.owner}/{self.repo}/blob/main{self.directory}/{quote(title)}.md'

    def get(self, title):
        response = requests.get(self.URL_NOTE.format(self.owner, self.repo, self.branch, self.directory, quote(title)))
        return None if response.status_code == 404 else {'title': title, 'content': response.text}

    def get_list(self, page_number, count_on_page):
        archive_dir = Path(__file__).resolve().parent.parent / 'cache_archives'
        archive_path = archive_dir / '{}.zip'.format('__'.join((self.owner, self.repo, self.branch)))
        if not os.path.exists(archive_dir):
            os.mkdir(archive_dir)

        if not os.path.exists(archive_path):
            response = requests.get(self.URL_ARCHIVE.format(self.owner, self.repo, self.branch))
            with open(archive_path, 'wb') as archive_file:
                archive_file.write(response.content)

        notes = []
        path_to_notes = '{}-{}{}'.format(self.repo, self.branch, self.directory)
        total_count = 0
        with zipfile.ZipFile(archive_path) as archive_object:
            for member_info in archive_object.infolist():
                filename = member_info.filename
                if not filename.startswith(path_to_notes) or not filename.endswith('.md') or member_info.is_dir():
                    continue

                total_count += 1
                if len(notes) >= count_on_page:
                    continue

                current_page = (total_count // count_on_page) + 1 if total_count % count_on_page > 0 else 0
                if current_page != page_number:
                    continue

                with archive_object.open(member_info) as member_file:
                    file_name, _ = os.path.splitext(os.path.basename(filename))
                    file_content = str(member_file.read(), 'utf-8')
                    notes.append({'title': file_name, 'content': file_content})

        return notes, {'num_pages': self.total_count_objects_to_count_pages(total_count, count_on_page)}
