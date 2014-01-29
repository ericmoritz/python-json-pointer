"""
An implementation of JSON pointer querying

http://tools.ietf.org/html/draft-pbryan-zyp-json-pointer-02

Usage:

    >>> from fp.monads.maybe import Maybe, Just, Nothing
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

    >>> queryM(Maybe, data, 'http://example.com/example.json#/zingo')
    Nothing

"""
from core.json_pointer import queryM, url_to_pointerM
