# ESTA Developers Guide

ESTA is a Python-based modeling system. As such, it is designed as a stand-alone program inside a working environment, and not as an installable Python library.

> TODO: This guide is incomplete.

## Design Goals

Modularity is the primary design goal for ESTA. Applying spatial surrogates and gridding an inventory is not, generally, a hard problem. The hard work it typically: (1) file wrangling, and (2) the need for continuous updating.

TODO

## Architecture and Code Structure

ESTA makes use of Python's basic object-oriented functionality to achieve the modularity described above. Each step in the modeling process is defined by an abstract class. And the classes listed in the config files are subclasses of those, designed for a particular emissions or file type. In addition, a few very general data structures are defined to hold the: emissions data, spatial surrogates, temporal surrogates, and final gridded emissions.

TODO

#### Technology

TODO

#### General Structure

TODO

#### The Core

TODO

#### ESTA Data Structures

TODO


## Important Algorithms

TODO

* Sparse-Matrix Design: Because many sub-areas will be involved in a larger modeling domain (grid)
* KD Trees Algorithm: Efficient intersection of links onto projected modeling domain

## Developing for ESTA

TODO

## Implementing Your Own Step

TODO

## Defining a New Domain

TODO


[Back to Main Readme](../README.md)
