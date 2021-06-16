# ESTA
> Emissions Spatial and Temporal Allocator

ESTA is a command-line tool for processing raw emissions data into spatially and temporally-allocated emissions inventories, suitable for photochemicaly modeling or other analysis. ESTA is an open-source, Python-based tool designed by the AQPSD branch of the [California EPA][CalEPA]'s [Air Resources Board][ARB].  Though it is a general-purpose model, it is currently only used for processing on-road inventories.


## Recent Updates

The source code is updated to read EMFAC2017 emissions, and has the option to output diesel PM emissions.
The directory NH3_data_EF17_MPO010 contains the NH3 emissions files for several years and user can append the specific year of the NH3 emissions files to the EMFAC2017 emissions files.  The scripts that append the NH3 emissions files to the EMFAC2017 emissions files are provided at EF17_format_ld and EF17_format_hd directories.
The current version of the NH3 inventory is MPO010.


## ESTA Documentation

The ESTA documentation is provided as its own repository:

* [The ESTA Documentation on GitHub](https://github.com/mmb-carb/ESTA_Documentation)


## Open-Source Licence

As ESTA was developed by the California State government, the model and its documenation are part of the public domain. They are openly licensed under the GNU GPLv3 license, and free for all.

* [GNU GPLv3 License](LICENSE)


[ARB]: http://www.arb.ca.gov/homepage.htm
[CalEPA]: http://www.calepa.ca.gov/

