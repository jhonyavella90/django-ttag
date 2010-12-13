from django import template


class TagValidationError(template.TemplateSyntaxError):
    pass


class TagArgumentMissing(KeyError):
    pass
