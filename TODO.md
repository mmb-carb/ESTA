# ESTA

> EMFAC Spatial & Temporal Allocator


## TODO List & Thoughts

* make test plots of ITN / DTIM spatial surrogates
* make sure everything is independent of our file structure & types
* read ITN files and build
 * spatial surrogates by EIC-mapped categories & GAI
 * temporal surrogates by EIC-mapped categories & GAI
 * there should be a class setup here, to read DTIM4 format or a newer CSV format
* this should be done in parallel runs, by GAI
* read EMFAC inputs
 * Some classes here, to read my CSV files or directly from a DB
 * all emissions need to be by day, so use some call-by-ref logic to expand monthly/seasonal data
* apply surrogates directly to EMFAC data, by EIC
 * create output PMEDS (maybe NetCDF)
 * class it up, so people can define their own output classes/file types
* config file driven
* improvements over DTIM
 * Leo wants to be able to use the CalTrans Truck Network
 * This means using multiple kinds of input files in the same run
 * Or define different input files and types for different EICs/groupings
* QA Tools
 * plot spatial/temporal surrogates  (imshow)
 * spatially/temporally plot final results  (imshow)
* Things that need to stay flexible
 * Using new types of input files
 * creating new types of output files
 * have a "fast" mode, that ignores the complexity (maybe only uses one spatial surrogate)
 * input files come in wierd DOW/Month-of-Day mixings
* Sparse-Matrix Design: Because many sub-areas will be involved in a larger grid domain


## Code Outline

#### Project Layout

* esta.py
* default.ini
* LICENSE
* README.md
* src
* input
 * possible mostly empty, depending on config.ini
* output
 * possible mostly empty, depending on config.ini

#### Processing Steps

> This is for a single sub-area (don't use the word "county" or "GAI").

1. read ITN activity files and fully parse them
 a. read in each day and create spatial surrogates by vehicle type and process type
 b. sum emissions by sub-area and hourly file
 c. use above emission totals to create temporal surrogates
 d. create the above surrogates as objects
 e. call-by-reference link (not copy) the above object into all the hours of the timespan (year)
2. read in EMFAC2014 files
 a. find all the emissions by EIC, process, and pollutant (met data was in EMFAC, no emis rates)
 b. create the above as object, and call-by-ref link them to each relevant hour of the timespan (yr)
 c. read in all data to EICs
 d. To save time/space later, make sure you've got no duplicate VTP-poll in the sub-area.
3. read in mapping from ITN activity vehicle/process/fuel categories to EICs
4. Go through each hour and apply the spatial and temporal surrogate to each EIC
5. Write output file (can allow more than one file type)
6. Possible QA Tools
 a. simple `imshow` plotting of spatial surrogates


#### Config File Information

1. A list of ITN activity files
 a. with complete information about which DOW, HR, MONTH YEAR they apply to
 b. call to class designed to read DTIM4.2 ITN link & TAZ files
2. A list of EMFAC emission files
 a. with complete info on day(s) of year the file applies to
 b. call to class designed to read EMFAC2014 CSV files
3. Call to class designed to map DTIM4.2 ITN vehicle categories to EICS
4. Call to class(es) designed to create final output files (can be multiple)
5. Description of the QA you want to do
6. output directory
7. date range to process
8. sub-areas to process


#### Code Structure (contents of /src/)

esta.py (take ConfigParser)
abstract class EmissionsLoader
class EMFAC2014CSVLoader(EmissionsLoader)
abstract class RoadNetworkLoader
class DTIM4Loader(RoadNetworkLoader)
class SpatialSurrogate
class TemporalSurrogate
class DailyEmissions
class SurrogatesApplier (takes SpatialSurrogate, TemporalSurrogate, & DailyEmissions)
abstract class OutputFileCreator


## Testing

If we want to run all 58 counties in 12 parallel runs, we need a way to break the counties into 12
even groups. Of course, they won't be exactly even, because LA is more than 1/12th of the state's
total run time. But I ran the spatial-surrogate-mapping portion of my ITN plotting script and timed
the results. What follows is a list of 12 county grouping which will produce the optimal, though
not perfect, 12 parallel runs (FIPS codes):


    county_groups = [[37],
                     [19],
                     [29],
                     [71],
                     [65, 97, 3, 81, 105, 91],
                     [73, 1, 93, 35, 33, 21],
                     [99, 39, 13, 69, 75, 5, 51],
                     [59, 53, 17, 27, 103, 41, 11],
                     [79, 111, 85, 23, 49, 15, 63],
                     [107, 77, 25, 87, 95, 115, 9],
                     [67, 47, 7, 113, 101, 109, 55],
                     [31, 89, 83, 61, 45, 57, 43]]


## Class Importing

I want people to just be able to drop new Import/Export classes in and use them, no playing around
with imports. So, let's make this automatic:

>>> import sys

>>> mod = sys.modules['dtim4loader']

>>> loader = mod.DTIM4Loader

