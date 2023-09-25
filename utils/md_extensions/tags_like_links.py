from urllib.parse import quote
import re

from django.shortcuts import resolve_url
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension

TAG_PATTERN = rf'(?:^|[^\\])(#[a-zA-Zа-яА-ЯёЁ][a-zA-Z0-9а-яА-ЯёЁ_-]*)'


class TagsLikeLinksInlineProcessor(Preprocessor):
    def build_link(self, match):
        tag = match.group(1)
        quoted_tag = quote(tag)
        return f'[{tag}]({self.url}?s={quoted_tag}) '

    def run(self, lines):
        self.url = resolve_url('note_list')
        new_lines = []
        for line in lines:
            line = re.sub(TAG_PATTERN, self.build_link, line)
            new_lines.append(line)

        return new_lines


class TagsLikeLinksExtension(Extension):
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
        md.preprocessors.register(TagsLikeLinksInlineProcessor(), 'tags_like_links', 1)
