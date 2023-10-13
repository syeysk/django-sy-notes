from django.shortcuts import resolve_url
from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension
import xml.etree.ElementTree as etree


class WikiLinksInlineProcessor(InlineProcessor):
    def __init__(self, pattern, md, source):
        super().__init__(pattern, md)
        self.source = source

    def handleMatch(self, m, data):
        title = (m.group(1) or '').strip().replace('\|', '|')
        link_title = (m.group(2) or '').strip().replace('\|', '|')

        el = etree.Element('a')
        el.text = link_title[1:] or title
        el.set('href', resolve_url('note_editor2', source=self.source, quoted_title=title))
        return el, m.start(0), m.end(0)


class WikiLinksExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {'source': ['', 'knowledge database']}
        super().__init__(**kwargs)

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
        source = self.getConfig('source')
        md.inlinePatterns.register(WikiLinksInlineProcessor(LINK_PATTERN, md, source), 'wiki_links', 10)
