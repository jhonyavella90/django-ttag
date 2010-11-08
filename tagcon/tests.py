import datetime

from django.test import TestCase
from django.template import Library, Template, Context, add_to_builtins,\
        TemplateSyntaxError, VariableDoesNotExist
from django.db import models
import tagcon
register = Library()


class Link(models.Model):

    url = models.URLField()

    def __unicode__(self):
        return u'<%s>' % self.url


class KeywordTag(tagcon.TemplateTag):

    limit = tagcon.IntegerArg(default=5)

    def render(self, context):
        self.resolve(context)
        return 'The limit is %d' % self.args.limit


class KeywordNoDefaultTag(tagcon.TemplateTag):

    limit = tagcon.IntegerArg()

    def render(self, context):
        self.resolve(context)
        return 'The limit is %d' % self.args.limit


class NoArgumentTag(tagcon.TemplateTag):

    def render(self, context):
        return 'No arguments here'


class ArgumentTypeTag(tagcon.TemplateTag):

    age = tagcon.IntegerArg(null=True)
    name_ = tagcon.StringArg(null=True)
    url = tagcon.ModelInstanceArg(model=Link, required=False,
                                        null=True)
    date = tagcon.DateArg(null=True)
    time = tagcon.TimeArg(null=True)
    datetime = tagcon.DateTimeArg(null=True)

    def render(self, context):
        self.resolve(context)
        order = 'name age url date time datetime'.split()
        return ' '.join([str(self.args[x]) for x in order if self.args[x] is not
                         None])

add_to_builtins(KeywordTag.__module__)
add_to_builtins(NoArgumentTag.__module__)
add_to_builtins(ArgumentTypeTag.__module__)

render = lambda t: Template(t).render(Context())


class TagExecutionTests(TestCase):

    def test_no_args(self):
        """A tag with keyword arguments works with or without the argument as
        long as a default value is set"""

        self.assertEqual(Template('{% keyword limit 200 %}').render(Context()),
                         'The limit is 200')

        self.assertEqual(Template('{% keyword %}').render(Context()),
                         'The limit is %d' %
                         KeywordTag._keyword_args['limit'].default)


        self.assertRaises(tagcon.TemplateTagValidationError,
                          render,
                          '{% keyword_no_default %}')

        # what if we change the arg to be null=True?
        KeywordNoDefaultTag._keyword_args['limit'].null = True

        # now instead of on validation the error moves to when rendering. None
        # is not an integer
        self.assertRaises(TemplateSyntaxError,
                          render,
                          '{% keyword_no_default %}')

    def test_args_format(self):
        """keyword argument syntax is {% tag arg value %}"""
        self.assertRaises(TemplateSyntaxError,
                          Template,
                          '{% keyword limit=25 %}')

        self.assertRaises(TemplateSyntaxError,
                          Template,
                          "{% keyword limit='25' %}")

    def test_handle_args(self):
        """tags with no arguments take no arguments"""
        self.assertRaises(TemplateSyntaxError,
                          Template,
                          '{% no_argument this fails %}')


class TestArgumentTypes(TestCase):

    def test_model_instance_arg(self):
        t = Template('{% argument_type url object %}')
        object = Link(url='http://bing.com')
        c = Context({'object': object})
        self.assertEqual(t.render(c), object.__unicode__())

        c = Context({'object': int()})
        self.assertRaises(tagcon.TemplateTagValidationError,
                          t.render,
                          c)

    def test_integer_arg(self):
        t = Template('{% argument_type age 101 %}')
        self.assertEqual(t.render(Context()), '101')

        # IntegerArg.clean calls int(value) to convert "23" to 23
        t = Template('{% argument_type age "23" %}')
        self.assertEqual(t.render(Context()), '23')

        # IntegerArg.clean will choke on the string
        self.assertRaises(tagcon.TemplateTagValidationError,
                          render,
                          '{% argument_type age "7b" %}')

    def test_string_arg(self):

        t = Template('{% argument_type name "alice" %}')
        self.assertEqual(t.render(Context()), 'alice')

        # i can't remember which one (url perhaps?) but there was a tag that
        # worked with single quotes but not double quotes and so we check both
        t = Template("{% argument_type name 'bob' %}")
        self.assertEqual(t.render(Context()), 'bob')

        # will not find a var named dave in the context
        try:
            render('{% argument_type name dave %}')
        except TemplateSyntaxError, e:
            self.assertTrue(isinstance(e.exc_info[1], VariableDoesNotExist))

    def test_datetime_arg(self):
        t = Template('{% argument_type datetime dt %}')
        self.assertEqual(t.render(
                Context({'dt': datetime.datetime(2010, 1, 9, 22, 33, 47)})),
                         '2010-01-09 22:33:47')

    def test_date_arg(self):
        t = Template('{% argument_type date d %}')
        self.assertEqual(t.render(
                Context({'d': datetime.date(2010, 1, 9)})),
                         '2010-01-09')

    def test_time_arg(self):
        t = Template('{% argument_type time t %}')
        self.assertEqual(t.render(
                Context({'t': datetime.time(22, 33, 47)})),
                         '22:33:47')

