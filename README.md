# ESTA
> Emissions Spatial and Temporal Allocator

ESTA is a command-line tool for processing raw emissions data into spatially and temporally-allocated emissions inventories, suitable for photochemicaly modeling or other analysis. ESTA is an open-source, Python-based tool designed by the AQPSD branch of the [California EPA][CalEPA]'s [Air Resources Board][ARB].  Though it is a general-purpose model, it is currently only used for processing on-road inventories.


## Recent Updates

The source code is updated to read EMFAC2021 emissions, and has the option to output diesel PM emissions.
EMFAC2021 output file includes the NH3 emissions.
A day specifc fraction file which created by the PeMS data is used for the Heavy Heavy-duty vehicles.
The 2017 day specific fraction file (doy_fractions_2017_truck_final.csv) is located at input/defaults/surrogates/temporal directory.  User needs to replace this file if the model year is not 2017.


## ESTA Documentation

The ESTA documentation is provided as its own repository:

* [The ESTA Documentation on GitHub](https://github.com/mmb-carb/ESTA_Documentation)


## Open-Source Licence

As ESTA was developed by the California State government, the model and its documenation are part of the public domain. They are openly licensed under the GNU GPLv3 license, and free for all.

* [GNU GPLv3 License](LICENSE)


[ARB]: http://www.arb.ca.gov/homepage.htm
[CalEPA]: http://www.calepa.ca.gov/

