try:
    import sys, os, random
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    from fGlobal import *  # this is the global functions file
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")


class FlowRecord:
    def __init__(self, *args, **kwargs):
        """
        Need to create a class that imports the historical flow record that the user provides (csv) and calculates the
        recession rate as a difference in the WSE between days.
        :param args: Optional arguments
        :param kwargs: Optional keyword arguments
        """

        # Create a temporary cache folder for, e.g., geospatial analyses; use self.clear_cache() function to delete
        self.cache = os.path.dirname(__file__) + "\\.cache%s\\" % str(random.randint(10000, 99999))
        chk_dir(self.cache)  # from fGlobal

        # Enable logger
        self.logger = logging.getLogger("logfile")

        """ REMOVE THIS BLOCK COMMENT TO USE UNIT-SENSITIVE PARAMETERS
        self.unit = unit
        if self.unit == "us":
            self.area_unit = "SQUARE_FEET_US"
            self.u_length = "ft"
            self.u_discharge = "cfs"
            self.ft2ac = 1 / 43560
        else:
            self.area_unit = "SQUARE_METERS"
            self.u_length = "m"
            self.u_discharge = "m3"
            self.ft2ac = 1
        """

    def clear_cache(self):
        try:
            rm_dir(self.cache)  # from fGlobal
            self.logger.info("   >> .cache cleared")
        except:
            self.logger.info("ERROR: .cache in use.")  # see https://riverarchitect.github.io/RA_wiki/Troubleshooting

    @err_info
    @spatial_license
    def use_spatial_analyst_function(self, input_raster_path):
        """
        This is an example function for using arcpy.sa (spatial analyst). The function wrappers @err_info and
        @spatial_license come from fGlobal (see header)
        :param input_raster_path: STR of full path to a raster, including its own name with extension (please use .tif )
        :return: output_ras_path: STR of the output raster path
        """
        try:
            self.logger.info("  >> loading raster %s ..." % str(input_raster_path))
            in_ras = arcpy.Raster(input_raster_path)
        except:
            # go here if the input_raster_path is invalid and write a USEFUL error message
            self.logger.info("ERROR: Game over ... add this error message to RA_wiki/Troubleshooting")
            return -1

        try:
            self.logger.info("  >> performing map algebra ...")
            out_ras = Con(~IsNull(in_ras), Float(10))  # example of using arcpy.sa expressions (loaded in fGlobal)
        except:
            # go here if the raster calculation failed and write a USEFUL error message
            self.logger.info("ERROR: Game over ... add this error message to RA_wiki/Troubleshooting")
            return -1

        try:
            output_ras_path = in_ras.path + "result.tif"
            self.logger.info("  >> saving result raster as %s ..." % output_ras_path)
            out_ras.save(output_ras_path)
        except:
            # go here if saving the result raster failed and write a USEFUL error message
            self.logger.info("ERROR: Game over ... add this error message to RA_wiki/Troubleshooting")
            return -1
        self.logger.info("  >> SUCCESS")
        return output_ras_path

    def __call__(self, *args, **kwargs):
        # Object call should return class name, file location and class attributes (dir)
        print("Class Info: <type> = TEMPLATE (%s)" % os.path.dirname(__file__))
        print(dir(self))
