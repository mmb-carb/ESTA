# ESTA

> Emissions Spatial and Temporal Allocator

## General Introduction

> TODO

## How to Run

To run ESTA, you will need to have Python (v2.6 or 2.7) installed. To run the test case, go to the command line and type:

    ./esta.py default.ini

Or you can type:

    python esta.py default.ini

All of the information about your run can be found in the `default.ini` configuration file.

## Code Structure

> TODO: Introduction

#### On-Road Processing of EMFAC2014 Emissions

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
6. QA Tools

* Sparse-Matrix Design: Because many sub-areas will be involved in a larger modeling domain (grid)
* KD Trees Algorithm: Efficient intersection of links onto projected modeling domain

## TODO

* QA Tools
 * plot spatial/temporal surrogates  (imshow)
 * spatially/temporally plot final results  (imshow)
 * simple `plt.imshow(grid, interpolation=None)` plotting of spatial surrogates

* Fast Parallel county run groups

    fips_grouping = [[37],
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

    county_groups = [[19],
                     [10],
                     [15],
                     [36],
                     [33, 49, 2, 41, 53, 46],
                     [37, 1, 47, 18, 17, 11],
                     [50, 20, 7, 35, 38, 3, 26],
                     [30, 27, 9, 14, 52, 21, 6],
                     [40, 56, 43, 12, 25, 8, 32],
                     [54, 39, 13, 44, 48, 58, 5],
                     [34, 24, 4, 57, 51, 55, 28],
                     [16, 45, 42, 31, 23, 29, 22]]

