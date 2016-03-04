# ESTA User's Guide

The purpose of this document is to show new users how to run ESTA. This does not present what ESTA does, or what it exists, you will find that [here](USER_DOCS.md).

## How to Run a Default Case

ESTA comes with some default configuration and input files, so you can test the model and learn how to use it. The first test is to generate on-road emissions on the 4km California modeling domain. Go to the command line and type:

    ./esta.py config/default_onroad_ca_4km.ini

Or you can type:

    python esta.py config/default_onroad_ca_4km.ini

The default examples included with ESTA are designed to be fast, and should finish in well under a minute on a modern computer.

## Config Files

The configuration (config) files used in ESTA are divided into sections. This makes the config files easier to read and keeps them organized. But there are no required fields in any section; the config files are very general and will change greatly dependent upon your run. That being said, there are a few general principles that can help you understand how to run ESTA.

### General Config Ideas

The config files used in ESTA are a common format, defined by the Python standard library `ConfigParser`. You can find the developer's documentation on `ConfigParser` [here](https://docs.python.org/2/library/configparser.html) and some basic introductory information for everybody [here](https://wiki.python.org/moin/ConfigParserExamples).

There are a few features of the config files to note:

* **Section headers** are defined inside square brackets `[Dates]`.
* **Config variables** must be on their own line, following a section header line. And the value of the config variable comes after a colon and a space.
* **Variables have string values.** Whatever follows the colon is the string value of the variable. If you want an integer, you will have to convert from strint to integer in the code later.
 * **Lists are spaced-separated.** You could certainly do this another way, but in ESTA, we separate list items with spaces.
* **Comments** are lines where the first character is the pound/hashtag symbol (`#`). This is a reduced case of the Python comment notation, where you can have just part of a line be a comment.

### Choose a class

* Direct class inheritance by string, and Python will wire them together

### Standard Sections, one-by-one

TODO

## Input Files

The default example config files that come package with ESTA each list a great number of input files. The input files cover things like emissions, spatial distributions, temporal distributions, regional boundaries, EIC groupings, and more. It is important to understand what most of these files are, so that you can make your own choices when designing your first config file.

#### Input Files - Gridding

TODO: This guide is incomplete.

#### Input Files - EMFAC2014 On-Road

TODO: This guide is incomplete.


[Back to Main Readme](../README.md)
