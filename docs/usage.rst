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

By default, arguments are positional, meaning that they must appear in the
tag in the order they are defined in your tag class.

Here is an example of using arguments to extend the basic ``{% welcome %}``
example tag above so we can greet the user personally::

    class Welcome(ttag.Tag):
        user = ttag.Arg()

        def output(self, data):
            name = data['user'].get_full_name()
            return "Hi, %s!" % name

The tag would then be used like: ``{% welcome user %}``

Arguments are usually resolved against the template context. For simpler cases
where you don't want this behaviour, use :class:`ttag.BasicArg`.

Sometimes, the argument name you want to use is a Python keyword and can't be
used as a class attribute (such as ``with``, ``as``, ``and``, etc.). In these
cases append an underscore::

    class Format(ttag.Tag):
        as_ = ttag.Arg()

This is only used during the definition; the argument name is stored without
(and therefore should be referenced without) this trailing underscore.

Named arguments
---------------

Arguments can alternatively be marked as a named argument. In these cases
the argument name is part of the tag definition in the template.

Named arguments can be defined in the template tag in any order.

Here are a few examples of named arguments::

    * ``{% slap with fish %}`` has an argument named ``with``.
    * ``{% show_people country "NZ" limit 10 %}`` has two named arguments,
      ``country`` and ``limit``. They could potentially be marked as optional
      and can be listed in any order.
    * ``{% show_countries populated_only %} has a boolean argument,
      demonstrating that an argument may not always take a single value.
      Boolean arguments take no values, and a special argument type could take
      more than one value (for example, :class:`ttag.KeywordsArg`).

Space separated arguments
~~~~~~~~~~~~~~~~~~~~~~~~~

The first named argument format looks like ``[argument name] [value]``, for
example:

Here's an example of what the ``{% slap %}`` tag above may look like::

    class Slap(ttag.Tag):
        with_ = ttag.Arg(named=True)

        def output(self, data):
            return "You have been slapped with a %s" % data['with']

Keyword arguments
~~~~~~~~~~~~~~~~~

An alternate named argument format is to use keyword arguments::

    class Output(ttag.Tag):
        list_ = self.Arg()
        limit = self.Arg(keyword=True)
        offset = self.Arg(keyword=True)

This would result in a tag which can be used like this::

    {% output people limit=10 offset=report.offset %}

.. note::

    If your tag should define a list of arbitrary keywords, you may benefit
    from :class:`ttag.KeywordsArg` instead.

Validation arguments
--------------------

Some default classes are included to assist with validation of template
arguments.

.. todo::

   define arguments and show an example


Using context
=============

The :meth:`~ttag.Tag.output` method which we have used so far is just a
shortcut the :meth:`~ttag.Tag.render`.

The shortcut method doesn't provide direct access to the context, so if you
need alter the context, or check other context variables, you can use
:meth:`~ttag.Tag.render` directly.

.. note:: The :class:`ttag.helpers.AsTag` class is available for the common
          case of tags that end in ``... as something %}``. 

For example::

    class GetHost(ttag.Tag):
        """
        Returns the current host. Requires that ``request`` is on the template
        context.
        """

        def render(self, context):
            print context['request'].get_host()

Use :meth:`~ttag.Tag.resolve` to resolve the tag's arguments into a data
dictionary::

    class Welcome(ttag.Tag):
        user = ttag.Arg()

        def render(self, context):
            context['welcomed'] = True
            data = self.resolve(context)
            name = data['user'].get_full_name()
            return "Hi, %s!" % name


Cleaning arguments
==================

You can validate / clean arguments similar to Django's forms.

To clean an individual argument, use a ``clean_[argname](value)`` method.
Ensure that your method returns the cleaned value.

After the individual arguments are cleaned, a ``clean(data, context)`` method
is run. This method must return the cleaned data dictionary.

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
            super(AdvancedTag, self).__init__(parser, token)
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
        instance = ttag.ModelInstanceArg(model=NamedModel)
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
