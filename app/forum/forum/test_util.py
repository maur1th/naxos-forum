from django.test import SimpleTestCase

from .util import normalize_query, keygen


class NormalizeQueryTests(SimpleTestCase):

    def test_splits_words_and_groups_quoted_terms(self):
        # Behaviour documented in normalize_query's own docstring.
        self.assertEqual(
            normalize_query(
                ' some random  words "with   quotes  " and   spaces  '),
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces'])

    def test_blank_string_yields_no_terms(self):
        self.assertEqual(normalize_query('    '), [])


class KeygenTests(SimpleTestCase):

    ALLOWED = set('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')

    def test_key_has_expected_length_and_charset(self):
        for _ in range(10):
            key = keygen()
            self.assertEqual(len(key), 50)
            self.assertLessEqual(set(key), self.ALLOWED)

    def test_keys_are_not_repeated(self):
        self.assertNotEqual(keygen(), keygen())
