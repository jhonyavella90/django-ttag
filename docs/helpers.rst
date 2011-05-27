=======
Helpers
=======

AsTag
=====

.. currentmodule:: ttag.helpers

.. class:: AsTag

    Assists with the common case of tags which want to add something to the
    context.

    For example, if you wanted a tag which would add a QuerySet containing a
    user's friends to the context (``{% get_friends user as friends %}``)::

        class GetName(ttag.helpers.AsTag)
            user = ttag.Arg()

            def output(self, data, context):
                return data['user'].friends_set.all()

    Some additional customization attributes to those which are provided in the
    standard ``Tag``'s :attr:`~ttag.Tag.Meta` class are available:

    .. class:: Meta

        .. attribute:: as_name

            Use some other argument name rather than the default of ``as``.

        .. attribute:: as_required
        
            Set whether or not ``as varname`` argument is required
            (defaults to ``True``).

    Two additional methods of interest are ``as_value``, which allows you to
    more completely customise output.

    .. method:: as_value(self, data, context)
        
        Returns the value you want to put into the context variable.
        By default, returns the value of :meth:`~ttag.Tag.output`.

    .. method::  as_output(self, data, context)

        Returns the data you want to render when ``as varname`` is used.
        Defaults to ``''``.
