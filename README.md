# Welcome to River Architect
River Architect is a Python 2 - based open-source package that supports stream designers with a set of 
GUI modules.

 * Lifespan mapping of stream design features (Modules: LifespanDesign and MaxLifespan).
 * Calculating terraforming activities (mass differences and simple terrain modifications wiht the ModifyTerrain module).
 * Habitat quality evaluations for various aquatic species (Module: HabitatEvaluation).
 * Project cost-benefit assessments (Module: ProjectMaker).
    
# Requirements

 * Digital terrain elevation models (DEMs). 
 * 2D hydrodynamic modeling of multiple steady flow scenarios. 
 * ESRI ArcMap and licenses for SpatialAnalyst (coming soon: update for ArcPro and Python 3). 
 * Batchfile launches are designed for working on any Windows platform.
 
 Note: Running River Architect with sample data requires at least ArcMap 10.6.

# Usage
Quick guide: Right-click on [Start_River_Architect.bat][1] and open the batchfile in a text editor. Ensure that the file points to the correct python interpreter (ArcMap's python.exe -- typically stored in C:\Python27\ArcGISx6410.6\). Save edits, close the batchfile and double-click on it to launch River Architect. For detailed installation and usage instructions, please refer to the code [documentation][2].

Please note that the 64-bit version of ArcGIS' python.exe is needed and that running the sample dataset requires ArcMap version 10.6 (10.5 will not work).

[1]: https://github.com/sschwindt/RiverArchitect_development/blob/master/Start_River_Architect.bat
[2]: https://github.com/sschwindt/RiverArchitect_development/blob/master/00_Documentation/CodeDocumentation.pdf
