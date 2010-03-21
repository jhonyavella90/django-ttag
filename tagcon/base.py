"""
tagcon: a template tag constructor library for Django

Based on the syntax and implementation of Django's Model and Form classes.
"""
import sys
import weakref

from django import template
from django.conf import settings

from tagcon.args import Arg
from tagcon.exceptions import TemplateTagValidationError, TemplateTagArgumentMissing
from tagcon.utils import smarter_split, get_tag_name, verbose_quantity, unroll_render

__all__ = (
    'TemplateTag',
)

class Arguments(dict):
    def __getattr__(self, name):
        if name.endswith('_'):
            name = name.rstrip('_')
        return self[name]

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            err_msg = "'%s' (Did you forget" \
            " to call '.resolve(context)'?)" % (key,)
            raise TemplateTagArgumentMissing(err_msg)


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
            return unroll_render(unwrapped_render(self, context))
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
        try:
            library = meta.library
        except AttributeError:
            # try auto-lookup
            module = sys.modules[attrs['__module__']]
            library = getattr(module, 'register', None)
        if not isinstance(library, template.Library):
            raise TypeError("A valid library is required.")

        # use supplied name, or generate one from class name
        tag_name = getattr(meta, 'name', get_tag_name(name))
        attrs['name'] = tag_name

        attrs['silence_errors'] = getattr(meta, 'silence_errors', False)

        attrs['block'] = getattr(meta, 'block', False)

        # wrap render so it can optionally yield strings as a generator, and so
        # we can catch exceptions if necessary
        unwrapped_render = attrs.pop('render')
        attrs['render'] = _wrap_render(unwrapped_render)

        # positional tag arguments
        positional_args = attrs.pop('_', ())
        # shortcut for single-arg case
        if isinstance(positional_args, Arg):
            positional_args = (positional_args,)
        else:
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
                        "positional args must be Arg instances or strings"
                    )
                elif not arg:
                    raise ValueError("Empty strings are not valid arguments.")
        attrs['_positional_args'] = positional_args
        all_args = dict(
            (arg.name, arg) for arg in positional_args if isinstance(arg, Arg)
        )

        # keyword tag arguments
        keyword_args = {}
        # can't use iteritems, since we mutate attrs
        keys = attrs.keys()
        for key in keys:
            value = attrs[key]
            if not isinstance(value, Arg):
                continue
            del attrs[key]
            if key.endswith('_'):
                # hack for reserved names, e.g., "for_" -> "for"; the tag's
                # .args object understands this, too
                key = key.rstrip('_')
            value.keyword = key
            if not value.name:
                value.name = key
            keyword_args[key] = value
            all_args[value.name] = value
        # _keyword_args is keyed by *keyword*
        attrs['_keyword_args'] = keyword_args
        # _args and _positional_args are keyed by *arg/var name*
        attrs['_args'] = all_args

        # create the new class
        new_class = super_new(cls, name, bases, attrs)

        # register the tag
        library.tag(tag_name, new_class)

        return new_class


class TemplateTag(template.Node):
    """
    A template tag.
    """
    __metaclass__ = TemplateTagBase

    def __init__(self, parser, token):
        # don't keep the parser alive
        self.parser = weakref.proxy(parser)
        self.args = Arguments()
        self._vars = {}
        self._raw_args = list(smarter_split(token.contents))[1:]
        # self._raw_args = token.split_contents()[1:]
        self._process_positional_args()
        self._process_keyword_args()
        if self.block:
            self.nodelist = parser.parse(('end%s' % (self.name,),))
            parser.delete_first_token()

    def _process_positional_args(self):
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
                    verbose_quantity('argument', self._positional_args),
                )
                raise template.TemplateSyntaxError(err_msg)
            if isinstance(arg, basestring):
                if raw_arg != arg:
                    err_msg = "%s argument to '%s' must be '%s'" % (
                        _ordinal(pos).capitalize(), self.name, name,
                    )
                    raise template.TemplateSyntaxError(err_msg)
            else:
                self._set_var(arg, raw_arg)

    def _process_keyword_args(self):
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
                self._set_var(arg, True)
                continue
            try:
                value = self._raw_args.pop(0)
            except IndexError:
                err_msg = "'%s' argument to '%s' missing value" % (
                    keyword,
                    self.name,
                )
                raise template.TemplateSyntaxError(err_msg)
            self._set_var(arg, value)
        # handle missing items: required, default, flag
        for keyword, arg in self._keyword_args.iteritems():
            if arg.name in self._vars:
                continue
            if arg.flag:
                self._set_var(arg, False)
                continue
            if arg.required:
                err_msg = "'%s' argument to '%s' is required" % (
                    keyword, self.name,
                )
                raise template.TemplateSyntaxError(err_msg)
            self._set_var(arg, arg.default)

    def _compile_filter(self, arg, value):
        fe = template.FilterExpression(value, self.parser)
        if not arg.resolve and fe.var.lookups:
            fe.var.lookups = None
            fe.var.literal = fe.var.var
        return fe

    def _set_var(self, arg, value):
        if value and isinstance(value, (list, tuple)):
            self._vars[arg.name] = [
                self._compile_filter(arg, v) for v in value
            ]
            return
        if not isinstance(value, basestring):
            # non-string default value; short-circuit as FilterExpression can
            # only handle strings
            self._vars[arg.name] = value
            return
        self._vars[arg.name] = self._compile_filter(arg, value)

    def clean(self):
        """
        Additional tag-wide argument cleaning after each individual Arg's
        ``clean`` has been called.
        """
        return

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
        Resolve variables and run clean methods.

        Cleaning happens after variable/filter resolution.

        Cleaning order is similar to forms:

        1) The argument's ``.clean()`` method.
        2) The tag's ``clean_ARGNAME()`` method, if any.
        3) The tag's ``.clean()`` method.
        """
        for k, v in self._vars.iteritems():
            if isinstance(v, (list, tuple)):
                v = [self._resolve_single(context, x) for x in v]
            else:
                v = self._resolve_single(context, v)
            arg = self._args[k]
            v = arg.base_clean(v)
            try:
                tag_arg_clean = getattr(self, 'clean_%s' % (arg.name,))
            except AttributeError:
                pass
            else:
                v = tag_arg_clean(v)
            self.args[k] = v
        self.clean()
