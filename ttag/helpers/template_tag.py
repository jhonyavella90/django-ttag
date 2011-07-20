from django.template import TemplateSyntaxError
from django.template.loader import render_to_string

from ttag import core, args

class TemplateTagOptions(core.Options):

    def __init__(self, meta, *args, **kwargs):
        super(TemplateTagOptions, self).__init__(meta=meta, *args, **kwargs)
        self.template_required = getattr(meta, 'template_required', True)
        self.template_name = getattr(meta, 'template_name', 'with')

    def post_process(self):
        super(TemplateTagOptions, self).post_process()
        if self.template_name in [name for name, arg in self.named_args.items()
                                  if not arg.keyword]:
            raise TemplateSyntaxError(
                "%s can not explicitly define an named argument called %r" % (
                    self.name,
                    self.template_name,
                )
            )
        arg = args.Arg(required=self.template_required, named=True)
        arg.name = self.template_name
        self.named_args[self.template_name] = arg


class TemplateTagMetaclass(core.DeclarativeArgsMetaclass):
    options_class = TemplateTagOptions


class TemplateTag(core.BaseTag):
    __metaclass__ = TemplateTagMetaclass

    def render(self, context):
        data = self.resolve(context)
        template_name = data.get(
            self._meta.template_name,
            'ttag/%s/%s.html' % (
                self.__class__.__module__.split('.')[-1].lower(),
                self._meta.name.lower()
            ))
        value = self.output(data)
        return render_to_string(template_name,
                                {'data': data, 'output': value}, context)
