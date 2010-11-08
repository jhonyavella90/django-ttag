import re

from django.utils.encoding import force_unicode

_split_single = r"""
    ([^\s",]*"(?:[^"\\]*(?:\\.[^"\\]*)*)"[^\s,]*|
     [^\s',]*'(?:[^'\\]*(?:\\.[^'\\]*)*)'[^\s,]*|
     [^\s,]+)
"""
_split_multi = r"""%s(?:\s*,\s*%s)*""" % (_split_single, _split_single)
_split_single_re = re.compile(_split_single, re.VERBOSE)
_split_multi_re = re.compile(_split_multi, re.VERBOSE)

def smarter_split(input):
    input = force_unicode(input)
    for multi_match in _split_multi_re.finditer(input):
        hit = []
        for single_match in _split_single_re.finditer(multi_match.group(0)):
            hit.append(single_match.group(0))
        if len(hit) == 1:
            yield hit[0]
        else:
            yield hit


CLASS_NAME_RE = re.compile(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))')
def get_tag_name(class_name):
    name = CLASS_NAME_RE.sub(r'_\1', class_name).lower().strip('_')
    if name.endswith('_tag'):
        name = name[:-4]
    return name


def cardinal(n):
    """
    Return the cardinal number for an integer.

    Returns words (e.g., "one") for 0 through 10; returns digits for numbers
    greater than 10.

    TODO: check usage guide to decide if 9 or 10 should be the cutoff.
    """
    n = int(n)
    if n < 0:
        raise ValueError("Argument must be >= 0")
    try:
        return (u'zero', u'one', u'two', u'three', u'four', u'five',
                u'six', u'seven', u'eight', u'nine', u'ten')[n]
    except IndexError:
        return unicode(n)


def ordinal(n):
    """
    Return the ordinal number for an integer.

    Differs from the humanize version as it returns full words (e.g., "first")
    for 1 through 9, and does not work for numbers less than 1.
    """
    n = int(n)
    if n < 1:
        raise ValueError("Argument must be >= 1")
    try:
        return (u'first', u'second', u'third', u'fourth', u'fifth', u'sixth',
                u'seventh', u'eighth', u'ninth')[n-1]
    except IndexError:
        t = ('th', 'st', 'nd', 'rd') + (('th',) * 6)
        if n % 100 in (11, 12, 13):
            return u"%d%s" % (n, t[0])
        return u'%d%s' % (n, t[n % 10])


def pluralize(singular, quantity, suffix='s'):
    if quantity == 1:
        return singular
    return '%s%s' % (singular, suffix)


def verbose_quantity(singular, quantity, suffix='s'):
    try:
        quantity = int(quantity)
    except TypeError:
        try:
            quantity = len(quantity)
        except TypeError:
            raise TypeError("Quantity must be an integer or sequence.")
    return '%s %s' % (
        cardinal(quantity),
        pluralize(singular, quantity, suffix=suffix),
    )

def unroll_render(s):
    if s is None:
        err_msg = "'render' must return a string or an iterable (got None)"
        raise TypeError(err_msg)
    if isinstance(s, basestring):
        return s
    return ''.join(unicode(piece) for piece in s)


