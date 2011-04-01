from django import template

from ttag import core, args


class AsTagOptions(core.Options):

    def __init__(self, meta, *args, **kwargs):
        super(AsTagOptions, self).__init__(meta=meta, *args, **kwargs)
        self.as_required = getattr(meta, 'as_required', True)
        self.as_name = getattr(meta, 'as_name', 'as')

    def post_process(self):
        super(AsTagOptions, self).post_process()
        if self.as_name in [name for name, arg in self.named_args
                            if not arg.keyword]:
            raise template.TemplateSyntaxError(
                "%s can not explicitly define an named argument called %r" % (
                    self.name,
                    self.as_name,
                )
            )
        arg = args.BasicArg(required=self.as_required)
        arg.name = self.as_name
        self.named_args[self.as_name] = arg


class AsTagMetaclass(core.DeclarativeArgsMetaclass):
    options_class = AsTagOptions


class AsTag(core.BaseTag):
    __metaclass__ = AsTagMetaclass

    def render(self, context):
        data = self.resolve(context)
        as_var = data.get(self._meta.as_name)
        value = self.as_value(data, context)
        if as_var:
            context[as_var] = value
            return self.as_output(data, context)
        return value

    def as_value(self, data, context):
        return self.output(data)

    def as_output(self, data, context):
        return ''
