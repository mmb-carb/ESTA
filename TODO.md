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


## Code Outline

#### Layout

* esta.py
* default.ini
* LICENSE
* README.md
* src
* input
 * possible mostly empty, depending on config.ini
* output
 * possible mostly empty, depending on config.ini
