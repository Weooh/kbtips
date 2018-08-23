# coding: utf-8
import argparse
import glob
import os

import gens
import utils



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--kbe-path', type=str, 
                        help='KBEngine project root path',
                        required=True)
    return parser

def main():
    _parser = parse_args()
    args = _parser.parse_args()

    kbe_root = args.kbe_path
    kbe_base = utils.get_kbe_base_path(kbe_root)
    kbe_cell = utils.get_kbe_cell_path(kbe_root)
    kbe_defs = utils.get_entity_def_path(kbe_root)

    types_fp = os.path.join(kbe_defs, 'types.xml')
    defs_fps = glob.iglob(os.path.join(kbe_defs, '*.def'))

    # ---------
    # counts
    s_count = 0
    f_count = 0
    # ---------

    types_op = os.path.join(kbe_defs, 'def_types.pyi')
    print('[-] Generate types file located at: "{}" ...'.format(types_fp))
    try:
        gens.gen_types_file(types_fp, types_op)
    except Exception as err:
        print('[E] Genrate types file failed.', err)
        f_count += 1
    else:
        print('[S] Generate types file succeed at: "{}"'.format(types_op))
        s_count += 1

    imports = """from def_types import *"""

    for defs_fp in defs_fps:
        defs_name = os.path.basename(defs_fp).split('.')[0] + '.pyi'
        print('[-] Generate def file located at: "{}" ...'.format(defs_fp))
        try:
            gens.gen_defs_file(
                defs_fp,
                c_p=os.path.join(kbe_cell, defs_name),
                c_imps=imports,
                b_p=os.path.join(kbe_base, defs_name),
                b_imps=imports)
        except Exception as err:
            print('[E] Genrate def file failed.', err)
            f_count += 1
        else:
            print('[S] Generate def file succeed.')
            s_count += 1

    print(' ----------------------------------------')

    if f_count:
        print('generate done, some failed')
        print('succeed: {}'.format(s_count))
        print('failed: {}'.format(f_count))
        exit(f_count)
    else:
        print('generate all completed')
        print('succeed: {}'.format(s_count))
        print('failed: {}'.format(f_count))


if __name__ == '__main__':
    main()
