from html.parser import HTMLParser
from django.conf import settings

from urllib.parse import quote

import re
import os
import postmarkup
import markdown

from user.models import ForumUser
from .extra_tags import CustomImgTag, SpoilerTag, VideoTag


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


# Smiley stuff
def compile_smileys():

    special_smileys = [
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
        [(r":-?\/", "bof")] +  # 1st to avoid replacing other smileys' http://
        [(":" + re.escape(s) + ":", s) for s in double_colon] +
        special_smileys
    )

    return [(re.compile(smiley), name) for smiley, name in all_smileys]


def _smiley_replacer(text):
    for smiley, name in compile_smileys():
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


# TODO: Remove, make db migration instead
def rm_legacy_tags(text):

    "Replace legacy tags by bbcode"
    base_tags = [(r'ita', 'i'),
                 (r'bold', 'b'),
                 (r'under', 'u')]
    all_tags = ([(re.escape('[' + old + ']'), '[' + new + ']')
                for old, new in base_tags] +
               [(re.escape('[/' + old + ']'), '[/' + new + ']')
                for old, new in base_tags])
    query = [(re.compile(old), new) for old, new in all_tags]
    for old_match, new in query:
        text = old_match.sub(new, text)
    return text


def add_user_tags(text):

    def process_tag(matchobj):
        user = ForumUser.objects.filter(username=matchobj.group(2)).first()
        if user:
            return matchobj.group(1) + "[user]@" + matchobj.group(2) + "[/user]"
        else:
            return matchobj.group(1) + "@" + matchobj.group(2)

    # https://stackoverflow.com/a/24676780/4122595
    return re.sub(r"(?i)(^| )@((?:(?![×Þß÷þø])[-'0-9a-zÀ-ÿ_-])+)", process_tag, text)


# Rendering
render_bbcode = postmarkup.create(use_pygments=False, annotate_links=False, exclude=["img"])
render_bbcode.add_tag(CustomImgTag, 'img')
render_bbcode.add_tag(SpoilerTag, 'spoiler')
render_bbcode.add_tag(postmarkup.SimpleTag, 'user', "a class='user-tag'")
render_bbcode.add_tag(VideoTag, 'video')


def render(text, markup='bbcode'):
    if markup == 'bbcode':
        text = rm_legacy_tags(text)  # TODO: make db migration instead
        text = add_user_tags(text)
        return smilify(render_bbcode(text, cosmetic_replace=False))
    elif markup == 'markdown':
        return markdown.markdown(text, safe_mode='escape')
