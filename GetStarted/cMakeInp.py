try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
    import cInputOutput as cIO
except:
    print("ExceptionERROR: Missing RiverArchitect packages (riverpy).")


class MakeInputFile:
    def __init__(self, dir2condition):
        self.dir2condition_act = dir2condition
        self.logger = logging.getLogger("logfile")
        self.inp_file_name = self.dir2condition_act + "\\input_definitions.inp"
        self.return_periods = []
        self.dod = []
        self.dmean = ""
        self.h_rasters = []
        self.u_rasters = []

    def get_info(self, flow_info_table):
        self.logger.info("   * Reading flow information from % s" % flow_info_table)
        # HYDRAULIC
        flow_info_xlsx = cIO.Read(flow_info_table)
        temp_return_periods = flow_info_xlsx.read_float_column_short("C", 5)
        temp_h_rasters = flow_info_xlsx.read_float_column_short("D", 5)
        temp_u_rasters = flow_info_xlsx.read_float_column_short("E", 5)
        flow_info_xlsx.close_wb()
        # remove entries with return periods of less than one year
        last_entry = 100.0
        for e in range(0, temp_return_periods.__len__()):
            value_applies = True
            if float(last_entry) == 1.0:
                if float(temp_return_periods[e]) == 1.0:
                    value_applies = False
            if value_applies:
                self.return_periods.append(str(temp_return_periods[e]))
                self.h_rasters.append(str(temp_h_rasters[e]).split(".tif")[0])
                self.u_rasters.append(str(temp_u_rasters[e]).split(".tif")[0])
                last_entry = temp_return_periods[e]

        self.return_periods.reverse()
        self.h_rasters.reverse()
        self.u_rasters.reverse()

        # DOD  and dmean
        self.logger.info("   * Reading dod and dmean info")
        ras_name_list = [i for i in os.listdir(self.dir2condition_act) if i.endswith('.tif')]
        for ras in ras_name_list:
            if ("scour" in str(ras)) or ("fill" in str(ras)):
                self.dod.append(str(ras).split(".tif")[0])
            if "dmean" in str(ras):
                self.dmean = str(ras).split(".tif")[0]

    def make_info(self, flow_info_table):
        self.get_info(flow_info_table)
        self.write_info()
        return self.inp_file_name

    def write_info(self):
        self.logger.info("   * Writing %s " % self.inp_file_name)
        sline = '#---------------------------------------------------------------------------------------\n'
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        f = open(self.inp_file_name, 'w')
        f.write("# RASTER META DATA - ONLY MODIFY VALUES BETWEEN \'=\' AND \'#\'\n")
        f.write('#\n')
        f.write(sline)
        f.write('Return periods = {0} #[Comma separated LIST] defines lifespans\n'.format(", ".join(self.return_periods)))
        f.write('#\n')
        f.write('# RASTER NAMES\n')
        f.write(sline)
        f.write('composite Habitat Suitability Index (CHSI) = max_chn #[STRING] for habitat matching\n')
        f.write('DEM of differences = {0} #[Comma separated LIST]\n'.format(", ".join(self.dod)))
        f.write('Detrended DEM = dem_detrend #[STRING]\n')
        f.write('Flow velocity (u) = {0} #[Comma separated LIST]\n'.format(", ".join(self.u_rasters)))
        f.write('Flow depth (h) = {0} #[Comma separated LIST]\n'.format(", ".join(self.h_rasters)))
        f.write('Grain sizes (D mean) = {0} #[STRING]\n'.format(self.dmean))
        f.write('Morphological units (mu) = mu #[STRING]\n')
        f.write('Depth to water table (d2w) = d2w #[STRING]\n')
        f.write('DEM = dem #[STRING] \n')
        f.write('Side channel = sidech #[STRING] side channel delineation raster\n')
        f.write('Wildcard raster = wild #[STRING] any raster for spatial analysis confinement\n')
        f.close()
        self.logger.info("   * OK")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = MakeInputFile (dir: %s)" % os.path.dirname(__file__))
        print(dir(self))
