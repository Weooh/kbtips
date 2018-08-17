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


P_CLIENT = M_CLIENT = 'cl'
P_CELL = M_CELL = 'c'
P_BASE = M_BASE = 'b'

PROPERTIES_FLAGS_MAPPING = {
    'BASE': (P_BASE, ),
    'BASE_AND_CLIENT': (P_BASE, P_CLIENT),
    'CELL_PRIVATE': (P_CELL, ),
    'CELL_PUBLIC': (P_CELL, ),
    'CELL_PUBLIC_AND_OWN': (P_CELL, P_CLIENT),
    'ALL_CLIENTS': (P_CLIENT, ),
    'OWN_CLIENT': (P_CLIENT, ),
    'OTHER_CLIENTS': (P_CELL, P_CLIENT),
}

METHODS_TAG_MAPPING = {
    'clientmethods': M_CLIENT,
    'basemethods': M_BASE,
    'cellmethods': M_CELL,
}


def _gen_def_properties(trans_def):
    PROS = {P_BASE: {}, P_CELL: {}, P_CLIENT: {}}

    for p_name, p_prm in trans_def['properties'].items():
        _prop = {'name': p_name, 'type': p_prm['type'],
                 'default': p_prm.get('default'), 'flags': p_prm['flags']}
        
        _type = PROPERTIES_FLAGS_MAPPING[p_prm['flags']]

        if P_BASE in _type:
            PROS[P_BASE][p_name] = _prop

        if P_CELL in _type:
            PROS[P_CELL][p_name] = _prop

        if P_CLIENT in _type:
            PROS[P_CLIENT][p_name] = _prop

    return PROS


def _gen_def_methods(trans_def):
    PROS = {M_BASE: {}, M_CELL: {}, M_CLIENT: {}}

    for mt_name, mt_type in METHODS_TAG_MAPPING.items(): 
        for m_name, m_prm in trans_def[mt_name].items():
            _prop = {'args': m_prm['args'], 'name': m_name}

            if mt_type == M_CLIENT:
                PROS[M_CLIENT][m_name] = _prop
            elif mt_type == M_CELL:
                PROS[M_CELL][m_name] = _prop
            elif mt_type == M_BASE:
                PROS[M_BASE][m_name] = _prop

    return PROS


def _format_def(x_props, x_methods, cls_name, imps: str=None):
    file_template = """# coding: utf-8{imports}   

{codes}
 """
    def _gen_imports():
        if imps:
            return imps if imps.startswith('\n') else '\n{}'.format(imps)
        return '\n'

    imps_str = _gen_imports()
    
    cls_str = _format_def_cls(x_props, x_methods, cls_name)

    o_str = file_template.format(imports=imps_str, codes=cls_str) 

    return o_str


def _format_def_cls(x_props, x_methods, cls_name):
    cls_template = """
class {cls_name}(object):
    '''Auto Generated, Please don't modify manully'''

    def __init__(self, *args, **kwargs):
{props}

{methods}
"""
    props = '        ...'
    if x_props:
        props = '\n'.join(['        self.{} : {} = {}'.format(
            k, v['type'], v['default'] if v['default'] is not None else '...')
                           for k, v in x_props.items()])

    methods = ''
    if x_methods:
        methods = '\n'.join(
            ['    def {}(self, {}): ...'.format(
                k, ', '.join(('arg{0}: {1}'.format(idx, arg)
                              for idx, arg in enumerate(v['args']))))
             for k, v in x_methods.items()])

    return cls_template.format(
        cls_name=cls_name, props=props, methods=methods)


def gen_defs(
        def_file_path: str,
        cl_imps: str=None, cl_p: str=None, cl_cls: str=None,
        b_imps: str=None, b_p: str=None, b_cls: str=None,
        c_imps: str=None, c_p: str=None, c_cls: str=None):

    def _filter(_type):
        if _type == M_BASE:
            return b_imps, b_p, b_cls
        elif _type == M_CELL:
            return c_imps, c_p, c_cls
        elif _type == M_CLIENT:
            return cl_imps, cl_p, cl_cls
        else:
            raise TypeError('error handled type, got {}'.format(_type))
    
    import os.path

    transed_def = _defhlr.get_merged_def(def_file_path)
    
    props = _gen_def_properties(transed_def)
    methods = _gen_def_methods(transed_def)

    return_dic = {}
    for _t in (M_BASE, M_CELL, M_CLIENT):
        x_imps, _, x_clsname = _filter(_t)

        if not x_clsname:
            x_clsname = os.path.basename(def_file_path).split('.')[0]
        
        if not props[_t] and not methods[_t]:
            continue

        return_dic[_t] = _format_def(props[_t], methods[_t], x_clsname, x_imps)

    # write to file
    for _t in (M_BASE, M_CELL, M_CLIENT):
        _, x_outpath, _  = _filter(_t)

        if not x_outpath:
            continue
        
        if _t not in return_dic:
            continue

        with open(x_outpath, 'w+') as fd:
            fd.write(return_dic[_t])

    return return_dic
