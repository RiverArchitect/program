try:
    import sys, os, random
    import logging
    from tkinter.messagebox import askyesno, showinfo
    import pandas as pd
    import datetime as dt
    import numpy as np
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
    import cInputOutput as cIO
    from cLogger import Logger
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")
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

    def __init__(self, condition, flow_data, species, selected_year, units, ex_veg_ras, grading_ext_ras):
        # initialize logger
        self.logger = Logger("logfile")
        self.logger = logging.getLogger("logfile")
        # Create a temporary cache folder for, e.g., geospatial analyses; use self.clear_cache() function to delete
        self.cache = os.path.dirname(__file__) + "\\.cache%s\\" % str(random.randint(10000, 99999))
        fGl.chk_dir(self.cache)  # from fGlobal
        # define condition (i.e. DEM)
        self.condition = str(condition)
        self.dir2condition = config.dir2conditions + self.condition + "\\"
        # define flow data file path
        self.flow_data = flow_data
        # define species
        self.species = species
        # define selected year
        self.selected_year = int(selected_year) if len(selected_year) else None
        # define existing vegetation raster
        self.ex_veg_ras = ex_veg_ras
        # define grading extents raster
        self.grading_ext_ras = grading_ext_ras
        # define instance of cRecruitmentCriteria
        self.rc = cRC.RecruitmentCriteria()
        # get relevant recruitment criteria data for species of interest
        self.rc_data = self.rc.species_dict[self.species]

        # define units
        self.units = units
        self.area_units = "ft^2" if self.units == 'us' else 'm^2'
        self.length_units = 'ft' if self.units == 'us' else 'm'
        self.u_units = self.length_units + '/s'
        self.ft2ac = config.ft2ac if self.units == 'us' else 1
        self.ft2m = config.ft2m if self.units == 'us' else 1
        # (in/ft) conversion factor for US customary units else dummy conversion in SI
        self.ft2in = 12 if self.units == 'us' else 1
        # relative grain density (ratio of rho_s and rho_w)
        self.s = 2.68
        # (ft/cm) conversion factor for US customary units else dummy conversion in SI
        self.cm2ft = 1 / 30.48
        # (ft/mm) conversion factor for US customary units else dummy conversion in SI
        self.mm2ft = 1 / 304.8

        # populated by self.ras_q_mobile()
        self.q_mobile_ras_fp = None
        self.q_mobile_ras_pp = None

        # populated by self.get_date_range()
        self.sd_start = None
        self.sd_end = None
        self.base_flow_start = None
        self.bed_prep_period = None

        # populated by self.get_bed_prep_period()
        self.bp_start_date = None
        self.bp_end_date = None
        
        # populated by self.get_grain_size_crit()
        self.grain_size_crit = None

        # populated by self.get_recession_period()
        self.rec_start_date = None
        self.rec_end_date = None

        # populated by self.get_inundation_period()
        self.inund_start_date = None
        self.inund_end_date = None

        # populated by self.bed_prep_ras()
        self.bp_flow_df = None
        self.q_bp_max = None

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
        self.dem_mat = None
        self.get_dem_ras()

        # populated by self.get_sd_crop_area()
        self.crop_area_mat = None
        self.crop_area_ras = None

        # populated by self.recruitment_band_area()
        self.rec_band_mat = None
        self.rec_band_ras = None

        # populated by self.interpolate_wle()
        self.Q_wle_dict = {}

        # populated by self.interp_wle_by_q() (done as needed/on the fly)
        self.Q_wle_mat_dict = {}

        # populated by self.rec_inund_survival()
        self.rr_fav_d_mat = []
        self.rr_stress_d_mat = []
        self.rr_lethal_d_mat = []

        self.import_flow_data()
        self.read_rc_xlsx()
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

    def read_rc_xlsx(self):
        try:
            self.logger.info("Determining range of dates for relevant recruitment period...")
            # seed dispersal start date
            self.sd_start = self.rc_data.loc[self.rc.sd_start].VALUE
            # seed dispersal end date
            self.sd_end = self.rc_data.loc[self.rc.sd_end].VALUE
            # dates do not have associated year in worksheet, use selected year with given month/date
            if self.selected_year:
                self.sd_start = dt.datetime(self.selected_year, self.sd_start.month, self.sd_start.day, 0, 0)
                self.sd_end = dt.datetime(self.selected_year, self.sd_end.month, self.sd_end.day, 0, 0)
                # start of base flow period
                self.base_flow_start = self.rc_data.loc[self.rc.base_flow_start].VALUE
                self.base_flow_start = dt.datetime(self.selected_year, self.base_flow_start.month, self.base_flow_start.day, 0, 0)
            # length of bed preparation period
            self.bed_prep_period = self.rc_data.loc[self.rc.bed_prep_period].VALUE
        except:
            self.logger.error("ERROR: Could not determine season start date, base flow start date and/or bed prep period,"
                              "check recruitment_criteria.xlxs to ensure that values exist for species of interest.")
        try:
            self.logger.info("Determining bed shear stress criteria...")
            # critical dimensionless bed shear stress threshold for fully prepared bed
            self.taux_cr_fp = self.rc_data.loc[self.rc.taux_cr_fp].VALUE
            # critical dimensionless bed shear stress threshold for partially prepared bed
            self.taux_cr_pp = self.rc_data.loc[self.rc.taux_cr_pp].VALUE
        except:
            self.logger.error("ERROR: Could not determine bed shear stress criteria, "
                              "check recruitment_criteria.xlxs to ensure that values exist for species of interest.")
        try:
            self.logger.info(f'Determining grain size criteria (within grading extents)...')
            grain_size_crit_mm = self.rc_data.loc[self.rc.grain_size_crit].VALUE
            self.grain_size_crit = grain_size_crit_mm * self.mm2ft
        except:
            self.logger.error("ERROR: Could not determine grain size criteria (for within grading extents).")
        try:
            self.logger.info("Determining recession rate criteria...")
            # stressful recession rate criteria
            rr_stress_cm = self.rc_data.loc[self.rc.rr_stress].VALUE
            self.rr_stress = rr_stress_cm * self.cm2ft
            # lethal recession rate criteria
            rr_lethal_cm = self.rc_data.loc[self.rc.rr_lethal].VALUE
            self.rr_lethal = rr_lethal_cm * self.cm2ft
        except:
            self.logger.error("ERROR: Could not determine recession rate criteria,"
                              "check recruitment_criteria.xlxs to ensure that values exist for species of interest.")
        try:
            self.logger.info("Determining inundation criteria...")
            # stressful inundation criteria
            self.inund_stress = self.rc_data.loc[self.rc.inund_stress].VALUE
            # lethal inundation criteria
            self.inund_lethal = self.rc_data.loc[self.rc.inund_lethal].VALUE
        except:
            self.logger.error("ERROR: could not determine inundation criteria, "
                              "check recruitment_criteria.xlxs to ensure that values exist for species of interest.")
        try:
            self.logger.info("Determining recruitment band elevation criteria...")
            # lower elevation criteria
            band_elev_lower_cm = self.rc_data.loc[self.rc.band_elev_lower].VALUE
            self.band_elev_lower = band_elev_lower_cm * self.cm2ft
            # upper elevation criteria
            band_elev_upper_cm = self.rc_data.loc[self.rc.band_elev_upper].VALUE
            self.band_elev_upper = band_elev_upper_cm * self.cm2ft
        except:
            self.logger.error("ERROR: Could not determine lower and upper elevation criteria of the recruitment band,"
                              "check recruitment_criteria.xlxs to ensure that values exist for species of interest.")

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

    def get_recession_period(self):
        try:
            self.rec_start_date = dt.datetime(self.selected_year, self.sd_start.month, self.sd_start.day, 0, 0)
            self.rec_end_date = dt.datetime(self.selected_year, self.base_flow_start.month, self.base_flow_start.day, 0, 0)
        except:
            self.logger.error("ERROR: Could not determine recession period.")

    def get_inundation_period(self):
        try:
            self.inund_start_date = self.sd_start
            self.inund_end_date = dt.datetime(self.selected_year + 1, self.sd_start.month, self.sd_start.day, 0, 0) - dt.timedelta(days=1)
        except:
            self.logger.error("ERROR: Could not determine inundation survival period.")

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

    def check_flow_range(self):
        start, end = self.get_analysis_period(self.selected_year)
        analysis_flows = self.flow_df[start:end]
        if max(analysis_flows['Mean daily']) > max(self.discharges) or min(analysis_flows['Mean daily']) < min(self.discharges):
            proceed = showinfo('WARNING: Mean daily flow range is outside of the modeled flow range for the selected analysis period.'
                             'Update condition to include required hydraulic rasters or select a different analysis period.')
            raise Exception('ERROR: Could not complete analysis, missing hydraulic rasters required for selected analysis period.')
        else:
            return

    def get_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            mkt = cMkT.MakeFlowTable(self.condition, "", unit=self.units)
            self.discharges = sorted(mkt.discharges)
            self.check_flow_range()
            self.Q_h_dict = {Q: self.dir2condition + mkt.dict_Q_h_ras[Q] for Q in self.discharges}
            self.Q_u_dict = {Q: self.dir2condition + mkt.dict_Q_u_ras[Q] for Q in self.discharges}

            if len(mkt.dict_Q_wse_ras) > 0:
                self.Q_wse_dict = {Q: self.dir2condition + mkt.dict_Q_wse_ras[Q] for Q in self.discharges}
            else:
                self.Q_wse_dict = {}
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
                        temp_ras = Con(IsNull(taux_ras), 0, taux_ras)
                        q_mobile_ras = Con(temp_ras >= taux_cr, Q, q_mobile_ras)
                q_mobile_ras.save(out_ras_path)
                self.logger.info(f'Saved Q_mobile raster: {out_ras_path}')
            if prep_level == "fp":
                self.q_mobile_ras_fp = q_mobile_ras
            else:
                self.q_mobile_ras_pp = q_mobile_ras
        except:
            self.logger.info("ERROR: Could not create Q_mobile raster...")
            return -1

    def remove_grading_areas(self, ras):
        try:
            self.logger.info('Retrieving grading limits raster for selected condition...')
            # retrieves grading extents raster
            grading_ext_ras = Raster(self.grading_ext_ras)
            # retrieves dmean raster
            grain_ras = Raster(self.grain_ras)
            # check for dmean greater than grain size set in recruitment criteria worksheet to remove from prepared bed area
            self.logger.info(f'Assigning value of "fully prepped" to cells where dmean is less than grain size criteria...')
            self.bp_ras = Con(~IsNull(grading_ext_ras), Con(self.grain_size_crit >= grain_ras, 1, ras), ras)
        except:
            self.logger.error(f'Could not retrieve grading limits raster, check that it is in selected condition folder.')
            return -1

    def remove_veg_areas(self, ras):
        try:
            self.logger.info("Retrieving existing vegetation raster for selected condition...")
            # retrieves existing vegetation raster
            veg_ras = Raster(self.ex_veg_ras)
            # remove areas where existing vegetation exists
            self.logger.info("Removing areas where there is existing vegetation that will not be removed by flood flows...")
            ras_minus_veg = Con(IsNull(veg_ras), ras)
            self.logger.info("Existing vegetation removed from raster...")
            return ras_minus_veg
        except:
            self.logger.error("Could not retrieve existing vegetation raster, check that it is in selected condition folder.")
            return -1

    def recruitment_band(self):
        """
        Creates a integer raster used to create crop raster based
        on the upper and lower limits of recruitment band (from the base flow WLE).
        """
        try:
            self.logger.info(f"Determining flow on the day that base flow begins: {self.base_flow_start}... ")
            q_baseflow = self.flow_df['Mean daily'].loc[self.base_flow_start]
            # create wle mat for q_baseflow
            baseflow_wle_mat = self.interp_wle_by_q(q_baseflow)
            rec_band_mat = self.dem_mat - baseflow_wle_mat
            # create recruitment band with value of 1 where the DEM - q_baseflow WLE is within the elevation upper and lower limits
            self.rec_band_mat = np.where(np.logical_and(rec_band_mat >= self.band_elev_lower, rec_band_mat <= self.band_elev_upper), 1, np.nan)
            rec_band_ras_path = os.path.join(self.sub_dir, f"rec_elev_band.tif")
            self.rec_band_ras = self.convert_array2ras(self.rec_band_mat, rec_band_ras_path)
        except:
            self.logger.error("ERROR: Could not create recruitment band raster.")

    def get_sd_rb_crop_area(self):
        """Gets raster representing area between low and high flow wetted areas during seed dispersal
        and within the recruitment band (if criteria provided).
        """
        self.logger.info("Getting wetted area between low/high seed dispersal period flows...")
        try:
            # create seed dispersal flow dataframe with seed dispersal start and end dates
            self.sd_df = self.flow_df.loc[self.sd_start:self.sd_end]
            # get lowest and highest flows during seed dispersal
            q_low_sd = self.sd_df['Mean daily'].min()
            q_high_sd = self.sd_df['Mean daily'].max()
            # get corresponding WLEs (arrays)
            q_low_sd_wle_mat = self.interp_wle_by_q(q_low_sd)
            q_high_sd_wle_mat = self.interp_wle_by_q(q_high_sd)
            # get corresponding wetted areas (arrays)
            q_low_sd_wetted_area = self.get_wetted_area(q_low_sd_wle_mat)
            q_high_sd_wetted_area = self.get_wetted_area(q_high_sd_wle_mat)
            # set area between low/high flow wetted area to 1, else nan
            self.wa_sd_mat = np.where((q_low_sd_wetted_area != 1) & (q_high_sd_wetted_area == 1), 1, np.nan)
            # create crop raster using wetted areas and recruitment band (arrays) if there are values for recruitment band elevation criteria
            if (~np.isnan(self.band_elev_lower)) and (~np.isnan(self.band_elev_upper)):
                self.logger.info("Cropping the wetted area during seed dispersal to area within recruitment band elevations...")
                self.recruitment_band()
                wa_rb_ras_path = os.path.join(self.sub_dir, f"wa_rb_crop_area.tif")
                self.crop_area_mat = np.where(np.logical_and(self.wa_sd_mat == 1, self.rec_band_mat == 1), 1, np.nan)
                self.convert_array2ras(self.crop_area_mat, wa_rb_ras_path)
                self.crop_area_ras = wa_rb_ras_path
            else:
                self.logger.info(f"No value for recruitment band elevation criteria is provided in recruitment_criteria.xlsx.")
                # save as raster
                self.crop_area_mat = self.wa_sd_mat
                self.wa_ras_path = os.path.join(self.sub_dir, f"wa_sd_ras.tif")
                self.convert_array2ras(self.wa_sd_mat, self.wa_ras_path)
                self.crop_area_ras = self.wa_ras_path
            # remove existing vegetation that will not be removed by flood flows
            if self.ex_veg_ras is not None:
                self.crop_area_minus_veg_path = os.path.join(self.sub_dir, f"crop_area_minus_veg.tif")
                crop_ras = self.remove_veg_areas(self.crop_area_ras)
                crop_ras.save(self.crop_area_minus_veg_path)
                self.logger.info('Saving wetted area raster with vegetation removed...')
                self.crop_area_ras = self.crop_area_minus_veg_path
                self.crop_area_mat = arcpy.RasterToNumPyArray(self.crop_area_ras, nodata_to_value=np.nan)
            else:
                self.logger.info(f'No existing vegetation raster provided, skipping area removal.')
                pass
            return
        except:
            self.logger.info("ERROR: Failed to get crop area.")

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
            # create bed prep flows dataframe with bed prep period for selected year
            self.bp_flow_df = self.flow_df.loc[self.bp_start_date:self.bp_end_date]
            # determine maximum Q from bed prep flows dataframe
            self.q_bp_max = int(self.bp_flow_df.max().values[0])
            self.logger.info(f'Maximum Q from bed prep period: {self.q_bp_max}')
        except:
            self.logger.error("ERROR: Could not determine Q max from bed prep period.")
        # determine if flow has occurred during relevant time period to prepare the bed
        try:
            self.bp_ras_path = os.path.join(self.sub_dir, f"bed_prep_ras.tif")
            # determine if the maximum flow (Q) in bed prep period is greater than or equal to q_mobile_ras values
            bp_ras_fp = Con(self.q_mobile_ras_fp <= self.q_bp_max, 1, 0)
            bp_ras_pp = Con(self.q_mobile_ras_pp <= self.q_bp_max, 0.5, 0)
            # combine fully prepped and partially prepped
            bp_ras = Con(IsNull(bp_ras_fp), bp_ras_pp, bp_ras_fp)
            # assign areas in grading extents with grain size smaller than grain size criteria a value of 1
            if self.grading_ext_ras is not None:
                self.remove_grading_areas(ras=bp_ras)
            else:
                self.logger.info(f'No grading extents raster provided, not assigning "fully prepped" value to area.')
                pass
            # excluding area outside of wetted area (during seed dispersal) from bed prep raster
            self.logger.info(f"Excluding area outside of the crop area during "
                             f"seed dispersal from bed preparation assessment...")
            # convert raster to array
            bp_mat = arcpy.RasterToNumPyArray(bp_ras, nodata_to_value=np.nan)
            bp_mat_crop = np.where(self.crop_area_mat == 1, bp_mat, np.nan)
            self.bp_mat = np.where(np.logical_and(self.crop_area_mat == 1, np.isnan(bp_mat)), 0, bp_mat_crop)
            self.bp_ras = self.convert_array2ras(self.bp_mat, self.bp_ras_path)
            self.save_info_file(self.sub_dir)
        except:
            self.logger.error("ERROR: Could not create bed preparation raster.")

    def get_dem_ras(self):
        self.logger.info("Retrieving DEM raster...")
        try:
            # defining dem raster location
            self.dem_ras = os.path.join(self.dir2condition, 'dem.tif')
            assert os.path.exists(self.dem_ras)
            self.dem_mat = arcpy.RasterToNumPyArray(self.dem_ras, nodata_to_value=np.nan)
        except:
            self.logger.error("ERROR: Could not retrieve DEM raster...")
            self.dem_ras = None
            self.dem_mat = None

    def _set_arcpy_env(func):
        def wrapper(self, *args, **kwargs):
            # configure arcpy environment before calling main function
            self.logger.info("Configuring arcpy environment...")
            arcpy.env.workspace = self.cache
            arcpy.env.overwriteOutput = True
            self.snap_raster = Raster(self.dem_ras)
            # set selected raster as environment snap raster and output coordinate system
            arcpy.env.snapRaster = self.snap_raster
            arcpy.env.outputCoordinateSystem = Raster(self.snap_raster).spatialReference
            # set extent to max of inputs
            arcpy.env.extent = self.dem_ras
            # get cell size
            self.cell_size_x = arcpy.GetRasterProperties_management(self.snap_raster, 'CELLSIZEX')[0]
            self.cell_size_y = arcpy.GetRasterProperties_management(self.snap_raster, 'CELLSIZEY')[0]
            self.cell_size = str(self.cell_size_x) + ' ' + str(self.cell_size_y)
            # call main function
            self.logger.info("arcpy environment configured.")
            func(self, *args, **kwargs)
            # can do stuff after function call here
        return wrapper

    def interpolate_wle(self):
        # interpolate water level elevation using method (WLE) from cWaterLevel
        try:
            # if flow-WSE raster dictionary exists, interpolate using WSE rasters rather than with depth rasters
            q_ras_dict = self.Q_wse_dict if self.Q_wse_dict else self.Q_h_dict
            input_wse = True if self.Q_wse_dict else self.Q_h_dict
            for q, ras in q_ras_dict.items():
                self.logger.info(f"Q = {q}...")
                wle_path = os.path.join(self.dir2condition, f'wle{fGl.write_Q_str(q)}.tif')
                self.Q_wle_dict[q] = wle_path
                wle = cWL.WLE(ras, self.dem_ras, self.dir2condition, unique_id=True, input_wse=input_wse, method='IDW')
                if not wle.check_interp_ras(wle_path):
                    wle.interpolate_wle()
                else:
                    self.logger.info("Using existing interpolated WLE raster ...")
        except:
            self.logger.error("ERROR: Could not interpolate water level elevation...")

    def interp_wle_by_q(self, q):
        self.logger.info(f"Q = {q}...")
        q_u_index = np.searchsorted(self.discharges, q, side='right')
        q_l_index = q_u_index - 1
        q_l = self.discharges[q_l_index]
        q_u = self.discharges[q_u_index]
        self.logger.info(f"Closest modeled flows for interpolation: {q_l} - {q_u}")
        try:
            q_l_wle_ras = self.Q_wle_dict[q_l]
            q_u_wle_ras = self.Q_wle_dict[q_u]
            try:
                # update dict of wle mats on the fly (if haven't needed yet)
                try:
                    # see if we've already calculated this
                    q_l_wle_mat = self.Q_wle_mat_dict[q_l]
                except:
                    # otherwise, convert WLE raster to numpy array and add to dict for later use
                    q_l_wle_mat = arcpy.RasterToNumPyArray(q_l_wle_ras, nodata_to_value=np.nan)
                    self.Q_wle_mat_dict[q_l] = q_l_wle_mat
                try:
                    # see if we've already calculated this
                    q_u_wle_mat = self.Q_wle_mat_dict[q_u]
                except:
                    # otherwise, convert WLE raster to numpy array and add to dict for later use
                    q_u_wle_mat = arcpy.RasterToNumPyArray(q_u_wle_ras, nodata_to_value=np.nan)
                    self.Q_wle_mat_dict[q_u] = q_u_wle_mat
                try:
                    q_wle_mat = q_l_wle_mat + ((q_u_wle_mat - q_l_wle_mat) * (q - q_l) / (q_u - q_l))
                    return q_wle_mat
                except:
                    self.logger.info(f"Failed to interpolate WLE array for Q = {q}.")
            except:
                self.logger.info(f"Unable to convert required interpolated WLE rasters into arrays...")
        except:
            self.logger.info(f"Unable to retrieve required interpolated WLE rasters...")

    def convert_array2ras(self, mat, ras_path):
        try:
            # set reference point for array to raster conversion
            self.logger.info(f"Converting array to raster...")
            ref_pt = arcpy.Point(self.snap_raster.extent.XMin, self.snap_raster.extent.YMin)
            ras = arcpy.NumPyArrayToRaster(mat, lower_left_corner=ref_pt,
                                           x_cell_size=float(self.cell_size_x),
                                           y_cell_size=float(self.cell_size_y),
                                           value_to_nodata=np.nan)
            ras.save(ras_path)
            self.logger.info(f'Saved converted raster: {ras_path}')
        except:
            self.logger.info(f'Unable to convert array to raster...')

    def get_wetted_area(self, wle_mat):
        # calculate wetted area array
        self.logger.info(f"Calculating wetted area...")
        try:
            # subtract wle raster from dem raster to determine depth raster
            self.logger.info(f'Subtracting DEM from WLE array...')
            h_mat = wle_mat - self.dem_mat
            # convert depth raster to integer raster
            self.logger.info(f'Converting depth array to interger mat...')
            wetted_area_mat = np.where(h_mat > 0, 1, 0)
            return wetted_area_mat
        except:
            logging.info(f"Failed to convert depth array to integer array...")

    def is_inundated(self, q_wle_mat):
        # determine if cell is inundated (WSE > DEM)
        # returns value of True if inundated and False if dry
        return q_wle_mat > self.dem_mat

    def calc_mortality_coef(self):
        try:
            # calculate mortality coefficient with recession rate stressful and lethal days totals
            self.logger.info('Calculating mortality coefficient array...')
            # calculate arrays as percent of total days
            self.rr_stress_per_mat = (self.rr_stress_d_mat / self.rr_total_d) * 100
            self.rr_lethal_per_mat = (self.rr_lethal_d_mat / self.rr_total_d) * 100
            mort_coef_mat = ((self.rr_lethal_per_mat * 3) + (self.rr_stress_per_mat * 1)) / 3
            # set null outside max flow wetted area
            mort_coef_mat = np.where(self.crop_area_mat == 1, mort_coef_mat, np.nan)
            # convert mortality coefficient array to raster
            self.logger.info('Converting mortality coefficient to raster...')
            self.mort_coef_ras_path = os.path.join(self.sub_dir, f"mortality_coef_ras.tif")
            self.convert_array2ras(mort_coef_mat, self.mort_coef_ras_path)
        except:
            self.logger.info(f"Unable to calculate mortality coefficient array...")

    def rec_inund_survival(self):
        """
        Recruitment Box Model, Objective 2: Spring Recession Rates
        Creates recession rate raster (optimal, at-risk, lethal) from water surface elevation rasters for each day
        at each pixel.
        Recruitment Box Model, Objective 3: Prolonged inundation after establishment
        Creates raster of recruitment areas that are inundated for stressful and lethal periods after germination.
        """
        self.logger.info("Creating dataframe from flow_df of recession period...")
        # determine recession rate and inundation survival periods for selected year
        self.get_recession_period()
        self.get_inundation_period()
        try:
            # create recession rate flow dataframe with recession start and end dates
            # include 3 days before start so we can get 3 day moving average on first day of recession period
            self.rr_df = self.flow_df.loc[self.rec_start_date - dt.timedelta(days=3):self.rec_end_date]
            rr_end_day = np.datetime64(self.rec_end_date)
            # create inundation flow dataframe with inundation start and end dates
            self.inund_df = self.flow_df.loc[self.inund_start_date:self.inund_end_date]
            inund_start_day = np.datetime64(self.inund_start_date)
            # dataframe spanning recession and inundation survival periods so we can handle both in one loop
            self.rr_inund_df = self.flow_df.loc[self.rec_start_date - dt.timedelta(days=3):self.inund_end_date]
            # create seed dispersal flow dataframe with seed dispersal start and end dates
            self.sd_df = self.flow_df.loc[self.sd_start:self.sd_end]
            sd_end_day = np.datetime64(self.sd_end)
            # determine maximum Q from seed dispersal dataframe
            self.q_sd_max = int(self.sd_df.max().values[0])
        except:
            self.logger.error("ERROR: Could not create recession rate or seed dispersal flow dataframe.")
        # defining recession rate total days
        self.rr_total_d = (len(self.rr_df) - 3)
        window = []
        have_gone_dry = False
        # iterating over groups of 4 consecutive rows (for 3 day moving average of recession rate)
        # starting 3 days before beginning of recession/seed dispersal start date
        self.logger.info(f'Beginning to track cell inundation and recession rate...')
        for i in range(len(self.rr_inund_df) - 4):
            # take 4 day slice from total flow record
            slice = self.rr_inund_df.iloc[i: i + 4]
            qm3, qm2, qm1, q = slice['Mean daily'].values
            day = slice.index.values[-1]
            # get "today's" wle array
            q_wle_mat = self.interp_wle_by_q(q)
            # if first iteration in loop:
            if i == 0:
                # get wle arrays for first 3 days
                window.append(self.interp_wle_by_q(qm3))
                window.append(self.interp_wle_by_q(qm2))
                window.append(self.interp_wle_by_q(qm1))
                # initialize stressful/lethal days arrays
                self.rr_stress_d_mat = np.zeros_like(q_wle_mat)
                self.rr_lethal_d_mat = np.zeros_like(q_wle_mat)
                # initialize consecutive inundation days array
                self.consec_inund_days_max = np.zeros_like(q_wle_mat)
                self.consec_inund_days_now = np.zeros_like(q_wle_mat)
                self.inund_surv_mat = np.ones_like(q_wle_mat)
            # update window of wle arrays (add in today's and take out array from 3 days prior)
            window.append(q_wle_mat)
            qm3_wle_mat = window.pop(0)
            # have gone dry if previously went dry or currently dry
            dry_now = ~self.is_inundated(q_wle_mat)
            have_gone_dry = have_gone_dry | dry_now
            # keep track of area inundated for entire seed dispersal period, this area will be excluded
            if day == sd_end_day:
                inundated_during_sd = ~have_gone_dry
            # if we are in recession rate analysis period
            if day < rr_end_day:
                # if we haven't gone dry yet, subtract that time from total recession rate days (denominator for mortality coefficient)
                self.rr_total_d = self.rr_total_d - np.where(~have_gone_dry, 1, 0)
                # calculate 3-day avg recession rate
                rr = (q_wle_mat - qm3_wle_mat) / 3
                # calculate stressful and lethal recession rate total arrays (only lethal/stressful recession if dry)
                one_if_dry = np.where(dry_now, 1, 0)
                self.rr_stress_d_mat = np.where((self.rr_stress < rr) & (rr <= self.rr_lethal), (self.rr_stress_d_mat + one_if_dry), self.rr_stress_d_mat)
                self.rr_lethal_d_mat = np.where((self.rr_lethal < rr), (self.rr_lethal_d_mat + one_if_dry), self.rr_lethal_d_mat)
            # if we are in inundation analysis period
            if day >= inund_start_day:
                # if dry, reset consecutive inundation days to zero, otherwise if wet add 1
                self.consec_inund_days_now = np.where(dry_now, 0, self.consec_inund_days_now + 1)
                # keep track of max consecutive inundation days
                self.consec_inund_days_max = np.maximum(self.consec_inund_days_now, self.consec_inund_days_max)
        # convert max consecutive inundated days to inundation survival classification (stress & lethal criteria)
        self.inund_surv_mat = np.where((self.consec_inund_days_max > self.inund_stress) & (self.consec_inund_days_max <= self.inund_lethal), 0.5, self.inund_surv_mat)
        self.inund_surv_mat = np.where((self.consec_inund_days_max > self.inund_lethal), 0, self.inund_surv_mat)
        # calculate favorable recession rate days (total) array
        self.rr_fav_d_mat = self.rr_total_d - self.rr_stress_d_mat - self.rr_lethal_d_mat
        try:
            # interpolating wle of maximum flow during seed dispersal period
            q_sd_max_wle_mat = self.interp_wle_by_q(self.q_sd_max)
            # excluding area outside of wetted area array from recession rate days arrays
            self.logger.info(f"Excluding area outside of the crop area during "
                             f"seed dispersal from recession rate/inundation assessment...")
            self.rr_fav_d_mat = np.where(self.crop_area_mat == 1, self.rr_fav_d_mat, np.nan)
            self.rr_stress_d_mat = np.where(self.crop_area_mat == 1, self.rr_stress_d_mat, np.nan)
            self.rr_lethal_d_mat = np.where(self.crop_area_mat == 1, self.rr_lethal_d_mat, np.nan)
            self.consec_inund_days_max = np.where(self.crop_area_mat == 1, self.consec_inund_days_max, np.nan)
            self.inund_surv_mat = np.where(self.crop_area_mat == 1, self.inund_surv_mat, np.nan)
        except:
            self.logger.info(f'ERROR: Unable to exclude area outside of maximum wetted area during seed dispersal '
                             f'from recession rate/inundation assessment...')
        try:
            # convert recession rate days (total) arrays to rasters
            self.logger.info('Converting recession rate (days) arrays to rasters...')
            rr_fav_ras_path = os.path.join(self.sub_dir, f"rr_fav_days_ras.tif")
            rr_stress_ras_path = os.path.join(self.sub_dir, f"rr_stress_days_ras.tif")
            rr_lethal_ras_path = os.path.join(self.sub_dir, f"rr_lethal_days_ras.tif")
            self.convert_array2ras(self.rr_fav_d_mat, rr_fav_ras_path)
            self.convert_array2ras(self.rr_stress_d_mat, rr_stress_ras_path)
            self.convert_array2ras(self.rr_lethal_d_mat, rr_lethal_ras_path)
        except:
            self.logger.info(f'ERROR: Unable to convert recession rate (days) arrays to rasters...')
        # convert recession rate days to mortality coefficient
        self.calc_mortality_coef()
        try:
            # convert inundation arrays (max consecutive days and survival) to rasters
            self.logger.info('Converting max inundation days array to raster...')
            self.consec_inund_max_path = os.path.join(self.sub_dir, f"max_inund_days_ras.tif")
            self.convert_array2ras(self.consec_inund_days_max, self.consec_inund_max_path)
            self.logger.info('Converting inundation survival array (fav, stress, lethal) to raster...')
            self.inund_surv_path = os.path.join(self.sub_dir, f"inundation_survival.tif")
            self.convert_array2ras(self.inund_surv_mat, self.inund_surv_path)
        except:
            self.logger.info(f'ERROR: Unable to convert max inundation days and inundation survival arrays to rasters...')

    def scour_burial_ras(self):
        """
        Recruitment Box Model, Objective 4: Uprooting or burial after establishment
        Creates raster of recruitment areas that experience bed preparing flows.
        """
        try:
            # create scour & burial survival period dataframe (same as inundation survival period dataframe)
            scour_burial_df = self.inund_df
            # determine maximum Q from scour & burial survival period dataframe
            self.q_sb_max = int(scour_burial_df.max().values[0])
            self.logger.info(f'Maximum Q from scour & burial survival period: {self.q_sb_max}')
        except:
            self.logger.error("ERROR: Could not determine Q max from scour & burial survival period.")
        # determine if flow has occurred after seed dispersal that could potentially scour or bury seedlings
        try:
            self.sb_ras_path = os.path.join(self.sub_dir, f"scour_burial_ras.tif")
            # determine if the maximum flow (Q) in scour & burial survival period is greater than or equal to q_mobile_ras values
            sb_ras_fp = Con(self.q_sb_max >= self.q_mobile_ras_fp, 0)
            sb_ras_pp = Con(self.q_sb_max >= self.q_mobile_ras_pp, 0.5)
            # combine fully prepped and partially prepped to indicate if seedlings have potentially been scoured or buried
            sb_ras = Con(IsNull(sb_ras_fp), sb_ras_pp, sb_ras_fp)
            self.sb_ras = Con(IsNull(sb_ras), 1, sb_ras)
            # excluding area outside of wetted area (during seed dispersal) from scour/burial raster
            self.logger.info(f"Excluding area outside of the crop area during "
                             f"seed dispersal from scour/burial assessment...")
            # convert raster to array
            sb_mat = arcpy.RasterToNumPyArray(sb_ras, nodata_to_value=np.nan)
            sb_mat_crop = np.where(self.crop_area_mat == 1, sb_mat, np.nan)
            # assign areas within the crop area a value of 1 if the value of the sb_mat is null
            self.sb_mat = np.where(np.logical_and(self.crop_area_mat == 1, np.isnan(sb_mat)), 1, sb_mat_crop)
            self.sb_ras = self.convert_array2ras(self.sb_mat, self.sb_ras_path)
            self.save_info_file(self.sub_dir)
        except:
            self.logger.error("ERROR: Could not create the scour & burial survival raster.")

    def recruitment_potential_ras(self):
        """
        Creates raster that combined all objectives of the Recruitment Box Model.
        """
        try:
            self.logger.info(f"Retrieving bed preparation raster...")
            # retrieve bed preparation raster and assign values of 0 (unprepared) to all cells with Null value
            bp_ras = Raster(self.bp_ras_path)
            self.logger.info(f"Retrieving mortality coefficient raster...")
            # retrieve mortality coefficient raster and convert coefficient to metric
            mort_coef_ras = Raster(self.mort_coef_ras_path)
            rr_ras = Con(mort_coef_ras > 30, 0, 1)
            rr_ras = Con((mort_coef_ras <= 30) & (mort_coef_ras > 20), 0.5, rr_ras)
            self.logger.info(f"Retrieving inundation survival raster...")
            # retrieve inundation survival raster
            inund_ras = Raster(self.inund_surv_path)
            self.logger.info(f"Retrieving scour & burial survival raster...")
            # retrieve scour & burial survival raster and assign values of 1 (unprepared) to all cells with null value
            sb_ras = Raster(self.sb_ras_path)
            self.logger.info(f"Combining rasters to calculate the overall recession potential...")
            # combine objectives into single metric by taking the product of the bed prep, recession rate, inundation, and scour & burial rasters
            rec_pot_ras = bp_ras * rr_ras * inund_ras * sb_ras
            rec_pot_ras_path = os.path.join(self.sub_dir, f"recruitment_potential_ras.tif")
            self.logger.info(f"Saving the recruitment potential raster: {rec_pot_ras_path}")
            rec_pot_ras.save(rec_pot_ras_path)
        except:
            self.logger.info(f"ERROR: Unable to combine rasters to calculate the overall recession potential...")

    def get_total_recruitment_area(self):
        """
        Uses recruitment potential raster to calculate total area for each metric
        """
        self.xlsx = os.path.join(self.sub_dir, "rp_total_area.xlsx")
        self.xlsx_writer = cIO.Write(config.xlsx_recruitment_output)
        rec_pot_ras = Raster(os.path.join(self.sub_dir, f"recruitment_potential_ras.tif"))
        cell_size = float(arcpy.GetRasterProperties_management(rec_pot_ras, 'CELLSIZEX').getOutput(0))
        opt_rp = Con(rec_pot_ras == 1, 1)
        fav_rp = Con(rec_pot_ras == 0.5, 1)
        str_rp = Con(rec_pot_ras == 0.25, 1)
        tol_rp = Con(rec_pot_ras == 0.125, 1)
        ll_rp = Con(rec_pot_ras == 0.0625, 1)
        let_rp = Con(rec_pot_ras == 0, 1)
        rp_metric_list = [opt_rp, fav_rp, str_rp, tol_rp, ll_rp, let_rp]
        cols = ["B", "C", "D", "E", "F", "G"]
        row_num = 3
        self.xlsx_writer.write_cell("A", row_num, self.selected_year)
        for metric, col in zip(rp_metric_list, cols):
            # cumulative area for the metric (opt, fav, str, tol, ll, let)
            mat = arcpy.RasterToNumPyArray(metric, nodata_to_value=0)
            area = np.sum(mat) * (cell_size**2)
            self.xlsx_writer.write_cell(col, row_num, area)
        self.xlsx_writer.save_close_wb(self.xlsx)

    def get_bed_prep_area(self):
        """
        Uses bed prep raster to calculate total area for each metric
        """
        bp_ras = Raster(os.path.join(self.sub_dir, f"bed_prep_ras.tif"))
        cell_size = float(arcpy.GetRasterProperties_management(bp_ras, 'CELLSIZEX').getOutput(0))
        ff_bp = Con(bp_ras == 1, 1)
        pp_bp = Con(bp_ras == 0.5, 1)
        up_bp = Con(bp_ras == 0, 1)
        bp_metric_list = [ff_bp, pp_bp, up_bp]
        cols = ["H", "I", "J"]
        row_num = 3
        for metric, col in zip(bp_metric_list, cols):
            # cumulative area for the metric (opt, fav, str, tol, ll, let)
            mat = arcpy.RasterToNumPyArray(metric, nodata_to_value=0)
            area = np.sum(mat) * (cell_size**2)
            self.xlsx_writer.write_cell(col, row_num, area)
        self.xlsx_writer.save_close_wb(self.xlsx)

    def get_recession_rate_area(self):
        """
        Uses mortality coefficient raster to calculate total area for each metric
        """
        mort_coef_ras = Raster(os.path.join(self.sub_dir, f"mortality_coef_ras.tif"))
        cell_size = float(arcpy.GetRasterProperties_management(mort_coef_ras, 'CELLSIZEX').getOutput(0))
        fr_mort = Con(mort_coef_ras <= 20, 1)
        sr_mort = Con((mort_coef_ras > 20) & (mort_coef_ras <= 30), 1)
        lr_mort = Con(mort_coef_ras > 30, 1)
        mort_metric_list = [fr_mort, sr_mort, lr_mort]
        cols = ["K", "L", "M"]
        row_num = 3
        for metric, col in zip(mort_metric_list, cols):
            # cumulative area for the metric (opt, fav, str, tol, ll, let)
            mat = arcpy.RasterToNumPyArray(metric, nodata_to_value=0)
            area = np.sum(mat) * (cell_size**2)
            self.xlsx_writer.write_cell(col, row_num, area)
        self.xlsx_writer.save_close_wb(self.xlsx)

    def get_inundation_surv_area(self):
        """
        Uses inudation survival raster to calculate total area for each metric
        """
        ind_surv_ras = Raster(os.path.join(self.sub_dir, f"inundation_survival.tif"))
        cell_size = float(arcpy.GetRasterProperties_management(ind_surv_ras, 'CELLSIZEX').getOutput(0))
        fi_surv = Con(ind_surv_ras == 1, 1)
        si_surv = Con(ind_surv_ras == 0.5, 1)
        li_surv = Con(ind_surv_ras == 0, 1)
        mort_metric_list = [fi_surv, si_surv, li_surv]
        cols = ["N", "O", "P"]
        row_num = 3
        for metric, col in zip(mort_metric_list, cols):
            # cumulative area for the metric (opt, fav, str, tol, ll, let)
            mat = arcpy.RasterToNumPyArray(metric, nodata_to_value=0)
            area = np.sum(mat) * (cell_size**2)
            self.xlsx_writer.write_cell(col, row_num, area)
        self.xlsx_writer.save_close_wb(self.xlsx)

    def get_scour_burial_area(self):
        """
        Uses scour & burial survival raster to calculate total area for each metric
        """
        sb_surv_ras = Raster(os.path.join(self.sub_dir, f"scour_burial_ras.tif"))
        cell_size = float(arcpy.GetRasterProperties_management(sb_surv_ras, 'CELLSIZEX').getOutput(0))
        up_surv = Con(sb_surv_ras == 1, 1)
        pp_surv = Con(sb_surv_ras == 0.5, 1)
        fp_surv = Con(sb_surv_ras == 0, 1)
        mort_metric_list = [up_surv, pp_surv, fp_surv]
        cols = ["Q", "R", "S"]
        row_num = 3
        for metric, col in zip(mort_metric_list, cols):
            # cumulative area for the metric (opt, fav, str, tol, ll, let)
            mat = arcpy.RasterToNumPyArray(metric, nodata_to_value=0)
            area = np.sum(mat) * (cell_size**2)
            self.xlsx_writer.write_cell(col, row_num, area)
        self.xlsx_writer.save_close_wb(self.xlsx)

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
            if (~np.isnan(self.band_elev_lower)) and (~np.isnan(self.band_elev_upper)):
                info_file.write(f"\nRecruitment Band Upper Elevation: {self.band_elev_upper}")
                info_file.write(f"\nRecruitment Band Lower Elevation: {self.band_elev_lower}")
            else:
                pass
        self.logger.info(f"Saved info file: {info_path}")

    @_set_arcpy_env
    def run_rp(self):
        self.make_yoi_dir()
        self.get_hydraulic_rasters()
        self.interpolate_wle()
        self.get_sd_rb_crop_area()
        self.get_grain_ras()
        self.ras_taux()
        self.ras_q_mobile(prep_level="fp")
        self.ras_q_mobile(prep_level="pp")
        self.bed_prep_ras()
        self.rec_inund_survival()
        self.scour_burial_ras()
        self.recruitment_potential_ras()
        self.get_total_recruitment_area()
        self.get_bed_prep_area()
        self.get_recession_rate_area()
        self.get_inundation_surv_area()
        self.get_scour_burial_area()

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
    flowdata = 'D:\\LYR\\LYR_Restore\\RiverArchitect\\00_Flows\\InputFlowSeries\\flow_series_LYR_accord_LB_mod.xlsx'
    ex_veg_ras = 'D:\\LYR\\LYR_Restore\\RiverArchitect\\01_Conditions\\2017_lb_baseline\\lb_baseline_veg_clip.tif'
    #grading_ext_ras = 'D:\\LYR\\LYR_Restore\\RiverArchitect\\01_Conditions\\2017_lb_lvl_03\\LB_grading_extents_lvl0203.tif'
    #rp = RecruitmentPotential(condition='2017_lb_baseline', flow_data=flowdata, species='Fremont Cottonwood', selected_year='2006', units='us', ex_veg_ras=ex_veg_ras, grading_ext_ras=None)
    #rp.run_rp()

    for year in range(1924, 2017):
        year = str(year)
        print(f'\n\nRUNNING YEAR {year}\n\n')
        rp = RecruitmentPotential(condition='2017_lb_baseline', flow_data=flowdata, species='Fremont Cottonwood', selected_year=year, units='us', ex_veg_ras=ex_veg_ras, grading_ext_ras=None)
        rp.run_rp()
        rp.logger = None  # try to suppress duplicate logging messages when looping
