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

# Test with: And [b]some[/b] tags [i]along[/i] the [u]way[/u]. [b][u]Even[/b][/u] [url=www.google.com]links[/url] and emails: test@gmail.com !!!


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
