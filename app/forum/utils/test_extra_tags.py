from django.test import SimpleTestCase

from .extra_tags import VideoTag
from .renderer import render_bbcode


class YouTubeEmbedTests(SimpleTestCase):
    """Cover the YouTube URL normalisation used by the [video] tag (#118)."""

    EMBED = 'https://www.youtube.com/embed/xvFZjo5PgG0'

    def assertEmbed(self, url, expected=None):
        self.assertEqual(VideoTag._to_youtube_embed(url), expected or self.EMBED)

    def test_watch_url_is_rewritten(self):
        self.assertEmbed('https://www.youtube.com/watch?v=xvFZjo5PgG0')

    def test_watch_url_without_www(self):
        self.assertEmbed('https://youtube.com/watch?v=xvFZjo5PgG0')

    def test_mobile_watch_url(self):
        self.assertEmbed('https://m.youtube.com/watch?v=xvFZjo5PgG0')

    def test_short_youtu_be_url(self):
        self.assertEmbed('https://youtu.be/xvFZjo5PgG0')

    def test_extra_query_params_are_dropped(self):
        self.assertEmbed('https://www.youtube.com/watch?v=xvFZjo5PgG0&list=PLabc')

    def test_timestamp_becomes_start_param(self):
        self.assertEmbed(
            'https://www.youtube.com/watch?v=xvFZjo5PgG0&t=90s',
            self.EMBED + '?start=90',
        )
        self.assertEmbed(
            'https://youtu.be/xvFZjo5PgG0?t=42',
            self.EMBED + '?start=42',
        )

    def test_already_embed_url_is_unchanged(self):
        # Videos posted before #118 use the /embed/ form directly.
        url = 'https://www.youtube.com/embed/xvFZjo5PgG0'
        self.assertEqual(VideoTag._to_youtube_embed(url), url)

    def test_non_youtube_url_is_unchanged(self):
        for url in (
            'https://player.vimeo.com/video/12345',
            'https://example.com/clip.mp4',
        ):
            self.assertEqual(VideoTag._to_youtube_embed(url), url)

    def test_invalid_video_id_is_left_untouched(self):
        # Not a valid 11-char id: don't build a broken embed URL.
        url = 'https://www.youtube.com/watch?v=not-a-real-id-too-long'
        self.assertEqual(VideoTag._to_youtube_embed(url), url)


class VideoWidthTests(SimpleTestCase):
    """Optional ``w`` width option of the [video] tag (#62)."""

    URL = 'https://www.youtube.com/embed/xvFZjo5PgG0'
    DEFAULT = '<div class="embed-responsive embed-responsive-16by9">'

    def render(self, text):
        return render_bbcode(text)

    def test_default_is_unchanged(self):
        html = self.render('[video]%s[/video]' % self.URL)
        self.assertIn(self.DEFAULT, html)
        self.assertNotIn('max-width', html)

    def test_width_option(self):
        html = self.render('[video w=640]%s[/video]' % self.URL)
        self.assertIn(
            '<div class="embed-responsive embed-responsive-16by9" '
            'style="max-width: 640px">', html)
        self.assertIn('src="%s"' % self.URL, html)

    def test_width_option_with_inline_url(self):
        html = self.render('[video w=640 %s][/video]' % self.URL)
        self.assertIn('max-width: 640px', html)
        self.assertIn('src="%s"' % self.URL, html)

    def test_range_bounds_accepted(self):
        for w in (200, 1920):
            html = self.render('[video w=%d]%s[/video]' % (w, self.URL))
            self.assertIn('max-width: %dpx' % w, html)

    def test_invalid_width_falls_back(self):
        for w in ('abc', '199', '1921', '0', '-5', '640px', '6.4', '<x>'):
            html = self.render('[video w=%s]%s[/video]' % (w, self.URL))
            self.assertIn(self.DEFAULT, html, w)
            self.assertNotIn('max-width', html, w)
            self.assertIn('src="%s"' % self.URL, html, w)
