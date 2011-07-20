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


TemplateTag
===========

.. currentmodule:: ttag.helpers

.. class:: TemplateTag

    Allows creating a template tag whose output is rendered with a template.

    For example, if you wanted a tag which would render a QuerySet containing
    a user's friends with a specific template
    (``{% render_friends user with "friend_list.html" %}``)::

        class RenderFriends(ttag.helpers.TemplateTag)
            user = ttag.Arg()

            def output(self, data):
                return data['user'].friends_set.all()

    the template ``friend_list.html`` would automatically be passed the
    data and output variables as well as the rest of the context in which
    the template tag was called in::

        <h3>Friends of {{ data.user }} for {{ user }}</h3>
        <ul>
        {% for friend in output %}
            <li>{{ friend.username }}</li>
        {% endfor %}
        </ul>

    Some additional customization attributes to those which are provided in the
    standard ``Tag``'s :attr:`~ttag.Tag.Meta` class are available:

    .. class:: Meta

        .. attribute:: template_name

            Use some other argument name rather than the default of ``with``.

        .. attribute:: template_required

            Set whether or not ``with template`` argument is required
            (defaults to ``True``).

            In case ``template_required`` is set to ``False`` and you don't
            specify a specific template, ttag will automatically construct the
            template path to render the template tag's output like this:
            ``ttag/<lowercase module name>/<lowercase template tag name>.html``

            For example, if the above template tag can be found in the
            ``friends_tags`` template tag library, it could be called with
            ``{% render_friends user %}``) and a template with the name
            ``'ttag/friends_tags/render_friends.html'``.

