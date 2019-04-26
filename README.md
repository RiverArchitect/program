# River Architect ![logo](https://raw.githubusercontent.com/sschwindt/RiverArchitect/master/images/logo_small.ico)
River Architect is a Python3-based open-source package that supports stream designers with a set of 
GUI modules (the last stable Python2 version can be downloaded [here][8] with sample data). The current core functionalities are:

 * Lifespan mapping of stream design features according to [Schwindt et al. (2019)][1] with the LifespanDesign and MaxLifespan modules.   
 
 * Calculate terraforming activities (mass differences and simple terrain modifications) with the ModifyTerrain module.
 
 * Evaluate habitat quality for various aquatic species with the HabitatEvaluation module and investigate functional flow regimes related to geomorphologic features ([Lane et al. 2019](https://www.onlinelibrary.wiley.com/doi/abs/10.1002/eco.1969)) with the EcoMorphology module (under construction with [@leogoesger](https://github.com/leogoesger)'s [FFF-connectors](https://github.com/leogoesger/FFF-connectors)).
 
 * Assess project cost-benefit with the ProjectMaker module.

# Requirements

 * Digital terrain elevation models (DEMs).
 
 * 2D hydrodynamic modeling of multiple steady flow scenarios.
 
 * ESRI ArcMap and licenses for SpatialAnalyst (coming soon: update for ArcPro and Python 3).
 
 * Batchfile launches are designed for working on any Windows platform.


# How to use it?
The quick version: Download [River Architect][5] and double-click on [Start_River_Architect.bat][1]. Modifications of the batchfile might be required, for example, to fit the conda environment. The standard ennvironment is `"%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\propy"`, which typically refers to `"C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat"`. ArcGIS provides more information on running stand-alone Python scripts on their [website](https://pro.arcgis.com/en/pro-app/arcpy/get-started/using-conda-with-arcgis-pro.htm).

The robust version:

 1. Download the program file directory from [GitHub][2] (or [sample data][4]). 
 2. Follow the detailed [Installation][6] instructions for setting up the Environment and read the [Signposts][7] about the terminology. 
 3. The application of *River Architect*'s modules are described on their Wiki pages:
   * [LifespanDesign](https://github.com/sschwindt/RiverArchitect/wiki/LifespanDesign)
   * [MaxLifespan](https://github.com/sschwindt/RiverArchitect/wiki/MaxLifespan)
   * [ModifyTerrain](https://github.com/sschwindt/RiverArchitect/wiki/ModifyTerrain)
   * [HabitatEvaluation](https://github.com/sschwindt/RiverArchitect/wiki/HabitatEvaluation)
   * [ProjectMaker](https://github.com/sschwindt/RiverArchitect/wiki/ProjectMaker)
   * [EcoMorphology](https://github.com/sschwindt/RiverArchitect/wiki/EcoMorphology) (under construction)
 
 The Wiki also provides detailed solutions for [Troubleshooting](https://github.com/sschwindt/RiverArchitect/wiki/Troubleshooting).
 
Please note that *River Architect* has undergone important changes since the last stable Python2 version ([download last stable Python2-River-Architect][8]).

# Documentation
The usage of River Architect is described in the [River Architect's Wiki][3].


# About
The code was developed based on data from California's Yuba River and example results can be downloaded.

Future developments will focus on improving the GUIs, developing the ModifyTerrain module for automating
terraforming planning, and migrating to QGIS's Python core.


# Contributing
Do not hesitate to contact river.architect.program [at] gmail.com for reporting bugs, suggestions, or any feedback.

Bug reports, feature requests, and pull requests are welcome on GitHub at https://github.com/sschwindt/RiverArchitect .


[1]: https://www.sciencedirect.com/science/article/pii/S0301479718312751 "Lifespan mapping"
[2]: https://github.com/sschwindt/RiverArchitect_development
[3]: https://github.com/sschwindt/RiverArchitect/wiki
[4]: https://www.dropbox.com/s/pv9n2y0nmulidme/RiverArchitect_with_Example.zip?dl=0
[5]: https://github.com/sschwindt/RiverArchitect_development/archive/master.zip
[6]: https://github.com/sschwindt/RiverArchitect/wiki/Installation
[7]: https://github.com/sschwindt/RiverArchitect/wiki/Signposts
[8]: https://www.dropbox.com/s/8d6c096r4ouzxy2/RiverArchitect_Py2.zip?dl=0

