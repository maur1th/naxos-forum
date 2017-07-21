import re
from postmarkup import TagBase


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
