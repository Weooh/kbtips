# coding: utf-8
import logging


TRANS_DICT = ['\t', '\n', '\r']
MTAGS = ('BaseMethods', 'ClientMethods', 'CellMethods')
LOGGER = logging.getLogger(__name__)


class DefInvalidError(Exception):
    """raise this exception when check def file failed"""


def trans_text(raw_str, replace='', beside_space=False):
    new_str = raw_str.translate({ord(i): replace for i in TRANS_DICT})

    if not beside_space:
        new_str = new_str.strip()

    return new_str


def _parse_interfaces(root):
    interfaces = root.find('Interfaces')
    for interface in interfaces or ():
        if interface.tag != 'Interface':
            LOGGER.warning('tag error, skipped')
            continue
        iname = trans_text(interface.text)
        yield iname


def _parse_volatile(root):
    volatile = root.find('Volatile')

    for v in volatile or ():
        if isinstance(v.text, (str, bytes)):
            if 'true' in v.text.lower():
                yield v.tag, True
            else:
                yield v.tag, False

            continue

        yield v.tag, v.text


def _parse_properties(root):
    properties = root.find('Properties')
    for pdata in properties or ():
        pprm = {}
        for _p in pdata:
            if _p.tag.lower() == 'default':
                pprm[_p.tag.lower()] = eval(_p.text)
                continue
            pprm[_p.tag.lower()] = trans_text(_p.text)
        yield pdata.tag, pprm


def _parse_methods(methods):
    for method  in methods or ():
        args = []
        mprm = {'args': args, 'exposed': False}
        margs = method.findall('Arg')
        for marg in margs:
            args.append(trans_text(marg.text))
        exposed = method.find('exposed')
        if exposed:
            mprm['exposed'] = True

        yield method.tag, mprm


def parse_def_file(def_path):
    try:
        from xml.etree import cElementTree as ET
    except ImportError:
        from xml.etree import ElementTree as ET

    parser_data = {}

    root = ET.parse(def_path, parser=ET.XMLParser(encoding='utf-8'))
    root = root.getroot() 
    # check root depulicates
    _rvs = [i.tag for i in root]
    if len(_rvs) != len(set(_rvs)):
        raise DefInvalidError('Duplicated settings in root')

    # ====================
    # parse interfaces
    # ====================
    # interfaces include:
    #   Interfaces:
    #       interface_1
    #       ...
    parser_data.setdefault('interfaces', list(_parse_interfaces(root))) 
    # ====================

    # ====================
    # parse Volatile
    # ====================
    parser_data.setdefault('volatile', dict(_parse_volatile(root)))
    # ====================

    # ====================
    # parse properties
    # ====================
    parser_data.setdefault('properties', dict(_parse_properties(root)))
    # ====================

    # ====================
    # parse methods
    # ====================
    for mtag in MTAGS:
        methods = root.find(mtag)
        parser_data.setdefault(mtag.lower(), dict(_parse_methods(methods)))

    return parser_data


def _iter_interface_struc(interfaces: list, file_path):
    from os.path import join as _pjoin, dirname
    from functools import partial

    get_ipath = partial(_pjoin, dirname(file_path), 'interfaces')

    sstack = []
    sstack.extend(interfaces)

    _yielded_set = set()

    while sstack:
        iname = sstack.pop()

        if iname in _yielded_set:
            raise DefInvalidError('Cirtular reference in interfaces')

        ipath = get_ipath(iname + '.def')
        istruc = parse_def_file(ipath)

        if 'interfaces' in istruc:
            iis = istruc['interfaces']
            if iis:
                sstack.extend(iis)
        yield iname, istruc
        _yielded_set.add(iname)

    del sstack
    del _yielded_set


def get_merged_def(file_path):
    main_def = parse_def_file(file_path)

    if 'interfaces' in main_def:
        for _tag in list(MTAGS) + ['Properties'] + ['volatile']:
            _tag = _tag.lower()
            for iname, istruc in _iter_interface_struc(
                    main_def['interfaces'], file_path):
                for k, v in istruc.get(_tag, {}).items():
                    main_def.setdefault(_tag, {})
                    if k in main_def[_tag]:
                        raise DefInvalidError(
                            'Duplicated {} setting in {}'.format(_tag, iname))
                    main_def[_tag][k] = v

        main_def.pop('interfaces')
    return main_def

