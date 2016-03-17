# ESTA USER Documentation

The purpose of this document is give a clear understanding of what ESTA is, and what it does. This is not meant as a guide to how to run ESTA, you will find that in the [User Guide](USERS_GUIDE.md).

## Introduction

The ESTA (Emissions Spatial and Temporal Allocator) model applies spatial and temporal surrogates to emissions to create top-down emission inventory files.  The model is very general and can apply spatial and/or temporal surrogates any kind of emissions file.  However, ESTA was originally developed with the goal of gridding on-road emissions from the EMFAC2014 model as a replacement for the DTIM model. 

## How It Works

ESTA is written entirely in Python, using only free, open-source technology. It has a modular design to make it easier to upgrade, improve, and modify. It is a command-line program, executable on Linux, PC, and Mac. The flow of the code is easy to understand, there are six basic steps:

![Figure 1: ESTA work flow, generic version](resources/esta_box_diagram_1.png)
 
As shown in Figure 1, the ESTA work flow is straight forward. In the first step, emissions files are read in and parsed to something Python can understand. In the second step, input files are read and spatial surrogates are created. In the third step, more input files are read and the temporal surrogates are created. In the fourth step, the spatial and temporal surrogates are applied to the emissions and a gridded inventory is created in memory. In the fifth step, custom-formatted output files are created from the inventory. There is an optional sixth step, where quality assurance tests are run on the output files.

The work flow above is very general and can apply to gridding an on-road inventory, or any other kind of inventory. However, in practice, your work flow might be more complex. For instance, what if you want to read in multiple different kinds of temporal surrogates: diurnal and day-of-week? Or what if you want to read in several different types of emissions files? ESTA's modular design helps support this common type of work flow by allowing each box in Figure 1 to be replaced by a list of boxes/steps.

## Detailed Example - On-Road with EMFAC2014

It might be easier to see an example. Figure 2 below shows the work flow for spatially gridding the on-road emissions from EMFAC2014. Notice that some of the steps are now repeated for different file types.

![Figure 2: ESTA work flow, EMFAC example](resources/esta_box_diagram_on_road.png)

As shown in Figure 2, there are two implementations of the first "read emissions" step. This is because we read monthly EMFAC files for Heavy-Duty Diesel emissions, but daily files for other emissions. Being able to support reading two different kinds of input emissions files is important. The third step is also different, because we need both diurnal temporal surrogates and day-of-week temporal surrogates in step 3, such as from California Vehicle Activity Database (CalVAD). In Step 4 only one specialized module is needed to apply the surrogates to the emissions and step 5 has only one box in this case. In step 6, the gridded, hourly emissions are summed and compare with the daily totals from EMFAC. We could also imagine wanting to write files of different formats, and wanting multiple boxes in that step as well.

ESTA is designed so that developers can create new versions of the steps above to fit their own unique problem.  This modularity allows developers to create new output files, read new input files, and change their work flow. ESTA will handle linking all of the data together.


[Back to Main Readme](../README.md)
