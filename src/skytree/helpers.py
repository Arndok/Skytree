"""
A repository of helper functions.

Functions:
nop(): do nothing (to be used as a default argument function).
is_collection(obj): check if obj is "intuitively" a collection.
tupleize(obj): put obj inside a tuple unless it's one itself.
repack2(obj): turn obj into (obj, obj) if it's a single value.
repack4(obj): turn obj into (obj, obj, obj, obj)|(*obj, *obj) if it's a single value or a collection with size 2.
bake_obj(obj): build the object if it's a type or a tuple (type, {kwargs}).
distance(p1, p2): return euclidean distance between given 2D points.
ComboClass(*classes): return a new class combining provided ones as arguments and generating an appropriate name.
"""

from collections.abc import Sequence 

def nop():
    """Do nothing."""
    pass

def is_collection(obj):
    """Return True if obj is a Sequence but not a string, bytes or bytearray; False otherwise."""
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray))

def tupleize(obj):
    """Put obj inside a tuple unless it's one itself."""
    return obj if isinstance(obj, tuple) else (obj,)

def repack2(obj):
    """Return obj if it's a collection of 2 elements or a tuple (obj, obj) otherwise."""
    if not is_collection(obj):
        return (obj, obj)
    elif len(obj) == 2:
        return tuple(obj)
    raise ValueError("repack_2 got called on object {o}; this function only admits single values or collections of length 2.".format(o=obj))

def repack4(obj):
    """Return obj if it's a collection of 4 elements, a tuple (*obj, *obj) if it's a collection of 2 elements or a tuple (obj, obj, obj, obj) otherwise."""
    if not is_collection(obj):
        return (obj, obj, obj, obj)
    elif len(obj) == 2:
        return (*obj, *obj)
    elif len(obj) == 4:
        return tuple(obj)
    raise ValueError("repack_4 got called on object {o}; this function only admits single values or collections of length 2 or 4.".format(o=obj))

def bake_obj(obj):
    """
    Return the given object after trying to build it if necessary.
    
    If obj is a type, try to call constructor without arguments.
    If it's a tuple, try to build it assuming the tuple's in the form (Class, {kwargs})
    """
    if isinstance(obj, tuple):
        try:
            return obj[0](**obj[1])
        except Exception as err:
            print("Something went wrong when trying to construct an object from tuple {t}.\n\
                   First item must be class, second one must be dict with kwargs.\n".format(t=obj), err)
            raise
    elif isinstance(obj, type):
        return obj()
    else:
        return obj

def distance(p1, p2):
    """Return number representing euclidean distance between two 2D points."""
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**.5
    
def ComboClass(*classes):
    """Return a new class combining provided ones as arguments and generating an appropriate name."""
    if len(classes) < 2:
        raise TypeError(f"At least two classes must be provided. Classes: {classes}")
    if not all(isinstance(cls, type) for cls in classes):
        raise TypeError(f"All arguments in *classes must be valid classes. Current arguments: {classes}")
    return type("ComboClass_" + "_".join(cls.__name__ for cls in classes), classes, {})