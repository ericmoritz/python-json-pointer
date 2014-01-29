from fp.collections import lookup
from fp.monads.maybe import Maybe, Just, Nothing
from fp.monads.iomonad import IO
from fp import trampoline
from itertools import ifilter
from abc import ABCMeta, abstractmethod
from urlparse import urlparse
from urllib import unquote


###-------------------------------------------------------------------
### Public
###-------------------------------------------------------------------
def queryM(return_type, data, url):
    """
    json_data() :: unicode() | number() | dict() | list()
    queryM(fp.monads.Monad, json_data(), unicode())

    >>> from fp.monads.maybe import Maybe, Just, Nothing
    >>> from fp.monads.either import Either

    >>> import json
    >>> data = json.loads('''{
    ...    "foo": {
    ...        "bar": [ "element0", "element1" ],
    ...        "inner object": {
    ...            "baz": "qux"
    ...        }
    ...    }
    ... }''')
    >>> queryM(Maybe, data, '') == Just(data)
    True

    >>> queryM(Maybe, data, 'http://example.com/example.json#') == Just(data)
    True

    >>> queryM(Maybe, data, 'http://example.com/example.json#/') == Just(data)
    True

    >>> queryM(Maybe, data, 'http://example.com/example.json#/foo') == Just(data['foo'])
    True

    >>> queryM(Maybe, data, 'http://example.com/example.json#/foo/inner%20object') == Just(data['foo']['inner object'])
    True

    >>> queryM(Maybe, data, 'http://example.com/example.json#/foo/inner%20object/baz') == Just(data['foo']['inner object']['baz'])
    True

    >>> queryM(Maybe, data, 'http://example.com/example.json#/foo/bar/0') == Just(data['foo']['bar'][0])
    True

    ## Failure cases:

    Missing key:
    >>> queryM(Either, data, 'http://example.com/example.json#/zingo')
    Left(KeyError('zingo',))

    Invalid URL
    >>> queryM(Either, data, 'http://[xyzzy/example.json#/zingo')
    Left(ValueError('Invalid IPv6 URL',))

    """
    return url_to_pointerM(return_type, url).bind(
        lambda pointer: return_type.ret(__parse_pointer(pointer))
    ).bind(
        lambda keys: __fold_keysM(return_type, data, keys)
    )


def url_to_pointer(url):
    """
    >>> url_to_pointer('http://[fooo/')
    ''

    >>> url_to_pointer('')
    ''

    
    >>> url_to_pointer('http://example.com/foo.json#/')
    '/'

    """
    return url_to_pointerM(Maybe, url).default('')


def url_to_pointerM(return_type, url):
    """
    >>> from fp.monads.maybe import Maybe

    Invalid URL
    >>> url_to_pointerM(Maybe, 'http://[fooo/')
    Nothing

    Blank URL
    >>> url_to_pointerM(Maybe, '')
    Just('')

    >>> url_to_pointerM(Maybe, 'http://example.com/foo.json#/')
    Just('/')
    """
    return return_type.catch(
        lambda: urlparse(url)
    ).bind(
        lambda bits: return_type.ret(bits.fragment)
    )


###-------------------------------------------------------------------
### Internal
###-------------------------------------------------------------------
def __fold_keysM(return_type, obj, keys):
    accM = return_type.ret(obj)
    for key in keys:
        accM = accM.bind(
            lambda obj: __map_key(obj, key).bind(
                lambda key: lookup(return_type, obj, key)
            )
        )
    return accM


def __map_key(obj, key):
    """
    >>> __map_key([], '0')
    Just(0)

    >>> __map_key({}, '0')
    Just('0')
    
    >>> __map_key([], 'foo')
    Nothing

    >>> __map_key('', '0') # can't index into strings with JSON pointer
    Nothing

    >>> __map_key(1024, '0') # can't index into numbers with JSON pointer
    Nothing
    """
    if isinstance(obj, list):
        return Maybe.catch(lambda: int(key))
    elif isinstance(obj, dict):
        return Just(key)
    else:
        return Nothing
        

def __parse_pointer(pointer):
    """
    >>> __parse_pointer('')
    []

    >>> __parse_pointer('/')
    []

    >>> __parse_pointer('/foo')
    ['foo']

    >>> __parse_pointer('/foo/')
    ['foo']

    >>> __parse_pointer('/foo/inner%20object')
    ['foo', 'inner object']
    """
    return [
        unquote(x)
        for x in pointer.split("/")
        if len(x) > 0
    ]
