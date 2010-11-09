"""
tagcon: a template tag constructor library for Django

Based on the syntax and implementation of Django's Model and Form classes.
"""
import sys

from django import template

from tagcon import utils
from tagcon.args import Arg

__all__ = (
    'TemplateTag',
)


class TemplateTagBase(type):
    def __new__(cls, name, bases, attrs):
        super_new = super(TemplateTagBase, cls).__new__
        parents = [b for b in bases if isinstance(b, TemplateTagBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)
        try:
            meta = attrs.pop('Meta')
        except KeyError:
            meta = None

        library = getattr(meta, 'library', None)
        if library:
            if not isinstance(library, template.Library):
                raise TypeError("A valid library is required.")
        else:
            # try auto-lookup
            module = sys.modules[attrs['__module__']]
            module_library = getattr(module, 'register', None)
            if isinstance(module_library, template.Library):
                library = module_library

        positional_args = []
        keyword_args = {}
        all_args = {}

        # Find and remove the arguments from attrs.
        keys = attrs.keys()
        for key in keys:
            arg = attrs[key]
            if not isinstance(arg, Arg):
                continue
            del attrs[key]
            if key.endswith('_'):
                key = key.rstrip('_')
            arg.name = key
            if arg.positional:
                positional_args.append(arg)
            else:
                keyword_args[key] = arg
            all_args[arg.name] = arg

        # Positional args are currently always required. This may change in the
        # future.
        for arg in positional_args:
            arg.required = True

        attrs['_positional_args'] = positional_args
        attrs['_keyword_args'] = keyword_args
        attrs['_args'] = all_args

        # use supplied name, or generate one from class name
        tag_name = getattr(meta, 'name', utils.get_tag_name(name))
        attrs['name'] = tag_name

        attrs['block'] = getattr(meta, 'block', False)

        # create the new class
        new_class = super_new(cls, name, bases, attrs)

        # register the tag if a tag library was provided
        if library:
            library.tag(tag_name, new_class)

        return new_class


class TemplateTag(template.Node):
    """
    A template tag.
    """
    __metaclass__ = TemplateTagBase

    def __init__(self, parser, token):
        self._vars = {}
        tokens = list(utils.smarter_split(token.contents))[1:]
        self._process_positional_args(parser, tokens)
        self._process_keyword_args(parser, tokens)
        if self.block:
            self.nodelist = parser.parse(('end%s' % (self.name,),))
            parser.delete_first_token()

    def _process_positional_args(self, parser, tokens):
        keywords = self._keyword_args.keys()
        for arg in self._positional_args:
            value = arg.consume(parser, tokens, keywords)
            self._vars[arg.name] = value

    def _process_keyword_args(self, parser, tokens):
        keywords = self._keyword_args.keys()

        while tokens:
            keyword = tokens.pop(0)
            try:
                arg = self._keyword_args[keyword]
            except KeyError:
                raise template.TemplateSyntaxError(
                    "'%s' does not take argument '%s'" % (self.name, keyword)
                )
            value = arg.consume(parser, tokens, keywords)
            self._vars[arg.name] = value

        # Handle missing items: required, default.
        for keyword, arg in self._keyword_args.iteritems():
            if arg.name in self._vars:
                continue
            if arg.default is not None:
                self._vars[arg.name] = arg.default
            elif arg.required:
                raise template.TemplateSyntaxError(
                    "'%s' argument to '%s' is required" % (keyword, self.name)
                )

    def clean(self, data):
        """
        Additional tag-wide argument cleaning after each individual Arg's
        ``clean`` has been called.
        """
        return data

    def render(self, context):
        """
        Render the tag.
        """
        data = self.resolve(context)
        return self.output(data)

    def output(self, data):
        raise NotImplementedError(
            "TemplateTag subclasses must implement this method."
        )

    def resolve(self, context):
        """
        Resolve variables and run clean methods, returning a dictionary
        containing the cleaned data.

        Cleaning happens after variable/filter resolution.

        Cleaning order is similar to forms:

        1) The argument's ``.clean()`` method.
        2) The tag's ``clean_ARGNAME()`` method, if any.
        3) The tag's ``.clean()`` method.
        """
        data = {}
        for name, value in self._vars.iteritems():
            arg = self._args[name]
            value = arg.resolve(value, context)
            value = arg.base_clean(value)
            try:
                tag_arg_clean = getattr(self, 'clean_%s' % arg.name)
            except AttributeError:
                pass
            else:
                value = tag_arg_clean(value)
            data[name] = value
        data = self.clean(data)
        return data
