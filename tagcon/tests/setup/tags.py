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


class MultiplePositionalTag(tagcon.TemplateTag):
    _ = tagcon.IntegerArg(name="multiplier", default=5)

    limit = tagcon.IntegerArg(default=5, positional=True)

    def output(self, data):
        return '%s' % data['limit'] * data['multiplier']


class ArgumentTypeTag(tagcon.TemplateTag):
    age = tagcon.IntegerArg(null=True)
    name_ = tagcon.StringArg(null=True)
    url = tagcon.ModelInstanceArg(model=models.Link, required=False,
                                  null=True)
    date = tagcon.DateArg(null=True)
    time = tagcon.TimeArg(null=True)
    datetime = tagcon.DateTimeArg(null=True)

    def output(self, data):
        order = 'name age url date time datetime'.split()
        return ' '.join([str(data[x]) for x in order if data[x] is not None])


class ConstantTag(tagcon.TemplateTag):
    start = tagcon.Arg(positional=True)
    to = tagcon.ConstantArg()
    finish = tagcon.Arg(positional=True)

    def output(self, data):
        return '%s - %s' % (data['start'], data['finish'])
