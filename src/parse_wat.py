from __future__ import annotations

import io
import re
import subprocess
from functools import lru_cache
from typing import Union
import string
from ast import literal_eval

pattern = re.compile(r'0x(\d*)\.?([pP])?([+\-])?(\d*)?')


def numeric_literal(token) -> Union[int, float]:
    token = ''.join(token)

    if token.startswith('0x'):

        # in case this breaks: treat it as an opaque string instead
        p, is_float, sign, e = pattern.match(token).groups()
        if is_float:
            return int(p, 16) * (2 ** numeric_literal(f'{sign}{e}'))
        else:
            return int(p, 16)
        # ok we don't really know if it's a float or an int
        # they both start with '0x' and then a hexnum

    else:
        # note that this is not complete: it doesn't work for hex literals (but we shouldn't see any)
        return literal_eval(token)


def keyword_literal(token):
    return KeywordLiteral(''.join(token))


def string_literal(token):
    return literal_eval(''.join(token))


def type_token(token: list[str]):
    # helpfully, the first character basically identifies the type
    c = token[0]
    if c in {'+', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:
        return numeric_literal(token)
    elif c in string.ascii_lowercase:
        return keyword_literal(token)
    elif c == '"':
        assert False, 'string literals are handled elsewhere'
    else:
        raise NotImplementedError(token)


def parse_comment(file):
    while c := file.read(1):
        if c != ';':
            continue
        if file.read(1) == ')':
            break


def parse_string(file):
    # strings are hard so they get their own mini-parser
    token = ['"']
    while c := file.read(1):
        if c == '"':
            break
        elif c == '\\':
            token.append('\\')
            c2 = file.read(1)
            if c2 in {'t', 'n', 'r', '"', "'", '\\'}:
                token.append(c2)
            else:
                # it's a unicode escape -- read bytes until they stop being numbers
                num = [c2]
                last_pos = file.tell()
                while (c3 := file.read(1)) in {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:
                    num.append(c3)
                    last_pos = file.tell()
                token.append('x')
                token.append(''.join(num))

                if c3:  # seek backwards one if we didn't reach EOF
                    file.seek(last_pos)
        else:
            token.append(c)

    # we eval it so we don't have to handle escapes manually
    token.append('"')
    content = literal_eval(''.join(token))

    return StringLiteral(content)


def tokenize(file):
    token = []

    while True:
        c = file.read(1)

        # line comment -- read until the end of the line
        if c == ';':
            assert file.read(1) == ';'
            while file.read(1) != '\n':
                pass
            continue

        if c == '(':
            # we may need to look ahead if it's an inline comment
            last_pos = file.tell()
            c2 = file.read(1)
            if c2 == ';':
                parse_comment(file)
                continue
            else:
                file.seek(last_pos)
                yield c
                continue

        if c in ['(', ')']:
            if token:
                yield type_token(token)
                token = []
            yield c
            continue

        # if we ever start a string, it must be the start of a token
        if c == '"':
            assert not token
            yield parse_string(file)
            continue

        if c in {'', ' ', '\t', '\n', '\r'}:
            if token:
                yield type_token(token)
            token = []
        else:
            token.append(c)

        if not c:
            break


def tree_ify(token_stream) -> Node:
    # to start a module, we read a single '('. In all other cases, we have already read it.
    name = next(token_stream)
    if name == '(':
        name = next(token_stream)

    children = []
    for token in token_stream:
        if token == '(':
            children.append(tree_ify(token_stream))
        elif token == ')':
            break
        else:
            children.append(token)

    # the name is a keyword literal, but we only care about the content
    return parse_based_on_name(str(name), children)


class Node:
    def __init__(self, children, name):
        self.children = children
        self.name: str = name

    def __str__(self) -> str:
        return ' '.join(['(', self.name, *self._body_to_wat(), ')'])

    def __repr__(self):
        # 1/0
        return f'{type(self).__name__}({str(self)})'

    def _body_to_wat(self) -> list[str]:
        return [
            (
                str(child)
                # if isinstance(child, Node)
                # else print(child) or repr(child)
            )
            for child in self.children
        ]


class Module(Node):
    name = 'module'

    def __init__(self, children, name):
        super().__init__(children, name)

        self.types = []
        self.imports = []
        self.funcs = []
        self.exports = []
        self.globals = []
        self.misc_nodes = []
        self.funcs_by_name: dict[str, Node] = {}
        self.global_index_by_name: dict[str, int] = {}
        self.table = []
        self.elems = []
        self.table_indices_by_name: dict[str, int] = {}

        mapping = {
            Type: self.types,
            Import: self.imports,
            Func: self.funcs,
            Export: self.exports,
            Global: self.globals,
            Table: self.table,
            Elem: self.elems,
        }

        for child in children:
            mapping.get(type(child), self.misc_nodes).append(child)

            if isinstance(child, Export):
                if child.ref_type == 'func':
                    self.funcs_by_name[child.ref_name] = self.get_func_by_index(child.ref_index)
                elif child.ref_type == 'global':
                    self.global_index_by_name[child.ref_name] = child.ref_index

        assert len(self.table) == 1

        self.tmp_register = self.add_func_to_table('__internal__tmp_register', 0)

    def add_func(self, func: Func, name: str):
        self.funcs.append(func)
        self.funcs_by_name[name] = func
        self.add_func_to_table(name, func_id=self.get_func_index_by_name(name))
        # ok this might not work
        self.children.append(func)

    def get_func_by_index(self, i):
        # technically we can import globals, but I don't see this happening
        if i < len(self.imports):
            raise IndexError("Index too low")
        return self.funcs[i - len(self.imports)]

    @lru_cache
    def get_func_index_by_name(self, name):
        target = self.funcs_by_name[name]
        for i, func in enumerate(self.funcs):
            if func == target:
                return len(self.imports) + i
        raise ValueError(f'function {name} not found!')

    def increase_table_size(self):
        # the first is the min size, second is max. Second is optional, but seems to be included by the compiler
        self.table[0].children[0] += 1
        if isinstance(self.table[0].children[1], int):
            self.table[0].children[1] += 1

        # return the number of items in the table (probably?)
        return self.table[0].children[0]

    def add_elem(self, func_id, offset):
        elem = Elem([
            Node(
                name='i32.const',
                children=[offset],
            ),
            KeywordLiteral('func'),
            func_id
            ],
            name='elem'
        )
        self.elems.append(elem)
        self.children.append(elem)

    def add_func_to_table(self, name, func_id):
        if name not in self.table_indices_by_name:
            offset = self.increase_table_size() - 1
            self.add_elem(func_id, offset)
            self.table_indices_by_name[name] = offset
            return offset
        else:
            print(f'tried to add func {name} {func_id} to table twice!')

    def get_table_entry_by_name(self, name):
        class LazyEntry:
            def __str__(_self):
                return str(self.table_indices_by_name[name])
        return LazyEntry()

    def compile(self, save_name=None, opt=True) -> bytes:
        process = subprocess.run(['wat2wasm', '--enable-reference-types', '-', '-o', '/dev/stdout'], input=str(self).encode(), capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(f'Failed to compile:\n {process.stderr.decode()}')

        if save_name:
            open(f'tmp/{save_name}.wasm', 'wb').write(process.stdout)

        if opt:
            return self.opt_wasm(process.stdout, save_name)
        else:
            return process.stdout

    @staticmethod
    def opt_wasm(wasm: bytes, save_name=None) -> bytes:
        process = subprocess.run(['wasm-opt', '--enable-multivalue', '--enable-reference-types', '-', '-O4', '-o', '/dev/stdout'],
                                 input=wasm, capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(f'Failed to optimise:\n {process.stderr.decode()}')
        if save_name:
            open(f'tmp/{save_name}_opt.wasm', 'wb').write(process.stdout)
        return process.stdout


class Type(Node):
    name = 'type'


class Import(Node):
    name = 'import'


class Func(Node):
    name = 'func'


class Global(Node):
    name = 'global'


class Table(Node):
    name = 'table'


class Elem(Node):
    name = 'elem'


class Export(Node):
    name = 'export'

    def __init__(self, children, name):
        super().__init__(children, name)
        self.ref_name = children[0].content
        if len(children) > 1:
            node: Node = children[1]
            self.ref_type = node.name
            self.ref_index = node.children[0]
        else:
            self.ref_type = self.ref_index = None


class StringLiteral(Node):
    def __init__(self, content):
        super().__init__(children=[], name=None)
        self.content = content

    def __str__(self) -> str:
        # returns the string literal, represented as a string
        # the repr for python strings gets it most of the way there, but writes NULL as \x00 instead of \00
        # and uses ' instead of "
        # and doesn't escape all non-ascii characters (only non-printable ones)
        def fmt(c):
            # note: this is NOT string.printable -- it's missing ", \, and control chars
            if c in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%%&\'()*+,-./:;<=>?@[]^_`{|}~ ':
                return c
            else:
                return f'\\{hex(ord(c))[2:].zfill(2)}'

        almost_str = ''.join(
            fmt(c) for c in self.content
        )

        # almost_str = (
        #     repr(self.content)
        #         .encode('ascii', 'backslashreplace').decode()
        #         .replace('\\x', '\\').replace('"', '\\"')
        #         .strip("'")
        # )

        a2 = ['"', almost_str, '"']
        return ''.join(a2)


class KeywordLiteral(Node):
    def __init__(self, *content):
        super().__init__(children=[], name=None)
        self.content = content

    def __str__(self):
        return ' '.join(str(c) for c in self.content)


class FloatLiteral(Node):
    name = 'float'


def parse_based_on_name(name, children) -> Node:
    mapping = {
        'module': Module,
        'type': Type,
        'import': Import,
        'func': Func,
        'export': Export,
        'global': Global,
        'table': Table,
        'elem': Elem,
    }
    return mapping.get(name, Node)(children, name)


def load(path) -> Module:
    # probably really bad for memory -- if it starts using too much, we can start caching to disk
    with open(path, 'rb') as f:
        process = subprocess.run(['wasm2wat', '-', '-o', '/dev/stdout'], stdin=f, capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(f'Failed to decompile {path} {process}')

    stream = io.StringIO(process.stdout.decode())
    return tree_ify(token_stream=tokenize(file=stream))
