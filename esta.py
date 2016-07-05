#! /usr/bin/env python

import os
import sys
from src.core.custom_parser import CustomParser
from src.core.esta_model_builder import EstaModelBuilder


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

    process_esta(config_file_path)


def process_esta(config_file_path):
    ''' Parse config file, then
        initialize and run ESTA model
    '''
    # config file parsing
    config = CustomParser(config_file_path)

    # build ESTA model chain, based on config file
    builder = EstaModelBuilder(config)
    model = builder.build()

    # Run the ESTA Model
    model.process()

    # Perform various post-processing or QA steps, if necessary
    model.postprocess()


def usage():
    help_text = '''\n\nESTA Model Usage
\nSimply provide the path to a config file:\n
\t python esta.py config/default_onroad_ca_4km.ini
\t./esta.py /path/to/user_defined_config.ini\n
'''
    print(help_text)
    sys.exit()


if __name__ == '__main__':
    main()
