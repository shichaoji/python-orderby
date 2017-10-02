"""
Main use-case: sort list of dictionaries. Better explanation to appear here.
TODO: repr() or str() -> back to parseable sql string :)
"""
import re
from operator import attrgetter, itemgetter
from functools import total_ordering


class Getter:
    ATTR_RE = re.compile('\$([\w\.]+)', flags=re.ASCII)

    def __init__(self, attr, desc=False):
        self.attr = attr
        self.desc = desc
        self.eval = '$' in attr

    def __call__(self, obj):
        try:
            if self.eval:
                value = eval(self.ATTR_RE.sub(r'itemgetter("\1")(obj)', self.attr))
            else:
                value = itemgetter(self.attr)(obj)
        except Exception:
            if self.eval:
                value = eval(self.ATTR_RE.sub(r'attrgetter("\1")(obj)', self.attr))
            else:
                value = attrgetter(self.attr)(obj)

        return Desc(value) if self.desc else value


@total_ordering
class Desc:
    """
    Helper class for reverse-comparing two objects.
    """

    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.obj)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            raise NotImplemented
        return self.obj > other.obj

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise NotImplemented
        return self.obj == other.obj


def orderby(qstring):
    """
    Factory function for creating OrderBy chain from SQL-like ORDER BY string

    Example: `orderby('age DESC, name')`

    :param qstring: SQL-like ORDER BY string
    :return: OrderBy() object to be used as key function
    """
    ret = OrderBy()
    for part in qstring.split(','):
        key, _, order = part.strip().partition(' ')
        key = key.strip()
        order = order.strip().lower()
        if not key:
            raise ValueError("Empty key")
        if order in ('', 'asc'):
            ret = ret.asc(key)
        elif order == 'desc':
            ret = ret.desc(key)
        else:
            raise ValueError("Unknown sort direction %r for key %r" % (order, key))
    return ret


def asc(*args):
    """
    Factory function for creating OrderBy chain, starting with ascending sort.
    :param args: passed to `operator.itemgetter()`/`operator.attrgetter()`
    :return: chainable OrderBy() instance with .desc() and .asc() methods
    """
    return OrderBy().asc(*args)


def desc(*args):
    """
    Factory function for creating OrderBy chain, starting with descending sort.
    :param args: passed to `operator.itemgetter()`/`operator.attrgetter()`
    :return: chainable OrderBy() instance with .desc() and .asc() methods
    """
    return OrderBy().desc(*args)


class OrderBy:
    """
    Chain together multiple ascending or descending item getters, to be used
    as key function in `sorted()` and others.

    Chaining is achieved by returning `self` in `asc()` and `desc()` methods

    There is usually no need to instantiate this class directly.
    Use the exposed `asc()` and `desc()` functions instead.
    """

    def __init__(self):
        self.ordering = []

    def asc(self, *args):
        self.ordering.append(Getter(*args))
        return self

    def desc(self, *args):
        self.ordering.append(Getter(*args, desc=True))
        return self

    def __call__(self, obj):
        return tuple(x(obj) for x in self.ordering)
