=============
django-tagcon
=============

Django-Tagcon is a template tag constructor library for Django.  It supports a
range of features to make writing template tags easier:

- Syntax modeled on Django's friendly syntaxes for models and forms

- Standardized argument handling -- never write tag boilerplate again!

- Positional and optional arguments

- Required arguments and argument defaults

- Comma-separated sequence arguments (e.g., ``1, 2, 3``)

- Flag arguments (that take no value)

- Argument validation support (``clean`` methods similar to forms)

- Automatic tag naming based on the class name (with optional override)

- Automatic tag registration with the module's ``register`` Library

- Easy resolution of context variable arguments, including filters

- Support for yielding strings from the ``render`` method


Requirements
============

Django-Tagcon requires Python 2.5 and the latest formal release of Django
(1.1.1, at the time of writing).

The library is actually developed against The Onion's internal Django branch,
which is based upon Django's Subversion trunk; even so, the author considers it
a bug if something doesn't work in the latest formal Django release.  (Tests,
once written, should help enforce this.)


Installation
============

Just drop ``tagcon.py`` somewhere on Python's module path.


Example
=======

A simple example with a single optional argument::

    from django import template
    from django.contrib.auth.models import User
    import tagcon

    register = template.Library()

    class UserListTag(tagcon.TemplateTag):
        limit = tagcon.IntegerArg(default=10)

        def output(self, data):
            yield "<ul>"
            for user in User.objects.all()[:data['limit']]:
                yield "<li>%s</li>" % user.username
            yield "</ul>"

And then, in a template (after loading the library)::

    {% user_list %}

or::

    {% user_list limit 20 %}


History
=======

The idea for a new, less painfully verbose and more consistent template tag
syntax for Django came up a few years ago at the Lawrence Journal-World, where
the author first implemented what he then called "newtags".  Newtags was a
modification of the template-handling code in LJW's internal Django branch; the
syntax was modeled somewhat after Django's model syntax, as this seemed like a
natural fit.  As this was the Dark Age around Django 0.91, the implementation
was eventually abandoned and became impossibly out of sync with upstream
Django.

A few years later the author found himself at The Onion, helping to expand and
manage a Django-based library that included an increasing number of template
tags.  He decided to again write a library for easier template tag construction
-- but this time based upon modern Django, and implemented as a separate
library.


To-Do
=====

Lots, including documentation and proper tests.  (We *are* using this code in
production at The Onion, though, for what that's worth.)  Unlike most other
tools that I've worked on over time and never released for want of polishing, I
figured it was better to just push it out first and polish later.

In particular, I'm not entirely comfortable with the underscore syntax to
denote positional arguments; I'm open to better ideas there.


Contributing
============

Just fork, hack, and point me to the branch (preferably on GitHub); if it looks
good, I'll gladly pull it in.

There's more information in the "Contributing" document regarding submissions
and style.  In particular, contributions *must* be in a Git repository I can
pull from; I don't accept patch files.


Contact
=======

- Tom X. Tobin <tomxtobin@tomxtobin.com>
- "tomxtobin" on GitHub
