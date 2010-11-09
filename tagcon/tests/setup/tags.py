from django import template

import tagcon
from tagcon.tests.setup import models

register = template.Library()


class KeywordTag(tagcon.TemplateTag):
    limit = tagcon.IntegerArg(default=5)

    def output(self, data):
        return 'The limit is %d' % data['limit']


class KeywordNoDefaultTag(tagcon.TemplateTag):
    limit = tagcon.IntegerArg()

    def output(self, data):
        if 'limit' in data:
            return 'The limit is %d' % data['limit']
        return 'No limit was specified'


class NoArgumentTag(tagcon.TemplateTag):

    def output(self, data):
        return 'No arguments here'


class PositionalTag(tagcon.TemplateTag):
    limit = tagcon.IntegerArg(default=5, positional=True)

    def output(self, data):
        return '%s' % data['limit']


class PositionalMixedTag(tagcon.TemplateTag):
    limit = tagcon.IntegerArg(default=5, positional=True)
    as_ = tagcon.BasicArg()

    def render(self, context):
        data = self.resolve(context)
        context[data['as']] = data['limit']
        return ''


class ArgumentTypeTag(tagcon.TemplateTag):
    age = tagcon.IntegerArg(required=False)
    name_ = tagcon.StringArg(required=False)
    url = tagcon.ModelInstanceArg(model=models.Link, required=False)
    date = tagcon.DateArg(required=False)
    time = tagcon.TimeArg(required=False)
    datetime = tagcon.DateTimeArg(required=False)

    def output(self, data):
        order = 'name age url date time datetime'.split()
        return ' '.join([str(data[x]) for x in order if x in data])


class ConstantTag(tagcon.TemplateTag):
    start = tagcon.Arg(positional=True)
    to = tagcon.ConstantArg()
    finish = tagcon.Arg(positional=True)

    def output(self, data):
        return '%s - %s' % (data['start'], data['finish'])
