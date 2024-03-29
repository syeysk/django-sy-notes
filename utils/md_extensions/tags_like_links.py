from urllib.parse import quote
import re

from django.shortcuts import resolve_url
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension

TAG_PATTERN = rf'(?:^|[\s])(#[a-zA-Zа-яА-ЯёЁ][a-zA-Z0-9а-яА-ЯёЁ_-]*)'


class TagsLikeLinksInlineProcessor(Preprocessor):
    def __init__(self, source):
        super().__init__(md=None)
        self.source = source

    def build_link(self, match):
        tag = match.group(1)
        quoted_tag = quote(tag)
        return f'[{tag}]({self.url}?s={quoted_tag}) '

    def run(self, lines):
        self.url = resolve_url('note_list_db', self.source)
        new_lines = []
        for line in lines:
            line = re.sub(TAG_PATTERN, self.build_link, line)
            new_lines.append(line)

        return new_lines


class TagsLikeLinksExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {'source': ['', 'knowledge database']}
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """
        Text
        ```
        #test
        ```
        will convert
        ```
        <a href="/note/?s=test">#test</a>
        ```
        """
        source = self.getConfig('source')
        md.preprocessors.register(TagsLikeLinksInlineProcessor(source), 'tags_like_links', 1)
