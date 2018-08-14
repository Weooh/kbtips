# coding: utf-8
"""KBEngine Types handler"""
from enum import IntEnum


_DEFAULT_TYPES = ('UINT8', 'UINT16', 'UINT32', 'UINT64',
                  'INT8', 'INT16', 'INT32', 'INT64', 'FLOAT', 'DOUBLE',
                  'VECTOR2', 'VECTOR3', 'VECTOR4', 'STRING', 'UNICODE',
                  'PYTHON', 'PY_DICT', 'PY_TUPLE', 'PY_LIST', 
                  'ENTITYCALL', 'BLOB',
                  # WARNING: PLEASE MAKE SURE THAT
                  # Array and fixed_dict were not allow for default define
                  'ARRAY', 'FIXED_DICT')


class TypeSelect(IntEnum):
    """types type select"""
    TYPE_DEFAULT = 0    # default type
    TYPE_ALIAS   = 1    # default type alias
    TYPE_ARRAY   = 2    # array type
    TYPE_DICT    = 3    # fix dict type
    
    @classmethod
    def to_select(cls, t_org_name):
        t_name = t_org_name.upper()

        if t_name == 'ARRAY':
            return cls.TYPE_ARRAY
        elif t_name == 'FIXED_DICT':
            return cls.TYPE_DICT
        else:
            return cls.TYPE_ALIAS


class _Type(object):
    def __init__(self):
        self.type_name = ''             # defined type name
        self.origin_type = None         # defined type origin name
        self.type_select = None         # defined types type select
        # array
        self.array_node_type = None     # array each node type
        # fixed_dict
        self.fixed_kw = None            # fixed_dict properties
        self.fixed_impname = ''         # fixed dict implemant name

    def __repr__(self):
        return "{1}<{0}>".format(
            self.type_name, self.type_select.name)

    @classmethod
    def get_factory_by_type_select(cls, type_select: TypeSelect):
        if type_select == TypeSelect.TYPE_DEFAULT:
            return cls.create_default_type
        elif type_select == TypeSelect.TYPE_ALIAS:
            return cls.create_alias_type
        elif type_select == TypeSelect.TYPE_ARRAY:
            return cls.create_array_type
        elif type_select == TypeSelect.TYPE_DICT:
            return cls.create_fixed_dict_type
        else:
            raise TypeError('UNKNOWN TYPE SELECT, got {}'.format(type_select))

    @classmethod
    def create_default_type(cls, type_name):
        obj = cls()
        obj.type_name = type_name
        obj.type_select = TypeSelect.TYPE_DEFAULT
        return obj

    @classmethod
    def create_alias_type(cls, type_name, origin_type):
        obj = cls()
        obj.type_name = type_name
        obj.origin_type = origin_type
        obj.type_select = TypeSelect.TYPE_ALIAS
        return obj

    @classmethod
    def create_array_type(cls, type_name, origin_type, node_type):
        obj = cls()
        obj.type_name = type_name
        obj.origin_type = origin_type
        obj.array_node_type = node_type
        obj.type_select = TypeSelect.TYPE_ARRAY
        return obj

    @classmethod
    def create_fixed_dict_type(cls, type_name, origin_type, properties,
                               imp_name):
        obj = cls()
        obj.type_name = type_name
        obj.origin_type = origin_type
        obj.fixed_kw = properties
        obj.fixed_impname = imp_name
        obj.type_select = TypeSelect.TYPE_DICT
        return obj


DEFAULT_TYPES = {k: _Type.create_default_type(k) for k in _DEFAULT_TYPES}


def trans_types(types_path: str):
    try:
        from xml.etree import cElementTree as ET
    except ImportError:
        from xml.etree import ElementTree as ET

    ALL_TYPES = {}
    ALL_TYPES.update(DEFAULT_TYPES)

    parser = ET.parse(types_path, parser=ET.XMLParser(encoding='utf-8'))
    root = parser.getroot()
    
    # -----------------------------------
    # HALF INIT
    for _e in root:
        t_name = _e.tag.strip()
        t_origin_name = _e.text.strip()
        t_select = TypeSelect.to_select(t_origin_name)

        if t_select is TypeSelect.TYPE_ALIAS:
            obj = _Type.create_alias_type(t_name, None)
        elif t_select is TypeSelect.TYPE_ARRAY:
            obj = _Type.create_array_type(t_name, None, None)
        elif t_select is TypeSelect.TYPE_DICT:
            _imp = _e.find('implementedBy')
            _imp_name = _imp.text.strip() if _imp else ''
            obj = _Type.create_fixed_dict_type(t_name, None, None, _imp_name)
        
        if t_name in ALL_TYPES:
            raise TypeError('multi key in types.xml, got {}'.format(t_name))

        ALL_TYPES[t_name] = obj
    # -----------------------------------

    # -----------------------------------
    # FULL INIT
    for _e in root:
        t_name = _e.tag.strip()
        t_origin_name = _e.text.strip()
        t_select = TypeSelect.to_select(t_origin_name)

        if t_select is TypeSelect.TYPE_ALIAS:
            ALL_TYPES[t_name].origin_type = ALL_TYPES[t_origin_name]
        elif t_select is TypeSelect.TYPE_ARRAY:
            _t = ALL_TYPES[t_name]
            _t.origin_type = ALL_TYPES[t_origin_name]
            _t.array_node_type = ALL_TYPES[_e.find('of').text.strip()]
        elif t_select is TypeSelect.TYPE_DICT:
            _t = ALL_TYPES[t_name]
            _t.origin_type = ALL_TYPES[t_origin_name]
            
            def __init_properties():
                for p in _e.find('Properties') or ():
                    p_name = p.tag.strip()
                    p_origin_name = p.text.strip()
                    
                    if p_origin_name:
                        yield (p_name, ALL_TYPES[p_origin_name])
                    else:
                        pt = p.find('Type')
                        if pt:
                            yield(p_name,
                                  _Type.create_array_type(
                                      p_name,
                                      ALL_TYPES[pt.text.strip()],
                                      ALL_TYPES[pt.find('of').text.strip()]))
      
           
            _t.fixed_kw = dict(__init_properties())
    # -----------------------------------

    return ALL_TYPES
