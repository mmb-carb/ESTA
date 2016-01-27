#! /usr/bin/env python

import ConfigParser
import sys
from src.core.esta_model_builder import EstaModelBuilder
from src.core.esta_model import EstaModel
# TODO: from src.testing.surrogate_plotter import SurrogatePlotter


def main():
    # command line parsing
    config_file_path = 'default.ini'
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--h', '-help', '--help']:
        usage()
    elif len(sys.argv) == 2:
        config_file_path = sys.argv[1]
    elif len(sys.argv) > 2:
        usage()

    # config file parsing
    config = ConfigParser.ConfigParser()
    config.read(config_file_path)
    config_dict = config_to_dict(config)

    # ESTA processing
    model = esta_preprocess(config_dict)
    esta_process(config_dict, model)
    # TODO: esta_postprocess(config_dict, model)


def esta_preprocess(config_dict):
    '''Pre-process ESTA Model'''
    builder = EstaModelBuilder(config_dict)
    return builder.build()


def esta_process(config_dict, model):
    '''Process ESTA Model'''
    model.process()


def gate_postprocess(config_dict, model):
    '''Perform various post-processing steps, if necessary'''
    if config_dict['Testing']['plot_surrogates'] == 'True':
        print('''\nPerform various post-processing steps''')
        s = SurrogatePlotter(model.surrogates, config_dict['Testing']['surr_plot_dir'])
        s.plot_runways()


def usage():
    help_text = '''\nESTA Model Usage Notes:
\tGive a path to a config file, or default.ini will be used:
\tpython gate.py
\tpython gate.py default.ini
\tpython gate.py user-defined.ini
'''
    print(help_text)
    sys.exit()


def config_to_dict(config):
    '''Quickly convert config options into a dictionary'''
    config_dict = {}
    for section in config.sections():
        config_dict[section] = {}
        options = config.options(section)
        for option in options:
            try:
                config_dict[section][option] = config.get(section, option)
            except:
                print("Exception parsing config file for section/option: %s/%s" % (section, option))
                config_dict[section][option] = None

    return config_dict


if __name__ == '__main__':
    main()
