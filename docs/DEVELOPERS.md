# ESTA Developers Guide

ESTA is a Python-based model. As such, it is designed as a stand-alone program inside a working environment, and not as an installable Python library. The purpose of this document is to aquaint a potential developer with the ESTA code base so they can add new components and make updates to the model. A solid understanding of object-oriented programming in Python is assumed.

## Design Goals

Modularity is the primary design goal for ESTA. Applying spatial surrogates and gridding an inventory is not, generally, a hard problem. The hard work it typically: (1) file wrangling, and (2) the need for continuous updating. The goal is that ESTA should be sufficiently generic to allow for the gridding of any emission inventory, not just on-road inventories (where were the first, primary use of the model).

The term modularity here is used to describe a model whose operation can be changed greatly by the non-programming end-user through a simple config file. The process of gridding an inventory is broken into six steps, each of which is defined by a piece of code that is independent and replacable. In this way, the end-user can simply ask for different choices for each step, and gain great power over their ESTA model run.

ESTA needs to be able to run easily from the command line in Linux. Though would be beneficial if it ran under the Mac OS and Windows as well. ESTA was also developed for Python 2.7, though it should not be hard to support Python 2.6 and 3.x as well. This would be ideal.

## Architecture and Code Structure

ESTA makes use of Python's object-oriented functionality to achieve the modularity described above. Each step in the modeling process is defined by an abstract class. And users select which versions of each step they want in the config file by directly listing the class names. In addition, a few very general data structures are defined to hold the: emissions data, spatial surrogates, temporal surrogates, and final gridded emissions.

What follows is a quick introduction into ESTAs basic code structure. Not every subclass of the core abstract classes will be shown, as ESTA will hopefully grow over time. Instead, a single example implementation of each core abstract class will be discussed.

#### General Structure

Here is a basic diagram of ESTA's code structure:

    ESTA
    │   esta.py
    │   README.md
    │   LICENSE
    │
    ├───config/
    ├───docs/
    ├───input/
    ├───output/
    └───src/
        ├───core/emissions_loader.py
        │        emissions_scaler.py
        │        esta_model_builder.py
        │        esta_model.py
        │        output_tester.py
        │        output_writer.py
        │        spatial_loader.py
        │        temporal_loader.py
        │        version.py
        │
        ├───emissions/emfac2014csvloader.py
        │             emfac2014hddslcsvloader.py
        │             emissions_table.py
        │             sparce_emissions.py
        │
        ├───output/pmeds1writer.py
        │
        ├───scaling/dtim4emfac2014scaler.py
        │           scaled_emissions.py
        │
        ├───surrogates/dtim4calvadtemporalloader.py
        │              dtim4loader.py
        │              spatial_surrogate.py
        │              temporal_surrogate.py
        │
        └───testing/emfac2014totalstester.py

The `esta.py` script in the home folder acts as an executable so the ESTA model can be run. It's major purpose is to take a path to the config file and call the `esta_model_builder.py` script, in `src.core`. The `esta_model_builder.py` script doesn't fully parse the config file, but it parses those parts of the config file where class names are listed for each gridding step.

For instance, when parsing the scaling step, a small section of code parses the config file and instantiates a list of classes to do the scaling:

    scaler_name = self.config['Scaling']['scalor']
    try:
        __import__('src.scaling.' + scaler_name.lower())
        mod = sys.modules['src.scaling.' + scaler_name.lower()]
        scaler = getattr(mod, scaler_name)(self.config)
    except (NameError, KeyError) as e:
        sys.exit('ERROR: Unable to find class: ' + scaler_name + '\n' + str(e))

Here you can see that the emissions-scaling classes must be found under `src.scaling.`, in a file name that is a lower case version of the full class name. For example, the class name `Dtim4Emfac2014Scaler` is used in the config file, and the above code tries to load that class in the following way:

    from src.scaling.dtim4emfac2014scaler import Dtim4Emfac2014Scaler

To correspond with each of the five major gridding steps, there is a section in the config file which matches to a class path in the src folder:

    [Emissions] --> src.emissions
    [Surrogates] --> src.surrogates
    [Scaling] --> src.scaling
    [Output] --> src.output
    [Testing] --> src.testing

#### The Core

As seen above, the ESTA code base has modules for each of the ESTA gridding steps. But the classes in these modules are simply subclasses of those in the core. So to understand the function of ESTA, you only need to understand the core. The rest are implementation details specific to the science involved. The easiest file to understand is `version.py`, which sets the current version of ESTA, which is printed to the screen during each run. Let us go through each of the core gridding steps by referencing their abstract classes.

The **emissions loading** step is generically defined by the abstract class `EmissionsLoader`.

The **spatial surrogate loading** step is generically defined by the abstract class `SpatialLoader`.

The **temporal surrogate loading** step is generically defined by the abstract class `TemporalLoader`.

The **emissions scaling step** is generically defined by the abstract class `EmissionsScaler`.

The **output writing** step is generically defined by the abstract class `OutputWriter`.

The **QA/QC** step is generically defined by the abstract class `OutputTester`.

TODO

#### ESTA Data Structures

Inside the core module `src.core`, there are [[[TODO: untrue]]] data structures defined to help organize the flow of data through ESTA. These are... [[[TODO]]]

TODO

## Important Algorithms

This section is by no means meant to be an exhaustive study of all the algorithms used in ESTA. This is more a place to outline some key points in the design.

#### Sparce Matrix Design

Sparce-matrix design is important to ESTA. The term "sparce-matrix" is used here to describe the design goal of describing the spatial distribution of emissions (or spatial surrogates) using a collection of key-value pairs, where the key is a two or three-dimensional tuple describing a grid cell and the value is a emission value or fraction. This is an alternative to simply defining a ROW-by-COLUMN dimensional array to store a value in every grid cell in the modeling domain. The reason a sparce matrix approach was chosen in ESTA is that it is very common for most of the grid cells in a modeling domain to have zero values. And in most scenarios, modeling will take a lot less memory if a sparce matrix approach is used

In the section above on ESTA's native data structures, the classes [[[TODO]]] and [[[TODO]]] use this sparce matrix design.


As seen in the data structures above: TODO and TODO, the spatial surrgates and emissions passed between steps in ESTA are done so using

TODO

#### KD Trees

* KD Trees Algorithm: Efficient intersection of links onto projected modeling domain

## Developing for ESTA

TODO

## Implementing Your Own Step

TODO

## Defining a New Domain

It is fairly simple to implement a new modeling domain in ESTA for both on-road and aircraft emissions gridding. They both depend on finding (or creating) a CMAQ-ready `GRIDCRO2D` file. This is a CMAQ-standard file, with a long history, that defines the lat/lon bounding boxes of each grid cell in a modeling domain. The decision was made to use these files as the best way to define the grid because:

1. It is a well-established file format.
2. People who need gridded emissions inventories will frequently already have this file for their domain.
3. It is an extremely detailed format.
4. It is lat-lon based (and thus projection-free).
5. It is unamiguous.

The `GRIDCRO2D` file is not the only file you need to define your new domain. There is one more, the region boxes file. To speed up the process of locating which grid cell a certain lat/lon point is in on your modeling domain, your domain is split up into rectangular regions (one for each county, state, or whatever). This will give a much smaller region for Python to hunt in. You will find examples of these files for the three default cases in the input folder:

    ESTA
    └───input
        └───defaults
            └───california/county_boxes_ca_4km.py
                           county_boxes_ca_12km.py
                           county_boxes_scaqmd_4km.py

These files are simple Python dictionaries that map the county a grid cell bounding box in a particular domain, e.g.:

    {1: {'lon': (130, 154), 'lat': (152, 168)},
     2: {'lon': (177, 195), 'lat': (180, 193)},
     3: {'lon': (158, 184), 'lat': (160, 188)},
     ...
    }

If your domain is very small, or you want to quickly test a new domain, you could easily mock up one of these regional boxes file by defaulting every box to the entire grid. For instance, if the domain is 100 rows by 200 columns:

    {1: {'lon': (0, 199), 'lat': (0, 99)},
     2: {'lon': (0, 199), 'lat': (0, 99)},
     3: {'lon': (0, 199), 'lat': (0, 99)},
     ...
    }

But there is a better way. Whether you are working with the counties, states, or whatever. Chances are you already know the bounding boxes of your regions in lat/lon. Or you can at least come up with some. If so, there is a script you can use to generate the regional boxes file. It is in the default EMFAC input directory next to the GRIDCRO2D input files:

    ESTA/input/defaults/emfac2014/preprocess_grid_boxes.py

TODO: Build an example of this for US states


[Back to Main Readme](../README.md)
