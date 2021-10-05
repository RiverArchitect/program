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
        self.cm2ft = 1 / 30.48

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

        # populated by self.get_recession_period()
        self.rec_start_date = None
        self.rec_end_date = None

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

        # populated by self.interpolate_wle()
        self.Q_wle_dict = {}

        # populated by self.recession_rate_ras()
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
            # start of base flow period
            self.base_flow_start = self.rc_data.loc[self.rc.base_flow_start].VALUE
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
            self.logger.info("Determining recession rate criteria...")
            # favorable recession rate criteria
            rr_fav_cm = self.rc_data.loc[self.rc.rr_fav].VALUE
            self.rr_fav = rr_fav_cm * self.cm2ft
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
            self.logger.info("Determining elevation criteria...")
            # favorable elevation criteria
            self.elev_fav = self.rc_data.loc[self.rc.elev_fav].VALUE
            # stressful elevation criteria
            self.elev_stress = self.rc_data.loc[self.rc.elev_stress].VALUE
            # lethal elevation criteria
            self.elev_lethal = self.rc_data.loc[self.rc.elev_lethal].VALUE
        except:
            self.logger.error("ERROR: Could not determine elevation criteria,"
                              "check recruitment_criteria.xlxs to ensure that values exist for species of interest.")
        try:
            self.logger.info("Determining inundation criteria...")
            # favorable inundation criteria
            self.inund_fav = self.rc_data.loc[self.rc.inund_fav].VALUE
            # stressful inundation criteria
            self.inund_stress = self.rc_data.loc[self.rc.inund_stress].VALUE
            # lethal inundation criteria
            self.inund_lethal = self.rc_data.loc[self.rc.inund_lethal].VALUE
        except:
            self.logger.error("ERROR: could not determine inundation criteria,"
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
            # create bed prep flows dataframe with bed prep period for selected year
            self.bp_flow_df = self.flow_df.loc[self.bp_start_date:self.bp_end_date]
            # determine maximum Q from bed prep flows dataframe
            self.q_bp_max = int(self.bp_flow_df.max().values[0])
        except:
            self.logger.error("ERROR: Could not determine Q max from bed prep period.")
        # determine if flow has occurred during relevant time period to prepare the bed
        try:
            out_ras_path = os.path.join(self.sub_dir, f"bed_prep_ras.tif")
            if os.path.exists(out_ras_path):
                Raster(out_ras_path)
                self.logger.info(f'Bed prep raster already exists ({out_ras_path}). Skipping...')
                return
            # determine if the maximum flow (Q) in bed prep period is greater than or equal to q_mobile_ras values
            bp_ras_fp = Con(self.q_mobile_ras_fp <= self.q_bp_max, 1)
            bp_ras_pp = Con(self.q_mobile_ras_pp <= self.q_bp_max, 2)
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

    def set_arcpy_env(self):
        self.logger.info("Setting up arcpy environment...")
        self.snap_raster = Raster(self.dem_ras)
        # set selected raster as environment snap raster and output coordinate system
        arcpy.env.snapRaster = self.snap_raster
        arcpy.env.outputCoordinateSystem = Raster(self.snap_raster).spatialReference
        # get cell size
        self.cell_size_x = arcpy.GetRasterProperties_management(self.snap_raster, 'CELLSIZEX')[0]
        self.cell_size_y = arcpy.GetRasterProperties_management(self.snap_raster, 'CELLSIZEY')[0]
        self.cell_size = str(self.cell_size_x) + ' ' + str(self.cell_size_y)

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
        q_l_index = np.searchsorted(self.discharges, q)
        q_u_index = q_l_index + 1
        q_l = self.discharges[q_l_index]
        q_u = self.discharges[q_u_index]
        self.logger.info(f"Closest modeled flows for interpolation: {q_l} - {q_u}")
        try:
            q_l_wle_ras = self.Q_wle_dict[q_l]
            q_u_wle_ras = self.Q_wle_dict[q_u]
            try:
                # convert WLE raster to numpy array
                q_l_wle_mat = arcpy.RasterToNumPyArray(q_l_wle_ras, nodata_to_value=np.nan)
                q_u_wle_mat = arcpy.RasterToNumPyArray(q_u_wle_ras, nodata_to_value=np.nan)
                try:
                    q_wle_mat = q_l_wle_mat + ((q_u_wle_mat - q_l_wle_mat) * (q - q_l) / (q_u - q_l))
                    return q_wle_mat
                except:
                    self.logger.info(f"Failed to interpolate WLE array for Q = {q}.")
            except:
                self.logger.info(f"Unable to convert required interpolated WLE rasters into arrays...")
        except:
            self.logger.info(f"Unable to retrieve required interpolated WLE rasters...")

    def convert_array2raster(self, mat, ras_path):
        # set arcpy environment for raster
        self.set_arcpy_env()
        # set reference point for array to raster conversion
        ref_pt = arcpy.Point(self.snap_raster.extent.XMin, self.snap_raster.extent.YMin)
        ras = arcpy.NumPyArrayToRaster(mat, lower_left_corner=ref_pt,
                                       x_cell_size=float(self.cell_size_x),
                                       y_cell_size=float(self.cell_size_y),
                                       value_to_nodata=np.nan)
        ras.save(ras_path)
        self.logger.info(f'Saved converted raster: {ras_path}')

    def get_wetted_area(self, h_ras, ras_path):
        # calculate wetted area raster
        self.logger.info(f"Calculating wetted area...")
        try:
            # convert depth raster to integer raster
            logging.info(f'Converting depth raster {h_ras} to interger raster...')
            interger_ras = Con(Raster(h_ras), 1)
            interger_ras.save(ras_path)
        except:
            logging.info(f"Failed to convert depth raster {h_ras} to interger raster...")

    def recession_rate_ras(self):
        """
        Recruitment Box Model, Objective 2: Spring Recession Rates
        Creates recession rate raster (optimal, at-risk, lethal) from water surface elevation rasters for each day
        at each pixel.
        """
        self.logger.info("Creating dataframe from flow_df of recession period...")
        # determine recession rate period for selected year
        self.get_recession_period()
        try:
            # create recession rate flow dataframe with recession start and end dates
            self.rr_df = self.flow_df.loc[self.rec_start_date - dt.timedelta(days=3):self.rec_end_date]
            # create seed dispersal flow dataframe with seed dispersal start and end dates
            self.sd_df = self.flow_df.loc[self.sd_start:self.sd_end]
            # determine maximum Q from seed dispersal dataframe
            self.q_sd_max = int(self.rr_df.max().values[0])
        except:
            self.logger.error("ERROR: Could not create recession rate or seed dispersal flow dataframe.")
        q_sd_max_mat = self.interp_wle_by_q(self.q_sd_max)
        q_sd_max_ras_path = os.path.join(self.cache, f"wle{self.q_sd_max}.tif")
        self.convert_array2raster(q_sd_max_mat, q_sd_max_ras_path)
        wa_ras_path = os.path.join(self.sub_dir, f"wetted_area_sd_ras.tif")
        self.get_wetted_area(q_sd_max_ras_path, wa_ras_path)
         
        rr_total_d = (len(self.rr_df) - 3)
        window = []
        # iterating over groups of 4 consecutive rows
        for i in range(len(self.rr_df) - 4):
            slice = self.rr_df.iloc[i: i + 4]
            qm3, qm2, qm1, q = slice['Mean daily'].values
            day = slice.index.values[-1]
            self.logger.info(f'Getting recession rate for {pd.to_datetime(day).strftime("%Y-%m-%d")}...  ')
            q_wle_mat = self.interp_wle_by_q(q)
            if i == 0:
                window.append(self.interp_wle_by_q(qm3))
                window.append(self.interp_wle_by_q(qm2))
                window.append(self.interp_wle_by_q(qm1))
                self.rr_stress_d_mat = np.zeros_like(q_wle_mat)
                self.rr_lethal_d_mat = np.zeros_like(q_wle_mat)
            # update window of wle arrays
            window.append(q_wle_mat)
            qm3_wle_mat = window.pop(0)
            # calculate 3-day avg recession rate
            rr = (q_wle_mat - qm3_wle_mat) / 3
            # calculate stressful and lethal recession rate total arrays
            self.rr_stress_d_mat = np.where((self.rr_stress < rr) & (rr <= self.rr_lethal), (self.rr_stress_d_mat + 1), self.rr_stress_d_mat)
            self.rr_lethal_d_mat = np.where((self.rr_lethal < rr), (self.rr_lethal_d_mat + 1), self.rr_lethal_d_mat)
        # calculate favorable recession rate days (total) array
        self.rr_fav_d_mat = rr_total_d - self.rr_stress_d_mat - self.rr_lethal_d_mat
        # convert recession rate days (total) arrays to rasters
        self.logger.info('Converting recession rate (days) arrays to rasters...')
        rr_fav_ras_path = os.path.join(self.sub_dir, f"rr_fav_days_ras.tif")
        rr_stress_ras_path = os.path.join(self.sub_dir, f"rr_stress_days_ras.tif")
        rr_lethal_ras_path = os.path.join(self.sub_dir, f"rr_lethal_days_ras.tif")
        self.convert_array2raster(self.rr_fav_d_mat, rr_fav_ras_path)
        self.convert_array2raster(self.rr_stress_d_mat, rr_stress_ras_path)
        self.convert_array2raster(self.rr_lethal_d_mat, rr_lethal_ras_path)
        # calculate mortality coefficient with recession rate stressful and lethal days totals
        self.logger.info('Calculating mortality coeffient array...')
        # calculate arrays as percent of total days
        self.rr_stress_per_mat = (self.rr_stress_d_mat / rr_total_d) * 100
        self.rr_lethal_per_mat = (self.rr_lethal_d_mat / rr_total_d) * 100
        mort_coef_mat = ((self.rr_lethal_per_mat * 3) + (self.rr_stress_per_mat * 1)) / 3
        # convert mortality coefficient array to raster
        self.logger.info('Converting mortality coefficient to raster...')
        mort_coef_ras_path = os.path.join(self.sub_dir, f"mortality_coeff_ras.tif")
        self.convert_array2raster(mort_coef_mat, mort_coef_ras_path)

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
    flowdata = 'D:\\LYR_Restore\\RiverArchitect\\00_Flows\\InputFlowSeries\\flow_series_LYR_accord_LB.xlsx'
    rp = RecruitmentPotential(condition='2017_lbp', flow_data=flowdata, species='Fremont Cottonwood', selected_year='1952', units='us')
    rp.run_rp()
