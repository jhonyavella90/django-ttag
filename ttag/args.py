import datetime
import re
from django.template import TemplateSyntaxError, FilterExpression
from ttag.exceptions import TagValidationError


class Arg(object):
    """
    A template tag argument used for parsing and validation.

    This is the base class for all other argument types, but this class can
    still be used directly for generic arguments.
    """
    # Tracks each time an Arg instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, required=True, default=None, null=False,
                 positional=False, keyword=False):
        """
        :param required:
            Whether the argument is required as part of the tag definition in
            the template. Required positional arguments can not occur after
            optional ones.

            Defaults to ``True``.

        :param default:
            The default value if this argument is not specified in the tag.

            Defaults to ``None``.

        :param null:
            Determines whether a value of ``None`` is an acceptable value for
            the argument resolution.

            When set to ``False``, a value of ``None`` or a missing context
            variable will cause a ``TagValidationError`` when this
            argument is cleaned.

            Defaults to ``False``.

        :param positional:
            Whether this is a positional tag (i.e. the argument name is not
            part of the tag definition).

            Defaults to ``False``.

        :param keyword:
            Use an equals to separate the value from the argument name, rather
            than the standard space separation.

            This parameter is only used for named arguments (i.e.
            ``positional=False``).

            Defaults to ``False``.
        """
        self.required = required
        self.default = default
        self.null = null
        self.positional = positional
        self.keyword = keyword

        # Increase the creation counter, and save our local copy.
        self.creation_counter = Arg.creation_counter
        Arg.creation_counter += 1

    def consume(self, parser, tokens, valid_named_args):
        """
        Return the values that this argument should capture.

        :param tokens: A list of available tokens for consumption in the tag.
        :param valid_named_args: A list of other valid named arguments for the
            tag.

        This method may be overridden by subclasses to change the behaviour of
        the argument, in which case the :meth:`resolve` may also need to be
        overridden.

        The default behaviour is to use the :meth:`consume_one` method,
        compiling the result as a template variable that can be used for
        resolution later.
        """
        if self.required:
            # The default consume method consumes exactly one argument.
            # Therefore, if the argument is required it doesn't matter if it
            # clashes with a named argument so don't pass valid_named_args on.
            valid_named_args = ()
        value = self.consume_one(tokens, self.required, valid_named_args)
        if value:
            return self.compile_filter(parser, value)

    def consume_one(self, tokens, required, valid_named_args=()):
        """
        Consume a single token, raising an error if it's required.

        If the next token matches on in ``valid_named_args``, it won't be
        consumed.
        """
        if tokens and not self.is_token_named_arg(tokens[0], valid_named_args):
            return tokens.pop(0)
        if required:
            raise TemplateSyntaxError("Value for '%s' not provided" %
                                      self.name)

    def is_token_named_arg(self, token, valid_named_args):
        """
        Check to see if the token is a valid named argument.
        
        :param valid_named_args: List of valid arguments.

            Keyword named arguments must be in the format ``'name='`` so they
            can be differentiated from standard named arguments.
        """
        keyword_token = token.find('=')
        if keyword_token != -1:
            token = token[keyword_token + 1]
        return token in valid_named_args

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
            raise TagValidationError(
                "Value for '%s' must not be null." % self.name
            )
        return self.clean(value)

    def clean(self, value):
        """
        Validate the resolved ``value``.

        This method is often overridden or extended by subclasses to alter or
        perform further validation of the value, raising
        ``TagValidationError`` as necessary.
        """
        return value


class BasicArg(Arg):
    """
    A simpler argument which doesn't compile its value as a
    ``FilterExpression``.

    Example usage::

        class GetUsersTag(ttag.Tag)
            as_ = ttag.BasicArg()

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

        class Cool(ttag.Tag)
            cool = ttag.BooleanArg()

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

    def consume(self, parser, tokens, valid_named_args):
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
            raise TagValidationError(
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
            raise TagValidationError(
                self.error_message % {'arg_name': self.name, 'value': value,
                                      'class_name': class_name}
            )
        return value


class ConstantArg(BasicArg):

    def __init__(self, *args, **kwargs):
        """
        The ``positional`` parameter is ignored and always set to ``True``.
        """
        super(ConstantArg, self).__init__(*args, **kwargs)
        self.positional = True

    def consume(self, *args, **kwargs):
        """
        Consume the next token, ensuring its value matches the :attr:`name` of
        this argument.
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

    It takes a single additional keyword argument, ``model``.
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


class KeywordsArg(Arg):
    """
    Parses in one or more keyword tokens.

    Depending on the meth:`__init__` parameters, the keyword argument format
    may be compact (``foo=1 bar=2``), verbose (``1 as foo and 2 as bar``) or
    mixed (``foo=1 and 2 as bar``). The default is compact.

    In verbose mode, the ``and`` is required for multiple arguments, in mixed
    mode it is optional, and in compact mode it is obviously not used.
    """
    re_compact = re.compile(r'(\w+)=(.+)')
    re_keyword = re.compile(r'\w+$')

    def __init__(self, *args, **kwargs):
        """
        :param compile_values: Compile values as template variables (default
            ``True``).
        :param compact: Accept the compact ``foo=1`` argument format (default
            ``True``).
        :param verbose: Accept the verbose ``1 as foo`` argument format
            (default ``False``).
        """
        self.compile_values = kwargs.pop('compile_values', True)
        self.compact = kwargs.pop('compact', True)
        self.verbose = kwargs.pop('verbose', False)
        super(KeywordsArg, self).__init__(*args, **kwargs)

    def consume(self, parser, tokens, valid_named_args):
        """
        Consume one or more keyword arguments.
        """
        kwargs = {}
        while tokens:
            key = None
            if self.compact:
                match = self.re_compact.match(tokens[0])
                if match:
                    del tokens[0]
                    key, value = match.groups()
            if not key and self.verbose:
                if len(tokens) >= 3 and tokens[1] == 'as' and \
                        self.re_keyword.match(tokens[2]):
                    key, value = tokens[2], tokens[0]
                    del tokens[0:3]
            if not key:
                break
            if key in kwargs:
                raise TemplateSyntaxError("Duplicate keyword argument ('%s') "
                                          "provided for '%s'" % (key,
                                                                 self.name))
            if self.compile_values:
                value = self.compile_filter(parser, value)
            kwargs[key] = value
            if self.verbose:
                if tokens and tokens[0] == 'and':
                    del tokens[0]
                elif not self.compact:
                    # If we're in exclusive verbose mode so 'and' is required
                    # for multiple keywords.
                    break
        if self.required and not kwargs:
            raise TemplateSyntaxError("No keyword arguments provided for '%s'"
                                      % self.name)
        return kwargs

    def resolve(self, value, context, *args, **kwargs):
        """
        Resolve the keyword argument values for this argument for the given
        ``context``.
        """
        keywords = {}
        for key, val in value.items():
            keywords[key] = super(KeywordsArg, self).resolve(val, context,
                                                             *args, **kwargs)
        return keywords
