from django.shortcuts import resolve_url
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree


class WikiLinksInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        title = (m.group(1) or '').strip().replace('\|', '|')
        link_title = (m.group(2) or '').strip().replace('\|', '|')

        el = etree.Element('a')
        el.text = link_title[1:] or title
        el.set('href', resolve_url('note_editor', quoted_title=title))
        return el, m.start(0), m.end(0)


class WikiLinksExtension(Extension):
    def extendMarkdown(self, md):
        """
        Text
        ```
        - [[note link]]
        - [[note link|тест]]
        - [[note link|тест\|ик]]
        - [[note link \|here|тест]]
        - [[note link \|here|тест\|ик]]
        ```
        will convert
        ```
        <ul>
            <li><a href="/note/note%20link.md">note link</a></li>
            <li><a href="/note/note%20link.md">тест</a></li>
            <li><a href="/note/note%20link.md">тест|ик</a></li>
            <li><a href="/note/note%20link%20%7Chere.md">тест</a></li>
            <li><a href="/note/note%20link%20%7Chere.md">тест|ик</a></li>
        </ul>
        ```
        """
        NOT_VERT_PATTERN = r'(?:[^|]|\\\|)'
        LINK_PATTERN = rf'\[\[({NOT_VERT_PATTERN}*?)(\|{NOT_VERT_PATTERN}*?)?\]\]'  # like [[note title]] or [[note title|view title]]
        md.inlinePatterns.register(WikiLinksInlineProcessor(LINK_PATTERN, md), 'wiki_links', 10)
