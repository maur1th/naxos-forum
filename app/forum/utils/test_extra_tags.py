from django.test import SimpleTestCase

from .extra_tags import VideoTag


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
