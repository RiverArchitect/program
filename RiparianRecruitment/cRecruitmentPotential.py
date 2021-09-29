try:
    import sys, os, random
    import logging
    from tkinter.messagebox import askyesno
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\LifespanDesign\\")
    from cParameters import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\GetStarted\\")
    import cWaterLevel as cWL
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

    def __init__(self, condition, flow_data, species, selected_year, units, *args, **kwargs):
        # initialize logger
        self.logger = Logger("logfile")
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
        # define selected year
        self.selected_year = int(selected_year) if len(selected_year) else None
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
        # (in/ft) conversion factor for US customary units else dummy conversion in SI
        self.ft2in = 12 if self.units == 'us' else 1
        # (s/ft^(1/3)) global Manning's n where k =1.49 converts to US customary, else (s/m^(1/3)) global Manning's n
        self.n = __n__ / 1.49 if self.units == 'us' else __n__
        self.n_label = "s/ft^(1/3)" if self.units == 'us' else "s/m^(1/3)"
        # relative grain density (ratio of rho_s and rho_w)
        self.s = 2.68
        # critical dimensionless bed shear stress threshold for fully prepared bed
        self.taux_cr_fp = self.rc_data.loc[self.rc.taux_cr_fp].VALUE
        # critical dimensionless bed shear stress threshold for partially prepared bed
        self.taux_cr_pp = self.rc_data.loc[self.rc.taux_cr_pp].VALUE

        # populated by self.ras_q_mobile()
        self.q_mobile_ras_fp = None
        self.q_mobile_ras_pp = None

        # populated by self.get_analysis_period()
        self.sd_start = None
        self.sd_end = None
        self.bed_prep_period = None

        # populated by self.get_bed_prep_period()
        self.bp_start_date = None
        self.bp_end_date = None

        # populated by self.bed_prep_ras()
        self.foi_df = None
        self.q_max = None

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2rp + "Output\\" + self.condition + "\\"
        fGl.chk_dir(self.out_dir)

        # populated by self.import_flow_data()
        self.flow_df = None

        # populated by self.get_years_list()
        self.years_list = []

        # populated by self.get_flows_list()
        self.flows_list = []

        # populated by self.make_yoi_dir()
        self.sub_dir = None

        # populated by self.get_hydraulic_rasters()
        self.discharges = []
        self.Q_h_dict = {}
        self.Q_u_dict = {}
        self.Q_wse_dict = {}

        # populated by self.get_grain_ras()
        self.grain_ras = None

        # populated by self.ras_taux()
        self.Q_taux_dict = {}

        # populated by self.get_dem_ras()
        self.dem_ras = None

        # populated by self.recession_rate_ras()
        self.Q_wle_dict = {}

        self.import_flow_data()
        self.get_date_range()
        self.get_years_list()

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

    def get_date_range(self):
        self.logger.info("Determining range of dates for relevant recruitment period...")
        try:
            self.sd_start = self.rc_data.loc[self.rc.sd_start].VALUE
            self.sd_end = self.rc_data.loc[self.rc.sd_end].VALUE
            self.bed_prep_period = self.rc_data.loc[self.rc.bed_prep_period].VALUE
        except:
            self.logger.error("ERROR: Could not determine season start date and/or bed prep period, check "
                              "recruitment_criteria.xlxs to ensure that values exist for species of interest.")

    def get_analysis_period(self, year):
        try:
            # make sure we have period from start date to end date in flow data for year to be valid choice for analysis
            # starting self.bed_prep_period years before season start date
            analysis_start_date = dt.datetime(year - self.bed_prep_period, self.sd_start.month, self.sd_start.day, 0, 0)
            # ending one year after season start date (minus one day)
            analysis_end_date = dt.datetime(year + 1, self.sd_start.month, self.sd_start.day, 0, 0) - dt.timedelta(days=1)
            return analysis_start_date, analysis_end_date
        except:
            self.logger.error("ERROR: Could not determine analysis period.")

    def get_bed_prep_period(self):
        try:
            self.bp_start_date = dt.datetime(self.selected_year - self.bed_prep_period, self.sd_start.month, self.sd_start.day, 0, 0)
            self.bp_end_date = dt.datetime(self.selected_year, self.sd_end.month, self.sd_end.day, 0, 0)
        except:
            self.logger.error("ERROR: Could not determine bed prep period.")

    def get_years_list(self):
        self.logger.info("Creating list of years from flow data...")
        # create list of years from self.flow_df
        try:
            all_years_list = list(set(self.flow_df.index.year))
            for year in all_years_list:
                start_date, end_date = self.get_analysis_period(year)
                if (start_date in self.flow_df.index) and (end_date in self.flow_df.index):
                    self.years_list.append(year)
        except:
            self.logger.error("ERROR: Could not parse years from flow data.")

    def make_yoi_dir(self):
        # create directory for selected year as a sub-directory of out_dir
        self.sub_dir = os.path.join(self.out_dir, str(self.selected_year))
        try:
            if not os.path.exists(self.sub_dir):
                self.logger.info("Creating sub-directory (folder) for year-of-interest...")
                os.mkdir(self.sub_dir)
        except:
            self.logger.error("ERROR: Could not create sub-directory (folder) for year-of-interest.")

    def get_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            mkt = cMkT.MakeFlowTable(self.condition, "", unit=self.units)
            self.discharges = sorted(mkt.discharges)
            self.Q_h_dict = {Q: self.dir2condition + mkt.dict_Q_h_ras[Q] for Q in self.discharges}
            self.Q_u_dict = {Q: self.dir2condition + mkt.dict_Q_u_ras[Q] for Q in self.discharges}

            if len(mkt.dict_Q_wse_ras) > 0:
                self.Q_wse_dict = {Q: self.dir2condition + mkt.dict_Q_wse_ras[Q] for Q in self.discharges}
            else:
                self.Q_wse_dict = {}
                msg = "WARNING: WSE rasters not provided for condition. Will use DEM + depth for interpolation instead. Continue?"
                proceed = askyesno("Missing WSE data",
                                   "No WSE rasters exist for the selected condition. Use DEM + depth for interpolation instead?")
                if not proceed:
                    raise Exception("Use Condition Creator (Get Started tab) to add WSE rasters for the selected condition.")
                else:
                    self.logger.info("Proceeding...")
        except:
            msg = "ERROR: Could not retrieve hydraulic rasters."
            self.logger.error(msg)
            raise Exception(msg)

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

    def ras_q_mobile(self, prep_level):
        """
        Q_mobile is a raster where each cell has a value equal to the lowest discharge where taux >= taux_cr (threshold)
        Prep level is a string equal to "fp" for "fully prepped" or "pp" for "partially prepped"
        """
        if prep_level == "pp":
            taux_cr = self.taux_cr_pp
        elif prep_level == "fp":
            taux_cr = self.taux_cr_fp
        else:
            self.logger.info("ERROR: Unexpected prep level encountered, use \"fp\" or \"pp\" only.")
            return -1
        self.logger.info("Creating Q_mobile raster...")
        try:
            out_ras_path = os.path.join(self.out_dir, f"Q_mobile_{prep_level}_{str(taux_cr).replace('.', '_')}.tif")
            if os.path.exists(out_ras_path):
                q_mobile_ras = Raster(out_ras_path)
                self.logger.info(f'Q_mobile raster already exists ({out_ras_path}). Skipping...')
            else:
                q_mobile_ras = None
                # iterate through discharges in descending order
                for Q in sorted(self.discharges, reverse=True):
                    # retrieving taux rasters
                    self.logger.info(f'Analyzing Q = {Q}...')
                    taux_ras = Raster(self.Q_taux_dict[Q])
                    # creating Q_mobile raster if there is none created
                    if q_mobile_ras is None:
                        q_mobile_ras = Con(taux_ras >= taux_cr, Q)
                    # overwriting (if still mobilizing for lower flow) values in Q_mobile raster
                    else:
                        q_mobile_ras = Con(taux_ras >= taux_cr, Q, q_mobile_ras)
                q_mobile_ras.save(out_ras_path)
                self.logger.info(f'Saved Q_mobile raster: {out_ras_path}')
            if prep_level == "fp":
                self.q_mobile_ras_fp = q_mobile_ras
            else:
                self.q_mobile_ras_pp = q_mobile_ras
        except:
            self.logger.info("ERROR: Could not create Q_mobile raster...")
            return -1

    def bed_prep_ras(self):
        """
        Recruitment Box Model, Objective 1: Winter Peak Flows Bed Preparation
        Retrieves q mobile rasters ('fp' and 'pp') and determines the maximum flow from flow record.
        Creates bed preparation time raster from q mobile raster by comparing flows to the maximum flow.
        """
        self.logger.info("Creating dataframe from flow_df of period of interest...")
        # determine bed prep period for selected year
        self.get_bed_prep_period()
        try:
            # create flow-of-interest dataframe with bed prep period for selected year
            self.foi_df = self.flow_df.loc[self.bp_start_date:self.bp_end_date]
            # determine maximum Q from flows-of-interest
            self.q_max = int(self.foi_df.max().values[0])
        except:
            self.logger.error("ERROR: Could not determine Q max from bed prep period.")
        # determine if flow has occurred during relevant time period to prepare the bed
        try:
            out_ras_path = os.path.join(self.sub_dir, f"bed_prep_ras.tif")
            if os.path.exists(out_ras_path):
                bp_ras = Raster(out_ras_path)
                self.logger.info(f'Bed prep raster already exists ({out_ras_path}). Skipping...')
            else:
                bp_ras = None
            # determine if the maximum flow (Q) in bed prep period is greater than or equqal to q_mobile_ras values
            bp_ras_fp = Con(self.q_mobile_ras_fp <= self.q_max, 1)
            bp_ras_pp = Con(self.q_mobile_ras_pp <= self.q_max, 2)
            # combine fully prepped and partially prepped
            bp_ras = Con(IsNull(bp_ras_fp), bp_ras_pp, bp_ras_fp)
            bp_ras.save(out_ras_path)
            self.logger.info(f'Saved bed prep raster: {out_ras_path}')
            self.save_info_file(self.sub_dir)
        except:
            self.logger.error("ERROR: Could not create bed preparation raster.")
        # import existing vegetation rasters
        # exclude areas where large vegetation exists

    def get_dem_ras(self):
        self.logger.info("Retrieving DEM raster...")
        try:
            # defining dem raster location
            self.dem_ras = os.path.join(self.dir2condition, 'dem.tif')
            assert os.path.exists(self.dem_ras)
        except:
            self.logger.error("ERROR: Could not retrieve DEM raster...")
            self.dem_ras = None

    def interpolate_wle(self):
        # interpolate water level elevation using method (WLE) from cWaterLevel
        try:
            # if flow-WSE raster dictionary exists, interpolate using WSE rasters rather than with depth rasters
            if self.Q_wse_dict:
                for q, wse_ras in self.Q_wse_dict.items():
                    self.logger.info(f"Q = {q}...")
                    wle = cWL.WLE(wse_ras, self.dem_ras, self.dir2condition, unique_id=True, input_wse=True, method='IDW')
                    wle.interpolate_wle()
            # use depth rasters to interpolate with
            else:
                for q, h_ras in self.Q_h_dict.items():
                    self.logger.info(f"Q = {q}...")
                    wle = cWL.WLE(h_ras, self.dem_ras, self.dir2condition, unique_id=True, method='IDW')
                    wle.interpolate_wle()
            self.Q_wle_dict = {q: os.path.join(self.dir2condition, f'wle{fGl.write_Q_str(q)}.tif') for q in self.discharges}
        except:
            self.logger.error("ERROR: Could not interpolate water level elevation...")

    def recession_rate_ras(self):
        """
        Recruitment Box Model, Objective 2: Spring Recession Rates
        Creates recession rate raster (optimal, at-risk, lethal) from water surface elevation rasters for each day
        at each pixel.
        """
        # convert WLE rasters to numpy arrays
        for q, wle_ras in self.Q_wle_dict.items():
            self.logger.info(f"Q = {q}...")
            wle_mat = arcpy.RasterToNumPyArray(wle_ras, nodata_to_value=np.nan)

    def dry_season_ras(self):
        """
        Recruitment Box Model, Objective 3: Summer Low Flows No Inundation
        Creates raster of recruitment areas that are inundated after spring growth period in summer.
        """

    def recruitment_area_ras(self):
        """
        Creates raster of areas where all three objectives of the Recruitment Box Model area met.
        """

    def save_info_file(self, path):
        info_path = os.path.join(self.sub_dir, os.path.basename(path).rsplit(".", 1)[0] + '.info.txt')
        with open(info_path, "w") as info_file:
            info_file.write(f"Year-of Interest for Recruitment Potential Analysis: {self.selected_year}")
            info_file.write(f"\nBed Prep Period Start Date: {dt.datetime.strftime(self.bp_start_date, '%Y-%m-%d')}")
            info_file.write(f"\nBed Prep Period End Date: {dt.datetime.strftime(self.bp_end_date, '%Y-%m-%d')}")
            info_file.write(f"\nGermination Period Start Date: {dt.datetime.strftime(self.sd_start, '%Y-%m-%d')}")
            info_file.write(f"\nGermination Period End Date: {dt.datetime.strftime(self.sd_end, '%Y-%m-%d')}")
            info_file.write(f"\nCritical Dimensionless Shear Stress Threshold for Fully Prepared Bed: {self.taux_cr_fp}")
            info_file.write(f"\nCritical Dimensionless Shear Stress Threshold for Partially Prepared Bed: {self.taux_cr_pp}")
        self.logger.info(f"Saved info file: {info_path}")

    def run_rp(self):
            self.make_yoi_dir()
            self.get_hydraulic_rasters()
            self.get_grain_ras()
            self.ras_taux()
            self.ras_q_mobile(prep_level="fp")
            self.ras_q_mobile(prep_level="pp")
            self.bed_prep_ras()
            self.get_dem_ras()
            self.interpolate_wle()
            self.recession_rate_ras()
            #self.dry_season_ras()
            #self.recruitment_area_ras()


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
    rp = RecruitmentPotential(condition='2017_lbp', flow_data=flowdata, species='Fremont Cottonwood', selected_year='1995', units='us')
    rp.run_rp()
