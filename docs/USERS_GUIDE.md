# ESTA User's Guide

The purpose of this document is to show new users how to run ESTA. This does not present what ESTA does, or how it works, you can find that in the [User Documentation](USER_DOCS.md).

## How to Run a Default Case

ESTA comes with some default configuration and input files, so you can test the model and learn how to use it. The first test is to generate on-road emissions on the 4km California modeling domain. Go to the command line and type:

    ./esta.py config/example_onroad_ca_4km_dtim_pmeds.ini

Or you can type:

    python esta.py config/example_onroad_ca_4km_dtim_pmeds.ini

The default examples included with ESTA are designed to be fast, and should finish in well under a minute.


## Config Files

The configuration (config) files used in ESTA are divided into sections. This makes the config files easier to read and keeps them organized. But there are no required fields in any section; the config files are very general and will change greatly dependent upon your run. That being said, there are a few general principles that can help you understand how to run ESTA.

### General Config Ideas

The config files used in ESTA are a common format, defined by the Python standard library `ConfigParser`. You can find the developer's documentation on `ConfigParser` [here](https://docs.python.org/2/library/configparser.html) and some basic introductory information for everybody [here](https://wiki.python.org/moin/ConfigParserExamples).

There are a few features of the config files to note:

* **Section headers** are defined inside square brackets, e.g. `[Dates]`.
* **Config variables** must be on their own line, following a section header line. And the value of the config variable comes after a colon and a space.
 * **Lists are spaced-separated.** You could certainly do this another way, but in ESTA, we separate list items with spaces.
* **Comments** are lines where the first character in the line is the pound/hashtag symbol (`#`).

### Choosing a Class

In order for ESTA to be useful, it has to be easy for the user to design their own run. Each step in the ESTA model chain has various options. For instance, if you are reading in some kind of emissions file, there will have to be a different Python `class` designed to read that file type in ESTA. In order to select that class, all you have to do is list its name in the config file. For instance, in the default config file "example_onroad_ca_4km_dtim_pmeds.ini":

    [Scaling]
    scalor: EmfacSmokeScaler

If you look in the source code, you will find that class:

    src/scaling/emfacsmokescaler.py

Or, from inside Python:

    from src.scaling.emfacsmokescaler import EmfacSmokeScaler

If you list more than one class, both will be run in the order you listed them. This direct reference to the class name gives the user a huge amount of flexibility in how they run ESTA. Generally, most users will only have to design their run once, and they will be able to do most of their work with only slight modifications to their original config file.


## Config File Sections

There are five major steps in the emissions inventory gridding process, each of which have a dedicated section in the ESTA config files:

1. **Emissions** - where the emissions files are and how to read them
2. **Surrogates** - where the spatial and temporal surrogate files are and how to read them
3. **Scaling** - how to scale emissions using the spatial and temporal surrogates
4. **Output** - writing final output files
5. **Testing** - QA/QC of output files

In addition to those, ESTA has four other standard config sections:

1. **Dates** - define the the time span of the run
2. **Regions** - define the counties, GAIs, states, or other regions in your run
3. **GridInfo** - define your modeling domain
4. **Miscellaneous** - a catch-all, for shared resources or anything you want

Next, the nine sections above will be discussed in some detail, using examples from the default config files that are provided with ESTA.


### Dates

Most emissions inventories are built on a daily basis, even if they have hourly values. As such, this section allows the user to set the start and end dates for their run (both inclusive). Since these fields have to be passed as strings, there is also a `format` variable. The format must be something recognizable by the Python standard `datetime` module. Finally, all three config files also have a `base_year` variable, as emissions modeling frequently makes a distinction between base year and model year.

All of the provided example config files are set up for the same Wednesday in the Summer of 2012:

    [Dates]
    format: %Y-%m-%d
    start: 2012-07-18
    end: 2012-07-18
    base_year: 2012


### Regions

A typical example might be:

    [Regions]
    regions: 1..69
    region_info: input/defaults/california/gai_info.py

The purpose of this config section is to allow users to define which counties, states, or other regions they are modeling.  And supply extra information about the region definitions.

For instance, if you wanted to select all 69 GAIs in California, you would use the `..` notation to define a range:

    regions: 1..69

Of if you wanted to just select one region (say, the Santa Barbara GAI) you could change the available list of regions:

    regions: 57

Or you can list an arbitrary set of regions (say the 10 counties in the SCAQMD region):

    regions: 13 15 19 30 33 36 37 40 42 56


#### region_info

Example Location:

    input/defaults/california/gai_info.py

The `gai_info.py` file is an example "region_info" file in the "Regions" section of the config file.  This file contains a Python dictionary mapping each region code to a dictionary of attributes needed for the run.  Depending on your run configuration, you may not need *all* the information in this file.  And if you are developing your own ESTA modules you may want to put more information in this file, which is easily extensible.

The `gai_info.py` file has a dictionary of information for each GAI (because the example runs are by GAI). Each GAI has the following information:

* County [integer]
* Air Basin [2 or 3-letter code]
* District [2 or 3-letter code]
* Name [Long-Form County Name string, with District]


### GridInfo

In most gridded inventory processing the number of rows, columns, and possibly layers will need to be defined. This section fills the need for those constant vaues.

    [GridInfo]
    rows: 291
    columns: 321
    grid_cross_file: input/defaults/emfac2014/GRIDCRO2D.California_4km_291x321

Here the variables `rows` and `columns` define the number of rows and columns in your modeling grid.

#### grid_cross_file

Example Locations:

    input/defaults/domains/GRIDCRO2D.California_4km_291x321
    input/defaults/domains/GRIDCRO2D.California_12km_97x107
    input/defaults/domains/GRIDCRO2D.SCAQMD_4km_102x156

These GRIDCRO2D are the same files used in CMAQ to define the lat/lon corners of each modeling grid cell. This file type was chosen as it is already a community standard, and anyone wanting to run CMAQ will already have this file for their modeling domain.  For a full description of the file, see the [official CMAQ documentation][CMAQ].  But in short, it is a Classic-type NetCDF binary file, with two variables that are relevant to ESTA and completely define the modeling grid:

    float LAT(TSTEP, LAY, ROW, COL) ;
        LAT:long_name = "LAT             " ;
        LAT:units = "DEGREES         " ;
        LAT:var_desc = "latitude (south negative)                                                       " ;
    float LON(TSTEP, LAY, ROW, COL) ;
        LON:long_name = "LON             " ;
        LON:units = "DEGREES         " ;
        LON:var_desc = "longitude (west negative)                                                       " ;



### Surrogates

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

The difference between these two default runs is that the `example_onroad_ca_4km_dtim_pmeds.ini` config file defines a run where all spatial allocation comes from DTIM4-ready road network files and match DTIM4 outputs. And the `example_onroad_ca_4km_arb_pmeds.ini` file defines a run which also uses SMOKE-ready spatial surrogates and supports ARB's modern on-road modeling.

Let us go through these variables in more detail.

The `spatial_loaders` variable is a space-separated list of class names used to generate spatial surrogates. Likewise, `temporal_loaders` is a list of class names to generate spatial surrogates.  The `spatial_directories` and `temporal_directories` are where the input files for the surrogates is found. The length of the `spatial_loaders` list and the length of the `spatial_directories` must be the same, and likewise for the temporal surrogates.

The remaining four variables in the default config files are specific to on-road processing with EMFAC. The `calvad_dow` file is a simple CSV relating the total emissions for different vehicle classes and counties by day-of-week, relative to the typical weekday emissions output by EMFAC. The `calvad_diurnal` is a similar file for the diurnal patterns of various vehicle classes. Both of these files were taken from the CALVAD vehicle activity database.

Finally, when `Smoke4Dtim4Loader` is given as a class for the `spatial_loaders` option, a list of SMOKE-ready spatial surrogates, `smoke4_surrogates`, needs to be provided along with the `eic_info` label to map EICs to each of these surrogates.

#### eic_info

Example Locations:

    input/defaults/emfac2014/eic_info.py
    input/examples/onroad_emfac2014_santa_barbara/spatial_surrogates/eic_info.py

The `eic_info.py` file is used to help connect various data to each on-road Emission Inventory Codes (EICs) that we want to model.  The file contains a single Python dictionary mapping every EIC to a tuple containing the data we want associated with it.  The file will look something like:

    {71070111000000: (0, 'trips', 1.0),
     71070611000000: (0, 'vmt', 1.0),
     ...
     78076854100000: (25, 'vmt', 1.0)}

In particular, each EIC maps to a tuple with three elements:

1. The DTIM Column: The column (0-25) in the DTIM Link file that covers this EIC.
2. Spatial Surrogate Code: A string representing which SMOKE v4 spatial surrogate that is used to cover this EIC.
3. Scaling Fraction: This fraction is used to scale the emissions from this EIC. If the fraction is 1.0, the emissions are left unchanged. If the fraction is 0.5, you reduce the emissions by 50%. If the fraction is 3, you triple the emissions.

The first one is used for the default DTIM case, where the second column only points to "vmt" or "trips". But the second file is part of the Santa Barbara example, and the second tuple column points to SMOKE spatial surrogates for spatial disaggregation.

#### region_boxes

Example Locations:

    input/defaults/domains/gai_boxes_ca_4km.py
    input/defaults/domains/gai_boxes_ca_12km.py
    input/defaults/domains/gai_boxes_scaqmd_4km.py

The Grid Boxes files define the I/J (grid cell) bounding boxes of each region in the modeling domain.  For instance, included for example with ESTA are Grid Boxes files that define the extent of each GAI in three different modeling grids: the California 4km grid, the California 12km grid, and the South Coast AQMD 4km modeling grid.

These Grid Boxes files are used to when ESTA takes an lat/lon coordinate and tries to find which I/J grid cell it is in.  This process is very slow when searching the entire modeling domain. But it can be sped up significantly if you already know what GAI the lat/lon point is in: there are fewer I/J grid cells to test.

These files are simple Python dictionaries that provide the grid cell bounding box for a given county/GAI, e.g.:

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


#### Calvad Data

ESTA uses temporal profiles taken from real-world traffic measurements, aggregated by the Calvad database. In particular, ESTA includes two sets of on-road temporal profiles taken from Calvad: one for diurnal profiles and one for day-of-week profiles.

As Calvad is derived from real-world data, it only has three data types that are relevant to modeling using EMFAC2014: Light-Duty, Medium-Duty, and Heavy-Duty.  In addition, temporal profiles were added for one special case scenario: School Busses, whose driving patterns are quite regular.

The Calvad database was used to generate temporal profiles for 6 different weekday types: Sunday, Monday, Tuesday-through-Thursday, Friday, Saturday, and Holidays.


#### calvad_dow

Example Location:

    input/defaults/surrogates/temporal/calvad_gai_dow_factors_2012.csv

The Calvad day-of-week profiles are given by GAI, day-of-week, and the four Calvad vehicle types.  The CSV file format used is:

    REGION,Day,DOW,LD,LM,HH,SBUS
    1,1,sun,1.200535,0.823616,0.418047,0
    1,2,mon,1.006282,0.948747,0.913910,1
    1,3,tuth,1,1,1,1

Note that, by definition, we do not adjust the emissions from EMFAC for Tuesday-through-Thursday days.  This is because EMFAC is designed for these days, and is quite reliable. The purpose of the day-of-week emissions adjustments is to improve the accuracy for the rest of the days of the year.

As long as the developer keeps this file format the same, they can easily interchange this data with their own temporal profiles. For instance, if they have better data in their own local region for a particular vehicle type.


#### calvad_diurnal

Example Location:

    input/defaults/surrogates/temporal/calvad_gai_diurnal_factors_2012.csv

The Calvad diurnal profiles are given by GAI, day-of-week, and the four Calvad vehicle types.  The CSV file format used is:

    REGION,DOW,HR,LD,LM,HH,SBUS
    1,sun,0,0.010251,0.014314,0.031505,0
    1,sun,1,0.007435,0.010949,0.024310,0
    1,sun,2,0.005407,0.010759,0.022315,0

As long as the developer keeps this file format the same, they can easily interchange this data with their own temporal profiles. For instance, if they have better data in their own local region for a particular vehicle type.


#### smoke4_surrogates

Example Locations:

    input/defaults/surrogates/spatial/ca/4km/gai/ON_ROAD_CA_100_4km_2010.txt
    input/examples/onroad_emfac2014_santa_barbara/spatial_surrogates/ON_ROAD_CA_100_4km_2010.txt

To spatially disaggregate EMFAC's county/GAI-wide emissions across the modeling domain, ESTA uses spatial surrogates.  As the US EPA's SMOKE model is already in wide use, it was decided that ESTA will use the SMOKE v4 area source spatial surrogate format. This is a simple plain-text file that defines what fraction of each county goes into each grid cell.

For a more detailed description of the SMOKE area-source spatial surrogate file format, please see the [official SMOKE documentation][SMOKE].



### Emissions

This section is used to define the location of the raw emission input files, and the classes used to read them.

    [Emissions]
    emissions_directories: input/examples/onroad_emfac2014_santa_barbara/emfac2014_2012/ldv/
                           input/examples/onroad_emfac2014_santa_barbara/emfac2014_2012/hdv/
    emissions_loaders: Emfac2014CsvLoader
                       Emfac2014HdDslCsvLoader
    time_units: daily seasonally

In the case of the default config files, there are two types of EMFAC2014 input files being read: HDV-diesel emissions are read seasonally, and all non-HDV-diesel emissions are read daily. This means there are two different classes used to read the two different file types (listed under `emissions_loaders`) and two different input directories (list under `emissions_directories`). There is also a spare variable, `time_units`, used to explicitly identify the time-resolution of each EMFAC input file.

#### On-Road HDV-Diesel Emissions Files

Example Locations:

    input/examples/onroad_emfac2014_santa_barbara/emfac2014_2012/hdv/hd_summer/emfac_hd_summer.csv_all

One of the primary inputs to ESTA is emissions.  In the case of on-road modeling, one of the primary inputs is Heavy-Duty (HD) diesel emissions.  As it happens, these are provided to ESTA in the form of season-average emissions because the daily variation of meteorology does not greatly effect the emissions from HD diesel vehicles.

These input files are a simple (headerless) CSV that look like:

    2012,Santa Barbara (SCC),1.2e-06,IDLEX,T6 CAIRP heavy,TOG
    2012,Santa Barbara (SCC),0.3,RUNEX,T6 instate heavy,NOx
    2012,Santa Barbara (SCC),0.001,RUNEX,T6 instate construction heavy,PM

As the columns do not have a header, it might be helpful to define them:

1. Year that was modeled [4-digit integer]
2. County (District) [String]
3. Emissions [float - tons/day]
4. Vehicle Process [short string]
5. Vehicle Type [detailed string]
6. Pollutants [short string - criteria, not detailed species]


#### On-Road LDV Emissions Files

Example Locations:

    input/examples/onroad_emfac2014_santa_barbara/emfac2014_2012/ldv/07/18/emis/Santa_Barbara.csv.gz

One of the primary inputs to ESTA is emissions.  In the case of on-road modeling, one of the primary inputs is Light-Duty (LD) emissions.  Here "LD Emissions from EMFAC" actually means all non-HD-diesel emissions.  This is *mostly* LD, but also includes a small amount of HD-gasoline vehicles.

Unlike the above HD emissions, LD on-road vehicle emissions depends heavily on meteorology. As such, we cannot take seasonal-average emissions, and must instead take daily emissions, that were generated by EMFAC using daily meteorology.

These input files are a simple (headered) CSV that looks like:

    year,month,sub_area,vehicle_class,process,cat_ncat,pollutant,emission_tons_day
    2012,7,Santa Barbara (SCC),LDA,HOTSOAK,NCAT,TOG,0.02
    2012,7,Santa Barbara (SCC),LDA,PMTW,DSL,PM,0.0003
    2012,7,Santa Barbara (SCC),LDA,RUNEX,CAT,NOx,0.9

This file looks much like the HD-diesel file, but has a column header:

1. Year that was modeled [4-digit integer]
2. Month [integer (1 to 12)]
3. County (District) [String]
4. Vehicle Type [detailed string]
5. Vehicle Process [short string]
6. Fuel Type [short string: CAT, NCAT, DSL]
7. Pollutants [short string - criteria, not detailed species]
8. Emissions [float - tons/day]


### Scaling

The scaling section defines the classes used to scale the raw inventories using the calculated spatial and temporal surrogates.

    [Scaling]
    scalor: EmfacSmokeScaler
    nh3_inventory: input/defaults/emfac2014/nh3/rf2082_b_2012_20160212_onroadnh3.csv

The `scalor` class listed is the heart of your ESTA run, performing an arbitrary amount of math to apply the surrgates to your emissions.

#### nh3_inventory

Example Location:

    input/defaults/emfac2014/nh3/rf2082_b_2012_20160212_onroadnh3.csv

The NH3/CO inventory CSV file contains the NH3 and CO emissions from all on-road EICs, for all regions in California. This file is necessary because EMFAC2014 does not output NH3 emissions from on-road sources, but the NH3 is important in photochemical modeling.  This file is used ad-hoc to calculate NH3 emissions from the CO emissions given by EMFAC.

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


### Output

The output section defines how the final output files from ESTA are created. In example_onroad_ca_4km_dtim_pmeds.ini you will see something like:

    [Output]
    directory: output/example_onroad_ca_4km_dtim/
    writers: Pmeds1Writer
    by_region: True
    combine_regions: False
    eic_precision: 3
    inventory_version: v0100

The primary variables in this section are: `writers` which lists the output-creating classes, and `directories` which lists where you want the output files. All the rest of the variables in the default config files are specific to the EMFAC on-road process.

The `by_region` variable can be set to `True` if you want each county to have it's own output file, or `False` if you want all counties in the same file. The `inventory_version` variable is just a string used to uniquely identify your model run.

The `eic_precision` option is used to define how detailed you want to output your emissions. For instance, the outputs can be written using full EIC-14 categories by setting this option to `14`. But if the outputs are written using only EIC-3 (`eic_precision: 3`), the output files might be about 100 times smaller.

By contrast, in the input file example_onroad_ca_4km_dtim_ncf.ini you will see something like:

    [Output]
    directory: output/example_onroad_ca_4km_dtim/
    writers: CmaqNetcdfWriter
    by_region: False
    inventory_version: v0102
    gspro_file: input/examples/onroad_emfac2014_santa_barbara/ncf/gspro.cmaq.saprc.example.csv
    summer_gsref_file: input/examples/onroad_emfac2014_santa_barbara/ncf/gsref.cmaq.saprc.example.summer.csv
    winter_gsref_file: input/examples/onroad_emfac2014_santa_barbara/ncf/gsref.cmaq.saprc.example.winter.csv
    weight_file: input/examples/onroad_emfac2014_santa_barbara/ncf/molecular.weights.cmaq.mobile.txt

This file generates output files that are in the CMAQ-ready NetCDF format. Notice that since NetCDF files do not contain EIC information the `eic_precision` variable is missing.

The four new variables here all have to do with speciating EMFAC emissions. It turns out tha EMFAC only outputs criteria pollutants, but CMAQ needs speciated emissions. To help make this process transparent, we have decided to use the `GSPRO` and `GSREF` file formats from SMOKE as our input files for speciation. Please note that this config process allows for two different `GSREF` files, one for Summer and one for Winter. There will be no problem if you decide to list the same `GSREF` file twice for these two seasons. Finally, there is one `weight_file` variable that points to a SMOKE-formatted file that lists the molecular weights of each model species.


#### GSPRO / GSREF

The GSPRO, GSREF, and molecular weight files included in the `[Output]` section are used to speciate the emissions that come from EMFAC and produce the model species that CMAQ needs.  As speciation is a big topic in photochemical modeling, it was determined that ESTA should not create a new type of input file for the job.  As such, the GSPRO / GSREF file types were taken from the US EPA's SMOKE v4 modeling system.

For more information on these file formats, please see the official documentation for [GSPRO][GSPRO] and [GSREF][GSREF] files.


### Testing

The testing section exists to allow for automated QA/QC of the output ESTA results. If these fields are left blank, no tests will be run but nothing will break. Testing is optional.

As an example of how ARB runs ESTA, the config file example_onroad_ca_4km_arb_pmeds.ini says:

    [Testing]
    tests: EmfacPmedsTotalsTester EmfacPmedsDiurnalTester
    dates: 2012-07-18

Defining which test classes are run is handled by the `tests` variable, and the test results can be written to the output directory defined above. The `dates` variable gives you the option of spot-checking just certain dates in your time range.

Please note that there are tests available in ESTA for PMEDS and NetCDF output files respectively. Because the NetCDF format does not contain EIC information, there are fewer testing options than there are for NetCDF files.


### Misc

The miscellaneous section is just what is sounds like. In the case of the default config files, the miscellaneous section is used for input files that are shared between different processing steps.

    [Misc]
    vtp2eic: input/defaults/emfac2014/vtp2eic.py


#### vtp2eic.py

Example Location:

    input/defaults/emfac2014/vtp2eic.py

The `vtp2eic.py` file is used to map the EMFAC outputs to the EIC categories used by CARB.  EMFAC outputs emissions by vehicle categories such as:

    LDA, CAT, RUNEX

This is meant to represent "Light Duty Auto", "Catalytic Converter", and "Running Exhaust".  That is a great description, but CARB represents that using the EIC 71073411000000.  The `vtp2eic.py` file contains a singly Python dictionary mapping these EMFAC codes to EIC, for example:

    {('All Other Buses', 'DSL', 'IDLEX'): 77976512100000,
     ('All Other Buses', 'DSL', 'PMBW'): 77976854100000,
     ...
     ('UBUS', 'NCAT', 'STREX'): 76270111000000}


[Back to Main Readme](../README.md)


[CMAQ]: http://www.airqualitymodeling.org/cmaqwiki/index.php?title=CMAQ_version_5.0_%28February_2010_release%29_OGD
[GSPRO]: https://www.cmascenter.org/smoke/documentation/2.7/html/ch08s05s02.html
[GSREF]: https://www.cmascenter.org/smoke/documentation/2.7/html/ch08s05s04.html
[SMOKE]: https://www.cmascenter.org/smoke/documentation/2.7/html/ch08s04.html

