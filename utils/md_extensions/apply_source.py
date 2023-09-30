from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from django_sy_framework.utils.logger import logger


def collect_link_elements(root):
    links = []
    sources = set()
    for child in root.iter('a'):
        url = child.get('href')
        if url:
            try:
                url = urlparse(url)
            except Exception as error:
                logger.warn(f'ObsidianLinksTreeprocessor: {str(error)}: {url}')
                continue

            if url.scheme == 'obsidian' and url.hostname == 'open':
                query = parse_qs(url.query)
                vault = query.get('vault')
                file = query.get('file')
                if vault and file:
                    links.append((child, file[0], vault[0]))
                    sources.add(vault[0])

    return links, sources


class ApplySourceTreeprocessor(Treeprocessor):
    def __init__(self, md, source):
        super().__init__(md)
        self.source = source

    def run(self, root):
        if not self.source:
            return

        for link in root.iter('a'):
            url = link.get('href')
            try:
                url = urlparse(url)
            except Exception as error:
                logger.warn(f'ApplySourceTreeprocessor: {str(error)}: {url}')
                continue

            is_note = url.path.startswith('/note/') and url.path.endswith('.md')
            if not url.scheme and not url.hostname and (is_note or url.path == '/note/'):
                query = parse_qs(url.query)
                if not query.get('source'):
                    query['source'] = [self.source]
                    query = urlencode(query, doseq=True)
                    link.set('href', urlunparse((url.scheme, url.netloc, url.path, url.params, query, url.fragment)))


class ApplySourceExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {'source': ['', 'knowledge database']}
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        source = self.getConfig('source')
        preprocessor = ApplySourceTreeprocessor(md, source)
        md.treeprocessors.register(preprocessor, 'obsidian_link', 11)

    def reset(self):
        pass
