from fp.collections import lookup
from urlparse import urlparse
from urllib import unquote


###-------------------------------------------------------------------
### Public
###-------------------------------------------------------------------
def queryM(return_type, data, url):
    """
    json_data() :: unicode() | number() | dict() | list()
    queryM(fp.monads.Monad, json_data(), unicode())

    Query the data for the pointer in the URL or fails.

    >>> from fp.monads.maybe import Maybe, Just
    >>> from fp.monads.either import Either

    Example from the spec:

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

    Invalid Key for data type (string key on a list)
    >>> queryM(Either, data, 'http://example.com/example.json#/foo/bar/baz')
    Left(ValueError("invalid literal for int() with base 10: 'baz'",))

    """
    return url_to_pointerM(return_type, url).bind(
        lambda pointer: return_type.ret(__parse_pointer(pointer))
    ).bind(
        lambda keys: __fold_keysM(return_type, data, keys)
    )


def url_to_pointerM(return_type, url):
    """
    Attempts to extract the pointer from the URL as
    defined by the spec or fails if the URL is invalid.

    >>> from fp.monads.either import Either

    >>> url_to_pointerM(Either, 'http://example.com/foo.json#/')
    Right('/')

    >>> url_to_pointerM(Either, '')
    Right('')


    ## Error cases

    Invalid URL
    >>> url_to_pointerM(Either, 'http://[fooo/')
    Left(ValueError('Invalid IPv6 URL',))
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
    """
    Folds the keys over the object, fetching nested 
    objects until reaching the obj in the pointer 
    or failing.
    """
    accM = return_type.ret(obj)
    for key in keys:
        accM = accM.bind(
            lambda obj: __map_keyM(return_type, obj, key).bind(
                lambda key: lookup(return_type, obj, key)
            )
        )
    return accM


def __map_keyM(return_type, obj, key):
    """
    This maps the key to the approriate type or fails if the key
    can not be casted.

    >>> from fp.monads.either import Either
    >>> __map_keyM(Either, [], '0')
    Right(0)


    >>> __map_keyM(Either, {}, '0')
    Right('0')
    
    >>> __map_keyM(Either, [], 'foo')
    Left(ValueError("invalid literal for int() with base 10: 'foo'",))

    >>> __map_keyM(Either, '', '0') # can't index into strings with JSON pointer
    Left(TypeError("'str' object is not subscriptable",))

    >>> __map_keyM(Either, 1024, '0') # can't index into numbers with JSON pointer
    Left(TypeError("'int' object is not subscriptable",))

    """
    if isinstance(obj, list):
        return return_type.catch(lambda: int(key))
    elif isinstance(obj, dict):
        return return_type.ret(key)
    else:
        return return_type.fail(TypeError("'{}' object is not subscriptable".format(type(obj).__name__)))
        

def __parse_pointer(pointer):
    """
    Splits the pointer into its key bits, filtering out blank keys with are
    self referential.

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
