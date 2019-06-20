try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cFish as cFi
    import fGlobal as fG
    import cMakeTable as cMkT
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")


class ConnectivityAnalysis:

    def __init__(self, condition, species, lifestage, units, *args):
        self.logger = logging.getLogger("logfile")
        self.cache = config.dir2co + ".cache\\"
        fG.chk_dir(self.cache)
        arcpy.env.workspace = self.cache
        arcpy.env.overwriteOutput = True
        self.condition = condition
        self.dir2condition = config.dir2conditions + self.condition + "\\"
        self.species = species
        self.lifestage = lifestage
        self.units = units
        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2co + "Output\\" + self.condition + "\\"
            fG.chk_dir(self.out_dir)

        self.discharges = []
        self.Q_h_ras_dict = {}
        self.Q_u_ras_dict = {}
        self.get_hydraulic_rasters()
        self.connectivity_analysis()

    def connectivity_analysis(self):
        self.logger.info("\n>>> Connectivity Analysis:\n>>> Condition: %s\n>>> Species: %s\n>>> Lifestage: %s" % (self.condition, self.species, self.lifestage))

        for Q in sorted(self.discharges):
            self.analyze_flow(Q)

        self.clean_up()

    def get_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            mkt = cMkT.MakeFlowTable(self.condition, "", unit=self.units)
            self.discharges = sorted(mkt.discharges)
            self.Q_h_ras_dict = {Q: Raster(self.dir2condition + mkt.dict_Q_h_ras[Q]) for Q in self.discharges}
            self.Q_u_ras_dict = {Q: Raster(self.dir2condition + mkt.dict_Q_u_ras[Q]) for Q in self.discharges}
            self.logger.info("OK")
        except:
            self.logger.info("ERROR: Could not retrieve hydraulic rasters.")

    def analyze_flow(self, Q):
        self.logger.info("\n>>> Analyzing discharge: %i" % Q)

        # *** get/create interpolated depth and velocity rasters
        # use interpolated h from cWaterLevel, in new interpolated area set velocity = 0
        if "h%i_interp.tif" % Q in os.listdir(self.dir2condition):
            h_ras = Raster(os.path.join(self.dir2condition, "h%i_interp.tif" % Q))
            u_ras = self.Q_u_ras_dict[Q]
            u_ras = Con(IsNull(u_ras) & (h_ras > 0), 0, u_ras)
        else:
            # *** interpolate h first
            h_ras = self.Q_h_ras_dict[Q]
            u_ras = self.Q_u_ras_dict[Q]

        # read in fish data (minimum depth needed, max swimming speed, ...)
        h_min = cFi.Fish().get_travel_threshold(self.species, self.lifestage, "h_min")
        self.logger.info("minimum depth = %s" % h_min)

        self.logger.info("Masking rasters with thresholds...")
        # mask according to fish data
        mask_h = Con(h_ras > h_min, h_ras)
        # also make integer type raster for polygon conversion
        bin_h = Con(h_ras > h_min, 1)
        self.logger.info("OK")

        # raster to polygon conversion
        self.logger.info("Converting raster to polygon...")
        arcpy.RasterToPolygon_conversion(bin_h,
                                         self.cache + "masked_h.shp",
                                         "NO_SIMPLIFY"
                                         )
        wetted_shp = self.cache + "masked_h.shp"
        self.logger.info("OK")

        # compute fraction of area that is disconnected/not navigable
        arcpy.AddField_management(wetted_shp, "Area", "DOUBLE")
        if self.units == "us":
            exp = "!SHAPE.AREA@SQUAREFEET!"
        elif self.units == "si":
            exp = "!SHAPE.AREA@SQUAREMETERS!"

        arcpy.CalculateField_management(wetted_shp, "Area", exp)

        areas = arcpy.da.TableToNumPyArray(wetted_shp, ("Area"))
        areas = [area[0] for area in areas]
        # sort highest to lowest
        areas = sorted(areas, reverse=True)

        total_area = sum(areas)
        self.logger.info("Total navigable wetted area: %.2f" % total_area)
        disconnected_area = sum(areas[1:])
        self.logger.info("Disconnected wetted area: %.2f" % disconnected_area)
        percent_disconnected = disconnected_area / total_area * 100
        self.logger.info("Percent of area disconnected: %.2f" % percent_disconnected)

        # *** save data to a table in Connectivity/Output, open table when finished
        # graph theory metrics...
        # particle tracking...

    def clean_up(self):
        try:
            self.logger.info("Cleaning up ...")
            fG.clean_dir(self.cache)
            fG.rm_dir(self.cache)
            self.logger.info("OK")
        except:
            self.logger.info("Failed to clean up .cache folder.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = ConnectivityAnalysis (Module: Connectivity)")
        print(dir(self))
