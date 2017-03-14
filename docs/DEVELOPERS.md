# ESTA Developers Guide

ESTA is a Python-based model. It is designed as a stand-alone program inside a working environment, not as an installable Python library. The purpose of this document is to aquaint a potential developer with the ESTA code base so they can add new components and make updates to the model. An understanding of object-oriented programming in Python is assumed.

## Design Goals

Modularity is a primary design goal for ESTA. Applying spatial surrogates and gridding an inventory is not, generally, a hard problem. The hard work is typically: (1) file wrangling, and (2) the need for continuous updating. The goal is that ESTA should be sufficiently generic to allow for the gridding of any emission inventory, not just on-road inventories (which were the first, primary use of the model).

The term modularity here is used to describe a model whose operation can be changed greatly by the non-programming end-user through a simple config file. The process of gridding an inventory is broken into six steps, each of which is defined by a piece of code that is independent and replacable. In this way, the end-user can simply ask for different choices for each step, and gain great power over their ESTA model run.

ESTA was developed for Python 2.7.x, and needs to be able to run from the command line in a Linux environment. It should also run under Windows and the Mac OS, though these are not tested as often.

## Architecture and Code Structure

ESTA makes use of Python's object-oriented functionality to achieve the modularity described above. Each step in the modeling process is defined by an abstract class. And users select which versions of each step they want in the config file by directly listing the class names. In addition, a few very general data structures are defined to hold the: emissions data, spatial surrogates, temporal surrogates, and final gridded emissions.

What follows is a quick introduction into ESTAs basic code structure. Not every subclass of the core abstract classes will be shown, as ESTA will hopefully grow over time. Instead, a single example implementation of each core abstract class will be discussed.

#### General Structure

Here is a basic diagram of ESTA's code structure, including some default on-road classes:

    ESTA
    ├─── esta.py
    ├─── LICENSE
    ├─── README.md
    ├─── requirements.txt
    │
    ├─── config/
    ├─── docs/
    ├─── input/
    ├─── output/
    └─── src/
         ├─── core/custom_parser.py
         │         date_utils.py
         │         eic_utils.py
         │         emissions_loader.py
         │         emissions_scaler.py
         │         esta_model.py
         │         esta_model_builder.py
         │         output_files.py
         │         output_tester.py
         │         output_writer.py
         │         spatial_loader.py
         │         temporal_loader.py
         │         version.py
         │
         ├─── emissions/emfac2014csvloader.py
         │              emfac2014hddslcsvloader.py
         │              emissions_table.py
         │              sparce_emissions.py
         │
         ├─── output/cmaqnetcdfwriter.py
         │           pmeds1writer.py
         │
         ├─── scaling/emfac2cmaqscaler.py
         │            emfacsmokescaler.py
         │            scaled_emissions.py
         │
         ├─── surrogates/calvadsmoke4spatialsurrogateloader.py
         │               calvadtemporalloader.py
         │               dtim4loader.py
         │               spatial_surrogate.py
         │               temporal_surrogate.py
         │
         ├─── testing/emfacncftotaltester.py
         │            emfacpmedsdiurnaltester.py
         │            emfacpmedstotaltester.py

The `esta.py` run script in the home folder acts like an executable so the ESTA model can be run. Its major purpose is to take a path to the config file and call the `src.core.esta_model_builder.py` script. The `esta_model_builder.py` script breaks the config file into sections and options using the `CustomParser` class in `src.core.custom_parser.py`.

For instance, when parsing the scaling step, a small section of code parses the config file and instantiates a list of classes to do the scaling:

    scaler_name = self.config['Scaling']['scalor']
    try:
        __import__('src.scaling.' + scaler_name.lower())
        mod = sys.modules['src.scaling.' + scaler_name.lower()]
        scaler = getattr(mod, scaler_name)(self.config)
    except (NameError, KeyError) as e:
        sys.exit('ERROR: Unable to find class: ' + scaler_name + '\n' + str(e))

Here you can see that the emissions-scaling classes must be found under `src.scaling.`, in a file name that is a lower case version of the full class name. For example, the class name `EmfacSmokeScaler` is used in the config file, and the above code tries to load that class in the following way:

    from src.scaling.emfacsmokescaler import EmfacSmokeScaler

This approach offers a lot of flexibility. The developer only has to add a reference to their new class in a config file to wire into the model. If a new class is added to a file with the wrong name, the developer will see an error message clearly printing the desired file path

Corresponding to each of the five major gridding steps, there is a section in the config file which matches to a class path in the `src` folder:

    [Emissions] --> src.emissions
    [Surrogates] --> src.surrogates
    [Scaling] --> src.scaling
    [Output] --> src.output
    [Testing] --> src.testing

#### The Core

As seen above, the ESTA code base has modules for each of the ESTA gridding steps. But the classes in these modules are simply subclasses of those in the core. So to understand the function of ESTA, you only need to understand the core. The rest are implementation details specific to the science involved. The easiest file to understand is `version.py`, which sets the current version of ESTA, which is printed to the screen at the beggining of each run. Each step in the gridding process is represented in ESTA by an abstract class in `src.core`:

    **emissions loading** --> `EmissionsLoader`
    **spatial surrogate loading** --> `SpatialLoader`
    **temporal surrogate loading** --> `TemporalLoader`
    **emissions scaling step** --> `EmissionsScaler`
    **output writing** --> `OutputWriter`
    **QA/QC** --> `OutputTester`

Notice that in the config file there is a single major section for `[Surrogates]`, but under the hood there are separate abstract classes for spatial surrogates and temporal surrogates. This was a design choice to leave open the option that a single file might represent the spatial and temporal distribution of the emissions, so they would have to be loaded by the same class.

#### ESTA Data Structures

The ESTA model is designed to be independent of the data structures that are passed between each modeling step.  That is, there are no data structures defined in `src.core`, and the abstract step classes in `src.core` are independent of the data structure used. However, in order for the steps to work together, the subclasses of each step will have to be designed with knowledge some data structures to pass data around.

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
 * final value is emissions (a float)
* from src.emissions.sparce_emissions import SparceEmissions
 * A subclass of Python's `collections.defaultdict`
 * Two levels of keys: grid cell tuple and pollutant
 * final value is emissions (a float)
* from src.emissions.scaled_emissions import ScaledEmissions
 * simple multi-level dictionary container
 * the keys are, in order: region, date, hr, eic
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

The [KD Trees Algorithm][KDTrees] is fundamental to the performance of the on-road modeling in ESTA. The KD Trees algorithm is a space-partitioning algorithm that is used in ESTA to dramatically improve the speed of locating lat/lon coordinates on the modeling grid.

The problem that needs to be solved (as quickly and accurately as possible) is this: given a lat/lon pair, determine which grid cell it is inside on the modeling domain. The problem is that the modeling grid can be arbitarily large, and searching through every grid cell is prohibitively slow. And the problem is further complicated by the fact that the modeling grid can be in any arbitrary projection.

You can find an example of the usage of KD Trees in `src.surrogates.dtim4loader`. To further help speed up the grid cell identification, a sub-grid is isolated for each region (in this case county) on the grid and a KD Tree is created for that region:

    def _create_kdtrees(self):
        """ Create a KD Tree for each county / GAI / region """
        lat_vals = self.lat_dot[:] * self.rad_factor
        lon_vals = self.lon_dot[:] * self.rad_factor

        for region in self.counties:
            # find the grid cell bounding box for the region in question
            lat_min, lat_max = self.region_boxes[region]['lat']
            lon_min, lon_max = self.region_boxes[region]['lon']

            # slice grid down to this region
            latvals = lat_vals[lat_min:lat_max, lon_min:lon_max]
            lonvals = lon_vals[lat_min:lat_max, lon_min:lon_max]

            # create tree
            clat,clon = cos(latvals),cos(lonvals)
            slat,slon = sin(latvals),sin(lonvals)
            triples = list(zip(np.ravel(clat*clon), np.ravel(clat*slon), np.ravel(slat)))
            self.kdtrees[region] = cKDTree(triples)

This only works because we happen to know the region the lat/lon pair belongs in before we try to locate it on the grid:

    def _find_grid_cell(self, p, region):
        ''' Find the grid cell location of a single point in our 3D grid.
            (Point given as a tuple (height in meters, lon in degrees, lat in degrees)
        '''
        lat_min, lat_max = self.region_boxes[region]['lat']
        lon_min, lon_max = self.region_boxes[region]['lon']

        # define parameters
        lon0 = p[0] * self.rad_factor
        lat0 = p[1] * self.rad_factor

        # run KD Tree algorithm
        clat0,clon0 = cos(lat0),cos(lon0)
        slat0,slon0 = sin(lat0),sin(lon0)
        dist_sq_min, minindex_1d = self.kdtrees[region].query([clat0*clon0, clat0*slon0, slat0])
        y, x = np.unravel_index(minindex_1d, (lat_max - lat_min, lon_max - lon_min))

        return lat_min + y + 1, lon_min + x + 1

The end result of this technology is that these two methods were found to be a couple thousand times faster than the naive search of the entire grid for the default on-road-with-EMFAC simulations.


## File Formats

The modular design of ESTA allows a developer to easily read or write files of different formats at every stage of processing. However, the default version of ESTA comes with several types of input files unique to the ESTA processing of on-road emissions. The most unique are outlined below.


### eic_info.py

The `eic_info.py` file is used to help connect various data to each on-road Emission Inventory Codes (EICs) that we want to model.  The file contains a single Python dictionary mapping every EIC to a tuple containing the data we want associated with it.  The file will look something like:

    {71070111000000: (0, 'trips', 1.0),
     71070611000000: (0, 'vmt', 1.0),
     ...
     78076854100000: (25, 'vmt', 1.0)}

In particular, each EIC maps to a tuple with three elements:

1. The DTIM Column: The column (0-25) in the DTIM Link file that covers this EIC.
2. Spatial Surrogate Code: A string representing which SMOKE v4 spatial surrogate that is used to cover this EIC.
3. Scaling Fraction: This fraction is used to scale the emissions from this EIC. If the fraction is 1.0, the emissions are left unchanged. If the fraction is 0.5, you reduce the emissions by 50%. If the fraction is 3, you triple the emissions.

By default, there are two `eic_info.py` files that come with the standard ESTA distribution at:

    input/defaults/emfac2014/eic_info.py
    input/examples/onroad_emfac2014_santa_barbara/spatial_surrogates/eic_info.py

The first one is used for the default DTIM case, where the second column only points to "vmt" or "trips". But the second file is part of the Santa Barbara example, and the second tuple column points to SMOKE spatial surrogates for spatial disaggregation.


### gai_info.py

The `gai_info.py` file is an example "region_info" file in the "Regions" section of the config file.  This file contains a Python dictionary mapping each region code to a dictionary of attributes needed for the run.  Depending on your run configuration, you may not need *all* the information in this file.  And if you are developing your own ESTA modules you may want to put more information in this file, which is easily extensible.

The `gai_info.py` file has a dictionary of information for each GAI (because the example runs are by GAI). Each GAI has the following information:

* County [integer]
* Air Basin [2 or 3-letter code]
* District [2 or 3-letter code]
* Name [Long-Form County Name string, with District]


### vtp2eic.py

The `vtp2eic.py` file is used to map the EMFAC outputs to the EIC categories used by CARB.  EMFAC outputs emissions by vehicle categories such as:

    LDA, CAT, RUNEX

This is meant to represent "Light Duty Auto", "Catalytic Converter", and "Running Exhaust".  That is a great description, but CARB represents that using the EIC 71073411000000.  The `vtp2eic.py` file contains a singly Python dictionary mapping these EMFAC codes to EIC, for example:

    {('All Other Buses', 'DSL', 'IDLEX'): 77976512100000,
     ('All Other Buses', 'DSL', 'PMBW'): 77976854100000,
     ...
     ('UBUS', 'NCAT', 'STREX'): 76270111000000}


### NH3/CO CSV

The NH3/CO inventory CSV file contains the NH3 and CO emissions from all on-road EICs, for all regions in California. This file is necessary because EMFAC2014 does not output NH3 emissions from on-road sources, but the NH3 is important in photochemical modeling.  This file is used ad-hoc to calculate NH3 emissions from the CO emissions given by EMFAC.

An example NH3/CO CSV file is given at:

    input/defaults/emfac2014/nh3/rf2082_b_2012_20160212_onroadnh3.csv

The file format is used elsewhere at CARB, so several of the columns are unused:

* FYEAR - Unused
* CO - County [number]
* AB - Air Basin [2 or 3-letter code]
* DIS - District [2 or 3-letter code]
* FACID - Unused
* DEV - Unused
* PROID - Unused
* SCC - Unused
* SIC - Unused
* EIC - EIC [14-digit code]
* POL - Pollutant Code [CEIDARS numerical code]
* EMS - Emissions [decimal number in tons]


### Calvad Temporal Profiles CSVs

ESTA uses temporal profiles taken from real-world traffic measurements, aggregated by the Calvad database. In particular, ESTA includes two sets of on-road temporal profiles taken from Calvad: one for diurnal profiles and one for day-of-week profiles.

As Calvad is derived from real-world data, it only has three data types that are relevant to modeling using EMFAC2014: Light-Duty, Medium-Duty, and Heavy-Duty.  In addition, temporal profiles were added for one special case scenario: School Busses, whose driving patterns are quite regular.

The Calvad database was used to generate temporal profiles for 6 different weekday types: Sunday, Monday, Tuesday-through-Thursday, Friday, Saturday, and Holidays.


### Calvad Diurnal Factors CSV

The Calvad diurnal profiles are given by GAI, day-of-week, and the four Calvad vehicle types.  The CSV file format used is:

    REGION,DOW,HR,LD,LM,HH,SBUS
    1,sun,0,0.010251,0.014314,0.031505,0
    1,sun,1,0.007435,0.010949,0.024310,0
    1,sun,2,0.005407,0.010759,0.022315,0

As long as the developer keeps this file format the same, they can easily interchange this data with their own temporal profiles. For instance, if they have better data in their own local region for a particular vehicle type.


### Calvad DOW Factors CSV

The Calvad day-of-week profiles are given by GAI, day-of-week, and the four Calvad vehicle types.  The CSV file format used is:

    REGION,Day,DOW,LD,LM,HH,SBUS
    1,1,sun,1.200535,0.823616,0.418047,0
    1,2,mon,1.006282,0.948747,0.913910,1
    1,3,tuth,1,1,1,1

Note that, by definition, we do not adjust the emissions from EMFAC for Tuesday-through-Thursday days.  This is because EMFAC is designed for these days, and is quite reliable. The purpose of the day-of-week emissions adjustments is to improve the accuracy for the rest of the days of the year.

As long as the developer keeps this file format the same, they can easily interchange this data with their own temporal profiles. For instance, if they have better data in their own local region for a particular vehicle type.


## Developing for ESTA

ESTA is designed to be easily expanded by developers. The modular design means that changing the function of ESTA doesn't require touching the whole code base. Whether you want to read a different type of emissions file, add a special kind of spatial surrogate, or write a new type of output file, you should be able to do that buy writing a single class and dropping it into a `src` module.

A common problem for scientists and engineers is that they spend more time wrangling files than analyzing their data. In ESTA, you can write a single class to read or write any file type. And once this class is placed correctly into ESTA, you never need to worry about file wrangling again. The goal of software should always be to help people get things done, not to be a drain on their time. For that reason, ESTA is 100% configurable and makes no demands on the structure of your input/output files or on the data structures you pass around.

#### Implementing Your Own Step

Perhaps the most important design goal in ESTA is the ability to replace a step with one of your own. Let's look at an example of doing just that. In the example below, we create a special temporal surrogate: `RushHour`. In this new temporal surrogate, all onroad traffic will happen in two hours of the day (8AM and 5PM), the other 22 hours of the day will have no traffic.

The first thing to do when implementing `RushHour` will be to sub-class the temporal surrogate loader `TemporalLoader` in `src.core.temporal_loader.py`:

    from src.core.temporal_loader import TemporalLoader

    class RushHour(TemporalLoader):

        def __init__(self, config, directory):
            super(RushHour, self).__init__(config, directory)

The purpose of the `temporal_loader` subclass is to provide temporal surrogates. And in the case of on-road emissions, you will want diurnal and day-of-week surrogates. These are both created using the abstract `load` method. Because you will be default all regions (counties) to the same information, you will need a list of regions from the config file:

    [Regions]
    regions: 1..69

Following the example of several other classes in ESTA, you can add a list of regions/counties as a member variable of `RushHour` in the `__init__` method:

    from src.core.temporal_loader import TemporalLoader

    class RushHour(TemporalLoader):

        def __init__(self, config, directory):
            super(RushHour, self).__init__(config, directory)
            self.regions = self.config.parse_regions('Regions', 'regions')

Note that `parse_regions` is a custom method built into the `CustomParser` class in `src.core.custom_parser.py`. This method allows for a region list like `1..69` to generate a list of numbers from 1 to 69, inclusive. Otherwise, it is just a space-separated list.

All that is left is do the actual work of creating the temporal surrogates.

    def load(self, spatial_surrogates, temporal_surrogates):
        """ cars will only drive during rush hour """
        if not temporal_surrogates:
            temporal_surrogates = {'dow': {}, 'diurnal': {}}

        # day-of-week strings
        dows = ['mon', 'tuth', 'fri', 'sat', 'sun', 'holi']

        # create rush hour time profiles
        for region in self.regions:
            temporal_surrogates['dow'][region] = {}
            temporal_surrogates['diurnal'][region] = {}
            for dow in dows:
                temporal_surrogates['dow'][region][dow] = [1.0, 1.0, 1.0, 1.0]
                temporal_surrogates['diurnal'][region][dow] = [[0.0, 0.0, 0.0, 0.0] for i in xrange(24)]
                temporal_surrogates['diurnal'][region][dow][7] = [0.5, 0.5, 0.5, 0.5]
                temporal_surrogates['diurnal'][region][dow][16] = [0.5, 0.5, 0.5, 0.5]

        return temporal_surrogates

And that's it! Copy the above code into `ESTA/src/surrogates/rushhour.py`, and you can now run your (unrealistic) temporal profile by changing a single line in your config (.ini) script:

    temporal_loaders: RushHour

To recap the above process:

1. Identify which step you want to replace.
2. Find the abstract class for that step.
3. Build your own subclass of that abstract class.
4. Put your new subclass in the correct `src` module.
5. Make sure your file name is the lower case of your class name: `MyClass` is in `myclass.py`.
6. Point to your new class in the config file.

#### Defining a New Domain

It is fairly simple to implement a new modeling domain in ESTA. It all depends on finding (or creating) a CMAQ-ready `GRIDCRO2D` file. This is a CMAQ-standard file, with a long history, that defines the lat/lon bounding boxes of each grid cell in a modeling domain. The decision was made to use these files as the best way to define the grid because:

1. It is a well-established file format.
2. People who need gridded emissions inventories will frequently already have this file for their domain.
3. It is an extremely detailed format.
4. It is lat-lon based (and thus projection-free).
5. It is unambiguous.

The `GRIDCRO2D` file is not the only file you need to define your new domain. There is one more, the region boxes file. To speed up the process of locating which grid cell a certain lat/lon point is in, your domain is split up into rectangular regions (one for each county, state, or whatever). This will give a much smaller region for Python to hunt in. You will find examples of these files for five default cases in the input folder:

    ESTA
    └───input
        └───defaults
            └───domains/gai_boxes_ca_12km.py
                        gai_boxes_ca_4km.py
                        gai_boxes_scaqmd_4km.py

These files are simply Python dictionaries that provide the grid cell bounding box for a given county/GAI, e.g.:

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

But there is a better way. Whether you are working with the counties, GAIs, states, or whatever. Chances are you already know the bounding boxes of your regions in lat/lon. Or you can at least come up with some. If so, there is a script you can use to generate the regional boxes file. It is in the default EMFAC input directory next to the GRIDCRO2D input files:

    ESTA/input/defaults/domains/preprocess_grid_boxes.py

This script is easy to use. For example, if you wanted to generate the grid domain boxes for the counties in California for California's 12km ARB-CalEPA modeling domain, you would simply go to the command line and do:

    cd input/defaults/domains/
    python preprocess_grid_boxes.py -gridcro2d GRIDCRO2D.California_12km_97x107 -rows 97 -cols 107  -regions california_counties_lat_lon_bounding_boxes.csv

And this would print a nicely-formatted dictionary (JSON/Python) to the screen, which you can copy to a file called `county_boxes_ca_12km.py`.


[Back to Main Readme](../README.md)


[KDTrees][https://en.wikipedia.org/wiki/K-d_tree]

