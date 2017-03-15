# ESTA Input File Guide

ESTA can take a lot of kinds of input files.  Some to define spatial and temporal profiles, some to describe EICs and vehicle codes, and of course the basic emissions input files.  A typical ESTA user will only need to change their emissions input files between runs, as the rest of their definitions for temporal profiles and vehicle classification codes won't change.  Never-the-less, it may be helpful to have a clear definition of all of the default types of input files in ESTA.  Keep in mind, that an ESTA developer can add support for any kind of input file format they want.

To start off with, most of the input files to ESTA fall into two categories: plain comma separated values (CSV files), and Python dictionaries.


## Unique File Formats

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



