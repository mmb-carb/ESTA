#! /usr/bin/env python

import os
import sys
from src.core.custom_parser import CustomParser
from src.core.esta_model_builder import EstaModelBuilder
from src.core.esta_model import EstaModel


def main():
    # command line parsing
    config_file_path = ''
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--h', '-help', '--help']:
        usage()
    elif len(sys.argv) == 2:
        config_file_path = sys.argv[1]
    else:
        usage()

    if not os.path.exists(config_file_path):
        sys.exit('\nERROR: Config file not found: %s\n' % config_file_path)

    # config file parsing
    config = CustomParser(config_file_path)

    # ESTA processing
    model = esta_preprocess(config)
    esta_process(config, model)
    esta_postprocess(config, model)


def esta_preprocess(config_dict):
    '''Pre-process ESTA Model'''
    builder = EstaModelBuilder(config_dict)
    return builder.build()


def esta_process(config_dict, model):
    '''Process ESTA Model'''
    model.process()


def esta_postprocess(config_dict, model):
    '''Perform various post-processing steps, if necessary'''
    model.postprocess()


def usage():
    help_text = '''\nESTA Model Usage:
\tGive a path to a config file, or default.ini will be used:
\t./esta.py config/default.ini
\tpython esta.py /path/to/user-defined.ini
'''
    print(help_text)
    sys.exit()


if __name__ == '__main__':
    main()
