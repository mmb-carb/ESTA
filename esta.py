#! /usr/bin/env python

import os
import sys
from src.core.custom_parser import CustomParser
from src.core.esta_model_builder import EstaModelBuilder


def main():
    ''' Parse the command line arguments provided,
        and run ESTA if the arguments are valid.
    '''
    # if no input files are given, show help menu
    if len(sys.argv) < 2:
        usage()

    # if help flag is given, show help menu
    for arg in sys.argv[1:]:
        if arg.lower() in ['-h', '--h', '-help', '--help']:
            usage()

    # process input INI file(s)
    for config_file_path in sys.argv[1:]:
        if not os.path.exists(config_file_path):
            print('\n\nERROR: Config file not found: %s\n\n' % config_file_path)
            continue

        process_esta(config_file_path)


def process_esta(config_file_path):
    ''' Parse config file, then initialize and run ESTA model
    '''
    # config file parsing
    config = CustomParser(config_file_path)

    # build ESTA model chain, based on config file
    builder = EstaModelBuilder(config)
    model = builder.build()

    # run the ESTA Model
    model.run()


def usage():
    ''' In the event that the command line arguments to this script are invalid,
        print a very brief help menu, describing how to run ESTA from the command line.
    '''
    help_text = '''\n\nESTA Model Usage
\nSimply provide the path to a config file:\n
\t python esta.py config/example_onroad_ca_4km_txt_simple.ini
\t./esta.py /path/to/user_defined_config.ini\n
'''
    print(help_text)
    sys.exit()


if __name__ == '__main__':
    main()
