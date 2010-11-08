import datetime
from tagcon.exceptions import TemplateTagValidationError

__all__ = (
    'Arg',
    'DateArg',
    'DateTimeArg',
    'IntegerArg',
    'ModelInstanceArg',
    'StringArg',
    'TimeArg',
)


class Arg(object):
    """
    A template tag argument.

    ``name`` is the variable name, and is required if the argument is
    positional; otherwise it will use the keyword name by default.  This is
    *not* the keyword name (i.e., the name used in the tag iself).

    ``required`` and ``default`` are mutually exclusive, and only apply to
    keyword arguments; a positional argument is implicitly required.

    ``resolve`` determines whether a non-literal string (i.e., not surrounded
    in quotes) will be resolved as a variable; if false, it will be interpreted
    as a string.

    ``multi`` determines if the argument's value may consist of multiple
    comma-separated items (which would each be resolved, or not, according to
    the value of ``resolve``).

    ``flag`` denotes a keyword argument that does *not* have a separate value;
    its value is true if they keyword is given, and false otherwise.
    """

    def __init__(self, name=None, required=True, default=None, resolve=True,
                 multi=False, flag=False, positional=False):
        self.name = name
        self.required = required
        self.default = default
        self.resolve = resolve
        self.multi = multi
        self.keyword = None
        self.flag = flag
        self.positional = positional

    def base_clean(self, value):
        """
        Validation that always takes place.

        Don't override me; override ``clean`` instead.
        """
        if not self.multi and isinstance(value, (list, tuple)):
            err_msg = "Value for '%s' must be a single item." % (self.name,)
            raise TemplateTagValidationError(err_msg)
        return self.clean(value)

    def clean(self, value):
        """
        Validate the argument value.

        Subclasses should perform any munging here, raising
        ``TemplateTagValidationError`` as necessary.

        Filters are applied *before* ``clean`` is called.
        """
        return value


class IntegerArg(Arg):

    def clean(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise TemplateTagValidationError(
                "Value for '%s' must be an integer (got %r)" % (self.name,
                                                                value)
            )
        return value


class StringArg(Arg):

    def clean(self, value):
        if not isinstance(value, basestring):
            raise TemplateTagValidationError(
                "Value for '%s' must be a string" % self.name
            )
        return value


class ConstantArg(Arg):

    def __init__(self, *args, **kwargs):
        super(ConstantArg, self).__init__(*args, **kwargs)
        self.positional = True
        self.resolve = False

    def clean(self, value):
        if value != self.keyword:
            raise TemplateTagValidationError(
                "Expected constant value '%s' (received '%s')" % (self.keyword,
                                                                  value)
            )
        return value


class DateTimeArg(Arg):

    def clean(self, value):
        if not isinstance(value, datetime.datetime):
            raise TemplateTagValidationError(
                "Value for '%s' must be a datetime instance" % self.name
            )
        return value


class DateArg(Arg):

    def clean(self, value):
        if not isinstance(value, datetime.date):
            raise TemplateTagValidationError(
                "Value for '%s' must be a date instance" % (
                    self.name,
                )
            )
        return value


class TimeArg(Arg):

    def clean(self, value):
        if not isinstance(value, datetime.time):
            raise TemplateTagValidationError(
                "Value for '%s' must be a time instance" % self.name
            )
        return value


class ModelInstanceArg(Arg):

    def __init__(self, *args, **kwargs):
        from django.db import models
        try:
            model = kwargs.pop('model')
        except KeyError:
            err_msg = "A 'model' keyword argument is required"
            raise TypeError(err_msg)
        if not issubclass(model, models.Model):
            err_msg = "'model' must be a Model subclass"
            raise TypeError(err_msg)
        self.model_class = model
        super(ModelInstanceArg, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not isinstance(value, self.model_class):
            raise TemplateTagValidationError(
                "Value for '%s' must be an instance of %s.%s" % (
                    self.name,
                    self.model_class.__module__,
                    self.model_class.__name__,
                )
            )
        return value
