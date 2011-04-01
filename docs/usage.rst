=====
Usage
=====


``Tag`` and the various ``Arg`` classes are consciously modelled after
Django's ``Model``, ``Form``, and respective ``Field`` classes.

``Arg`` properties are set on a ``Tag`` in the same way ``Field`` properties
are set on a ``Model`` or ``Form``.


Example
=======

Following is a minimal example of a template tag::

    class Welcome(ttag.Tag):

        def output(self, data):
            return "Hi there!"

This would create a tag ``{% welcome %}`` which took no arguments and output
``Hi there!``.


Registering your tag
--------------------

TTag ``Tag`` classes are registered just like a standard tag::

    from django import template
    import ttag

    register = template.Library()


    class Welcome(ttag.Tag):

        def output(self, data):
            return "Hi there!"


    register.tag(Welcome)


Tag name
--------

The name of the tag is automatically based off of the class name, but this can
be explicitly specified by using an inner :class:`~ttag.Tag.Meta` class::

    class Welcome(ttag.Tag):

        class Meta:
            name = "hi"

        def output(self, data):
            return "Hi there!"

This would create a tag ``{% hi %}``, rather than ``{% welcome %}``.


Defining arguments
==================

The standard argument format is ``[argument name] [value]``, for example:

    * ``{% get_people as something %}`` has an argument named ``as``.
    * ``{% show_people country "NZ" limit 10 %}`` has two arguments,
      ``country`` and ``limit``. They could potentially be marked as optional
      and can be listed in any order)
    * ``{% show_countries populated_only %} has a boolean argument,
      demonstrating that an argument may not always take a single value.
      Boolean arguments take no values, and a special argument type could take
      more than one value (for example, :class:`ttag.KeywordsArg`).

Arguments are usually resolved against the template context. For simpler cases,
you can use :class:`ttag.BasicArg`.

Here's an example of how the ``{% get_people %}`` tag may look like::

    class GetPeople(ttag.Tag):
        as_ = ttag.BasicArg()

        def render(self, context):
            data = self.resolve(context)
            context[data['as']] = People.objects.all()
            return ''

Note that since ``as`` is a Python keyword, we're appending an underscore.
This is only used during the definition; the argument name can be referenced
with (and is stored with) this underscore stripped.

A helper tag is available for this common 'as context_var' pattern named
:class:`ttag.AsTag`.


Positional arguments
--------------------

When you don't want the argument name as part of the tag definition, you can
make the argument positional. The order of positional arguments defined in your
class is the order they will be consumed.

Here is an example of a positional argument used to extend the basic
``{% welcome %}`` example tag above so we can greet the user personally::

    class Welcome(ttag.Tag):
        user = ttag.Arg(positional=True)

        def output(self, data):
            name = data['user'].get_full_name()
            return "Hi, %s!" % name

The tag now has one positional tag which will be used to get the user from the
template context.

Keyword argument format
-----------------------

When using several named arguments, space-separated named arguments can start
to look a bit confusing. For these cases, you may want to use the named keyword
argument format (``name=value``)::

    class Output(ttag.Tag):
        limit = self.Arg(keyword=True)
        offset = self.Arg(keyword=True)

This would result in a tag which can be used like this::

    {% output limit=some_limit|default:1 offset=profile.offset %}

.. note::

    If your tag should define a list of arbitrary keywords, you may benefit
    from :class:`ttag.KeywordsArg` instead.

Validation arguments
--------------------

Some default classes are included to assist with validation of template
arguments.

.. todo::

   define arguments and show an example


Altering context
================

.. todo::

   explain that output() is a ust shortcut and that render() can be used
   (with resolve()).

   Perhaps use the common 'as var' as the example.


Cleaning arguments
==================

.. todo::

   You can validate / clean arguments similar to Forms.

   ``clean_[argname](value)`` (must return the cleaned value)

   ``clean(data)`` (must returned the cleaned data dictionary)

   Use the ``ttag.TagValidationError`` exception to raise validation errors.


Writing a block tag
===================

For simple block tags, use the :attr:`~ttag.Tag.Meta.block` option::

    class Repeat(ttag.Tag):
        count = ttag.IntegerArg()

        class Meta():
            block = True
            end_block = 'done'

        def render(self, context):
            data = self.resolve(context)
            output = []
            for i in range(data['count']):
                context.push()
                output.append(self.nodelist.render(context))
                context.pop()
            return ''.join(output)

As you can see, using the block option will add a ``nodelist`` attribute to the
tag, which can then be rendered using the context.

The optional ``end_block`` option allows for an alternate ending block. The
default value is ``'end%(name)s'``, so it would be ``{% endrepeat %}`` for the
above tag if the option hadn't been provided.


Working with multiple blocks
----------------------------

Say we wanted to expand on our repeat tag to look for an ``{% empty %}``
alternative section for when a zero-value count is received.

Rather than setting the ``block`` option to ``True``, we set it to a dictionary
where the keys are the section tags to look for and the values are whether the
section is required::

    class Repeat(ttag.Tag):
        count = ttag.IntegerArg()

        class Meta():
            block = {'empty': False}

        def render(self, context):
            data = self.resolve(context)
            if not data['count']:
                return self.nodelist_empty.render(context)
            output = []
            for i in range(data['count']):
                context.push()
                output.append(self.nodelist.render(context))
                context.pop()
            return ''.join(output)

This will cause two attributes to be added to the tag: ``nodelist`` will
contain everything collected up to the ``{% empty %}`` section tag, and
``nodelist_empty`` will contain everything up until the end tag.

If no matching section tag is found when parsing the template,
either a ``TemplateSyntaxError`` will be raised (if it's a required section)
or an empty node list will be used.

More advanced cases can be handled using Django's standard parser in the
``__init__`` method of your tag::

    class AdvancedTag(ttags.Tag):

        def __init__(self, parser, token):
            super(Repeat, self).__init__(parser, token)
            # Do whatever fancy parser modification you like.


Full Example
============

This example provides a template tag which outputs a tweaked version of the
instance name passed in.  It demonstrates using the various ``Arg`` types::

    class TweakName(ttag.Tag):
        """
        Provides the tweak_name template tag, which outputs a
        slightly modified version of the NamedModel instance passed in.

        {% tweak_name instance [offset=0] [limit=10] [reverse] %}
        """
        instance = ttag.ModelInstanceArg(positional=True, model=NamedModel))
        offset = ttag.IntegerArg(default=0, keyword=True)
        limit = ttag.IntegerArg(default=10, keyword=True)
        reverse = ttag.BooleanArg()

		def clean_limit(self, value):
            """
            Check that limit is not negative.
            """
            if value < 0:
                raise ttag.TagValidationError("limit must be >= 0")
            return value

        def output(self, data):
            name = data['instance'].name

            # Reverse if appropriate.
            if 'reverse' in data:
                name = name[::-1]

            # Apply our offset and limit.
            name = name[data['offset']:data['offset'] + data['limit']]

            # Return the tweaked name.
            return name

Example usages::

    {% tweak_name obj limit=5 %}

    {% tweak_name obj offset=1 %}

    {% tweak_name obj reverse %}

    {% tweak_name obj offset=1 limit=5 reverse %}
