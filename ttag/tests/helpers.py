from django.test import TestCase
from django import template

from ttag.tests.setup import as_tags

template.add_to_builtins(as_tags.__name__)


def render(contents, extra_context=None):
    return template.Template(contents).render(template.Context(extra_context))


class AsTag(TestCase):

    def test_simple(self):
        """
        A tag with named arguments works with or without the argument as long
        as a default value is set.
        """
        self.assertEqual(render('{% fish_as as out %}-{{ out }}'), '-fish')

    def test_optional(self):
        """
        A tag with named arguments works with or without the argument as long
        as a default value is set.
        """
        self.assertEqual(render('{% maybe_as %}-{{ out }}'), 'maybe-')
        self.assertEqual(render('{% maybe_as as out %}-{{ out }}'), '-maybe')

    def test_as_output(self):
        """
        A tag with named arguments works with or without the argument as long
        as a default value is set.
        """
        self.assertEqual(render('{% output_as 1 %}-{{ out }}'), '1-')
        self.assertEqual(render('{% output_as 1 as out %}-{{ out }}'),
                         'yes_as-1')
