from urllib.parse import urlparse

from django.conf import settings
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


def collect_imaages(root, images=None):
    if images is None:
        images = []

    for child in root:
        if child.tag == 'img':
            url = child.get('src')
            if url:
                url = urlparse(url)
                if not (url.scheme or url.hostname) and url.path:
                    images.append(child)
        else:
            collect_imaages(child, images)

    return images


class InternalImagesTreeprocessor(Treeprocessor):
    def run(self, root):
        for image in collect_imaages(root):
            src = image.get('src')
            image.set('src', f'{settings.MEDIA_URL}note/{src}')


class InternalImagesExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        self.reset()
        preprocessor = InternalImagesTreeprocessor(md)
        md.treeprocessors.register(preprocessor, 'internal_images', 10)

    def reset(self):
        pass
