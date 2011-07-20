import datetime
import ttag

from django import template

register = template.Library()


class Do(ttag.helpers.TemplateTag):

    class Meta:
        template_required = False
        template_name = 'it'

    def output(self, data):
        return 'done'


class Go(ttag.helpers.TemplateTag):

    def output(self, data):
        return 'home'


class Ask(ttag.helpers.TemplateTag):
    value = ttag.Arg()

    class Meta:
        template_required = False

    def output(self, data):
        if "date" in data['value']:
            return datetime.datetime.today()


register.tag(Do)
register.tag(Go)
register.tag(Ask)
