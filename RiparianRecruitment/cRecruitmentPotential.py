try:
    import sys, os, random
    import logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\LifespanDesign\\")
    from cParameters import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
    import fRasterCalcs as fRc
    import cMakeTable as cMkT
    import cLifespanDesignAnalysis as cLDA
    from cLogger import Logger
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

    def __init__(self, condition, units, *args, **kwargs):

        # if __name__ == __main__
        self.logger = Logger("logfile")
        # Enable logger
        self.logger = logging.getLogger("logfile")
        # Create a temporary cache folder for, e.g., geospatial analyses; use self.clear_cache() function to delete
        self.cache = os.path.dirname(__file__) + "\\.cache%s\\" % str(random.randint(10000, 99999))
        fGl.chk_dir(self.cache)  # from fGlobal
        # set arcpy environment and enable overwrite
        arcpy.env.workspace = self.cache
        arcpy.env.overwriteOutput = True
        # define condition (i.e. DEM)
        self.condition = str(condition)
        self.dir2condition = config.dir2conditions + self.condition + "\\"

        try:
            __n__ = float(args[2])
        except:
            __n__ = 0.0473934

        # define units
        self.units = units
        self.area_units = "ft^2" if self.units == 'us' else 'm^2'
        self.length_units = 'ft' if self.units == 'us' else 'm'
        self.u_units = self.length_units + '/s'
        self.ft2ac = config.ft2ac if self.units == 'us' else 1
        self.ft2m = config.ft2m if self.units == 'us' else 1
        self.ft2in = 12 if self.units == 'us' else 1 # (in/ft) conversion factor for US customary units
                                                     # else dummy conversion in SI
        self.n = __n__ / 1.49 if self.units == 'us' else __n__  # (s/ft^(1/3)) global Manning's n where k =1.49 converts
                                                                # to US customary, else (s/m^(1/3)) global Manning's n
        self.n_label = "s/ft^(1/3)" if self.units == 'us' else "s/m^(1/3)"
        self.s = 2.68  # (--) relative grain density (ratio of rho_s and rho_w)
        self.sf = 0.99  # (--) default safety factor

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2rp + "Output\\" + self.condition + "\\"
        fGl.chk_dir(self.out_dir)

        # populated by self.get_hydraulic_rasters()
        self.discharges = []
        self.Q_h_dict = {}
        self.Q_u_dict = {}

        self.get_hydraulic_rasters()
        self.get_grain_ras()
        self.ras_taux()
        #self.bed_prep_time_raster()
        #self.recession_rate_raster()
        #self.dry_season_raster()
        #self.recruitment_area_raster()


    def import_hyrologic_data(self):
        self.logger.info('Retrieving hydrologic data...')
        #try:
            # import hydrologic data for year of interest, prior two years, and subsequent year
            # hydrologic data uploaded in date(00/00/0000) and flow (cfs) format (csv)
        #except:
            #self.logger.error("ERROR: Could not retrieve hydrologic data.")


    def get_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            mkt = cMkT.MakeFlowTable(self.condition, "", unit=self.units)
            self.discharges = sorted(mkt.discharges)
            self.Q_h_dict = {Q: self.dir2condition + mkt.dict_Q_h_ras[Q] for Q in self.discharges}
            self.Q_u_dict = {Q: self.dir2condition + mkt.dict_Q_u_ras[Q] for Q in self.discharges}
        except:
            self.logger.error("ERROR: Could not retrieve hydraulic rasters.")


    def get_grain_ras(self):
        self.logger.info("Retrieving grain size raster...")
        try:
            self.grain_ras = os.path.join(self.dir2condition, 'dmean.tif')
            assert os.path.exists(self.grain_ras)
        except:
            self.logger.error("ERROR: Could not retrieve grain size raster...")
            self.grain_ras = None

    def ras_mobile_grain(self):
        """
        Create mobile grain rasters with depth and velocity rasters producing mobile grain rasters for all flows modeled.
        """
        self.logger.info("Creating mobile grain rasters...")
        try:
            # create mobile grain raster using method in cLifespanDesignAnalysis
            self.logger.info("")
            for Q in self.discharges:
                self.logger.info(f'Creating bed mobility raster for Q = {Q}...')
                h_ras = Raster(self.Q_h_dict[Q])
                u_ras = Raster(self.Q_u_dict[Q])
                ras_Dcr = cLDA.analyse_mobile_grains(h_ras, u_ras, s=self.s, units=self.units)
                out_ras_path = os.path.join(self.out_dir, "mobilegrain_%s.tif" % fGl.write_Q_str(Q))
                ras_Dcr.save(out_ras_path)
                self.logger.info(f'Saved: {out_ras_path}')
        except:
            self.logger.info("ERROR: Could not create mobile grain raster...")
            return -1
        self.logger.info('Saved mobile grain rasters: %s' % out_ras_path)

    def ras_taux(self):
        """
        Calculates dimensionless bed shear stress with depth, velocity, and grain distribution rasters producing
        taux rasters for all flows modeled.
        """

        self.logger.info("Creating dimensionless bed shear stress rasters...")
        try:
            # get grains raster
            self.logger.info("Retrieving grain size raster...")
            grain_ras = Raster(self.grain_ras)
            for Q in self.discharges:
                self.logger.info(f'Creating dimensionless shear stress raster for Q = {Q}...')
                h_ras = Raster(self.Q_h_dict[Q])
                u_ras = Raster(self.Q_u_dict[Q])
                taux_ras = fRc.calculate_taux(h_ras, u_ras, grain_ras, s=self.s, units=self.units)
                out_ras_path = os.path.join(self.out_dir, "taux_%s.tif" % fGl.write_Q_str(Q))
                taux_ras.save(out_ras_path)
                self.logger.info(f'Saved: {out_ras_path}')
        except:
            self.logger.info("ERROR: Could not create taux raster...")
            return -1
        self.logger.info("Saved taux rasters: %s" % out_ras_path)


    def bed_prep_time_raster(self):
        """
        Recruitment Box Model, Objective 1: Winter Peak Flows Bed Preparation
        Retrieves dimensionless bed shear stress.
        Creates bed preparation time raster from mobile grains raster and flow data.
        """
        # import relevant time period to check for bed preparation (years prior and year of interest, July)
        # taux threshold has been exceeded
        # import existing vegetation rasters
        # exclude areas where large vegetation exists
        # create Q* raster that represents the flows that mobilize grains for each pixel
        # determine if flow has occurred during relevant time period to prepare the bed

    def recession_rate_raster(self):
        """
        Recruitment Box Model, Objective 2: Spring Recession Rates
        Creates recession rate raster (optimal, at-risk, lethal) from water surface elevation rasters for each day
        at each pixel.
        """
        #

    def dry_season_raster(self):
        """
        Recruitment Box Model, Objective 3: Summer Low Flows No Inundation
        Creates raster of recruitment areas that are inundated after spring growth period in summer.
        """

    def recruitment_area_raster(self):
        """
        Creates raster of areas where all three objectives of the Recruitment Box Model area met.
        """

    def recruitment_potential(self):
        """
        Analyzes the recruitment potential at a given site for a year of interest.

        Outputs:
            -
        """
        self.logger.info("Applying flow data...")
        self.logger.info("Identifying potential recruitment area...")

        # make rasters of BSS associated with highest flows during bed preparation period
        self.ras_taux()

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

if __name__ == "__main__":

    rp = RecruitmentPotential(condition='2017_lbp', units='us')
    #print()

