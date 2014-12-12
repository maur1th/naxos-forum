from django.utils.six.moves.html_parser import HTMLParser, HTMLParseError
from django.template.defaultfilters import urlize as django_urlize
from django.db.models import Q

import re
import postmarkup
# try:
#     import markdown
# except ImportError:
#     pass

from naxos.settings.local import STATICFILES_DIRS as static, DEBUG


### Process search queries ###
# Code from Julien Phalip: http://goo.gl/EctTVy
def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of
        unecessary spaces and grouping quoted words together.
        Example:
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


### Urlize + BBCode filters ###
# Forked from https://github.com/slav0nic/DjangoBB/
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


spoiler_tag = ("<div class=\"panel panel-default spoiler-container\">"
               "<div class=\"panel-heading\" role=\"tab\" id=\"heading\">"
               "<h5 class=\"panel-title\">"
               "<a data-toggle=\"collapse\""
               "href=\"#spoiler-panel\" aria-expanded=\"false\" "
               "aria-controls=\"spoiler-panel\">Spoiler</a></h5></div>"
               "<div id=\"spoiler-panel\" class=\"panel-collapse collapse\" "
               "role=\"tabpanel\" aria-labelledby=\"heading\">"
               "<div class=\"panel-body\">")


class SpoilerTag(postmarkup.TagBase):
    def __init__(self, name, **kwargs):
        super().__init__(name)

    def render_open(self, parser, node_index):
        return spoiler_tag

    def render_close(self, parser, node_index):
        return '</div></div></div>'


render_bbcode = postmarkup.create(use_pygments=False)
render_bbcode.add_tag(SpoilerTag, 'spoiler')


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
                      (r':\?\?\?:', SMILEYS_PATH.format('special-3question')),
                      (r':jap:', SMILEYS_PATH.format('respect')),]

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
