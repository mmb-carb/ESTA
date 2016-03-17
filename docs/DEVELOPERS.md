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

Here is a basic diagram of ESTA's code structure, including some default on-road classes:

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

To correspond with each of the five major gridding steps, there is a section in the config file which matches to a class path in the `src` folder:

    [Emissions] --> src.emissions
    [Surrogates] --> src.surrogates
    [Scaling] --> src.scaling
    [Output] --> src.output
    [Testing] --> src.testing

#### The Core

As seen above, the ESTA code base has modules for each of the ESTA gridding steps. But the classes in these modules are simply subclasses of those in the core. So to understand the function of ESTA, you only need to understand the core. The rest are implementation details specific to the science involved. The easiest file to understand is `version.py`, which sets the current version of ESTA, which is printed to the screen during each run. Each step in the gridding process is represented in ESTA by an abstract class in `src.core`:

    **emissions loading** --> `EmissionsLoader`
    **spatial surrogate loading** --> `SpatialLoader`
    **temporal surrogate loading** --> `TemporalLoader`
    **emissions scaling step** --> `EmissionsScaler`
    **output writing** --> `OutputWriter`
    **QA/QC** --> `OutputTester`

Notice that in the config file there is a single major section for `[Surrogates]`, but under the hood there are separate abstract classes for spatial surrogates and temporal surrogates. This was a design choice to leave open the option that a single file might represent the spatial and temporal distribution of the emissions, so they would have to be loaded by the same class.

#### ESTA Data Structures

The ESTA model is designed to be independent of the data structures that are passed between each modeling step.  That is, there are no data structures defined in `src.core`, and the abstract step classes in `src.core` are independent of the data structure used. However, in order for the steps to work together, the subclasses of each step will have to be designed with knowledge of the data structures used.

For instance, in the master run script `src.core.esta_model.py`, you will find the following lines in the `EstaModel` class:

    for emis_loader in self.emis_loaders:
        self.emissions = emis_loader.load(self.emissions)

    self.scaled_emissions = self.emis_scaler.scale(self.emissions, self.spatial_surrs,
                                                   self.temporal_surrs)

Here you can see that the emissions loader instance (subclassed from `EmissionsLoader`) saves the emissions in a generic `self.emissions` variable. But in order for the next step (scaling) to use that variable, it will have to understand the data structure in `self.emissions`. In the the case of on-road emissions processing with EMFAC2014 (a default case, that comes with ESTA), `self.emissions` is of type `EmissionsTable`.

ESTA comes with several helpful data structures specifically designed for the emissions gridding process:

 * from src.emissions.emissions_table import EmissionsTable
  * A subclass of Python's `collections.defaultdict`
  * Two levels of keys: EIC and pollutant
  * final value is emissions
 * from src.emissions.sparce_emissions import SparceEmissions
  * A subclass of Python's `collections.defaultdict`
  * Two levels of keys: grid cell tuple and pollutant
  * Final value is Emissions
 * from src.emissions.scaled_emissions import ScaledEmissions
  * simple multi-level dictionary container
  * the keys are, in order: subarea, date, hr, eic
  * the values are of type `SparceEmissions`
 * from src.surrogates.spatial_surrogate import SpatialSurrogate
  * A subclass of Python's `collections.defaultdict`
  * key is a grid cell location tuple
  * value is fraction of the emissions in that grid cell
 * from src.surrogates.temporal_surrogate import TemporalSurrogate
  * A subclass of Python's `array.array`
  * The array has length 24
  * Elments of array sum to 1.0

## Important Algorithms

This section is by no means meant to be an exhaustive study of all the algorithms used in ESTA. This is meant only to highlight those algorithms that were key in the design.

#### Sparce Matrix Design

Sparce-matrix design is important to ESTA. The term "sparce-matrix" is used here to describe the design goal of describing the spatial distribution of emissions (or spatial surrogates) using a collection of key-value pairs, where the key is a two or three-dimensional tuple describing a grid cell and the value is an emission value or fraction. This is an alternative to simply defining a ROW-by-COLUMN dimensional array to store a value in every grid cell in the modeling domain. The reason a sparce matrix approach was chosen in ESTA is that it is very common for most of the grid cells in a modeling domain to have zero values. And in most scenarios, modeling will take a lot less memory if a sparce matrix approach is used

In the section above on ESTA's native data structures, the classes `SparceEmissions` and `SpatialSurrogate` use this sparce matrix design.

#### KD Trees

The [KD Trees Algorithm][KDTrees] is fundamental in the performance of the on-road and aircraft emissions modeling in ESTA. The KD Trees algorithm is a space-partitioning data structure that is used in ESTA to dramatically improve the speed of locating lat/lon coordinates on the modeling grid.

The problem that needs to be solved (as quickly and accurately as possible) is this: given a lat/lon pair, determine which grid cell it is inside on the modeling domain. The problem is that the modeling grid can be arbitarily large, and searching through every grid cell is prohibitively slow. And the problem is further complicated by the fact that the modeling grid can be in any arbitrary projection. 

You can find an example of the usage of KD Trees in `src.surrogates.dtim4loader`. To further help speed up the grid cell identification, a sub-grid is isolated for each region (in this case county) on the grid and a KD Tree is created for that region:

    def _create_kdtrees(self):
        """ Create a KD Tree for each county """
        lat_vals = self.lat_dot[:] * self.rad_factor
        lon_vals = self.lon_dot[:] * self.rad_factor

        for county in self.counties:
            # find the grid cell bounding box for the county in question
            lat_min, lat_max = self.county_boxes[county]['lat']
            lon_min, lon_max = self.county_boxes[county]['lon']

            # slice grid down to this county
            latvals = lat_vals[lat_min:lat_max, lon_min:lon_max]
            lonvals = lon_vals[lat_min:lat_max, lon_min:lon_max]

            # create tree
            clat,clon = cos(latvals),cos(lonvals)
            slat,slon = sin(latvals),sin(lonvals)
            triples = list(zip(np.ravel(clat*clon), np.ravel(clat*slon), np.ravel(slat)))
            self.kdtrees[county] = cKDTree(triples)

This only works because we happen to know the county the lat/lon pair belongs in before we try to locate it on the grid:

    def _find_grid_cell(self, p, county):
        ''' Find the grid cell location of a single point in our 3D grid.
            (Point given as a tuple (height in meters, lon in degrees, lat in degrees)
        '''
        lat_min, lat_max = self.county_boxes[county]['lat']
        lon_min, lon_max = self.county_boxes[county]['lon']

        # define parameters
        lon0 = p[0] * self.rad_factor
        lat0 = p[1] * self.rad_factor

        # run KD Tree algorithm
        clat0,clon0 = cos(lat0),cos(lon0)
        slat0,slon0 = sin(lat0),sin(lon0)
        dist_sq_min, minindex_1d = self.kdtrees[county].query([clat0*clon0, clat0*slon0, slat0])
        y, x = np.unravel_index(minindex_1d, (lat_max - lat_min, lon_max - lon_min))

        return lat_min + y + 1, lon_min + x + 1

The end result of this technology is that these two methods were found to be a couple thousand times faster than the naive search of the entire grid for the default on-road-with-EMFAC2014 scenario.

## Developing for ESTA

ESTA is designed to be easily expanded by developers. The modular design means that changing the function of ESTA doesn't require touching the whole code base. Whether you want to read a different type of emissions file, add a special kind of spatial surrogate, or write a new type of output file, you should be able to do that buy writing a single class and dropping it into a `src` module.

A common problem for scientists and engineers is that they spend more time wrangling the files that go into or come out of a model than they do analyzing their data. The goal of ESTA is to define a clean modeling framework so that only a single class needs to be read and your files will be handled. The goal of software should always be to help people get things done, not to be a drain on their time. For that reason, ESTA is 100% configurable and makes no demands on the structure of your input/output files or on the data structures you pass around.

## Implementing Your Own Step

Perhaps the most important design goal in ESTA is the ability to replace a step with one of your own. To that end, let's look at an example of doing just that. In the example below, we create a special temporal surrogate: `RushHour`. In this new temporal surrogate, all onroad traffic will happen in two hours of the day (8AM and 5PM), the other 22 hours of the day will have no traffic.

The first thing to do when implementing `RushHour` will be to sub-class the temporal surrogate loader `TemporalLoader` in `src.core.temporal_loader.py`:

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
            └───domains/county_boxes_ca_4km.py
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

    ESTA/input/defaults/domains/preprocess_grid_boxes.py

This script should be fairly easy to use. For example, if you wanted to generate the grid domain boxes for the counties in California for California's 12km ARB-CalEPA modeling domain, you would simply go to the command line and do:

    cd input/defaults/domains/
    python preprocess_grid_boxes.py -gridcro2d GRIDCRO2D.California_12km_97x107 -rows 97 -cols 107  -regions california_counties_lat_lon_bounding_boxes.csv

And this would print a nicely-formatted dictionary (JSON/Python) to the screen, which you can copy to a file for your own use.  NOTA BENE: If you enter a lat/lon bounding box outside your stated grid domain, this script will return a non-sensical bounding box.


[Back to Main Readme](../README.md)


[KDTrees][https://en.wikipedia.org/wiki/K-d_tree]
