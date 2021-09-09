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
    import fRasterCalcs as fRC
    import cRecruitmentCriteria as cRC
    import cMakeTable as cMkT
    from cLogger import Logger
    import pandas as pd
    import datetime as dt
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

    def __init__(self, condition, flow_data, species, units, *args, **kwargs):

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
        # define flow data file path
        self.flow_data = flow_data
        # define species
        self.species = species
        # define instance of cRecruitmentCriteria
        self.rc = cRC.RecruitmentCriteria()
        # get relevant recruitment criteria data for species of interest
        self.rc_data = self.rc.species_dict[self.species]

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
        self.ft2in = 12 if self.units == 'us' else 1  # (in/ft) conversion factor for US customary units
                                                      # else dummy conversion in SI
        self.n = __n__ / 1.49 if self.units == 'us' else __n__  # (s/ft^(1/3)) global Manning's n where k =1.49 converts
                                                                # to US customary, else (s/m^(1/3)) global Manning's n
        self.n_label = "s/ft^(1/3)" if self.units == 'us' else "s/m^(1/3)"
        self.s = 2.68  # (--) relative grain density (ratio of rho_s and rho_w)
        self.taux_cr = 0.047  # (--) critical dimensionless bed shear stress threshold

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2rp + "Output\\" + self.condition + "\\"
        fGl.chk_dir(self.out_dir)

        # populated by self.import_flow_data()
        self.flow_df = None

        # populated by self.get_years_list()
        self.years_list = []

        # populated by self.get_hydraulic_rasters()
        self.discharges = []
        self.Q_h_dict = {}
        self.Q_u_dict = {}

        # populated by self.ras_taux()
        self.Q_taux_dict = {}

        # populated by self.ras_mobile_grain()
        self.Q_mg_dict = {}

        self.import_flow_data()
        self.get_years_list()
        self.get_hydraulic_rasters()
        self.get_grain_ras()
        self.ras_taux()
        self.ras_mobile_grain()
        #self.bed_prep_time_raster()
        #self.recession_rate_raster()
        #self.dry_season_raster()
        #self.recruitment_area_raster()


    def import_flow_data(self):
        self.logger.info('Retrieving flow data...')
        # read self.flow_data file to dataframe (flow_df)
        try:
            if self.flow_data.endswith(".xlsx") or self.flow_data.endswith(".xls"):
                self.flow_df = pd.read_excel(self.flow_data, index_col=0, skiprows=[1])
            else:
                self.flow_df = pd.read_csv(self.flow_data, index_col=0, skiprows=[1])
        except:
            self.logger.error("ERROR: Could not retrieve flow data.")


    def get_years_list(self):
        self.logger.info("Creating list of years from flow data...")
        # create list of years from self.flow_df
        try:
            all_years_list = list(set(self.flow_df.index.year))
            season_start = self.rc_data.loc[self.rc.season_start].VALUE
            bed_prep_period = self.rc_data.loc[self.rc.bed_prep_period].VALUE
            for year in all_years_list:
                # make sure we have period from start date to end date in flow data for year to be valid choice for analysis
                # starting bed_prep_period years before season start date
                start_date = dt.datetime(year - bed_prep_period, season_start.month, season_start.day, 0, 0)
                # ending one year after season start date (minus one day)
                end_date = dt.datetime(year + 1, season_start.month, season_start.day, 0, 0) - dt.timedelta(days=1)
                if (start_date in self.flow_df.index) and (end_date in self.flow_df.index):
                    self.years_list.append(year)
        except:
            self.logger.error("ERROR: Could not parse years from flow data.")


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
                out_ras_path = os.path.join(self.out_dir, "taux_%s.tif" % fGl.write_Q_str(Q))
                if os.path.exists(out_ras_path):
                    self.logger.info(f'Dimensionless shear stress raster already exists ({out_ras_path}). Skipping...')
                else:
                    self.logger.info(f'Creating dimensionless shear stress raster for Q = {Q}...')
                    h_ras = Raster(self.Q_h_dict[Q])
                    u_ras = Raster(self.Q_u_dict[Q])
                    taux_ras = fRC.calculate_taux(h_ras, u_ras, grain_ras, s=self.s, units=self.units)
                    taux_ras.save(out_ras_path)
                    self.logger.info(f'Saved: {out_ras_path}')
                # Add taux raster to Q_taux_dict
                self.logger.info(f'Adding dimensionless shear stress raster to dictionary for Q = {Q}...')
                self.Q_taux_dict[Q] = out_ras_path
                self.logger.info('Added to dictionary.')
        except:
            self.logger.info("ERROR: Could not create taux raster...")
            return -1


    def ras_mobile_grain(self):
        """
        Create mobile grain rasters by comparing taux_ras to the critical threshold value to determine if grains have
        been mobilized.
        """

        self.logger.info("Creating mobile grain rasters...")
        try:
            # create rasters of cells representing where grains are mobilized based on dimensionless critical threshold
            self.logger.info("Retrieving taux raster...")
            for Q in self.discharges:
                out_ras_path = os.path.join(self.out_dir, "mg_%s.tif" % fGl.write_Q_str(Q))
                if os.path.exists(out_ras_path):
                    self.logger.info(f'Mobile grain raster already exists ({out_ras_path}). Skipping...')
                else:
                    self.logger.info(f'Creating mobile grain raster for Q = {Q}...')
                    taux_ras = Raster(self.Q_taux_dict[Q])
                    ras_mobilegrain = Con(taux_ras >= self.taux_cr, 1)
                    ras_mobilegrain.save(out_ras_path)
                    self.logger.info(f'Saved: {out_ras_path}')
                # Add mobile grain raster to Q_mg_dict
                self.logger.info(f'Adding mobile grain raster to dictionary for Q = {Q}...')
                self.Q_mg_dict[Q] = out_ras_path
                self.logger.info('Added to dictionary.')
        except:
            self.logger.info("ERROR: Could not create mobile grain raster...")
            return -1


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
    flowdata = 'D:\\LYR_Restore\\RiverArchitect\\00_Flows\\InputFlowSeries\\flow_series_example_data.xlsx'
    rp = RecruitmentPotential(condition='2017_lbp', flow_data=flowdata, species='Fremont Cottonwood', units='us')
