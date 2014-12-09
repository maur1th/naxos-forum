# Forked from https://github.com/slav0nic/DjangoBB/

from django.utils.six.moves.html_parser import HTMLParser, HTMLParseError
from django.template.defaultfilters import urlize as django_urlize

import re
from postmarkup import render_bbcode
# try:
#     import markdown
# except ImportError:
#     pass

from naxos.settings.local import STATICFILES_DIRS as static, DEBUG


### Urlize + BBCode filters ###
class HTMLFilter(HTMLParser):

    """
    Base class for html parsers that produce filtered output.
    """

    def __init__(self):
        HTMLParser.__init__(self)
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
    except HTMLParseError:
        if DEBUG:
            raise
        return html
    return urlized_html


def rm_legacy_tags(text):
    "Replace legacy tags by bbcode"
    base_tags = [(r'ita', 'i'),
                 (r'bold', 'b'),
                 (r'under', 'u')]
    allTags = ([(re.escape('['+old+']'), '['+new+']')
                for old, new in base_tags] +
               [(re.escape('[/'+old+']'), '[/'+new+']')
                for old, new in base_tags])
    query = [(re.compile(old), new) for old, new in allTags]
    for old_match, new in query:
        text = old_match.sub(new, text)
    return text


def convert_text_to_html(text, markup='bbcode'):
    if markup == 'bbcode':
        text = rm_legacy_tags(text)
        text = render_bbcode(text)
    # elif markup == 'markdown':
    #     text = markdown.markdown(text, safe_mode='escape')
    text = urlize(text)
    return text


### Smiley stuff ###
def compileSmileys():

    SMILEYS_PATH = ("<img class=\"smiley\" src=\""
                    "/static/img/smileys/{:s}.gif\">")

    specialSmileys = [(r':\)', SMILEYS_PATH.format('special-smile')),
                      (r';\)', SMILEYS_PATH.format('special-wink')),
                      (r':\(', SMILEYS_PATH.format('special-sad')),
                      (r':\/', SMILEYS_PATH.format('bof')),
                      (r':o', SMILEYS_PATH.format('-o')),
                      (r':D', SMILEYS_PATH.format('green')),
                      (r':\?:', SMILEYS_PATH.format('special-question')),
                      (r':\?\?\?:', SMILEYS_PATH.format('special-3question'))]

    def get_smileys(path):
        "Get all smileys"
        from subprocess import getoutput
        smileys = getoutput('ls ' + path + '/img/smileys/')
        return [smiley[:-len('.gif')] for smiley
                in smileys.split('\n')]

    smileys = get_smileys(*static)
    doubleColonSmileys = list()
    for smiley in smileys:
        if smiley.find("special-") == -1:
            doubleColonSmileys.append(smiley)

    allSmileys = ([(':' + re.escape(smiley) + ':', SMILEYS_PATH.format(smiley))
                   for smiley in doubleColonSmileys] + specialSmileys)

    return [(re.compile(smiley), path) for smiley, path in allSmileys]


def _smiley_replacer(text):
    for smiley, path in compileSmileys():
        text = smiley.sub(path, text)
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
    except HTMLParseError:
        if DEBUG:
            raise
        return html
    return smiled_html


### Misc ###
def get_title(value):
    title = (
        "<div id='div_id_title' class='form-group'>"
        "<label for='id_title' class='control-label requiredField'>"
        "Titre<span class='asteriskField'>*</span>"
        "</label>"
        "<div class='controls'>"
        "<input class='textinput textInput form-control' id='id_title' "
        "maxlength='140' name='title' type='text' value='{:s}' disabled/>"
        "</div>"
        "</div>").format(value)
    return title


def rm_trailing_spaces(s):
    "Helper function, removes trailing spaces in a string"
    if s[-1] != ' ':
        return s
    else:
        return rm_trailing_spaces(s[:-1])

def keygen():
    import random
    return ''.join([random.SystemRandom().choice(
        'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
        for i in range(50)])
