try:
    import sys, os, logging, random, shutil
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random, shutil).")
try:
    import cGraph
except:
    print("ExceptionERROR: Cannot import cGraph (check Connectivity directory)")
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cFish as cFi
    import fGlobal as fGl
    import cMakeTable as cMkT
    import cInputOutput as cIO
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
        fGl.chk_dir(self.cache)
        arcpy.env.workspace = self.cache
        arcpy.env.overwriteOutput = True
        self.condition = condition
        self.dir2condition = config.dir2conditions + self.condition + "\\"

        self.units = units
        self.q_units = 'cfs' if self.units == "us" else 'm^3/s'
        self.length_units = 'ft' if self.units == "us" else 'm'
        self.u_units = self.length_units + '/s'
        self.area_units = self.length_units + '^2'

        self.species = species
        self.lifestage = lifestage
        # read in fish data (minimum depth needed, max swimming speed, ...)
        self.h_min = cFi.Fish().get_travel_threshold(self.species, self.lifestage, "h_min")
        self.logger.info("minimum swimming depth = %s %s" % (self.h_min, self.length_units))
        self.u_max = cFi.Fish().get_travel_threshold(self.species, self.lifestage, "u_max")
        self.logger.info("maximum swimming speed  = %s %s" % (self.u_max, self.u_units))

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2co + "Output\\" + self.condition + "\\"
        fGl.chk_dir(self.out_dir)
        self.h_interp_dir = os.path.join(self.out_dir, "h_interp\\")
        fGl.chk_dir(self.h_interp_dir)
        self.u_interp_dir = os.path.join(self.out_dir, "u_interp\\")
        fGl.chk_dir(self.u_interp_dir)
        self.va_interp_dir = os.path.join(self.out_dir, "va_interp\\")
        fGl.chk_dir(self.va_interp_dir)
        self.areas_dir = os.path.join(self.out_dir, "areas\\")
        fGl.chk_dir(self.areas_dir)
        self.shortest_paths_dir = os.path.join(self.out_dir, "shortest_paths\\")
        fGl.chk_dir(self.shortest_paths_dir)
        # populated by self.get_hydraulic_rasters()
        self.discharges = []
        self.Q_h_dict = {}
        self.Q_u_dict = {}
        self.Q_va_dict = {}
        # populated by self.get_interpolated_rasters()
        self.Q_h_interp_dict = {}
        self.Q_u_interp_dict = {}
        self.Q_va_interp_dict = {}
        # populated by self.disconnected_areas(Q)
        self.Q_areas_dict = {}
        self.Q_d_area_vals = {}
        self.Q_d_area_percents = {}
        # populated by self.make_disconnect_Q_map()
        self.target = ''

        self.xlsx = os.path.join(self.out_dir, "disconnected_area.xlsx")
        self.xlsx_writer = cIO.Write(config.xlsx_connectivity)

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

    @fGl.err_info
    def get_interpolated_rasters(self):
        """
        Retrieves interpolated depth/velocity rasters, and produces them if they do not already exist.
        """
        self.logger.info("Retrieving interpolated hydraulic rasters...")
        for Q in self.discharges:
            # define paths to interpolated depths and velocities
            h_interp_basename = "h%06d_interp.tif" % Q
            u_interp_basename = "u%06d_interp.tif" % Q
            va_interp_basename = "va%06d_interp.tif" % Q
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
            self.Q_va_interp_dict[Q] = va_interp_path
        self.logger.info("OK")

    @fGl.err_info
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
        # compute disconnected areas
        for Q in sorted(self.discharges):
            self.disconnected_areas(Q)
        self.xlsx_writer.save_close_wb(self.xlsx)

        # make map of Qs where areas disconnect
        self.make_disconnect_Q_map()

        # make shortest escape route length map
        for Q in sorted(self.discharges):
            self.make_shortest_paths_map(Q)

        self.clean_up()
        self.logger.info("\nFinished.")

    def disconnected_areas(self, Q):
        self.logger.info("Computing disconnected areas...")
        self.logger.info("Discharge: %i %s" % (int(Q), self.q_units))

        # get interpolated depth/velocity rasters
        h_ras = Raster(self.Q_h_interp_dict[Q])

        self.logger.info("Masking depth raster with threshold...")
        # mask according to fish data
        mask_h = Con(h_ras > self.h_min, h_ras)
        # integer type masked raster for polygon conversion
        bin_h = Con(h_ras > self.h_min, 1)
        self.logger.info("OK")

        # raster to polygon conversion
        self.logger.info("Converting raster to polygon...")
        areas_shp_path = os.path.join(self.areas_dir, "areas%i.shp" % int(Q))
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
        self.logger.info("Total navigable wetted area: %.2f %s" % (total_area, self.area_units))
        disconnected_area = sum(areas[1:])
        row_num = sorted(self.discharges).index(Q) + 3
        self.xlsx_writer.write_cell("A", row_num, Q)
        self.xlsx_writer.write_cell("B", row_num, disconnected_area)
        self.Q_d_area_vals[Q] = disconnected_area
        self.logger.info("Disconnected wetted area: %.2f %s" % (disconnected_area, self.area_units))
        percent_disconnected = disconnected_area / total_area * 100
        self.Q_d_area_percents[Q] = percent_disconnected
        self.logger.info("Percent of area disconnected: %.2f" % percent_disconnected)

    def make_disconnect_Q_map(self):
        """
        Produces a raster where each cell value is the discharge at which disconnection occurs.
        If the cell is never in a disconnected area polygon, it assumes a default value of 0.
        """
        out_ras_path = os.path.join(self.out_dir, "Q_disconnect.tif")
        # start with highest Q raster, assign all wetted values to default of 0.
        out_ras = Raster(self.Q_h_interp_dict[max(self.discharges)])
        out_ras = Con(~IsNull(out_ras), 0) # *** should mask by thresholds too?
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
            # select largest area (mainstem)
            arcpy.SelectLayerByAttribute_management(disconnected_layer, "NEW_SELECTION", exp)
            # if Q = lowest discharge, save target raster
            if Q == min(self.discharges):
                self.logger.info("Creating target area raster...")
                arcpy.env.extent = Raster(self.Q_h_interp_dict[Q])  # target needs matching extent so matrices align
                target_lyr = os.path.join(self.cache, "target")
                self.target = os.path.join(self.out_dir, "target.tif")
                arcpy.MakeFeatureLayer_management(disconnected_layer, target_lyr, exp)
                # convert target feature layer to raster
                cell_size = arcpy.GetRasterProperties_management(self.Q_h_interp_dict[Q], 'CELLSIZEX').getOutput(0)
                arcpy.FeatureToRaster_conversion(target_lyr, 'gridcode', self.target, cell_size)
                self.logger.info("OK.")
            # delete mainstem polygon to get disconnected areas
            arcpy.DeleteFeatures_management(disconnected_layer)
            # convert back to polygon
            arcpy.FeatureClassToShapefile_conversion(disconnected_layer, self.cache)
            # delete feature layer (no longer needed, also removes schema lock issue)
            arcpy.Delete_management(disconnected_layer)
            # assign Q as value within disconnected area
            out_ras = Con(~IsNull(arcpy.sa.ExtractByMask(out_ras, disconnected_areas)), Q, out_ras)

        out_ras.save(out_ras_path)
        self.logger.info("Saved Q_disconnect raster: %s" % out_ras_path)

    def make_shortest_paths_map(self, Q):
        """
        Produces a raster where each cell value is the length of the least
        cost path back to the threshold masked low flow polygon.
        :param Q: corresponding discharge for finding path
        """
        self.logger.info("Making shortest escape route map...")
        self.logger.info("Discharge: %i %s" % (int(Q), self.q_units))
        self.logger.info("Aquatic ambiance: %s - %s" % (self.species, self.lifestage))
        self.logger.info("\tminimum swimming depth  = %s %s" % (self.h_min, self.length_units))
        self.logger.info("\tmaximum swimming speed  = %s %s" % (self.u_max, self.u_units))
        path2h_ras = self.Q_h_interp_dict[Q]
        path2u_ras = self.Q_u_interp_dict[Q]
        path2va_ras = self.Q_va_interp_dict[Q]

        cg = cGraph.Graphy(path2h_ras, path2u_ras, path2va_ras, self.h_min, self.u_max, self.target)
        shortest_paths_ras = cg.dynamic_shortest_paths()
        self.logger.info("Saving shortest paths raster...")
        shortest_paths_ras.save(os.path.join(self.shortest_paths_dir, "path_lengths%i.tif" % int(Q)))
        self.logger.info("OK")

    def clean_up(self):
        try:
            self.logger.info("Cleaning up ...")
            fGl.clean_dir(self.cache)
            fGl.rm_dir(self.cache)
            self.logger.info("OK")
        except:
            self.logger.info("Failed to clean up .cache folder.")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = ConnectivityAnalysis (Module: Connectivity)")
        print(dir(self))
