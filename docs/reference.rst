=========
Reference
=========


Overview
========

TTag replaces the normal method of creating custom template tags.  It
uses a custom template ``Node`` subclass called ``Tag`` which handles all of
the relevant aspects of a tag: defining and parsing arguments, handling
validation, resolving variables from the context, and rendering output.


Tag
===

.. class:: ttag.Tag

    A representation of a template tag. For example::

	    class Welcome(ttag.Tag):
	
	        def output(self, data):
	            return "Hi there!"

Meta options
------------

A ``Tag`` can take options via a ``Meta`` inner class::

    class Welcome(ttag.Tag):

        class Meta:
            name = "hi"

.. attribute:: ~ttag.Tag.Meta.name

    Explicitly choose a name for the tag. If not given, the tag's name will be
	created by taking the class's name and converting it from CamelCase to
	under_score format. For example, ``AmazingStuff`` would turn into
	``{% amazing_stuff %}``.

.. attribute:: ~ttag.Tag.Meta.register

    Register the tag in a tag library.
    
    Alternatively, a tag can still be rendered the standard way:
    ``some_library.tag(ThisTag)``.

.. attribute:: ~ttag.Tag.Meta.block

    Retrieve subsequent template nodes until ``{% end[tagname] %}``, adding
    them to ``self.nodelists``.

.. attribute:: ~ttag.Tag.Meta.end_block

    An alternative ending block node. Defaults to ``'end%(name)s'``.

output
------

If your tag does not modify the output, override this method to change the
output of this tag. 

.. method:: .output(self, data)

    :param data: A dictionary of data built from the arguments this tag uses,
    	usually built by the :meth:`resolve` method.

render
------

As an alternative to overriding the ``output`` method, a ``TemplateTag``
subclass may directly override the ``render`` method. This is useful for
when you want to alter the context.

.. method:: .render(self, context)

	:param context: The current template context.

    ``render`` must return a unicode string.

    If your tag doesn't return anything (e.g., it only manipulates the
    context), ``render`` should simply return an empty string.

To retrieve the values of the tag's arguments, if any, use the following method
inside ``render``::

.. method:: .resolve(self, context)

	Retrieve the values of the tag's arguments.
	
	:param context: The current template context.
	:returns: A data dictionary containing the values of the tag's arguments.


Arguments
=========

Arguments can be either positional or named. They are specified as properties
of the tag class, in a similar way to Django's forms and models.

If the property name clashes with a append a trailing slash - it will be
removed from the argument's ``name``. For example, pay attention to the ``as_``
argument in the tag below::

    class SetTag(ttag.Tag):
        value = ttag.Arg(positional=True)
        as_ = ttag.BasicArg()
        
        def render(self, context):
            data = self.resolve(context)
            as_var = data['as']
            context[as_var] = data['value']
            return ''

Positional arguments
--------------------

An argument may be marked as positional by using the ``positional`` flag::  

    class PositionalTag(ttag.Tag):
        first = ttag.Arg(positional=True)
        second = ttag.Arg(positional=True)

This would result in a tag named ``positional`` which took two required
arguments, which would be assigned to ``'first'`` and ``'second'`` items
of the data dictionary returned by the ``resolve`` method.

Use the ``ConstantArg`` for simple required string-based arguments which assist
readability (this Arg assumes ``positional=True``)::

    class MeasureTag(ttag.Tag):
        start = ttag.Arg(positional=True)
        to = ttag.ConstantArg()
        finish = ttag.Arg(positional=True)

Named arguments
---------------

Named arguments can appear in any order in a tag's arguments, after the
positional arguments.  They are specified as follows::

    class NamedTag(ttag.Tag):
        limit = ttag.Arg(required=False)
        offset = ttag.Arg(required=False)

This would create a tag named ``named`` which took two optional arguments,
``limit`` and ``offset``.  They could be specified in any order::

    {% named %}

    {% named limit 10 %}

    {% named offset 25 %}

    {% named limit 15 offset 42 %}

    {% named offset 4 limit 12 %}

If you prefer "keyword" style named arguments (e.g. ``{% named offset=25 %},
you can use the ``keyword`` parameter::

    class NamedTag(ttag.Tag):
        limit = ttag.Arg(required=False, keyword=True)
        offset = ttag.Arg(required=False, keyword=True)

If an optional argument is not specified in the template, it will not be
added to the data dictionary. Alternately, use ``default`` to have a default
value added to the data dictionary if an argument is not provided::

    class NamedTag(ttag.Tag):
        limit = ttag.Arg(default=100)
        offset = ttag.Arg(required=False)


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

Defaults to ``True``.

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

keyword
~~~~~~~

Use an equals to separate the value from the argument name, rather than the
standard space separation.

This parameter is only used for named arguments (i.e. ``positional=False``).

Defaults to ``False``.


BasicArg
--------

A simpler argument which doesn't compile its value as a ``FilterExpression``.

Example usage::

    class GetUsers(ttag.Tag)
        as_ = ttag.BasicArg()

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

    class CoolTag(ttag.Tag)
        cool = ttag.BooleanArg()

        def output(self, data):
            if 'cool' in data:
                return "That's cool!"
            else:
                return "Uncool."


IsInstanceArg
-------------

Validates that the argument is an instance of the provided class (``cls``),
otherwise throws a a template error, using the ``cls_name`` in the error
message.

	date = IsInstanceArg(cls=datetime.date, cls_name=_('Date'))


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


KeywordsArg
-----------

Parses one or more additional tokens as keywords.

Use ``compact`` and ``verbose`` boolean parameters to control the keyword
argument format. The default format is compact::

    {% compact with foo=1 bar=2 %}

Setting ``verbose=True`` and ``compact=False`` will require verbose format:

	{% verbose with 1 as foo and 2 as bar %}

If ``verbose=True`` and ``compact`` is left as ``True``, then either (or even
both) formats are allowed. This is usually only used for backwards
compatibility::

    {% mixed with foo=1 bar=2 %}
    {% mixed with 1 as foo and 2 as bar %}
    {% mixed with foo=1 and 2 as bar %}

In verbose mode, the ``and`` is required for multiple arguments, in mixed
mode it is optional, and in compact mode it is obviously not used.

Use the ``compile_values`` parameter to compile keyword values as template
variables (defaults to ``True``).
