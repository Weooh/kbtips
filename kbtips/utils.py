# coding: utf-8
import os


def get_kbe_script_path(kbe_root):
    root = os.path.abspath(kbe_root)
    return os.path.join(root, 'assets', 'scripts', '')


def get_kbe_base_path(kbe_root):
    scripts = get_kbe_script_path(kbe_root)
    return os.path.join(scripts, 'base', '')


def get_kbe_cell_path(kbe_root):
    scripts = get_kbe_script_path(kbe_root)
    return os.path.join(scripts, 'cell', '')


def get_entity_def_path(kbe_root, name='entity_defs'):
    scripts = get_kbe_script_path(kbe_root)
    return os.path.join(scripts, name, '')

