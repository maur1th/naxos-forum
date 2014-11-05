# Forked from https://github.com/slav0nic/DjangoBB/

# import re
from django.utils.six.moves.html_parser import HTMLParser, HTMLParseError
from django.conf import settings
from postmarkup import render_bbcode
# try:
#     import markdown
# except ImportError:
#     pass


# from django.http import Http404
from django.template.defaultfilters import urlize as django_urlize
# from django.core.paginator import Paginator, EmptyPage, InvalidPage

# from djangobb_forum import settings as forum_settings

#compile smiles regexp
# _SMILES = [(re.compile(smile_re), path) for smile_re, path in forum_settings.SMILES]

singleColonSmileys = ((':)', 'singleColon-smile'),
                      (';)', 'singleColon-wink'),
                      (':(', 'singleColon-sad'),
                      (':/', 'singleColon-bof'))


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
        #we don't need unescape data (without this possible XSS-attack)
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

    def __init__(self, func, tags=('a', 'pre', 'span')):
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
        if settings.DEBUG:
            raise
        return html
    return urlized_html


def convert_text_to_html(text, markup='bbcode'):
    if markup == 'bbcode':
        text = render_bbcode(text)
    # elif markup == 'markdown':
    #     text = markdown.markdown(text, safe_mode='escape')
    # else:
    #     raise Exception('Invalid markup property: %s' % markup)
    text = urlize(text)
    return text


toolbar = """
<div class="btn-toolbar" role="toolbar">
    <div class="btn-group">
        <div class="btn-group">
            <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
                <span class="glyphicon glyphicon-text-height"></span>
                <span class="caret"></span>
                <span style="font-family:serif"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
                <li><a href="#" id="toolbar-size" data-alt="10">10</a></li>
                <li><a href="#" id="toolbar-size" data-alt="12">12</a></li>
                <li><a href="#" id="toolbar-size" data-alt="16">16</a></li>
                <li><a href="#" id="toolbar-size" data-alt="18">18</a></li>
            </ul>
        </div>
        <button type="button" class="btn btn-default" id="toolbar-center">
            <span class="glyphicon glyphicon-align-center"></span>
            <span style="font-family:serif"></span>
        </button>
    </div>
    <div class="btn-group">
        <button type="button" class="btn btn-default" id="toolbar-list">
            <span class="glyphicon glyphicon-list"></span>
            <span style="font-family:serif"></span>
        </button>
        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
            <span class="caret"></span>
            <span style="font-family:serif"></span>
        </button>
        <ul class="dropdown-menu" role="menu">
            <li><a href="#" id="toolbar-ordered">1. 2. 3.</a></li>
            <li><a href="#" id="toolbar-unordered">&bull; ...</a></li>
        </ul>
    </div>
    <div class="btn-group">
        <button type="button" class="btn btn-default" id="colorpicker" value="">
            <span class="glyphicon glyphicon-tint"></span>
            <span style="font-family:serif"></span>
        </button>
        <button type="button" class="btn btn-default" id="colorpicker-apply" value="" disabled>
            <span class="glyphicon glyphicon-ok"></span>
            <span style="font-family:serif"></span>
        </button>
        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
            <span class="caret"></span>
            <span style="font-family:serif"></span>
        </button>
        <ul class="dropdown-menu" role="menu">
            <li><a href="#" id="toolbar-color" data-alt="dodgerblue">Bleu</a></li>
            <li><a href="#" id="toolbar-color" data-alt="crimson">Rouge</a></li>
            <li><a href="#" id="toolbar-color" data-alt="forestgreen">Vert</a></li>
            <li><a href="#" id="toolbar-color" data-alt="blueviolet">Violet</a></li>
            <li><a href="#" id="toolbar-color" data-alt="white">Blanc</a></li>
            <li><a href="#" id="toolbar-color" data-alt="gray">Gris</a></li>
        </ul>
    </div>
    <div class="btn-group">
        <button type="button" class="btn btn-default" id="toolbar-bold">
            <span style="font-weight:bold;font-family:serif">G</span>
        </button>
        <button type="button" class="btn btn-default" id="toolbar-italic">
            <span style="font-style:italic;font-family:serif">I</span>
        </button>
        <button type="button" class="btn btn-default" id="toolbar-underline">
            <span style="text-decoration:underline;font-family:serif">S</span>
        </button>
        <button type="button" class="btn btn-default" id="toolbar-strike">
            <span style="text-decoration:line-through;font-family:serif">ABC</span>
        </button>
    </div>
    <div class="btn-group">
        <button type="button" class="btn btn-default" id="toolbar-quote">
            <span class="glyphicon glyphicon-comment"></span>
            <span style="font-family:serif"></span>
        </button>
        <button type="button" class="btn btn-default" id="toolbar-link">
            <span class="glyphicon glyphicon-link"></span>
            <span style="font-family:serif"></span>
        </button>
        <button type="button" class="btn btn-default" id="toolbar-img">
            <span class="glyphicon glyphicon-picture"></span>
            <span style="font-family:serif"></span>
        </button>
        <button type="button" class="btn btn-default" id="toolbar-code">
            <span style="font-family:monospace">Code</span>
            <span style="font-family:serif"></span>
        </button>
    </div>
    <button type="button" class="btn btn-success">
        <span>Smileys</span>
        <span style="font-family:serif"></span>
    </button>
</div>
<br>
<script>
    function wrapText($textArea, openTag, closeTag, custCursor) {
        var len = $textArea.val().length;
        var start = $textArea[0].selectionStart;
        var end = $textArea[0].selectionEnd;
        var selectedText = $textArea.val().substring(start, end);
        var replacement = openTag + selectedText + closeTag;
        $textArea.val($textArea.val().substring(0, start) + replacement + $textArea.val().substring(end, len));
        if(!selectedText || custCursor){
            return start + openTag.length;
        };
    };
    $('#colorpicker').colorpicker().on('changeColor', function(ev) {
        var color = ev.color.toHex();
        $('#colorpicker-apply').data("color", color);
        $('#colorpicker-apply').removeAttr("disabled");
    });
    $('#colorpicker-apply').click(function() {
        var color = $(this).data("color");
        var $text = $("textarea[id$='content_plain']");
        var caret = wrapText($text, "[color="+color+"]", "[/color]");
        $text.focus();
        if(caret) {
            $text[0].setSelectionRange(caret, caret);
        };
    });
    $('*:regex(id,^toolbar-)').click(function() {
        var tags = {
            "center": "center",
            "bold": "b",
            "italic": "i",
            "underline": "u",
            "strike": "s",
            "code": "code",
            "img": "img",
            "list": "li",
            "quote": "quote",
        };
        var equalTags = {
            "link": "url",
        };
        var listTags = {
            "ordered": ["[ol]\\n[li]", "[/li]\\n[/ol]"],
            "unordered": ["[ul]\\n[li]", "[/li]\\n[/ul]"],
        };
        var fontTags = {
            "size": "size",
            "color": "color",
        };
        var m = this.id.match(/toolbar-([\w|-]+)/)[1];
        var $text = $("textarea[id$='content_plain']");
        if(m in tags) {
            var caret = wrapText($text, "["+tags[m]+"]", "[/"+tags[m]+"]");
            console.log(caret);
        } else if(m in equalTags) {
            tags = equalTags;
            var caret = wrapText($text, "["+tags[m]+"=]", "[/"+tags[m]+"]", true) - 1;
        } else if(m in listTags) {
            tags = listTags;
            var caret = wrapText($text, tags[m][0], tags[m][1]);
        } else if(m in fontTags) {
            tags = fontTags;
            var attr = $(this).data("alt");
            var caret = wrapText($text, "["+tags[m]+"="+attr+"]", "[/"+tags[m]+"]");
        } else if(m === "colorpicker") {
            var ev;
            $(this).colorpicker().on('hidePicker', function(ev) {
                var color = ev.color.toHex();
                var caret = wrapText($text, "[color="+color+"]", "[/color]");
                $text.focus();
                if(caret) {
                    $text[0].setSelectionRange(caret, caret);
                };
                return;
            });
        } else {
            return;
        };
        $text.focus();
        if(caret) {
            console.log(caret);
            $text[0].setSelectionRange(caret, caret);
        } else {
            var length = $text.val().length;
            $text[0].setSelectionRange(length, length);
        };
    });
</script>
"""


def get_title(value):
    title = """
    <div id="div_id_title" class="form-group">
        <label for="id_title" class="control-label  requiredField">
            Titre<span class="asteriskField">*</span>
        </label>
        <div class="controls ">
            <input class="textinput textInput form-control" id="id_title" maxlength="140" name="title" type="text" value="{:s}" disabled/>
        </div>
    </div>
    """.format(value)
    return title


def rm_trailing_spaces(s):
    "Helper function, removes trailing spaces in a string"

    if s[-1] != ' ':
        return s
    else:
        return rm_trailing_spaces(s[:-1])

# def paged(paged_list_name, per_page):
#     """
#     Parse page from GET data and pass it to view. Split the
#     query set returned from view.
#     """

#     def decorator(func):
#         def wrapper(request, *args, **kwargs):
#             result = func(request, *args, **kwargs)
#             if not isinstance(result, dict) or 'paged_qs' not in result:
#                 return result
#             try:
#                 page = int(request.GET.get('page', 1))
#             except ValueError:
#                 page = 1

#             real_per_page = per_page

#             #if per_page_var:
#                 #try:
#                     #value = int(request.GET[per_page_var])
#                 #except (ValueError, KeyError):
#                     #pass
#                 #else:
#                     #if value > 0:
#                         #real_per_page = value

#             from django.core.paginator import Paginator
#             paginator = Paginator(result['paged_qs'], real_per_page)
#             try:
#                 page_obj = paginator.page(page)
#             except (InvalidPage, EmptyPage):
#                 raise Http404
#             result[paged_list_name] = page_obj.object_list
#             result['is_paginated'] = page_obj.has_other_pages(),
#             result['page_obj'] = page_obj,
#             result['page'] = page
#             result['page_range'] = paginator.page_range,
#             result['pages'] = paginator.num_pages
#             result['results_per_page'] = paginator.per_page,
#             result['request'] = request
#             return result
#         return wrapper

#     return decorator


# def build_form(Form, _request, GET=False, *args, **kwargs):
#     """
#     Shorcut for building the form instance of given form class
#     """

#     if not GET and 'POST' == _request.method:
#         form = Form(_request.POST, _request.FILES, *args, **kwargs)
#     elif GET and 'GET' == _request.method:
#         form = Form(_request.GET, _request.FILES, *args, **kwargs)
#     else:
#         form = Form(*args, **kwargs)
#     return form





# def _smile_replacer(data):
#     for smile, path in _SMILES:
#         data = smile.sub(path, data)
#     return data


# def smiles(html):
#     """
#     Replace text smiles.
#     """
#     try:
#         parser = ExcludeTagsHTMLFilter(_smile_replacer)
#         parser.feed(html)
#         smiled_html = parser.html
#         parser.close()
#     except HTMLParseError:
#         # HTMLParser from Python <2.7.3 is not robust
#         # see: http://support.djangobb.org/topic/349/
#         if settings.DEBUG:
#             raise
#         return html
#     return smiled_html


# class AddAttributesHTMLFilter(HTMLFilter):
#     """
#     Class for html parsing that adds given attributes to tags.
#     """

#     def __init__(self, add_attr_map):
#         HTMLFilter.__init__(self)
#         self.add_attr_map = dict(add_attr_map)

#     def handle_starttag(self, tag, attrs):
#         attrs = list(attrs)
#         for add_attr in self.add_attr_map.get(tag, []):
#             if add_attr not in attrs:
#                 attrs.append(add_attr)

#         HTMLFilter.handle_starttag(self, tag, attrs)


# def paginate(items, request, per_page, total_count=None):
#     try:
#         page_number = int(request.GET.get('page', 1))
#     except ValueError:
#         page_number = 1

#     paginator = Paginator(items, per_page)
#     pages = paginator.num_pages
#     try:
#         paged_list_name = paginator.page(page_number).object_list
#     except (InvalidPage, EmptyPage):
#         raise Http404
#     return pages, paginator, paged_list_name
