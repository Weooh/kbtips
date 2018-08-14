# coding: utf-8
import collections

import _typehlr
import _defhlr


def TYPING_NEW_TYPE(name, basic):
    return "typing.NewType('{0}', {1})".format(name, basic)


def TYPING_GENERIC(name, *args):
    if not args:
        return "typing.TypeVar('{0}')".format(name)
    else:
        return "typing.TypeVar('{0}', {})".format(name, ', '.join(args))

def TYPING_ARRAY(T=None):
    if not T:
        return "typing.List"
    else:
        return "typing.List[{}]".format(T)


DEFAULT_TYPE_PY_MAPPIGN = {
    'UINT8': TYPING_NEW_TYPE('UINT8', int.__name__),
    'UINT16': TYPING_NEW_TYPE('UINT16', int.__name__),
    'UINT32': TYPING_NEW_TYPE('UINT32', int.__name__),
    'UINT64': TYPING_NEW_TYPE('UINT64', int.__name__),
    'INT8': TYPING_NEW_TYPE('INT8', int.__name__),
    'INT16': TYPING_NEW_TYPE('INT16', int.__name__),
    'INT32': TYPING_NEW_TYPE('INT32', int.__name__),
    'INT64': TYPING_NEW_TYPE('INT64', int.__name__),
    'FLOAT': TYPING_NEW_TYPE('FLOAT', float.__name__),
    'DOUBLE': TYPING_NEW_TYPE('DOUBLE', float.__name__),
    'VECTOR2': 'typing.Tuple[float, float]',
    'VECTOR3': 'typing.Tuple[float, float, float]',
    'VECTOR4': 'typing.Tuple[float, float, float, float]',
    'STRING': TYPING_NEW_TYPE('STRING', bytes.__name__),
    'UNICODE': TYPING_NEW_TYPE('UNICODE', str.__name__),
    'PYTHON': 'typing.Any',
    'PY_DICT': 'typing.Dict[typing.Any, typing.Any]',
    'PY_TUPLE': 'typing.Tuple',
    'PY_LIST': 'typing.List',
    'ENTITYCALL': 'typing.Any',
    'BLOB': TYPING_NEW_TYPE('BLOB', bool.__name__),
    'ARRAY': 'typing.List[typing.Any]',
    'FIXED_DICT': 'typing.Any',
}


def _gen_default_type(type_struc: _typehlr._Type):
    if type_struc.type_select is not _typehlr.TypeSelect.TYPE_DEFAULT:
        raise TypeError(
            'gens must handle default types, got {}'.format(type_struc))

    d_type = DEFAULT_TYPE_PY_MAPPIGN.get(type_struc.type_name)
    if d_type is None:
        raise TypeError(
            'Default type name not found, got {}'.format(type_struc))

    return d_type


def gen_types(type_file_path: str):
    transed_types = _typehlr.trans_types(type_file_path)

    ARGS = collections.OrderedDict()

    while len(ARGS) < len(transed_types):
        for _t_name, _t_type in transed_types.items():
            if _t_name in ARGS:
                continue

            if _t_type.type_select is _typehlr.TypeSelect.TYPE_DEFAULT:
                ARGS[_t_name] = _gen_default_type(_t_type)
            elif _t_type.type_select is _typehlr.TypeSelect.TYPE_ALIAS:
                origin_type_name = _t_type.origin_type.type_name
                if origin_type_name in ARGS:
                    ARGS[_t_name] = TYPING_NEW_TYPE(_t_name, origin_type_name)
            elif _t_type.type_select is _typehlr.TypeSelect.TYPE_ARRAY:
                node_type_name = _t_type.array_node_type.type_name
                if node_type_name in ARGS:
                    ARGS[_t_name] = TYPING_ARRAY(node_type_name)
            elif _t_type.type_select is _typehlr.TypeSelect.TYPE_DICT:
                if 'FIXED_DICT' in ARGS:
                    ARGS[_t_name] = TYPING_NEW_TYPE(_t_name, 'FIXED_DICT')
            else:
                # Dedault condition
                ARGS[_t_name] = TYPING_GENERIC(_t_name)

    return ARGS


def gen_types_file(type_file_path: str, out_path=None):
    args = gen_types(type_file_path)
    file_str =  """ # coding: utf-8
import typing

{typings}
""".format(
    typings='\n'.join(['{} = {}'.format(k, v) for k, v in args.items()]))

    if out_path is not None:
        with open(out_path, 'w+') as _fd:
           _fd.write(file_str)

    return file_str
