from ttag.args import Arg, BasicArg, BooleanArg, ConstantArg, DateArg, \
    DateTimeArg, IntegerArg, IsInstanceArg, KeywordsArg, ModelInstanceArg, \
    StringArg, TimeArg
from ttag.core import Tag
from ttag.exceptions import TagArgumentMissing, TagValidationError

VERSION = (1, 0, 'alpha')


def get_version(number_only=False):
    version = [str(VERSION[0])]
    number = True
    for bit in VERSION[1:]:
        if not isinstance(bit, int):
            if number_only:
                break
            number = False
        version.append(number and '.' or '-')
        version.append(str(bit))
    return ''.join(version)
