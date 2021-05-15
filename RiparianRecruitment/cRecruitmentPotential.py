try:
    import sys, os, random
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")
try:
    sys.path.append(config.dir2rp)
except:
    print("ExceptionERROR: ")
try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?).")
try:
    from arcpy import env
except:
    print("ExceptionERROR: env class from arcpy is not available (check license?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")

class RecruitmentPotential:

    def __init__(self, *args, **kwargs):
        # Create a temporary cache folder for, e.g., geospatial analyses; use self.clear_cache() function to delete
        self.cache = os.path.dirname(__file__) + "\\.cache%s\\" % str(random.randint(10000, 99999))
        chk_dir(self.cache)  # from fGlobal

        # Enable logger
        self.logger = logging.getLogger("logfile")

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

        # set arcpy environment and enable overwrite
        arcpy.env.workspace = self.cache
        arcpy.env.overwriteOutput = True

        # define condition (i.e. DEM)
        self.condition = condition
        self.dir2condition = config.dir2conditions + self.condition + "\\"

        # define flow data
        self.flow_data = flow_data

        self.get_hydraulic_rasters()
        self.bed_prep_time_raster()
        self.recession_rate_raster()
        self.dry_season_raster()
        self.recruitment_area_raster()

    @fGl.err_info
    @fGl.spatial_license
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

    def hydro_detection(self):
        """
        Determines seasonal periods using Patterson et al. 2020 functional flow calculator
        """

        self.logger.info("Determining seasonal periods from hydrologic data...")
        try:
            print('determine seasonal periods...')
        except:
            self.logger.info("ERROR: Could not retrieve hydraulic rasters.")


    def get_hydraulic_rasters(self):
        """
        Retrieves depth and velocity rasters.
        """

        self.logger.info("Retrieving hydraulic rasters...")
        try:
            print('get hydraulic rasters...')
        except:
            self.logger.info("ERROR: Could not retrieve hydraulic rasters.")

    def bed_prep_time_raster(self):
        """
        Recruitment Box Model, Objective 1: Winter Peak Flows Bed Preparation
        Retrieves dimensionless bed shear stress and mobile grains rasters or produces them if they do not exist.
        Creates bed preparation time raster from mobile grains raster and flow data.
        """


    def recession_rate_raster(self):
        """
        Recruitment Box Model, Objective 2: Spring Recession Rates
        Creates recession rate raster (optimal, at-risk, lethal) from water surface elevation rasters for each day
        at each pixel.
        """

    def dry_season_raster(self):
        """
        Recruitment Box Model, Objective 3: Summer Low Flows No Inundation
        Creates raster of recruitment areas that are inundated after spring growth period in summer.
        """

    def recruitment_area_raster(self):
        """
        Creates raster of areas where all three objectives of the Recruitment Box Model area met.
        """

    def clean_up(self):
            try:
                self.logger.info("Cleaning up ...")
                fGl.clean_dir(self.cache)
                fGl.rm_dir(self.cache)
                self.logger.info("OK")
            except:
                self.logger.info("Failed to clean up .cache folder.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = RecruitmentPotential (Module: Riparian Recruitment")
        print(dir(self))