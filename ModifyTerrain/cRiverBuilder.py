
# !/usr/bin/python
try:
    import sys, os, arcpy, logging
    import arcpy
    from arcpy.sa import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
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

        self.dir = os.path.dirname(__file__) + "/"
        self.dir2ra = self.input_dir_fa = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "/"
        self.dir_out = self.dir + "Output/RiverBuilder"

        self.R = robjects.r

        # set unit system variables
        if ("us" in str(units)) or ("si" in str(units)):
            self.units = units
        else:
            self.units = "us"
            self.logger.info("WARNING: Invalid unit_system identifier. unit_system must be either \'us\' or \'si\'.")
            self.logger.info("         Setting unit_system default to \'us\'.")

        if self.units == "us":
            self.m2ft = 0.3048
        else:
            self.m2ft = 1.0


    def run_riverbuilder(self, input_file_name):
        # input_file_name = STR of RiverBuilder Input.txt file that must be stored in self.dir
        self.R.setwd(self.dir)
        self.R.source('riverbuilder.r')
        # self.R.get("riverbuilder")  # uncomment if next command doesn't work
        self.R.riverbuilder(input_file_name, self.dir_out, overwrite='TRUE')  # difference to R: TRUE as STR


    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = MU (%s)" % os.path.dirname(__file__))
        print(dir(self))





