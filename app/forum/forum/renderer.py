from django.utils.six.moves.html_parser import HTMLParser
from django.template.defaultfilters import urlize as django_urlize
from django.conf import settings

from urllib.parse import quote

import re
import os
import postmarkup
import markdown


# Process search queries
# Urlize + BBCode filters
# Forked from https://github.com/slav0nic/DjangoBB/
class HTMLFilter(HTMLParser):

    """
    Base class for html parsers that produce filtered output.
    """

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=False)
        self.html = str()

    def handle_starttag(self, tag, attrs):
        self.html += '<{:s}{:s}>'.format(tag, self.__html_attrs(attrs))

    def handle_data(self, data):
        self.html += data

    def handle_startendtag(self, tag, attrs):
        self.html += '<{:s}{:s}/>'.format(tag, self.__html_attrs(attrs))

    def handle_endtag(self, tag):
        self.html += '</{:s}>'.format(tag)

    def handle_entityref(self, name):
        self.html += '&{:s};'.format(name)

    def handle_charref(self, name):
        self.html += '&#{:s};'.format(name)

    def unescape(self, s):
        # we don't need unescape data (without this possible XSS-attack)
        return s

    def __html_attrs(self, attrs):
        "Handle tag attributes"
        _attrs = ''
        if attrs:
            _attrs = ' %s' % (
                ' '.join(['{:s}="{:s}"'.format(k, v) for k, v in attrs]))
        return _attrs


class ExcludeTagsHTMLFilter(HTMLFilter):

    """
    Class for html parsing with excluding specified tags.
    """

    def __init__(self, func, tags=('a', 'pre', 'strike')):
        HTMLFilter.__init__(self)
        self.func = func
        self.is_ignored = False
        self.tags = tags

    def handle_starttag(self, tag, attrs):
        if tag in self.tags:
            self.is_ignored = True
        super(ExcludeTagsHTMLFilter, self).handle_starttag(tag, attrs)

    def handle_data(self, data):
        if not self.is_ignored:
            data = self.func(data)
        super(ExcludeTagsHTMLFilter, self).handle_data(data)

    def handle_endtag(self, tag):
        self.is_ignored = False
        super(ExcludeTagsHTMLFilter, self).handle_endtag(tag)


def urlize(html):
    """
    Urlize plain text links in the HTML contents.
    Do not urlize content of A and CODE tags.
    """
    try:
        parser = ExcludeTagsHTMLFilter(django_urlize)
        parser.feed(html)
        urlized_html = parser.html
        parser.close()
    except:
        if settings.DEBUG:
            raise
        return html
    return urlized_html


def rm_legacy_tags(text):
    "Replace legacy tags by bbcode"
    base_tags = [(r'ita', 'i'),
                 (r'bold', 'b'),
                 (r'under', 'u')]
    allTags = ([(re.escape('[' + old + ']'), '[' + new + ']')
                for old, new in base_tags] +
               [(re.escape('[/' + old + ']'), '[/' + new + ']')
                for old, new in base_tags])
    query = [(re.compile(old), new) for old, new in allTags]
    for old_match, new in query:
        text = old_match.sub(new, text)
    return text


class SpoilerTag(postmarkup.TagBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

    def render_open(self, parser, node_index):
        return (
            "<div class=\"panel panel-default spoiler-container\">"
            "<div class=\"panel-heading\" role=\"tab\" id=\"heading\">"
            "<h5 class=\"panel-title\">"
            "<a data-toggle=\"collapse\" href=\"#spoiler-panel\" "
            "aria-expanded=\"false\" aria-controls=\"spoiler-panel\" "
            "style=\"display:block\">Spoiler</a></h5></div>"
            "<div id=\"spoiler-panel\" class=\"panel-collapse collapse\" "
            "role=\"tabpanel\" aria-labelledby=\"heading\">"
            "<div class=\"panel-body\">"
        )

    def render_close(self, parser, node_index):
        return '</div></div></div>'


class VideoTag(postmarkup.TagBase):
    """Render videos.

    Forked from postmarkup.LinkTag.
    """

    _safe_chars = frozenset(
        u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg'
        u'hijklmnopqrstuvwxyz0123456789_.-=/&?:%&#'
    )

    _re_domain = re.compile(r"//([a-z0-9-\.]*)", re.UNICODE)

    iframe_domains = ['youtube.com', 'player.vimeo.com', 'dailymotion.com']

    def __init__(self, name, annotate_links=False, **kwargs):
        super().__init__(name, inline=True)
        self.annotate_links = annotate_links

    def render_open(self, parser, node_index):

        self.domain = u''
        tag_data = parser.tag_data
        name = u'link_nest_level'
        nest_level = tag_data[name] = tag_data.setdefault(name, 0) + 1

        if nest_level > 1:
            return u""

        if self.params:
            url = self.params.strip()
        else:
            url = self.get_contents_text(parser).strip()
            url = postmarkup.PostMarkup.standard_unreplace(url)

        self.domain = u""

        if u':' not in url:
            url = u'http://' + url

        scheme, uri = url.split(u':', 1)

        if scheme not in [u'http', u'https']:
            return u''

        try:
            domain_match = self._re_domain.search(uri.lower())
            if domain_match is None:
                return u''
            domain = domain_match.group(1)
        except IndexError:
            return u''

        domain = domain.lower()
        if domain.startswith(u'www.'):
            domain = domain[4:]

        def percent_encode(s):
            safe_chars = self._safe_chars

            def replace(c):
                if c not in safe_chars:
                    return u"%%%02X" % ord(c)
                else:
                    return c
            return u"".join([replace(c) for c in s])

        self.url = percent_encode(url)
        self.domain = domain

        if not self.url:
            return ""

        if self.domain in self.iframe_domains:
            return (
                '<div class="embed-responsive embed-responsive-16by9">'
                '<iframe class="embed-responsive-item" src="{}" '
                'frameborder="0" allowfullscreen="true"></iframe></div>'
            ).format(postmarkup.PostMarkup.standard_replace_no_break(self.url))
        elif self.domain:
            return (
                '<video loop="true" controls="true" src="{}"></video>'
            ).format(postmarkup.PostMarkup.standard_replace_no_break(self.url))
        else:
            return ""


render_bbcode = postmarkup.create(use_pygments=False, annotate_links=False)
render_bbcode.add_tag(SpoilerTag, 'spoiler')
render_bbcode.add_tag(VideoTag, 'video')


def convert_text_to_html(text, markup='bbcode'):
    if markup == 'bbcode':
        text = rm_legacy_tags(text)
        text = render_bbcode(text, cosmetic_replace=False)
    elif markup == 'markdown':
        text = markdown.markdown(text, safe_mode='escape')
    text = urlize(text)
    return text


# Smiley stuff
def compileSmileys():

    specialSmileys = [
        (r":-?\/", "bof"),
        (r":-?\)", "special-smile"),
        (r";-?\)", "special-wink"),
        (r":-?\(", "special-sad"),
        (r":o", "-o"),
        (r":-?D", "green"),
        (r":-?v", "v"),
        (r":\?:", "special-question"),
        (r":\?\?\?:", "special-3question"),
        (r":jap:", "respect"),
        (r":clap:", "bravo"),
    ]

    def get_smileys(path):
        "Get all smileys"
        from subprocess import getoutput
        smileys = getoutput("ls " + path + "/img/smileys/")
        return [smiley[:-len(".gif")] for smiley in smileys.split("\n")]

    smileys = get_smileys(settings.STATICFILES_DIRS[0])
    double_colon = filter(lambda s: not s.startswith("special-"), smileys)
    all_smileys = (
        specialSmileys +
        [(":" + re.escape(s) + ":", s) for s in double_colon]
    )

    return [(re.compile(smiley), name) for smiley, name in all_smileys]


def _smiley_replacer(text):
    for smiley, name in compileSmileys():
        tag = "<img class=\"smiley\" src=\"{:s}img/smileys/{:s}.gif\">"\
                    .format(settings.STATIC_URL, quote(name))
        text = smiley.sub(tag, text)
    return text


def smilify(html):
    """
    Replace text smileys.
    """
    try:
        parser = ExcludeTagsHTMLFilter(_smiley_replacer)
        parser.feed(html)
        smiled_html = parser.html
        parser.close()
    except:
        if settings.DEBUG:
            raise
        return html
    return smiled_html
