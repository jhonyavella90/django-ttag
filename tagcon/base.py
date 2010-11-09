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

        # use supplied name, or generate one from class name
        tag_name = getattr(meta, 'name', utils.get_tag_name(name))

        all_args = [(name.rstrip('_'), attrs.pop(name))
                    for name, obj in attrs.items() if isinstance(obj, Arg)]
        all_args.sort(key=lambda x: x[1].creation_counter)
    
        positional_args = []
        optional_positional = False
        keyword_args = {}

        # Find and remove the arguments from attrs.
        for name, arg in all_args:
            arg.name = name
            if arg.positional:
                if arg.required:
                    if optional_positional:
                        raise template.TemplateSyntaxError(
                            "Required '%s' positional argument of '%s' cannot "
                            "exist after optional positional arguments." % (
                                arg.name,
                                tag_name,
                            )
                        )
                else:
                    optional_positional = True
                positional_args.append(arg)
            else:
                keyword_args[name] = arg

        # If this class is subclassing another TemplateTag, add that tag's
        # positional arguments before ones declared here. The bases are looped
        # in reverse to preserve the correct order of positional arguments and
        # correctly override keyword arguments.
        for base in bases[::-1]:
            if hasattr(base, '_positional_args') and \
                    hasattr(base, '_keyword_args'):
                positional_args = base._positional_args + positional_args
                for name, arg in base._keyword_args.iteritems(): 
                    if name not in keyword_args:
                        keyword_args[name] = arg 

        attrs['_positional_args'] = positional_args
        attrs['_keyword_args'] = keyword_args
        attrs['_args'] = dict(all_args)

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
            if value is None:
                if arg.default is not None:
                    self._vars[arg.name] = arg.default
                elif arg.required:
                    raise template.TemplateSyntaxError(
                        "'%s' positional argument to '%s' is required" % (
                            arg.name,
                            self.name,
                        )
                    )
            else:
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
