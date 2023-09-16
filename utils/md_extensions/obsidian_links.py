from urllib.parse import urlparse, parse_qs, quote

from django.shortcuts import resolve_url
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from note.models import NoteStorageServiceModel


def collect_link_elements(root, links=None, sources=None):
    if links is None:
        links = []

    if sources is None:
        sources = set()

    for child in root:
        if child.tag == 'a':
            url = child.get('href')
            if url:
                url = urlparse(url)
                if url.scheme == 'obsidian' and url.hostname == 'open':
                    query = parse_qs(url.query)
                    vault = query.get('vault')
                    file = query.get('file')
                    if vault and file:
                        links.append((child, file[0], vault[0]))
                        sources.add(vault[0])
        else:
            collect_link_elements(child, links, sources)

    return links, sources


class ObsidianLinksTreeprocessor(Treeprocessor):
    def run(self, root):
        links, sources = collect_link_elements(root)
        existed_sources = set(
            NoteStorageServiceModel.objects.filter(source__in=sources).values_list('source', flat=True),
        )
        for link, title, source in links:
            if source in existed_sources:
                new_url = '{}?source={}'.format(
                    resolve_url('note_editor', quoted_title=title[:-3]),
                    quote(source),
                )
                link.set('href', new_url)


class ObsidianLinksExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        preprocessor = ObsidianLinksTreeprocessor(md)
        md.treeprocessors.register(preprocessor, 'obsidian_link', 10)

    def reset(self):
        pass
