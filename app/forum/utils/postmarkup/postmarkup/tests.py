# -*- coding: UTF-8 -*-

import postmarkup
import unittest


class TestPostmarkup(unittest.TestCase):

    def test_textilize(self):
        """Test textilize function"""
        tests = [("<b>No bold</b>", "No bold"),
                 ('<span class="blah">A span</span>', "A span"),
                 ("Just text", "Just text"),
                 ("<p>paragraph</p>", " paragraph")]

        for test, result in tests:
            self.assertEqual(postmarkup.textilize(test), result)

    def test_strip_bbcode(self):
        """Test strip_bbcode function"""
        tests = [("[b]Not bold[/b]", "Not bold"),
                 ("Just text", "Just text"),
                 ("[b][i][url][url=test]", "")]

        for test, result in tests:
            self.assertEqual(postmarkup.strip_bbcode(test), result)

    def test_cleanuphtml(self):
        """Test cleanup_html"""
        markup = postmarkup.create()

        tests = [("""\n<p>\n </p>\n""", ""),
                 ("""<b>\n\n<i>   </i>\n</b>Test""", "Test"),
                 ("""<p id="test">Test</p>""", """<p id="test">Test</p>""")]

        for test, result in tests:
            self.assertEqual(markup.cleanup_html(test).strip(), result)

    def test_simpletag(self):
        "Test simple tags"
        markup = postmarkup.create()

        tests = [('[b]Hello[/b]', "<strong>Hello</strong>"),
                 ('[i]Italic[/i]', "<em>Italic</em>"),
                 ('[s]Strike[/s]', "<strike>Strike</strike>"),
                 ('[u]underlined[/u]', "<u>underlined</u>"),
                 ]

        for test, result in tests:
            self.assertEqual(markup(test), result)

    def test_overlap(self):
        """Test overlapping tags produce correct output"""
        markup = postmarkup.create()

        tests = [('[i][b]Hello[/i][/b]', "<em><strong>Hello</strong></em>"),
                 ('[b]bold [u]both[/b] underline[/u]', '<strong>bold <u>both</u></strong><u> underline</u>')
                 ]

        for test, result in tests:
            self.assertEqual(markup(test), result)

    def test_links(self):
        """Test links produce correct output"""
        markup = postmarkup.create(annotate_links=False)

        tests = [('[link=http://www.willmcgugan.com]blog1[/link]', '<a href="http://www.willmcgugan.com">blog1</a>'),
                 ('[link="http://www.willmcgugan.com"]blog2[/link]', '<a href="http://www.willmcgugan.com">blog2</a>'),
                 ('[link http://www.willmcgugan.com]blog3[/link]', '<a href="http://www.willmcgugan.com">blog3</a>'),
                 ('[link]http://www.willmcgugan.com[/link]', '<a href="http://www.willmcgugan.com">http://www.willmcgugan.com</a>')
                 ]

        for test, result in tests:
            self.assertEqual(markup(test), result)

    def test_unknowntags(self):
        """Test unknown tags pass through correctly"""
        markup = postmarkup.create(annotate_links=False)

        tests = [('[REDACTED]', '[REDACTED]'),
                 ('[REDACTED this]', '[REDACTED this]'),
                 ('[REDACTED <b>]', '[REDACTED &lt;b&gt;]')]
        for test, result in tests:
            self.assertEqual(markup(test, render_unknown_tags=True), result)

    def test_unicode(self):
        """Test unicode support"""
        markup = postmarkup.create()

        tests = [('[b]Hello André[/b]', "<strong>Hello André</strong>"),
                 ('[i]ɸβfvθðsz[/i]', "<em>ɸβfvθðsz</em>"),
                 ]

        for test, result in tests:
            self.assertEqual(markup(test), result)

    def test_urls(self):
        """Test handling of URLs"""
        markup = postmarkup.create()

        tests = [("http://example.com", "[url]http://example.com[/url]")
                ]
        for test, result in tests:
            self.assertEqual(markup.tagify_urls(test), result)

    def test_tags_with_spaces(self):
        markup = postmarkup.create()
        tests = [("[i]one[/i][i]   [/i][i]two[/i][i] [/i][i]three[/i]", "<em>one</em> <em>two</em> <em>three</em>")]
        for test, result in tests:
            self.assertEqual(markup(test), result)

    def test_broken_img(self):
        markup = postmarkup.create()
        tests = [("[img]foo[/img", ""),
                 ("[img]fo[o[/img]", "")]
        for test, result in tests:
            self.assertEqual(markup(test), result)

    def test_url_with_accented_characters(self):
        """Test that URLs with accented characters are not over-encoded"""
        markup = postmarkup.create(annotate_links=False)
        # Wikipedia example with accented character
        input_url = '[link]https://fr.wikipedia.org/wiki/Métonymie[/link]'
        expected = '<a href="https://fr.wikipedia.org/wiki/Métonymie">https://fr.wikipedia.org/wiki/Métonymie</a>'
        self.assertEqual(markup(input_url), expected)

    def test_dangerous_schemes_are_not_linked(self):
        """[url] must never produce an href for non-http(s) schemes (XSS)."""
        markup = postmarkup.create(annotate_links=False)
        dangerous = [
            "[url]javascript://%0aalert(1)[/url]",  # netloc form bypassed the old check
            "[url]javascript:alert(1)[/url]",
            "[url]JAVASCRIPT://alert(1)[/url]",     # scheme match is case-insensitive
            "[url]vbscript://alert[/url]",
            "[url]data:text/html,<script>alert(1)</script>[/url]",
            "[url]ftp://example.com/file[/url]",
        ]
        for markup_text in dangerous:
            rendered = markup(markup_text)
            self.assertNotIn("<a ", rendered)
            self.assertNotIn("href", rendered)

    def test_http_and_https_urls_are_linked(self):
        """Legitimate schemes still render as links."""
        markup = postmarkup.create(annotate_links=False)
        for url in ("http://example.com", "https://example.com/path?q=1"):
            self.assertEqual(
                markup("[url]%s[/url]" % url),
                '<a href="%s">%s</a>' % (url, url))
