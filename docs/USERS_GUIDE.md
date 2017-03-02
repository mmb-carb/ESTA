# ESTA User's Guide

The purpose of this document is to show new users how to run ESTA. This does not present what ESTA does, or why it exists, you can find that in the [User Documentation](USER_DOCS.md).

## How to Run a Default Case

ESTA comes with some default configuration and input files, so you can test the model and learn how to use it. The first test is to generate on-road emissions on the 4km California modeling domain. Go to the command line and type:

    ./esta.py config/example_onroad_ca_4km_dtim_pmeds.ini

Or you can type:

    python esta.py config/example_onroad_ca_4km_dtim_pmeds.ini

The default examples included with ESTA are designed to be fast, and should finish in well under a minute on a modern computer.


## Config Files

The configuration (config) files used in ESTA are divided into sections. This makes the config files easier to read and keeps them organized. But there are no required fields in any section; the config files are very general and will change greatly dependent upon your run. That being said, there are a few general principles that can help you understand how to run ESTA.

### General Config Ideas

The config files used in ESTA are a common format, defined by the Python standard library `ConfigParser`. You can find the developer's documentation on `ConfigParser` [here](https://docs.python.org/2/library/configparser.html) and some basic introductory information for everybody [here](https://wiki.python.org/moin/ConfigParserExamples).

There are a few features of the config files to note:

* **Section headers** are defined inside square brackets `[Dates]`.
* **Config variables** must be on their own line, following a section header line. And the value of the config variable comes after a colon and a space.
 * **Lists are spaced-separated.** You could certainly do this another way, but in ESTA, we separate list items with spaces.
* **Comments** are lines where the first character is the pound/hashtag symbol (`#`). This is a reduced case of the Python comment notation, where you can have just part of a line be a comment.

### Choosing a Class

In order for ESTA to be useful, it has to be easy for the user to design their own run. Each step in the ESTA model chain has various options. For instance, if you are reading in some kind of emissions file, there will have to be a different `class` designed to read that file type in ESTA. In order to select that class, all you have to do is list it's name in the config file. For instance, in the default config file "default_onroad_ca_4km.ini":

    [Scaling]
    scalor: EmfacSmokeScaler

If you look in the source code, you will find that class:

    src/scaling/emfacsmokescaler.py

Or, from inside Python:

    from src.scaling.emfacsmokescaler import EmfacSmokeScaler

If you list more than one class, both will be run in the order you listed them. This direct reference to the class name gives the user a huge amount of flexibility in how they run ESTA. Generally, most users will only have to design their run once, and they will be able to do most of their work with only slight modifications to their original config file.

### Standard Config Sections

There are five major steps in the emissions inventory gridding process, each of which have a dedicated section in the ESTA config files:

1. **Reading Emissions**
2. **Reading/Creating Spatial/Temporal Surrogates**
3. **Emissions Scaling**
4. **Output File Creation**
5. **QA/QC**

In addition to those, ESTA has four other standard config sections:

1. **Dates** - define the the time span of the run
2. **Regions** - define the counties, states, or other regions in your run
3. **Grid Information** - define your modeling domain
4. **Miscellaneous** - a catch-all, for shared resources or anything you want

Next, the nine sections above will be discussed in some detail, using examples from the default config files that are provided with ESTA.

#### Dates

Most emissions inventories are built on a daily basis, even if they have hourly values. As such, this section allows the user to set the start and end dates of their run (both inclusive). Since these fields have to be passed as strings, there is also a `format` variable. The format must be something recognizable by the Python standard `datetime` module. Finally, purely for the purposes of on-road processing with EMFAC, all three config files also have a `base_year` variable, to help differentiate the base year and the model year.

All of the provided default config files are set up for the same Wednesday in the Summer of 2012:

    format: %Y-%m-%d
    start: 2012-07-18
    end: 2012-07-18
    base_year: 2012

#### Regions

The purpose of this config section is to allow users to define which counties, states, or other regions they are modeling.

For instance, if you wanted to select all 69 GAIs in California, you might do:

    regions: 1..69

Of if you wanted to just select one region (say, Santa Barbara county):

    regions: 42

Or the Santa Barbara GAI:

    regions: 57

Or you could even list several regions (say the 10 counties in the SCAQMD region):

    regions: 13 15 19 30 33 36 37 40 42 56

And if you want to list a range of values use the `..` notation:

    regions: 7..17

#### GridInfo

In most gridded inventory processing the number of rows, columns, and possibly layers will need to be defined. This section fills the need for those constant vaues.

    rows: 291
    columns: 321
    grid_cross_file: input/defaults/emfac2014/GRIDCRO2D.California_4km_291x321

It should also be noted that the `grid_cross_file` shown here is a standard "grid cross" NetCDF file needed to run the CMAQ photochemical model. For more information on the CMAQ file format, see the [official CMAQ documentation][CMAQ].

#### Surrogates

This section covers the information needed to generate spatial and temporal surrogates. In the `example_onroad_ca_4km_dtim_pmeds.ini` file you will find this section looks something like:

    [Surrogates]
    temporal_directories: input/defaults/surrogates/temporal/
    temporal_loaders: CalvadTemporalLoader
    calvad_dow: calvad_gai_dow_factors_2012.csv
    calvad_diurnal: calvad_gai_diurnal_factors_2012.csv
    spatial_directories: input/examples/onroad_emfac2014_santa_barbara/dtim4_gai_2012/
    spatial_loaders: Dtim4Loader
    eic_info: input/defaults/emfac2014/eic_info.py
    region_boxes: input/defaults/domains/gai_boxes_ca_4km.py

Where as in the `example_onroad_ca_4km_arb_pmeds.ini` file you will find it looks something like:

    [Surrogates]
    spatial_directories: input/examples/onroad_emfac2014_santa_barbara/spatial_surrogates/
    spatial_loaders: CalvadSmoke4SpatialSurrogateLoader
    smoke4_surrogates: ON_ROAD_CA_100_4km_2010.txt
                       ON_ROAD_CA_110_4km_2013.txt
                      ...
                       ON_ROAD_CA_332_4km_2012.txt
    smoke_eic_labels: linehaul
                      pop
                      ...
                      vmt_holiday_pm
    temporal_directories: input/defaults/surrogates/temporal/
    temporal_loaders: CalvadTemporalLoader
    calvad_dow: calvad_gai_dow_factors_2012.csv
    calvad_diurnal: calvad_gai_diurnal_factors_2012.csv
    region_boxes: input/defaults/domains/gai_boxes_ca_4km.py
    eic_info: input/examples/onroad_emfac2014_santa_barbara/spatial_surrogates/eic_info.py
    region_codes: input/defaults/california/gai_codes.py

The difference between these two default runs is that the `example_onroad_ca_4km_dtim_pmeds.ini` config file defines a run where all spatial allocation comes from DTIM4-ready road network files and match DTIM4 outputs. And the `example_onroad_ca_4km_arb_pmeds.ini` file defines a run which also uses SMOKE-ready spatial surrogates and supports ARB's modern on-road modeling.

The `spatial_loaders` variable is a space-separated list of class names used to generate spatial surrogates. Likewise, `temporal_loaders` is a list of class names to generate spatial surrogates.  The `spatial_directories` and `temporal_directories` are where the input information for these classes is found. The length of the `spatial_loaders` list and the length of the `spatial_directories` must be the same, and likewise for the temporal surrogates.

The remaining four variables in the default config files are specific to on-road processing with EMFAC. The `calvad_dow` file is a simple CSV relating the total emissions for different vehicle classes and counties by day-of-week, relative to the typical weekday emissions output by EMFAC. The `calvad_diurnal` is a similar file for the diurnal patterns of various vehicle classes. Both of these files were taken from the CALVAD vehicle activity database.

The `region_boxes` file is a simply Python dictionary expressing the bounding boxes of each county or GAI, in the reference of the current modeling grid. This information is used to speed up the calculation of which grid cells are intersected by each road link.

The `eic_info` variable is used to assign each EIC in the raw emissions to one of the 26 vehicle DTIM classes, for spatial distribution. Each EIC is also mapped to a "label" which describes which spatial surrogate is relevant.

Finally, when `Smoke4SpatialSurrogateLoader` is given as a class for the `spatial_loaders` option, a list of SMOKE-ready spatial surrogates, `smoke4_surrogates`, needs to be provided along with the `eic2dtim4` label to map EICs to each of these surrogates.

#### Emissions

This section is used to define the location of the raw emission input files, and the classes used to read them.

    [Emissions]
    emissions_directories: input/examples/onroad_emfac2014_santa_barbara/emfac2014_2012/ldv/
                           input/examples/onroad_emfac2014_santa_barbara/emfac2014_2012/hdv/
    emissions_loaders: Emfac2014CsvLoader
                       Emfac2014HdDslCsvLoader
    time_units: daily seasonally

In the case of the default config files, there are two types of EMFAC2014 input files being read: HDV-diesel emissions are read in seasonally, and all non-HDV-diesel emissions are read in daily. This means there are two different classes used to read the two different file types (listed under `emissions_loaders`) and two different input directories (list under `emissions_directories`). There is also a spare variable, `time_units`, used to explicitly identify the time-resolution of each EMFAC input file.

#### Scaling

The scaling section defines the classes used to scale the raw inventories using the calculated spatial and temporal surrogates.

    scalor: Dtim4Emfac2014Scaler
gai_codes: input/defaults/california/gai_codes.py
    nh3_inventory: input/defaults/emfac2014/nh3/rf2082_b_2012_20160212_onroadnh3.csv

The `scalor` class listed is the heart of your ESTA run, performing an arbitrary amount of math to apply the surrgates to your emissions.

The `gai_codes` option maps one of the long SMOKE v4 region strings to a simple numerical region. For instance, it maps the long string 'GBV006002GBU' to the GAI code 1.

In the default config files,tThe `nh3_inventory` is a file that lists the CO and NH3 emissions for a number of vehicle classes and processes, by California county. This is used to generate NH3 emissions by EIC from the EMFAC CO emissions, since EMFAC2014 does not calculate NH3 directly.

#### Output

The output section defines how the final output files from ESTA are created.

    directories: output/default_onroad_ca_4km/
    writers: Pmeds1Writer
    by_region: True
    combine_regions: False
    county_to_gai: input/defaults/california/county_to_gai.py
    eic_precision: 3
    gai_basins: input/defaults/california/gai_basins.py
    inventory_version: v0100
    multi_gai_coords: input/defaults/california/multi_gai_coords.py

The primary variables in this section are: `writers` which lists the output-creating classes, and `directories` which lists where you want the output files. All the rest of the variables in the default config files are specific to the EMFAC on-road process.

The `by_region` variable can be set to `True` if you want each county to have it's own output file, or `False` if you want all counties in the same file. The `version_number` variable is just a string used to uniquely identify your model run.

The remaining three variables list the paths to input Python files that associate California GAI codes to various other information. The `county_to_gai.py` file maps each county number to a list of the GAIs contained in that county. The `gai_basins.py` file is a simple dictionary mapping each GAI to the short string that represents which air basin that GAI is in. Finally, the `multi_gai_coords.py` file is a mapping for each grid cell that is split between more than one GAI and the fraction of area in each of those GAIs.

The `eic_precision` option is used to define how detailed you want your output emissions. For instance, the outputs can be written using full EIC-14 categories by setting this option to `14`. But if the outputs are written using only EIC-3 (`eic_precision: 3`), the output files might be 100 times shorter. It should be noted that this option does not affect the content of output files that are in NetCDF format.

#### Testing

The testing section exists to allow for automated QA/QC of the output ESTA results. If these fields are left blank, no tests will be run but nothing will break. Testing is optional.

    tests: EmfacPmedsTotalsTester
    dates: 2012-07-18

Defining which test classes are run is handled by the `tests` variable, and the test results can be written to the output directory defined above. The `dates` variable gives you the option of spot-checking just certain dates in your time range.

#### Misc

The miscellaneous section is just what is sounds like. In the case of the default config files, the miscellaneous section is used for input files that are shared between different processing steps.

    region_names: input/defaults/california/gai_names.py
    vtp2eic: input/defaults/emfac2014/vtp2eic.py

The `gai_names.py` file is a simple dictionary mapping a California GAI integer to the GAI name. The `vtp2eic.py` is another dictionary mapping a tuple `(vehicle type, technology, process)` to a 14-digit EIC number.


[Back to Main Readme](../README.md)


[CMAQ]: http://www.airqualitymodeling.org/cmaqwiki/index.php?title=CMAQ_version_5.0_%28February_2010_release%29_OGD

