from django import template

__all__ = (
    'TemplateTagArgumentMissing',
    'TemplateTagValidationError',
)

class TemplateTagValidationError(template.TemplateSyntaxError):
    pass

class TemplateTagArgumentMissing(KeyError):
    pass
    # # exceptions use __str__, not __unicode__ or __repr__
    # def __str__(self):
    #     return self.args[0]

