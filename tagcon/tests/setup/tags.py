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


class PositionalOptionalTag(tagcon.TemplateTag):
    start = tagcon.IntegerArg(positional=True)
    finish = tagcon.IntegerArg(positional=True, required=False)

    def output(self, data):
        if 'finish' in data:
            start, finish = data['start'], data['finish']
        else:
            start, finish = 0, data['start']
        return ','.join([str(i) for i in range(start, finish)])


class PositionalOptionalMixedTag(tagcon.TemplateTag):
    start = tagcon.IntegerArg(positional=True)
    finish = tagcon.IntegerArg(positional=True, required=False)
    step = tagcon.IntegerArg()

    def output(self, data):
        if 'finish' in data:
            start, finish = data['start'], data['finish']
        else:
            start, finish = 0, data['start']
        return ','.join([str(i) for i in range(start, finish, data['step'])])


class ArgumentTypeTag(tagcon.TemplateTag):
    age = tagcon.IntegerArg(required=False)
    name_ = tagcon.StringArg(required=False)
    url = tagcon.ModelInstanceArg(model=models.Link, required=False)
    date = tagcon.DateArg(required=False)
    time = tagcon.TimeArg(required=False)
    datetime = tagcon.DateTimeArg(required=False)
    flag = tagcon.BooleanArg()

    def output(self, data):
        order = 'name age url date time datetime'.split()
        values = [unicode(data[x]) for x in order if x in data]
        if 'flag' in data:
            values.append('flag_is_set')
        return u' '.join(values)


class ConstantTag(tagcon.TemplateTag):
    start = tagcon.Arg(positional=True)
    to = tagcon.ConstantArg()
    finish = tagcon.Arg(positional=True)

    def output(self, data):
        return '%s - %s' % (data['start'], data['finish'])
