
# !/usr/bin/python
try:
    import sys, os, arcpy, logging
    import arcpy
    from arcpy.sa import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy, os, sys, logging).")

try:
    from rpy2 import robjects
except:
    print("ExceptionERROR: Missing package (rpy2).")


class RiverBuilder:
    def __init__(self, units):
        # pipes to riverbuilder.r
        # units = STR (either "us" or "si")
        self.logger = logging.getLogger("logfile")

        self.dir2rb = config.dir2mt + "/RiverBuilder/"
        self.dir_out = config.dir2mt + "Output/RiverBuilder"

        self.R = robjects.r

        # set unit system variables
        if ("us" in str(units)) or ("si" in str(units)):
            self.units = units
        else:
            self.units = "us"
            self.logger.info("WARNING: Invalid unit_system identifier. unit_system must be either \'us\' or \'si\'.")
            self.logger.info("         Setting unit_system default to \'us\'.")

        if self.units == "us":
            self.m2ft = config.m2ft
        else:
            self.m2ft = 1.0

    def run_riverbuilder(self, input_file_name):
        # input_file_name = STR of RiverBuilder Input.txt file that must be stored in self.dir
        self.R.setwd(self.dir2rb)
        self.R.source('riverbuilder.r')
        # self.R.get("riverbuilder")  # uncomment if next command doesn't work
        self.R.riverbuilder(input_file_name, self.dir_out, overwrite='TRUE')  # difference to R: TRUE as STR
        return self.dir_out

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = RiverBuilder (%s)" % os.path.dirname(__file__))
        print(dir(self))






