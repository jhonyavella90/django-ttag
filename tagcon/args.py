import datetime
from django.template import TemplateSyntaxError, FilterExpression
from tagcon.exceptions import TemplateTagValidationError


class Arg(object):
    """
    A template tag argument.
    """
    # Tracks each time an Arg instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, required=True, default=None, null=False,
                 positional=False):
        """
        ``required`` and ``default`` are mutually exclusive, and only
        apply to keyword arguments; a positional argument is implicitly
        required.

        ``null`` determines whether a value of ``None`` is an acceptable
        value for the tag resolution. If set to ``False`` (default), a value of
        ``None`` or a missing context variable will cause a
        ``TemplateTagValidationError`` when cleaned.
        """
        self.required = required
        self.default = default
        self.null = null
        self.positional = positional

        # Increase the creation counter, and save our local copy.
        self.creation_counter = Arg.creation_counter
        Arg.creation_counter += 1

    def consume(self, parser, tokens, keywords):
        """
        Return the values that this argument should capture.
        
        ``tokens`` is a list of available tokens for consumption in the tag.
        Pop tokens as needed from the start of this list, returning a value
        which can be used for resolution later.
        """
        if self.required:
            # The default consume method consumes exactly one argument.
            # Therefore, if the argument is required it doesn't matter if it
            # clashes with a keyword, don't pass keywords on.
            keywords = ()
        value = self.consume_one(tokens, self.required, keywords)
        if value:
            return self.compile_filter(parser, value)

    def consume_one(self, tokens, required, keywords=()):
        """
        Consume a single token, raising an error if it's required.

        If the next token matches on in ``keywords``, it won't be consumed.
        """
        if tokens and tokens[0] not in keywords:
            return tokens.pop(0)
        if required:
            raise TemplateSyntaxError("Value for '%s' not provided" %
                                      self.name)

    def compile_filter(self, parser, value):
        return parser.compile_filter(value)

    def resolve(self, value, context):
        """
        Resolve the ``value`` for this argument for the given
        ``context``.
        
        This method is usually overridden by subclasses which also override
        :meth:`consume` to return different number of resolved values.
        """
        if not isinstance(value, FilterExpression):
            return value
        return value.resolve(context, ignore_failures=True)

    def base_clean(self, value):
        """
        Ensure the resolved ``value`` is not ``None`` if :attr:`null` is
        ``True``.

        Subclasses should override :meth:`clean` instead of this method.
        """
        if not self.null and value is None:
            raise TemplateTagValidationError(
                "Value for '%s' must not be null." % self.name
            )
        return self.clean(value)

    def clean(self, value):
        """
        Validate the resolved ``value``.

        This method is often overridden or extended by subclasses to alter or
        perform further validation of the value, raising
        ``TemplateTagValidationError`` as necessary.
        """
        return value


class BasicArg(Arg):

    def compile_filter(self, parser, value):
        """
        Don't compile the filter, just return it unaltered. 
        """
        return value


class IntegerArg(Arg):

    def clean(self, value):
        """
        Ensure the ``value`` is an integer.
        """
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
        """
        Ensure the ``value`` is a string or unicode.
        """
        if not isinstance(value, basestring):
            raise TemplateTagValidationError(
                "Value for '%s' must be a string" % self.name
            )
        return value


class BooleanArg(Arg):

    def consume(self, parser, tokens, keywords):
        """
        Simply return ``True``, not consuming any ``tokens``.
        """
        return True


class ConstantArg(BasicArg):

    def __init__(self, *args, **kwargs):
        super(ConstantArg, self).__init__(*args, **kwargs)
        self.positional = True

    def consume(self, *args, **kwargs):
        """
        Consume the Ensure the ``value`` matches the :attr:`name` of this argument.
        """
        value = super(ConstantArg, self).consume(*args, **kwargs)
        if value != self.name:
            raise TemplateSyntaxError("Expected constant '%s' instead of '%s'"
                                      % (self.name, value))
        return value


class DateTimeArg(Arg):

    def clean(self, value):
        """
        Ensure the ``value`` is a ``datetime.datetime`` instance.
        """
        if not isinstance(value, datetime.datetime):
            raise TemplateTagValidationError(
                "Value for '%s' must be a datetime instance" % self.name
            )
        return value


class DateArg(Arg):

    def clean(self, value):
        """
        Ensure the ``value`` is a ``datetime.date`` instance.
        """
        if not isinstance(value, datetime.date):
            raise TemplateTagValidationError(
                "Value for '%s' must be a date instance" % (
                    self.name,
                )
            )
        return value


class TimeArg(Arg):

    def clean(self, value):
        """
        Ensure the ``value`` is a ``datetime.time`` instance.
        """
        if not isinstance(value, datetime.time):
            raise TemplateTagValidationError(
                "Value for '%s' must be a time instance" % self.name
            )
        return value


class ModelInstanceArg(Arg):

    def __init__(self, *args, **kwargs):
        """
        Take an additional ``model`` argument which will be used to validate
        against.
        """
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
        """
        Ensure the ``value`` is an instance of the Model type defined by
        this argument.
        """
        if not isinstance(value, self.model_class):
            raise TemplateTagValidationError(
                "Value for '%s' must be an instance of %s.%s" % (
                    self.name,
                    self.model_class.__module__,
                    self.model_class.__name__,
                )
            )
        return value
