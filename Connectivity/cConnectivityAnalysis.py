try:
    import sys, os, logging, random
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cFish as cFi
    import fGlobal as fG
    import cMakeTable as cMkT
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")

try:
    sys.path.append(config.dir2gs)
    import cWaterLevel as cWL
except:
    print("ExceptionERROR: Cannot import cWaterLevel (check GetStarted directory).")
try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")
try:
    import pathos.multiprocessing as mp
except:
    print("WARNING: Missing pathos package (optional, required for multiprocessing).")


class ConnectivityAnalysis:

    def __init__(self, condition, species, lifestage, units, *args):
        self.logger = logging.getLogger("logfile")
        self.cache = config.dir2co + ".cache%s\\" % str(random.randint(1000000, 9999999))
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
        self.h_interp_dir = os.path.join(self.out_dir, "h_interp\\")
        fG.chk_dir(self.h_interp_dir)
        self.u_interp_dir = os.path.join(self.out_dir, "u_interp\\")
        fG.chk_dir(self.u_interp_dir)
        self.va_interp_dir = os.path.join(self.out_dir, "va_interp\\")
        fG.chk_dir(self.va_interp_dir)
        self.areas_dir = os.path.join(self.out_dir, "areas\\")
        fG.chk_dir(self.areas_dir)
        # populated by self.get_hydraulic_rasters()
        self.discharges = []
        self.Q_h_dict = {}
        self.Q_u_dict = {}
        self.Q_va_dict = {}
        # populated by self.get_interpolated_rasters()
        self.Q_h_interp_dict = {}
        self.Q_u_interp_dict = {}
        self.Q_va_interp_dict = {}
        # populated by self.analyze_flows(Q)
        self.Q_areas_dict = {}

        self.get_hydraulic_rasters()
        self.get_interpolated_rasters()
        self.connectivity_analysis()

    def get_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            mkt = cMkT.MakeFlowTable(self.condition, "", unit=self.units)
            self.discharges = sorted(mkt.discharges)
            self.Q_h_dict = {Q: self.dir2condition + mkt.dict_Q_h_ras[Q] for Q in self.discharges}
            self.Q_u_dict = {Q: self.dir2condition + mkt.dict_Q_u_ras[Q] for Q in self.discharges}
            self.Q_va_dict = {Q: self.dir2condition + mkt.dict_Q_va_ras[Q] for Q in self.discharges}
            self.logger.info("OK")
        except:
            self.logger.info("ERROR: Could not retrieve hydraulic rasters.")

    def get_interpolated_rasters(self):
        """
        Retrieves interpolated depth/velocity rasters, and produces them if they do not already exist.
        """
        self.logger.info("Retrieving interpolated hydraulic rasters...")
        for Q in self.discharges:
            # define paths to interpolated depths and velocities
            h_interp_basename = "h%i_interp.tif" % Q
            u_interp_basename = "u%i_interp.tif" % Q
            va_interp_basename = "va%i_interp.tif" % Q
            h_interp_path = os.path.join(self.h_interp_dir, h_interp_basename)
            u_interp_path = os.path.join(self.u_interp_dir, u_interp_basename)
            va_interp_path = os.path.join(self.va_interp_dir, va_interp_basename)
            # check if interpolated depth already exists
            if h_interp_basename in os.listdir(self.dir2condition):
                h_ras = Raster(os.path.join(self.dir2condition, h_interp_basename))
                h_ras.save(h_interp_path)  # save copy to output dir
            elif h_interp_basename in os.listdir(self.h_interp_dir):
                h_ras = Raster(h_interp_path)
            else:
                # if interpolated depth raster does not already exist, create one
                self.logger.info("%s not found in %s. Creating..." % (h_interp_basename, self.h_interp_dir))
                h_path = self.Q_h_dict[Q]
                dem_path = self.dir2condition + "dem.tif"
                wle = cWL.WLE(h_path, dem_path, self.h_interp_dir, unique_id=True)
                wle.calculate_h()
                h_ras = Raster(h_interp_path)
                self.logger.info("OK")
            # in new interpolated area set velocity and velocity angle = 0
            u_ras = Raster(self.Q_u_dict[Q])
            va_ras = Raster(self.Q_va_dict[Q])
            u_ras = Con(IsNull(u_ras) & (h_ras > 0), 0, u_ras)
            va_ras = Con(IsNull(va_ras) & (h_ras > 0), 0, va_ras)
            u_ras.save(u_interp_path)
            va_ras.save(va_interp_path)
            self.Q_h_interp_dict[Q] = h_interp_path
            self.Q_u_interp_dict[Q] = u_interp_path
            self.Q_va_dict[Q] = va_interp_path
        self.logger.info("OK")

    def connectivity_analysis(self):
        self.logger.info("\n>>> Connectivity Analysis:\n>>> Condition: %s\n>>> Species: %s\n>>> Lifestage: %s" % (self.condition, self.species, self.lifestage))
        """ *** fix multiprocessing hang
        self.logger.info("Attempting CPU multiprocessing of analysis...")
        try:
            thread_num = min(len(self.discharges), mp.cpu_count() - 1)
            p = mp.Pool(thread_num)
            p.map(self.analyze_flow, sorted(self.discharges))
            p.close()
            p.join()
        except:
            self.logger.info("ERROR: Multiprocessing failed, proceeding with serial processing.")
        """
        for Q in sorted(self.discharges):
            self.analyze_flow(Q)

        self.make_disconnect_Q_map()

        self.clean_up()

    def analyze_flow(self, Q):
        self.logger.info("\n>>> Analyzing discharge: %i" % Q)
        # get interpolated depth/velocity rasters
        h_ras = Raster(self.Q_h_interp_dict[Q])
        u_ras = Raster(self.Q_u_interp_dict[Q])

        # read in fish data (minimum depth needed, max swimming speed, ...)
        h_min = cFi.Fish().get_travel_threshold(self.species, self.lifestage, "h_min")
        self.logger.info("minimum swimming depth = %s" % h_min)
        u_max = cFi.Fish().get_travel_threshold(self.species, self.lifestage, "u_max")
        self.logger.info("maximum swimming speed  = %s" % h_min)

        self.logger.info("Masking rasters with thresholds...")
        # mask according to fish data
        mask_h = Con(h_ras > h_min, h_ras)
        # also make integer type masked raster for polygon conversion
        bin_h = Con(h_ras > h_min, 1)
        self.logger.info("OK")

        # raster to polygon conversion
        self.logger.info("Converting raster to polygon...")
        areas_shp_path = os.path.join(self.areas_dir, "areas%i.shp" % Q)
        arcpy.RasterToPolygon_conversion(bin_h,
                                         areas_shp_path,
                                         "NO_SIMPLIFY"
                                         )
        self.Q_areas_dict[Q] = areas_shp_path
        self.logger.info("OK")

        # compute fraction of area that is disconnected/not navigable
        arcpy.AddField_management(areas_shp_path, "Area", "DOUBLE")
        if self.units == "us":
            exp = "!SHAPE.AREA@SQUAREFEET!"
        elif self.units == "si":
            exp = "!SHAPE.AREA@SQUAREMETERS!"
        arcpy.CalculateField_management(areas_shp_path, "Area", exp)

        areas = arcpy.da.TableToNumPyArray(areas_shp_path, ("Area"))
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

    def make_shortest_paths_map(self, Q):
        """
        Produces a raster where each cell value is the length of the least
        cost path back to the threshold masked low flow polygon.
        :param Q: corresponding discharge for finding path
        """
        path2h_ras = self.Q_h_interp_dict[Q]
        path2u_ras = self.Q_u_interp_dict[Q]
        path2va_ras = self.Q_va_interp_dict[Q]

    def make_disconnect_Q_map(self):
        """
        Produces a raster where each cell value is the discharge at which disconnection occurs.
        If the cell is never in a disconnected area polygon, it assumes a default value of 0.
        """
        out_ras_path = os.path.join(self.out_dir, "Q_disconnect.tif")
        # start with highest Q raster, assign all wetted values to default of 0.
        out_ras = Raster(self.Q_h_interp_dict[max(self.discharges)])
        out_ras = Con(~IsNull(out_ras), 0)
        # starting from lowest Q and working up, assign cell value Q to cells in disconnected areas
        for Q in self.discharges:
            # make copy of areas and remove mainstem
            all_areas = self.Q_areas_dict[Q]
            disconnected_areas = os.path.join(self.cache, "disc_area.shp")
            arcpy.CopyFeatures_management(all_areas, disconnected_areas)
            max_area = max([value for (key, value) in arcpy.da.SearchCursor(all_areas, ['OID@', 'Area'])])
            exp = "Area = %f" % max_area
            disconnected_layer = os.path.join(self.cache, "disc_area")
            # convert shp to feature layer
            arcpy.MakeFeatureLayer_management(disconnected_areas, disconnected_layer)
            arcpy.SelectLayerByAttribute_management(disconnected_layer, "NEW_SELECTION", exp)
            # delete mainstem polygon to get disconnected areas
            arcpy.DeleteFeatures_management(disconnected_layer)
            # convert back to polygon
            arcpy.FeatureClassToShapefile_conversion(disconnected_layer, self.cache)
            # delete feature layer (no longer needed, also removes schema lock issue)
            arcpy.Delete_management(disconnected_layer)
            # assign Q as value within disconnected area
            out_ras = Con(~IsNull(arcpy.sa.ExtractByMask(out_ras, disconnected_areas)), Q, out_ras)

        out_ras.save(out_ras_path)

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
