=======================
django-tagcon reference
=======================


Overview
========

Django-Tagcon replaces the normal method of creating custom template tags.  It
uses a custom template ``Node`` subclass, ``TemplateTag``, which handles all of
the relevant aspects of a tag: defining and parsing arguments, handling
validation, resolving variables from the context, and rendering output.  It
tries to make the most common cases extremely simple, while making even complex
cases easier than they would be otherwise.

``TemplateTag`` and the various ``Arg`` classes are consciously modeled after
Django's ``Model``, ``Form``, and respective ``Field`` classes.  ``Arg``s are
set on a ``TemplateTag`` in the same way ``Field``s would be set on a
``Model`` or ``Form``.


TemplateTag
===========

A minimal ``TemplateTag`` might look like this::

    from django import template
    import tagcon

    register = template.Library()


    class CustomTag(tagcon.TemplateTag):

        def output(self, data):
            return "Hi there!"

This would create a tag ``{% custom %}`` which took no arguments and output
``Hi there!``.  Tag naming is automatically based off of the class name, but
can be overridden (see the `Meta options`_ below).  The library can likewise
be explicitly specified, but in most cases automatically using the module's
``register`` library will do what is wanted anyway.


Meta options
------------

A ``TemplateTag`` can take various options via a ``Meta`` inner class::

    class FoobarTag(tagcon.TemplateTag):

        class Meta:
            name = "special"

        def output(self, data):
            return "Yes, I'm special."

This would create a tag ``{% special %}``, rather than ``{% foobar %}``.

The various ``Meta`` options follow.


name
~~~~

As shown above, ``name`` lets you explicitly choose a name for your tag.  If
``name`` is not given, the tag's name will be created by taking the class's
name and converting it from CamelCase to under_score format, with any trailing
``Tag`` in the class name ignored.  Thus ``KittyCatTag`` would become.
``{% kitty_cat %}``, and ``AmazingStuff`` would turn into
``{% amazing_stuff %}``.


library
~~~~~~~

Explicitly specify a tag library to register this tag with.  As long as the tag
is defined in a normal tag module with a ``register = template.Library()``
line, this shouldn't be necessary.

If the module doesn't contain a tag library named ``register`` and a library is
not explicitly specified, the tag can still be explicitly registered using the
standard library ``register`` method::

    my_tag_library.register(MyTag.name, MyTag) 

silence_errors
~~~~~~~~~~~~~~

Whether to ignore exceptions raised by the tag, returning the settings'
``TEMPLATE_STRING_IS_INVALID`` string or ``''``.  This is ``False`` by default
at the moment, although this may change.


output
------

If your tag does not modify the output, override this method to 

Either this method or the ``render`` method must be overridden on
``TemplateTag`` subclasses.

render
------

As an alternative to overriding the ``output`` method, a ``TemplateTag``
subclass may directly override the ``render`` method. This is useful for
when you want to alter the context.

This method takes a template ``context`` as a required argument.

``render`` must return a unicode string.
If your tag doesn't return anything (e.g., it only manipulates the context),
``render`` can simply return an empty string.

To retrieve the values of the tag's arguments, if any, use the following method
inside ``render``::

    data = self.resolve(context)

This will perform any context resolution if necessary, and return a data
dictionary containing the values of the tag's arguments.


Arguments
---------

Arguments can be either positional or keyword. They are specified as properties
of the tag class, in a similar way to Django's forms and models.

If the property name clashes with a append a trailing slash - it will be
removed from the argument's ``name``. For example, pay attention to the ``as_``
argument in the tag below::

    class SetTag(tagcon.TemplateTag):
        value = tagcon.Arg(positional=True)
        as_ = tagcon.BasicArg()
        
        def render(self, context):
            data = self.resolve(context)
            as_var = data['as']
            context[as_var] = data['value']
            return ''

Positional arguments
~~~~~~~~~~~~~~~~~~~~

An argument may be marked as positional by using the ``positional`` flag::  

    class PositionalTag(tagcon.TemplateTag):
        first = tagcon.Arg(positional=True)
        second = tagcon.Arg(positional=True)

This would result in a tag named ``positional`` which took two required
arguments, which would be assigned to ``'first'`` and ``'second'`` items
of the data dictionary returned by the ``resolve`` method.

Use the ``ConstantArg`` for simple required string-based arguments which assist
readability (this Arg assumes ``positional=True``)::

    class MeasureTag(tagcon.TemplateTag):
        start = tagcon.Arg(positional=True)
        to = tagcon.ConstantArg()
        finish = tagcon.Arg(positional=True)

Keyword arguments
~~~~~~~~~~~~~~~~~

Keyword arguments can appear in any order in a tag's arguments, after the
positional arguments.  They are specified as follows::

    class KeywordTag(tagcon.TemplateTag):
        limit = tagcon.Arg(required=False)
        offset = tagcon.Arg(required=False)

This would create a tag named ``keyword`` which took two optional arguments,
``limit`` and ``offset``.  They could be specified in any order::

    {% keyword %}

    {% keyword limit 10 %}

    {% keyword offset 25 %}

    {% keyword limit 15 offset 42 %}

    {% keyword offset 4 limit 12 %}

If an optional argument is not specified in the template, it will not be
added to the data dictionary. Alternately, use ``default`` to have a default
value added to the data dictionary if an argument is not provided::

    class KeywordTag(tagcon.TemplateTag):
        limit = tagcon.Arg(default=100)
        offset = tagcon.Arg(required=False)


Argument Types
==============

Arg and its subclasses provide various other levels of parsing and validation.


Arg
---

This is the base class for all other argument types.  Behavior can be defined
via the following constructor arguments.


required
~~~~~~~~

Whether the argument is required as part of the tag definition in the template.
Required positional arguments can not occur after optional ones. 

Defaults to ``False``.

default
~~~~~~~

The default value for this argument if it is not specified.

If ``None`` and the field is required, an exception will be raised when the
template is parsed.

Defaults to ``None``.

null
~~~~

Determines whether a value of ``None`` is an acceptable value for the argument
resolution.

When set to ``False``, a value of ``None`` or a missing context variable will
cause a ``TemplateTagValidationError`` when this argument is cleaned.

Defaults to ``False``.

positional
~~~~~~~~~~

Whether this is a positional tag (i.e. the argument name is not part of the tag
definition).  

Defaults to ``False``.


BasicArg
--------

A simpler argument which doesn't compile its value as a ``FilterExpression``.

Example usage::

    class GetUsersTag(tagcon.TemplateTag)
        as_ = tagcon.BasicArg()

        def render(self, context)
            data = self.resolve(data)
            context[data['as']] = Users.objects.all()
            return '' 


IntegerArg
----------

Validates that the argument is an integer, otherwise throws a template error.


StringArg
---------

Validates that the argument is a ``string`` instance, otherwise throws a
template error.


BooleanArg
----------

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


DateTimeArg
-----------

Validates that the argument is a ``datetime`` instance, otherwise throws a
template error.


DateArg
-------

Validates that the argument is a ``date`` instance, otherwise throws a template
error.


TimeArg
-------

Validates that the argument is a ``time`` instance, otherwise throws a template
error.


ModelInstanceArg
----------------

Validates that the passed in value is an instance of the specified ``Model``
class.  It takes a single additional named argument, ``model``.

model
~~~~~

The ``Model`` class you want to validate against.


Full Example
============

This example provides a template tag which outputs a tweaked version of the
instance name passed in.  It demonstrates using the various ``Arg`` types to
have tagcon do the hard work for you::

    class TweakName(tagcon.TemplateTag):
        """
        Provides the tweak_name template tag, which outputs a
        slightly modified version of the NamedModel instance passed in.

        {% tweak_name instance [offset=0] [limit=10] [reverse] %}
        """
		instance = tagcon.ModelInstanceArg(positional=True, model=NamedModel))
        offset = tagcon.IntegerArg(default=0)
        limit = tagcon.IntegerArg(default=10)
        reverse = tagcon.BooleanArg()

        def output(self, data):
            name = data['instance'].name

            # reverse if appropriate
            if 'reverse' in data:
                name = name[::-1]

            # check that limit is not < 0
            if data['limit'] < 0:
                raise tagcon.TemplateTagValidationError("limit must be >= 0")

            # apply our offset and limit
            name = name[data['offset']:data['limit']]

            # return the tweaked name
            return name

Example usages::

    {% tweak_name obj limit 5 %}

    {% tweak_name obj offset 1 %}

    {% tweak_name obj reverse %}

    {% tweak_name obj offset 1 limit 5 reverse %}
