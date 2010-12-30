===========
django-ttag
===========

TTag is a template tag constructor library for Django created for the purpose
of making writing template tags easier.

The tag syntax is modelled on Django's friendly syntaxes for models and forms.
Here is a full example tag::

    class Welcome(ttag.Tag)
        user = ttag.Arg(positional=True)
        fallback = ttag.Arg(default='Hi!')

        def output(self, data)
            name = data['user'].get_full_name()
            if name:
            	return 'Hi, %s!' % name
            return data['fallback']

This would produce a tag named ``welcome`` which can be used like this::

    {% welcome current_user fallback "Hello, anonymous." %} 

More comprehensive usage and reference documentation can be found in the
``docs`` directory, or at http://packages.python.org/django-ttag/.