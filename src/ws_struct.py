# so, the point of a struct is it has a fixed layout of attributes
# maybe we define a struct like
# struct PyObject {
#   int type;
#   int size;
#   void* value;
# }
# ideally a nicer syntax, like
# class PyObject(struct):
#     type: i64
#     size: i64
#     value: pointer(void)
# can be created in the future

from __future__ import annotations
from abc import ABC


class Type(ABC):
    @property
    def size(self) -> int:
        raise NotImplementedError()

    def __eq__(self, other: Type) -> bool:
        raise NotImplementedError()


class I64(Type):
    @property
    def size(self) -> int:
        return 8

    def __eq__(self, other: Type) -> bool:
        return isinstance(other, I64)


class struct(Type):
    def __init__(self, attributes=None):
        self.attributes: dict[str, Type] = {} if attributes is None else attributes
        self.layout = {}
        self._total_size = 0
        self.do_layout()

    @property
    def size(self) -> int:
        return self._total_size

    def __eq__(self, other: Type) -> bool:
        return isinstance(other, struct) and self.layout == other.layout

    def do_layout(self):
        # potentially, in the future, we may want to try different layouts
        # such as aligning as many things as possible on word boundaries (maybe padding)
        self.layout = {}
        offset = 0
        for name, type_ in self.attributes.items():
            self.layout[name] = offset
            offset += type_.size
        self._total_size = offset

    def get(self, attr, base_addr='') -> str:
        # getting a value out of a struct kinda depends on what type it is
        # loading another struct should instead do addition (but probably should be optimised to just change the offset)
        # loading an int or a pointer is just a regular i64.load -- smaller types would use, eg, i64.load8_s

        # additionally, to load/store any values, we need to know the address of the struct. We can probably assume
        # that this address is given either as an argument, or is stored as a local variable
        # (why would a struct pointer be on the stack? Maybe we're doing pointer arithmetic? Maybe it's a temp value?)
        # (in the temp value case, we would want to free memory after it's been used, but loading something would remove
        #  the address, so we'd need to store it)
        # (ok, what about traversing a chain of pointers -- it would be nice to be able to call i64.get 3 times in a row
        #  rather than having to pointlessly store and retrieve each intermediate struct)

        # ok, either way -- there's either 0 or 1 instructions we can call to put the address on top of the stack
        # so we should have an optional argument containing that instruction (for example: '(locals.get 0)')
        # we can then embed that into our gets

        type_ = self.attributes[attr]
        offset = self.layout[attr]
        if type_ == i64:
            return f'(i64.load offset={offset} {base_addr})'
        else:
            raise NotImplementedError(f'No handler for loading type {type_} from linear memory!')

    def set(self, attr, base_addr='', value=''):
        if base_addr and not value:
            raise ValueError('must push base_addr before value!')

        type_ = self.attributes[attr]
        offset = self.layout[attr]
        if type_ == i64:
            return f'(i64.store offset={offset} {base_addr} {value})'
        else:
            raise NotImplementedError(f'No handler for storing type {type_} from linear memory!')


i64 = I64()

Either = struct(
    attributes={
        'a': i64,
        'b': i64
    }
)


if __name__ == '__main__':
    print(Either.get('b', '(local.get 1)'))
