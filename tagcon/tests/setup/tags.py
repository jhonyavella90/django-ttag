from django.template import Library

import tagcon

register = Library()


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
