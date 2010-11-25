import datetime
from django.template import TemplateSyntaxError, FilterExpression
from tagcon.exceptions import TemplateTagValidationError


class Arg(object):
    """
    A template tag argument used for parsing and validation.

    This is the base class for all other argument types.  Behavior can be
    defined via the following constructor arguments:

    ``required``
        Whether the argument is required as part of the tag definition in the
        template. Required positional arguments can not occur after optional
        ones.

        Defaults to ``True``.

    ``default``
        The default value for this argument if it is not specified.

        If ``None`` and the field is required, an exception will be raised when
        the template is parsed.

        Defaults to ``None``.

    ``null``
        Determines whether a value of ``None`` is an acceptable value for the
        argument resolution.

        When set to ``False``, a value of ``None`` or a missing context
        variable will cause a ``TemplateTagValidationError`` when this argument
        is cleaned.

        Defaults to ``False``.

    ``positional``
        Whether this is a positional tag (i.e. the argument name is not part of the tag
        definition).

        Defaults to ``False``.
    """
    # Tracks each time an Arg instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, required=True, default=None, null=False,
                 positional=False):
        """
        ``required`` and ``default`` are mutually exclusive.
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
    """
    A simpler argument which doesn't compile its value as a
    ``FilterExpression``.

    Example usage::

        class GetUsersTag(tagcon.TemplateTag)
            as_ = tagcon.BasicArg()

            def render(self, context)
                data = self.resolve(data)
                context[data['as']] = Users.objects.all()
                return ''
    """

    def compile_filter(self, parser, value):
        """
        Don't compile the filter, just return it unaltered.
        """
        return value


class BooleanArg(Arg):
    """
    A "flag" argument which doesn't consume any additional tokens.

    If it is not defined in the tag, the argument value will not exist in the
    resolved data dictionary.

    For example::

        class CoolTag(tagcon.TemplateTag)
            cool = tagcon.BooleanArg()

            def output(self, data):
                if 'cool' in data:
                    return "That's cool!"
                else:
                    return "Uncool."
    """

    def __init__(self, required=False, *args, **kwargs):
        """
        The change the default of the ``required`` argument to ``False``,
        since it makes little sense otherwise.
        """
        super(BooleanArg, self).__init__(required=required, *args, **kwargs)

    def consume(self, parser, tokens, keywords):
        """
        Simply return ``True``, not consuming any ``tokens``.
        """
        return True


class IntegerArg(Arg):
    """
    Tries to cast the argument value to an integer, throwing a template error
    if this fails.
    """

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


class IsInstanceArg(Arg):
    """
    This is a base class for easily creating arguments which require a specific
    type of instance.

    Subclasses must set :attr:`cls`.
    """

    #: Set to the class you want to ensure the value is an instance of.
    cls = None

    #: Optionally, override this to provide an alternate error message.
    error_message = "Value for '%(arg_name)s' must be a %(class_name)s "\
                    "instance"

    def clean(self, value):
        if not self.cls:
            raise NotImplementedError("This Arg class does not provide a cls "
                                      "attribute.")
        if not isinstance(value, self.cls):
            class_name = '%s.%s' % (self.cls.__module__, self.cls.__name__)
            raise TemplateTagValidationError(
                self.error_message % {'arg_name': self.name, 'value': value,
                                      'class_name': class_name}
            )
        return value


class ConstantArg(BasicArg):

    def __init__(self, *args, **kwargs):
        """
        The positional keyword argument is ignored and always set to ``True``.
        """
        super(ConstantArg, self).__init__(*args, **kwargs)
        self.positional = True

    def consume(self, *args, **kwargs):
        """
        Consume the Ensure the ``value`` matches the :attr:`name` of this
        argument.
        """
        value = super(ConstantArg, self).consume(*args, **kwargs)
        if value != self.name:
            raise TemplateSyntaxError("Expected constant '%s' instead of '%s'"
                                      % (self.name, value))
        return value


class StringArg(IsInstanceArg):
    """
    Validates that the argument is a ``string`` instance, otherwise throws a
    template error.
    """
    cls = basestring
    error_message = "Value for '%(arg_name)s' must be a string"


class DateTimeArg(IsInstanceArg):
    """
    Validates that the argument is a ``datetime.datetime`` instance, otherwise
    throws a template error.
    """
    cls = datetime.datetime


class DateArg(IsInstanceArg):
    """
    Validates that the argument is a ``datetime.date`` instance, otherwise
    throws a template error.
    """
    cls = datetime.date


class TimeArg(IsInstanceArg):
    """
    Validates that the argument is a ``datetime.time`` instance, otherwise
    throws a template error.
    """
    cls = datetime.time


class ModelInstanceArg(IsInstanceArg):
    """
    Validates that the passed in value is an instance of the specified
    ``Model`` class.

    It takes a single additional named argument, ``model``.
    """

    def __init__(self, *args, **kwargs):
        """
        :param model: The ``Model`` class you want to validate against.
        """
        from django.db import models
        try:
            model = kwargs.pop('model')
        except KeyError:
            raise TypeError("A 'model' keyword argument is required")
        if not issubclass(model, models.Model):
            raise TypeError("'model' must be a Model subclass")
        self.cls = model
        super(ModelInstanceArg, self).__init__(*args, **kwargs)
