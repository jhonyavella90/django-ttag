"""
tagcon: a template tag constructor library for Django

Based on the syntax and implementation of Django's Model and Form classes.
"""
import sys

from django import template
from django.conf import settings

from tagcon import utils
from tagcon.args import Arg
from django.template import FilterExpression, TemplateSyntaxError

__all__ = (
    'TemplateTag',
)

def _invalid_template_string(var):
    if settings.TEMPLATE_STRING_IF_INVALID:
        if template.invalid_var_format_string is None:
            template.invalid_var_format_string = \
                '%s' in settings.TEMPLATE_STRING_IF_INVALID
        if template.invalid_var_format_string:
            return settings.TEMPLATE_STRING_IF_INVALID % var
    return settings.TEMPLATE_STRING_IF_INVALID


def _wrap_render(unwrapped_render):
    def render(self, context):
        try:
            if self._resolve:
                self.resolve(context)
            return utils.unroll_render(unwrapped_render(self, context))
        except template.VariableDoesNotExist, exc:
            if self.silence_errors:
                return _invalid_template_string(exc.var)
            raise
        except Exception, exc:
            if self.silence_errors:
                return ''
            raise
    return render


class TemplateTagBase(type):
    def __new__(cls, name, bases, attrs):
        super_new = super(TemplateTagBase, cls).__new__
        parents = [b for b in bases if isinstance(b, TemplateTagBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)
        # module = attrs.pop('__module__')
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
        attrs['name'] = tag_name

        attrs['silence_errors'] = getattr(meta, 'silence_errors', False)

        attrs['block'] = getattr(meta, 'block', False)

        attrs['_resolve'] = getattr(meta, 'resolve', True)

        # wrap render so it can optionally yield strings as a generator, and so
        # we can catch exceptions if necessary
        unwrapped_render = attrs.pop('render')
        attrs['render'] = _wrap_render(unwrapped_render)

        # positional tag arguments
        positional_args = attrs.pop('_', [])
        if isinstance(positional_args, Arg):
            # shortcut for single-arg case
            positional_args = [positional_args]
        else:
            # Check that all args are *actually* args.
            positional_args = [a for a in positional_args
                               if isinstance(a, Arg)]

        for arg in positional_args:
            if isinstance(arg, Arg):
                if not arg.name:
                    raise TypeError(
                        "Positional arguments must have 'name' specified."
                    )
                # positional args are always required
                arg.required = True
            elif not isinstance(arg, basestring):
                raise TypeError(
                    "Positional args must be Arg instances or strings"
                )
            elif not arg:
                raise ValueError("Empty strings are not valid arguments.")

        keyword_args = {}
        all_args = {}

        # can't use iteritems, since we mutate attrs
        keys = attrs.keys()
        for key in keys:
            arg = attrs[key]
            if not isinstance(arg, Arg):
                continue
            if key.endswith('_'):
                key = key.rstrip('_')
            if not arg.name:
                arg.name = key
            if arg.positional:
                if arg.name in [arg.name for arg in positional_args]:
                    raise TypeError(
                        "Positional arg '%s' is defined twice." % key
                    )
                positional_args.append(arg)
            else:
                arg.keyword = key
                keyword_args[key] = arg
            all_args[arg.name] = arg
            del attrs[key]

        attrs['_positional_args'] = positional_args
        attrs['_keyword_args'] = keyword_args
        # _args and _positional_args are keyed by *arg/var name*
        attrs['_args'] = all_args

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
        # don't keep the parser alive
        self._vars = {}
        self._raw_args = list(utils.smarter_split(token.contents))[1:]
        # self._raw_args = token.split_contents()[1:]
        self._process_positional_args(parser)
        self._process_keyword_args(parser)
        if self.block:
            self.nodelist = parser.parse(('end%s' % (self.name,),))
            parser.delete_first_token()

    def _process_positional_args(self, parser):
        for i, arg in enumerate(self._positional_args):
            pos = i + 1
            if isinstance(arg, basestring):
                name = arg
            else:
                name = arg.name
            try:
                raw_arg = self._raw_args.pop(0)
            except IndexError:
                err_msg = "'%s' takes at least %s" % (
                    self.name,
                    utils.verbose_quantity('argument', self._positional_args),
                )
                raise template.TemplateSyntaxError(err_msg)
            if isinstance(arg, basestring):
                if raw_arg != arg:
                    err_msg = "%s argument to '%s' must be '%s'" % (
                        utils.ordinal(pos).capitalize(), self.name, name,
                    )
                    raise template.TemplateSyntaxError(err_msg)
            else:
                self._set_var(arg, raw_arg, parser)

    def _process_keyword_args(self, parser):
        while self._raw_args:
            keyword = self._raw_args.pop(0)
            try:
                arg = self._keyword_args[keyword]
            except KeyError:
                err_msg = "'%s' does not take argument '%s'" % (
                    self.name, keyword,
                )
                raise template.TemplateSyntaxError(err_msg)
            if arg.flag:
                self._set_var(arg, True, parser)
                continue
            try:
                value = self._raw_args.pop(0)
            except IndexError:
                err_msg = "'%s' argument to '%s' missing value" % (
                    keyword,
                    self.name,
                )
                raise template.TemplateSyntaxError(err_msg)
            self._set_var(arg, value, parser)
        # handle missing items: required, default, flag
        for keyword, arg in self._keyword_args.iteritems():
            if arg.name in self._vars:
                continue
            if arg.flag:
                self._set_var(arg, False, parser)
                continue
            if arg.required:
                err_msg = "'%s' argument to '%s' is required" % (
                    keyword, self.name,
                )
                raise template.TemplateSyntaxError(err_msg)
            self._set_var(arg, arg.default, parser)

    def _compile_filter(self, arg, value, parser):
        if not arg.resolve:
            return value
        return template.FilterExpression(value, parser)

    def _set_var(self, arg, value, parser):
        if value and isinstance(value, (list, tuple)):
            value = [self._compile_filter(arg, v, parser) for v in value]
        elif isinstance(value, basestring):
            value = self._compile_filter(arg, value, parser)
        else:
            if not isinstance(value, FilterExpression):
                raise TemplateSyntaxError('Could not compile argument value.')
        self._vars[arg.name] = value

    def clean(self, data):
        """
        Additional tag-wide argument cleaning after each individual Arg's
        ``clean`` has been called.
        """
        return data

    def render(self, context):
        raise NotImplementedError(
            "TemplateTag subclasses must implement this method."
        )

    def _resolve_single(self, context, value):
        if isinstance(value, template.FilterExpression):
            if isinstance(value.var, template.Variable):
                # we *want* VariableDoesNotExist to get raised, but
                # FilterExpression normally swallows it, so we first resolve
                # the encapsulated Variable directly
                try:
                    value.var.resolve(context)
                except template.VariableDoesNotExist, exc:
                    exc.var = value.var.var
                    raise
            # resolve the FilterExpression as normal
            value = value.resolve(context)
        elif isinstance(value, template.Variable):
            value = value.resolve(context)
        return value

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
        for k, v in self._vars.iteritems():
            if isinstance(v, (list, tuple)):
                v = [self._resolve_single(context, x) for x in v]
            else:
                v = self._resolve_single(context, v)
            arg = self._args[k]
            v = arg.base_clean(v)
            try:
                tag_arg_clean = getattr(self, 'clean_%s' % arg.name)
            except AttributeError:
                pass
            else:
                v = tag_arg_clean(v)
            data[k] = v
        data = self.clean(data)
        return data
