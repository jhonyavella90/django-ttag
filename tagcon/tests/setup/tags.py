from django import template

import tagcon
from tagcon.tests.setup import models

register = template.Library()


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
    url = tagcon.ModelInstanceArg(model=models.Link, required=False,
                                  null=True)
    date = tagcon.DateArg(null=True)
    time = tagcon.TimeArg(null=True)
    datetime = tagcon.DateTimeArg(null=True)

    def render(self, context):
        self.resolve(context)
        order = 'name age url date time datetime'.split()
        return ' '.join([str(self.args[x]) for x in order if self.args[x] is not
                         None])


register.tag('keyword', KeywordTag)
register.tag('keyword_no_default', KeywordNoDefaultTag)
register.tag('no_argument', NoArgumentTag)
register.tag('argument_type', ArgumentTypeTag)
