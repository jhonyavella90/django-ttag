from django import template

import ttag
from ttag.core import BaseTag, DeclarativeArgsMetaclass
from ttag.tests.setup import models

register = template.Library()


class SelfRegisteringMetaclass(DeclarativeArgsMetaclass):

    def __new__(cls, name, bases, attrs):
        cls = DeclarativeArgsMetaclass.__new__(cls, name, bases, attrs)
        parents = [b for b in bases if isinstance(b, DeclarativeArgsMetaclass)]
        if parents:
            register.tag(cls._meta.name, cls)
        return cls


class TestTag(BaseTag):
    __metaclass__ = SelfRegisteringMetaclass


class NamedArg(TestTag):
    limit = ttag.IntegerArg(default=5)

    def output(self, data):
        if 'limit' in data:
            return 'The limit is %d' % data['limit']
        return 'No limit was specified'


class NamedKeywordArg(NamedArg):
    limit = ttag.IntegerArg(keyword=True)


class NoArgument(TestTag):

    def output(self, data):
        return 'No arguments here'


class Positional(TestTag):
    limit = ttag.IntegerArg(default=5, positional=True)

    def output(self, data):
        return '%s' % data['limit']


class PositionalMixed(TestTag):
    limit = ttag.IntegerArg(default=5, positional=True)
    as_ = ttag.BasicArg()

    def render(self, context):
        data = self.resolve(context)
        context[data['as']] = data['limit']
        return ''


class PositionalMixedkw(TestTag):
    value = ttag.Arg(positional=True, required=False, null=True)
    default = ttag.Arg(keyword=True)

    def output(self, data):
        return unicode(data.get('value') or data['default'])


class PositionalOptional(TestTag):
    start = ttag.IntegerArg(positional=True)
    finish = ttag.IntegerArg(positional=True, required=False)

    def output(self, data):
        if 'finish' in data:
            start, finish = data['start'], data['finish']
        else:
            start, finish = 0, data['start']
        return ','.join([str(i) for i in range(start, finish)])


class PositionalOptionalMixed(TestTag):
    start = ttag.IntegerArg(positional=True)
    finish = ttag.IntegerArg(positional=True, required=False)
    step = ttag.IntegerArg()

    def output(self, data):
        if 'finish' in data:
            start, finish = data['start'], data['finish']
        else:
            start, finish = 0, data['start']
        return ','.join([str(i) for i in range(start, finish, data['step'])])


class ArgumentType(TestTag):
    age = ttag.IntegerArg(required=False)
    name_ = ttag.StringArg(required=False)
    url = ttag.ModelInstanceArg(model=models.Link, required=False)
    date = ttag.DateArg(required=False)
    time = ttag.TimeArg(required=False)
    datetime = ttag.DateTimeArg(required=False)
    flag = ttag.BooleanArg()

    def output(self, data):
        order = 'name age url date time datetime'.split()
        values = [unicode(data[x]) for x in order if x in data]
        if 'flag' in data:
            values.append('flag_is_set')
        return u' '.join(values)


class Constant(TestTag):
    start = ttag.Arg(positional=True)
    to = ttag.ConstantArg()
    finish = ttag.Arg(positional=True)

    def output(self, data):
        return '%s - %s' % (data['start'], data['finish'])


class KeywordsEcho(TestTag):
    keywords = ttag.KeywordsArg(positional=True)

    def output(self, data):
        keywords = data['keywords'].items()
        return ', '.join('%s: %s' % (key, value) for key, value in keywords)


class BaseInclude(TestTag):
    """
    A tag for testing KeywordsArg.
    """

    def output(self, data):
        out = 'including %s' % data['template']
        if data.get('with'):
            with_bits = data['with'].items()
            with_bits.sort(key=lambda bit: bit[0])
            out += ' with %s' % ' and '.join(['%s = %s' % (k, v)
                                              for k, v in with_bits])
        return out


class IncludeCompact(BaseInclude):
    template = ttag.Arg(positional=True)
    with_ = ttag.KeywordsArg(required=False)


class IncludeVerbose(BaseInclude):
    template = ttag.Arg(positional=True)
    with_ = ttag.KeywordsArg(required=False, compact=False, verbose=True)


class IncludeMixed(BaseInclude):
    template = ttag.Arg(positional=True)
    with_ = ttag.KeywordsArg(required=False, verbose=True)
