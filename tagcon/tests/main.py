import datetime

from django.test import TestCase
from django import template

import tagcon
from tagcon.tests.setup import tags, models

template.add_to_builtins(tags.__name__)


def render(contents, extra_context=None):
    return template.Template(contents).render(template.Context(extra_context))


class TagExecutionTests(TestCase):

    def test_no_args(self):
        """A tag with keyword arguments works with or without the argument as
        long as a default value is set"""

        self.assertEqual(render('{% keyword limit 200 %}'),
                         'The limit is 200')

        self.assertEqual(render('{% keyword %}'),
                         'The limit is %d' %
                         tags.KeywordTag._keyword_args['limit'].default)


        self.assertRaises(tagcon.TemplateTagValidationError, render,
                          '{% keyword_no_default %}')

        # what if we change the arg to be null=True?
        tags.KeywordNoDefaultTag._keyword_args['limit'].null = True

        # now instead of on validation the error moves to when rendering. None
        # is not an integer
        self.assertRaises(template.TemplateSyntaxError, render,
                          '{% keyword_no_default %}')

    def test_args_format(self):
        """keyword argument syntax is {% tag arg value %}"""
        self.assertRaises(template.TemplateSyntaxError, template.Template,
                          '{% keyword limit=25 %}')

        self.assertRaises(template.TemplateSyntaxError, template.Template,
                          "{% keyword limit='25' %}")

    def test_handle_args(self):
        """tags with no arguments take no arguments"""
        self.assertRaises(template.TemplateSyntaxError, template.Template,
                          '{% no_argument this fails %}')


class TestArgumentTypes(TestCase):

    def test_model_instance_arg(self):
        content = '{% argument_type url object %}'
        object = models.Link(url='http://bing.com')
        self.assertEqual(render(content, {'object': object}),
                         unicode(object))

        self.assertRaises(tagcon.TemplateTagValidationError, render, content,
                          {'object': int()})

    def test_integer_arg(self):
        self.assertEqual(render('{% argument_type age 101 %}'), '101')

        # IntegerArg.clean calls int(value) to convert "23" to 23
        self.assertEqual(render('{% argument_type age "23" %}'), '23')

        # IntegerArg.clean will choke on the string
        self.assertRaises(tagcon.TemplateTagValidationError, render,
                          '{% argument_type age "7b" %}')

    def test_string_arg(self):
        self.assertEqual(render('{% argument_type name "alice" %}'), 'alice')

        # i can't remember which one (url perhaps?) but there was a tag that
        # worked with single quotes but not double quotes and so we check both
        self.assertEqual(render("{% argument_type name 'bob' %}"), 'bob')

        # will not find a var named dave in the context
        self.assertRaises(template.TemplateSyntaxError, render,
                          '{% argument_type name dave %}')

    def test_datetime_arg(self):
        self.assertEqual(render('{% argument_type datetime dt %}',
                                {'dt': datetime.datetime(2010, 1, 9,
                                                         22, 33, 47)}),
                         '2010-01-09 22:33:47')

    def test_date_arg(self):
        self.assertEqual(render('{% argument_type date d %}',
                                {'d': datetime.date(2010, 1, 9)}),
                         '2010-01-09')

    def test_time_arg(self):
        self.assertEqual(render('{% argument_type time t %}',
                                {'t': datetime.time(22, 33, 47)}),
                         '22:33:47')
