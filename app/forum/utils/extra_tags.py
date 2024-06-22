import re
from urllib.parse import urlparse
from .postmarkup.postmarkup import PostMarkup, TagBase, strip_bbcode


class CustomImgTag(TagBase):

    def __init__(self, name, **kwargs):
        super(CustomImgTag, self).__init__(name, inline=True)

    def open(self, parser, params, *args):
        if params.strip():
            self.auto_close = True
        super(CustomImgTag, self).open(parser, params, *args)

    def render_open(self, parser, node_index):

        contents = self.get_contents(parser)
        self.skip_contents(parser)

        # Validate url to avoid any XSS attacks
        if self.params:
            url = self.params.strip()
        else:
            url = strip_bbcode(contents)

        url = url.replace(u'"', u"%22").strip()
        if not url:
            return u''
        try:
            scheme, netloc, path, params, query, fragment = urlparse(url)
            if not scheme:
                url = u'http://' + url
                scheme, netloc, path, params, query, fragment = urlparse(url)
        except ValueError:
            return u''
        if scheme.lower() not in (u'http', u'https', u'ftp'):
            return u''

        return u'<img class="img-responsive" src="%s"></img>' % PostMarkup.standard_replace_no_break(url)


class SpoilerTag(TagBase):
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


class VideoTag(TagBase):
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
            url = PostMarkup.standard_unreplace(url)

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
            return (''
                '<div class="embed-responsive embed-responsive-16by9">'
                '<iframe class="embed-responsive-item" src="{}" '
                'frameborder="0" allowfullscreen="true">'
            ).format(PostMarkup.standard_replace_no_break(self.url))
        elif self.domain:
            return (
                '<video loop="true" controls="true" src="{}">'
            ).format(PostMarkup.standard_replace_no_break(self.url))
        else:
            return ""

    def render_close(self, parser, node_index):

        tag_data = parser.tag_data
        tag_data[u'link_nest_level'] -= 1

        if tag_data[u'link_nest_level'] > 0:
            return u''

        if self.domain in self.iframe_domains:
            return u'</iframe></div>'+self.annotate_link(self.domain)
        elif self.domain:
            return u'</video>'+self.annotate_link(self.domain)
        else:
            return u''

    def annotate_link(self, domain=None):

        if domain and self.annotate_links:
            return annotate_link(domain)
        else:
            return u""
