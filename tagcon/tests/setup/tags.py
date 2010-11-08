from django import template

import tagcon
from tagcon.tests.setup import models

register = template.Library()


class KeywordTag(tagcon.TemplateTag):

    limit = tagcon.IntegerArg(default=5)

    def render(self, context):
        data = data = self.resolve(context)
        return 'The limit is %d' % data.limit


class KeywordNoDefaultTag(tagcon.TemplateTag):

    limit = tagcon.IntegerArg()

    def render(self, context):
        data = self.resolve(context)
        return 'The limit is %d' % data.limit


class NoArgumentTag(tagcon.TemplateTag):

    def render(self, context):
        return 'No arguments here'


class SinglePositionalTag(tagcon.TemplateTag):
    _ = tagcon.IntegerArg(name="single_arg", default=5)

    def render(self, context):
        data = self.resolve(context)
        return '%s' % data['single_arg']


class NewPositionalTag(tagcon.TemplateTag):

    limit = tagcon.IntegerArg(default=5, positional=True)

    def render(self, context):
        data = self.resolve(context)
        return '%s' % data['limit']


class MultipleNewPositionalTag(tagcon.TemplateTag):
    _ = tagcon.IntegerArg(name="multiplier", default=5)

    limit = tagcon.IntegerArg(default=5, positional=True)

    def render(self, context):
        data = self.resolve(context)
        return '%s' % data['limit'] * data['multiplier']


class ArgumentTypeTag(tagcon.TemplateTag):

    age = tagcon.IntegerArg(null=True)
    name_ = tagcon.StringArg(null=True)
    url = tagcon.ModelInstanceArg(model=models.Link, required=False,
                                  null=True)
    date = tagcon.DateArg(null=True)
    time = tagcon.TimeArg(null=True)
    datetime = tagcon.DateTimeArg(null=True)

    def render(self, context):
        data = self.resolve(context)
        order = 'name age url date time datetime'.split()
        return ' '.join([str(data[x]) for x in order if data[x] is not None])
