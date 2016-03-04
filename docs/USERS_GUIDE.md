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

### Choosing a Class

In order for ESTA to be useful, it has to be easy for the user to design their own run. Each step in the ESTA model chain has various options. For instance, if you are reading in some kind of emissions file, there will have to be a different `class` designed to read that file type in ESTA. In order to select that class, all you have to do is list it's name in the config file. For instance, in the default config file "default_onroad_ca_4km.ini":

    [Scaling]
    scalor: Dtim4Emfac2014Scaler

If you look in the source code, you will find that class:

    from src.scaling.dtim4emfac2014scaler import Dtim4Emfac2014Scaler

If you list more than one class, both will be run in the order you listed them. This direct reference to the class name gives the user a huge amount of flexibility in how they run ESTA. Generally, most users will only have to design their run once, and they will probably be able to do most of their work with only slight modifications to their original config file.

### Standard Config Sections

There are five major steps in the emissions inventory gridding process, each of which have a dedicated section in the ESTA config files:

1. **Reading Emissions**
2. **Reading/Creating Spatial/Temporal Surrogates**
3. **Emissions Scaling**
4. **Output File Creation**
5. **QA/QC**

In addition to those, ESTA has four other standard config sections:

1. **Dates** - define the the time span of the run
2. **Subareas** - define the counties, states, or other regions in your run
3. **Grid Information** - define your modeling domain
4. **Miscellaneous** - a catch all, for shared resources or anything you want

Next, the nine sections above will be discussed in some detail, using examples from the default config files that are provided with ESTA.

#### Dates

TODO

#### Subareas

TODO

#### GridInfo

TODO

#### Surrogates

TODO

#### Emissions

TODO

#### Scaling

TODO

#### Output

TODO

#### Testing

TODO

#### Misc

TODO


[Back to Main Readme](../README.md)
