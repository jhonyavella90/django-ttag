==============
TTag reference
==============


Overview
========

TTag replaces the normal method of creating custom template tags.  It
uses a custom template ``Node`` subclass called ``Tag`` which handles all of
the relevant aspects of a tag: defining and parsing arguments, handling
validation, resolving variables from the context, and rendering output.  It
tries to make the most common cases extremely simple, while making even complex
cases easier than they would be otherwise.

``TemplateTag`` and the various ``Arg`` classes are consciously modelled after
Django's ``Model``, ``Form``, and respective ``Field`` classes.  ``Arg``s are
set on a ``TemplateTag`` in the same way ``Field``s would be set on a
``Model`` or ``Form``.


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

Let's extend the basic example tag above to accept an argument so we can greet
the user personally::

    class Welcome(ttag.Tag):
    	user = ttag.Arg(positional=True)

        def output(self, data):
            name = data['user'].get_full_name()
            return "Hi, %s!" % name

The tag now has one positional tag which will be used to get the user from the
template context.

.. note::

    Arguments are usually resolved against the template context. For simpler
    cases, you can use :class:`ttag.BasicArg`.

Named arguments
---------------

The other standard argument type is a named argument.


Keyword argument format
~~~~~~~~~~~~~~~~~~~~~~~

When using several named arguments, space-separated named arguments can start
to look a bit confusing. For these cases, you may want to use the named keyword
argument format (``name=value``)::

    class Output(ttag.Tag):
        limit = self.Arg(keyword=True)
        offset = self.Arg(keyword=True)

This would result in a tag like this::

	{% output limit=some_limit|default:1 offset=profile.offset %}

.. note::

    If your tag should define a list of arbitrary keywords, you may benefit
    from :class:`ttag.KeywordsArg` instead.

Validation arguments
--------------------

Some default classes are included to assist with validation of template
arguments.

TODO: define arguments and show an example 


Altering context
================

TODO: explain that output() is a shortcut and that render() can be used
(with resolve())


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
            for i in data['count']:
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

Say we wanted to expand on our repeat tag to look for an {% empty %}
alternative section for when a zero-value count is received. 

    class Meta():
        block = {'empty': False}
        end_block = 'end%(name)s'

Rather than setting the ``block`` option to True, we set it to a dictionary
where the keys are the section tags to look for and the values are whether the
section is required. 

More advanced cases can be handled using Django's standard parser in the
``__init__`` method of your tag:

    class AdvancedTag(ttags.Tag):

		def __init__(self, parser, token):
			super(Repeat, self).__init__(parser, token)
			# Do whatever fancy parser modification you like.
