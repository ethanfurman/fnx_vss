class Sentinel(object):
    def __init__(yo, text):
        yo.text = text
    def __str__(yo):
        return "Sentinel: <%s>" % yo.text


try:
    next
except NameError:
    from dbf import next

try:
    basestring
except NameError:
    # only a problem on Python 3.1
    basestring = unicode


try:
    from collections import OrderedDict
except ImportError:
    # Backport of OrderedDict() class that runs on Python 2.4, 2.5, 2.6, 2.7 and pypy.
    # Passes Python2.7's test suite and incorporates all the latest updates.
    # Many thanks to Raymond Hettinger
    try:
        from thread import get_ident as _get_ident
    except ImportError:
        from dummy_thread import get_ident as _get_ident

    try:
        from _abcoll import KeysView, ValuesView, ItemsView
    except ImportError:
        pass


    class OrderedDict(dict):
        'Dictionary that remembers insertion order'
        # An inherited dict maps keys to values.
        # The inherited dict provides __getitem__, __len__, __contains__, and get.
        # The remaining methods are order-aware.
        # Big-O running times for all methods are the same as for regular dictionaries.

        # The internal self.__map dictionary maps keys to links in a doubly linked list.
        # The circular doubly linked list starts and ends with a sentinel element.
        # The sentinel element never gets deleted (this simplifies the algorithm).
        # Each link is stored as a list of length three:  [PREV, NEXT, KEY].

        def __init__(self, *args, **kwds):
            '''Initialize an ordered dictionary.  Signature is the same as for
            regular dictionaries, but keyword arguments are not recommended
            because their insertion order is arbitrary.

            '''
            if len(args) > 1:
                raise TypeError('expected at most 1 arguments, got %d' % len(args))
            try:
                self.__root
            except AttributeError:
                self.__root = root = []                     # sentinel node
                root[:] = [root, root, None]
                self.__map = {}
            self.__update(*args, **kwds)

        def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
            'od.__setitem__(i, y) <==> od[i]=y'
            # Setting a new item creates a new link which goes at the end of the linked
            # list, and the inherited dictionary is updated with the new key/value pair.
            if key not in self:
                root = self.__root
                last = root[0]
                last[1] = root[0] = self.__map[key] = [last, root, key]
            dict_setitem(self, key, value)

        def __delitem__(self, key, dict_delitem=dict.__delitem__):
            'od.__delitem__(y) <==> del od[y]'
            # Deleting an existing item uses self.__map to find the link which is
            # then removed by updating the links in the predecessor and successor nodes.
            dict_delitem(self, key)
            link_prev, link_next, key = self.__map.pop(key)
            link_prev[1] = link_next
            link_next[0] = link_prev

        def __iter__(self):
            'od.__iter__() <==> iter(od)'
            root = self.__root
            curr = root[1]
            while curr is not root:
                yield curr[2]
                curr = curr[1]

        def __reversed__(self):
            'od.__reversed__() <==> reversed(od)'
            root = self.__root
            curr = root[0]
            while curr is not root:
                yield curr[2]
                curr = curr[0]

        def clear(self):
            'od.clear() -> None.  Remove all items from od.'
            try:
                for node in self.__map.itervalues():
                    del node[:]
                root = self.__root
                root[:] = [root, root, None]
                self.__map.clear()
            except AttributeError:
                pass
            dict.clear(self)

        def popitem(self, last=True):
            '''od.popitem() -> (k, v), return and remove a (key, value) pair.
            Pairs are returned in LIFO order if last is true or FIFO order if false.

            '''
            if not self:
                raise KeyError('dictionary is empty')
            root = self.__root
            if last:
                link = root[0]
                link_prev = link[0]
                link_prev[1] = root
                root[0] = link_prev
            else:
                link = root[1]
                link_next = link[1]
                root[1] = link_next
                link_next[0] = root
            key = link[2]
            del self.__map[key]
            value = dict.pop(self, key)
            return key, value

        # -- the following methods do not depend on the internal structure --

        def keys(self):
            'od.keys() -> list of keys in od'
            return list(self)

        def values(self):
            'od.values() -> list of values in od'
            return [self[key] for key in self]

        def items(self):
            'od.items() -> list of (key, value) pairs in od'
            return [(key, self[key]) for key in self]

        def iterkeys(self):
            'od.iterkeys() -> an iterator over the keys in od'
            return iter(self)

        def itervalues(self):
            'od.itervalues -> an iterator over the values in od'
            for k in self:
                yield self[k]

        def iteritems(self):
            'od.iteritems -> an iterator over the (key, value) items in od'
            for k in self:
                yield (k, self[k])

        def update(*args, **kwds):
            '''od.update(E, **F) -> None.  Update od from dict/iterable E and F.

            If E is a dict instance, does:           for k in E: od[k] = E[k]
            If E has a .keys() method, does:         for k in E.keys(): od[k] = E[k]
            Or if E is an iterable of items, does:   for k, v in E: od[k] = v
            In either case, this is followed by:     for k, v in F.items(): od[k] = v

            '''
            if len(args) > 2:
                raise TypeError('update() takes at most 2 positional '
                                'arguments (%d given)' % (len(args),))
            elif not args:
                raise TypeError('update() takes at least 1 argument (0 given)')
            self = args[0]
            # Make progressively weaker assumptions about "other"
            other = ()
            if len(args) == 2:
                other = args[1]
            if isinstance(other, dict):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, 'keys'):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value
            for key, value in kwds.items():
                self[key] = value

        __update = update  # let subclasses override update without breaking __init__

        __marker = Sentinel('raise KeyError if not found and default not specified')

        def pop(self, key, default=__marker):
            '''od.pop(k[,d]) -> v, remove specified key and return the corresponding value.
            If key is not found, d is returned if given, otherwise KeyError is raised.

            '''
            if key in self:
                result = self[key]
                del self[key]
                return result
            if default is self.__marker:
                raise KeyError(key)
            return default

        def setdefault(self, key, default=None):
            'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
            if key in self:
                return self[key]
            self[key] = default
            return default

        def __repr__(self, _repr_running={}):
            'od.__repr__() <==> repr(od)'
            call_key = id(self), _get_ident()
            if call_key in _repr_running:
                return '...'
            _repr_running[call_key] = 1
            try:
                if not self:
                    return '%s()' % (self.__class__.__name__,)
                return '%s(%r)' % (self.__class__.__name__, self.items())
            finally:
                del _repr_running[call_key]

        def __reduce__(self):
            'Return state information for pickling'
            items = [[k, self[k]] for k in self]
            inst_dict = vars(self).copy()
            for k in vars(OrderedDict()):
                inst_dict.pop(k, None)
            if inst_dict:
                return (self.__class__, (items,), inst_dict)
            return self.__class__, (items,)

        def copy(self):
            'od.copy() -> a shallow copy of od'
            return self.__class__(self)

        @classmethod
        def fromkeys(cls, iterable, value=None):
            '''OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S
            and values equal to v (which defaults to None).

            '''
            d = cls()
            for key in iterable:
                d[key] = value
            return d

        def __eq__(self, other):
            '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
            while comparison to a regular mapping is order-insensitive.

            '''
            if isinstance(other, OrderedDict):
                return len(self)==len(other) and self.items() == other.items()
            return dict.__eq__(self, other)

        def __ne__(self, other):
            return not self == other

        # -- the following methods are only used in Python 2.7 --

        def viewkeys(self):
            "od.viewkeys() -> a set-like object providing a view on od's keys"
            return KeysView(self)

        def viewvalues(self):
            "od.viewvalues() -> an object providing a view on od's values"
            return ValuesView(self)

        def viewitems(self):
            "od.viewitems() -> a set-like object providing a view on od's items"
            return ItemsView(self)


try:
    from collections import TransformDict
except ImportError:
    class TransformDict(dict):
        '''Dictionary that calls a transformation function when looking
        up keys, but preserves the original keys.
    
        >>> d = TransformDict(str.lower)
        >>> d['Foo'] = 5
        >>> d['foo'] == d['FOO'] == d['Foo'] == 5
        True
        >>> set(d.keys())
        {'Foo'}
        '''
    
        __slots__ = ('_transform', '_original', '_data')
    
        def __init__(self, transform, init_dict=None, **kwargs):
            '''Create a new TransformDict with the given *transform* function.
            *init_dict* and *kwargs* are optional initializers, as in the
            dict constructor.
            '''
            if not callable(transform):
                raise TypeError("expected a callable, got %r" % transform.__class__)
            self._transform = transform
            # transformed => original
            self._original = {}
            self._data = {}
            if init_dict:
                self.update(init_dict)
            if kwargs:
                self.update(kwargs)
    
        def getitem(self, key):
            'D.getitem(key) -> (stored key, value)'
            transformed = self._transform(key)
            original = self._original[transformed]
            value = self._data[transformed]
            return original, value
    
        @property
        def transform_func(self):
            "This TransformDict's transformation function"
            return self._transform
    
        # Minimum set of methods required for MutableMapping
    
        def __len__(self):
            return len(self._data)
    
        def __iter__(self):
            return iter(self._original.values())
    
        def __getitem__(self, key):
            return self._data[self._transform(key)]
    
        def __setitem__(self, key, value):
            transformed = self._transform(key)
            self._data[transformed] = value
            self._original.setdefault(transformed, key)
    
        def __delitem__(self, key):
            transformed = self._transform(key)
            del self._data[transformed]
            del self._original[transformed]
    
        # Methods overriden to mitigate the performance overhead.
    
        def clear(self):
            'D.clear() -> None.  Remove all items from D.'
            self._data.clear()
            self._original.clear()
    
        def __contains__(self, key):
            return self._transform(key) in self._data
    
        def get(self, key, default=None):
            'D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.'
            return self._data.get(self._transform(key), default)
    
        __sentinel = Sentinel('raise KeyError if no default specified')
        def pop(self, key, default=__sentinel):
            '''D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
              If key is not found, d is returned if given, otherwise KeyError is raised.
            '''
            transformed = self._transform(key)
            if default is self.__sentinel:
                del self._original[transformed]
                return self._data.pop(transformed)
            else:
                self._original.pop(transformed, None)
                return self._data.pop(transformed, default)
    
        def popitem(self):
            '''D.popitem() -> (k, v), remove and return some (key, value) pair
               as a 2-tuple; but raise KeyError if D is empty.
            '''
            transformed, value = self._data.popitem()
            return self._original.pop(transformed), value
    
        # Other methods
    
        def copy(self):
            'D.copy() -> a shallow copy of D'
            other = self.__class__(self._transform)
            other._original = self._original.copy()
            other._data = self._data.copy()
            return other
    
        __copy__ = copy
    
        def __getstate__(self):
            return (self._transform, self._data, self._original)
    
        def __setstate__(self, state):
            self._transform, self._data, self._original = state
    
        def __repr__(self):
            try:
                equiv = dict(self)
            except TypeError:
                # Some keys are unhashable, fall back on .items()
                equiv = list(self.items())
            return '%s(%r, %s)' % (self.__class__.__name__,
                                   self._transform, repr(equiv))
    
    

try:
    from collections import Counter
except ImportError:
    from operator import itemgetter
    from heapq import nlargest
    from itertools import repeat, ifilter

    class Counter(dict):
        '''Dict subclass for counting hashable objects.  Sometimes called a bag
        or multiset.  Elements are stored as dictionary keys and their counts
        are stored as dictionary values.

        >>> Counter('zyzygy')
        Counter({'y': 3, 'z': 2, 'g': 1})

        '''

        def __init__(self, iterable=None, **kwds):
            '''Create a new, empty Counter object.  And if given, count elements
            from an input iterable.  Or, initialize the count from another mapping
            of elements to their counts.

            >>> c = Counter()                           # a new, empty counter
            >>> c = Counter('gallahad')                 # a new counter from an iterable
            >>> c = Counter({'a': 4, 'b': 2})           # a new counter from a mapping
            >>> c = Counter(a=4, b=2)                   # a new counter from keyword args

            '''        
            self.update(iterable, **kwds)

        def __missing__(self, key):
            return 0

        def most_common(self, n=None):
            '''List the n most common elements and their counts from the most
            common to the least.  If n is None, then list all element counts.

            >>> Counter('abracadabra').most_common(3)
            [('a', 5), ('r', 2), ('b', 2)]

            '''        
            if n is None:
                return sorted(self.iteritems(), key=itemgetter(1), reverse=True)
            return nlargest(n, self.iteritems(), key=itemgetter(1))

        def elements(self):
            '''Iterator over elements repeating each as many times as its count.

            >>> c = Counter('ABCABC')
            >>> sorted(c.elements())
            ['A', 'A', 'B', 'B', 'C', 'C']

            If an element's count has been set to zero or is a negative number,
            elements() will ignore it.

            '''
            for elem, count in self.iteritems():
                for _ in repeat(None, count):
                    yield elem

        # Override dict methods where the meaning changes for Counter objects.

        @classmethod
        def fromkeys(cls, iterable, v=None):
            raise NotImplementedError(
                'Counter.fromkeys() is undefined.  Use Counter(iterable) instead.')

        def update(self, iterable=None, **kwds):
            '''Like dict.update() but add counts instead of replacing them.

            Source can be an iterable, a dictionary, or another Counter instance.

            >>> c = Counter('which')
            >>> c.update('witch')           # add elements from another iterable
            >>> d = Counter('watch')
            >>> c.update(d)                 # add elements from another counter
            >>> c['h']                      # four 'h' in which, witch, and watch
            4

            '''        
            if iterable is not None:
                if hasattr(iterable, 'iteritems'):
                    if self:
                        self_get = self.get
                        for elem, count in iterable.iteritems():
                            self[elem] = self_get(elem, 0) + count
                    else:
                        dict.update(self, iterable) # fast path when counter is empty
                else:
                    self_get = self.get
                    for elem in iterable:
                        self[elem] = self_get(elem, 0) + 1
            if kwds:
                self.update(kwds)

        def copy(self):
            'Like dict.copy() but returns a Counter instance instead of a dict.'
            return Counter(self)

        def __delitem__(self, elem):
            'Like dict.__delitem__() but does not raise KeyError for missing values.'
            if elem in self:
                dict.__delitem__(self, elem)

        def __repr__(self):
            if not self:
                return '%s()' % self.__class__.__name__
            items = ', '.join(map('%r: %r'.__mod__, self.most_common()))
            return '%s({%s})' % (self.__class__.__name__, items)

        # Multiset-style mathematical operations discussed in:
        #       Knuth TAOCP Volume II section 4.6.3 exercise 19
        #       and at http://en.wikipedia.org/wiki/Multiset
        #
        # Outputs guaranteed to only include positive counts.
        #
        # To strip negative and zero counts, add-in an empty counter:
        #       c += Counter()

        def __add__(self, other):
            '''Add counts from two counters.

            >>> Counter('abbb') + Counter('bcc')
            Counter({'b': 4, 'c': 2, 'a': 1})


            '''
            if not isinstance(other, Counter):
                return NotImplemented
            result = Counter()
            for elem in set(self) | set(other):
                newcount = self[elem] + other[elem]
                if newcount > 0:
                    result[elem] = newcount
            return result

        def __sub__(self, other):
            ''' Subtract count, but keep only results with positive counts.

            >>> Counter('abbbc') - Counter('bccd')
            Counter({'b': 2, 'a': 1})

            '''
            if not isinstance(other, Counter):
                return NotImplemented
            result = Counter()
            for elem in set(self) | set(other):
                newcount = self[elem] - other[elem]
                if newcount > 0:
                    result[elem] = newcount
            return result

        def __or__(self, other):
            '''Union is the maximum of value in either of the input counters.

            >>> Counter('abbb') | Counter('bcc')
            Counter({'b': 3, 'c': 2, 'a': 1})

            '''
            if not isinstance(other, Counter):
                return NotImplemented
            _max = max
            result = Counter()
            for elem in set(self) | set(other):
                newcount = _max(self[elem], other[elem])
                if newcount > 0:
                    result[elem] = newcount
            return result

        def __and__(self, other):
            ''' Intersection is the minimum of corresponding counts.

            >>> Counter('abbb') & Counter('bcc')
            Counter({'b': 1})

            '''
            if not isinstance(other, Counter):
                return NotImplemented
            _min = min
            result = Counter()
            if len(self) < len(other):
                self, other = other, self
            for elem in ifilter(self.__contains__, other):
                newcount = _min(self[elem], other[elem])
                if newcount > 0:
                    result[elem] = newcount
            return result


class BiDict(object):
    """
    key <=> value (value must also be hashable)
    """

    def __init__(yo, *args, **kwargs):
        _dict = yo._dict = dict()
        original_keys = yo._primary_keys = list()
        for k, v in args:
            if k not in original_keys:
                original_keys.append(k)
            _dict[k] = v
            if v != k and v in _dict:
                raise ValueError("%s:%s violates one-to-one mapping" % (k, v))
            _dict[v] = k
        for key, value in kwargs.items():
            if key not in original_keys:
                original_keys.append(key)
            _dict[key] = value
            if value != key and value in _dict:
                raise ValueError("%s:%s violates one-to-one mapping" % (key, value))
            _dict[value] = key

    def __contains__(yo, key):
        return key in yo._dict

    def __delitem__(yo, key):
        _dict = yo._dict
        value = _dict[key]
        del _dict[value]
        if key != value:
            del _dict[key]
        target = (key, value)[value in yo._primary_keys]
        yo._primary_keys.pop(yo._primary_keys.index(target))

    def __getitem__(yo, key):
        return yo._dict.__getitem__(key)

    def __iter__(yo):
        return iter(yo._primary_keys)

    def __len__(yo):
        return len(yo._primary_keys)

    def __setitem__(yo, key, value):
        _dict = yo._dict
        original_keys = yo._primary_keys
        if key in _dict:
            mapping = key, _dict[key]
        else:
            mapping = ()
        if value in _dict and value not in mapping:
            raise ValueError("%s:%s violates one-to-one mapping" % (key, value))
        if mapping:
            k, v = mapping
            del _dict[k]
            if k != v:
                del _dict[v]
            target = (k, v)[v in original_keys]
            original_keys.pop(original_keys.index(target))
        _dict[key] = value
        _dict[value] = key
        original_keys.append(key)

    def __repr__(yo):
        result = []
        for key in yo._primary_keys:
            result.append(repr((key, yo._dict[key])))
        return "BiDict(%s)" % ', '.join(result)

    def keys(yo):
        return yo._primary_keys[:]

    def items(yo):
        return [(k, yo._dict[k]) for k in yo._primary_keys]

    def values(yo):
        return [yo._dict[key] for key in yo._primary_keys]

class PropertyDict(object):
    """
    allows dictionary lookup using . notation
    allows a default similar to defaultdict
    """

    _internal = ['_illegal', '_values', '_default', '_order']
    _default = None

    def __init__(yo, *args, **kwargs):
        "kwargs is evaluated last"
        if 'default' in kwargs:
            yo._default = kwargs.pop('default')
        needs_sorted = False
        yo._values = _values = {}
        yo._order = _order = []
        yo._illegal = _illegal = tuple([attr for attr in dir(_values) if attr[0] != '_'])
        if yo._default is None:
            default_factory = lambda : False
        else:
            default_factory = yo._default
        for arg in args:
            # first, see if it's a lone string
            if isinstance(arg, basestring):
                arg = [(arg, default_factory())]
            # next, see if it's a mapping
            try:
                arg = arg.items()
                if not needs_sorted:
                    needs_sorted = isinstance(arg, OrderedDict)
            except (AttributeError, ):
                pass
            # now iterate over it
            for item in arg:
                if isinstance(item, basestring):
                    key, value = item, default_factory()
                else:
                    key, value = item
                if not isinstance(key, basestring):
                    raise ValueError('keys must be strings, but %r is %r' % (key, type(key)))
                if key in _illegal:
                    raise ValueError('%s is a reserved word' % key)
                _values[key] = value
                if key not in _order:
                    _order.append(key)
        if kwargs:
            needs_sorted = True
            _values.update(kwargs)
            _order.extend([k for k in kwargs.keys() if k not in _order])
        if needs_sorted:
            _order.sort()

    def __contains__(yo, key):
        return key in yo._values

    def __delitem__(yo, name):
        if name[0] == '_':
            raise KeyError("illegal key name: %s" % name)
        if name not in yo._values:
            raise KeyError("%s: no such key" % name)
        yo._values.pop(name)
        yo._order.pop(yo._order.index(name))

    def __delattr__(yo, name):
        if name[0] == '_':
            raise AttributeError("illegal key name: %s" % name)
        if name not in yo._values:
            raise AttributeError("%s: no such key" % name)
        yo._values.pop(name)
        yo._order.pop(yo._order.index(name))

    def __eq__(yo, other):
        if isinstance(other, PropertyDict):
            other = other._values
        elif not isinstance(other, dict):
            return NotImplemented
        return other == yo._values

    def __ne__(yo, other):
        return not yo == other

    def __getitem__(yo, name):
        if name in yo._values:
            return yo._values[name]
        elif yo._default:
            yo._order.append(name)
            result = yo._values[name] = yo._default()
            return result
        raise KeyError("object has no key %s" % name)

    def __getattr__(yo, name):
        if name in yo._values:
            return yo._values[name]
        attr = getattr(yo._values, name, None)
        if attr is not None:
            return attr
        elif yo._default:
            yo._order.append(name)
            result = yo._values[name] = yo._default()
            return result
        raise AttributeError("object has no attribute %s" % name)

    def __iter__(yo):
        if len(yo._values) != len(yo._order):
            _order = set(yo._order)
            for key in yo._values:
                if key not in _order:
                    yo._order.append(key)
        return iter(yo._order)

    def __len__(yo):
        return len(yo._values)

    def __setitem__(yo, name, value):
        if name in yo._internal:
            object.__setattr__(yo, name, value)
        elif isinstance(name, basestring) and name[0:1] == '_':
            raise KeyError("illegal attribute name: %s" % name)
        else:
            if name not in yo._values:
                yo._order.append(name)
            yo._values[name] = value

    def __setattr__(yo, name, value):
        if name in yo._internal:
            object.__setattr__(yo, name, value)
        elif name[0] == '_' or name in yo._illegal:
            raise AttributeError("illegal attribute name: %s" % name)
        else:
            if name not in yo._values:
                yo._order.append(name)
            yo._values[name] = value

    def __repr__(yo):
        if not yo:
            return "PropertyDict()"
        return "PropertyDict([%s])" % ', '.join(["(%r, %r)" % (x, yo._values[x]) for x in yo])

    def __str__(yo):
        return '\n'.join(["%r=%r" % (x, yo._values[x]) for x in yo])

    def keys(yo):
        return yo._order[:]

    __pop_sentinel = Sentinel('raise KeyError if not found and default not specified')
    def pop(yo, name, default=__pop_sentinel):
        if name in yo._values:
            yo._order.pop(yo._order.index(name))
            return yo._values.pop(name)
        elif default is not yo.__pop_sentinel:
            return default
        else:
            raise KeyError('key not found: %r' % name)


def simplegeneric(func):
    """Make a trivial single-dispatch generic function (from Python3.4 functools)"""
    registry = {}
    def wrapper(*args, **kw):
        ob = args[0]
        try:
            cls = ob.__class__
        except AttributeError:
            cls = type(ob)
        try:
            mro = cls.__mro__
        except AttributeError:
            try:
                class cls(cls, object):
                    pass
                mro = cls.__mro__[1:]
            except TypeError:
                mro = object,   # must be an ExtensionClass or some such  :(
        for t in mro:
            if t in registry:
                return registry[t](*args, **kw)
        else:
            return func(*args, **kw)
    try:
        wrapper.__name__ = func.__name__
    except (TypeError, AttributeError):
        pass    # Python 2.3 doesn't allow functions to be renamed

    def register(typ, func=None):
        if func is None:
            return lambda f: register(typ, f)
        registry[typ] = func
        return func

    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    wrapper.register = register
    return wrapper


class suppress(object):
    "suppresses first execption and exits the with block"
    def __init__(self, *exceptions):
        self.exceptions = exceptions
    def __enter__(self):
        pass
    def __exit__(self, etype, val, tb):
        return etype is None or issubclass(etype, self.exceptions)



