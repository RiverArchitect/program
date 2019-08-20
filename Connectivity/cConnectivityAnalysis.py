try:
    import sys, os, logging, random, shutil
    import numpy as np
    import datetime as dt
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


class ConnectivityAnalysis:

    def __init__(self, condition, species, lifestage, units, *args, **kwargs):
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
            self.method = kwargs['method']
        except:
            self.method = "IDW"

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = config.dir2co + "Output\\" + self.condition + "\\"

        fGl.chk_dir(self.out_dir)
        # these directories don't depend on applied flow reduction, share with other runs
        self.h_interp_dir = os.path.join(self.out_dir, "h_interp\\")
        fGl.chk_dir(self.h_interp_dir)
        self.u_interp_dir = os.path.join(self.out_dir, "u_interp\\")
        fGl.chk_dir(self.u_interp_dir)
        self.va_interp_dir = os.path.join(self.out_dir, "va_interp\\")
        fGl.chk_dir(self.va_interp_dir)

        try:
            self.q_high = kwargs['q_high']
            self.q_low = kwargs['q_low']
            self.out_dir = os.path.join(self.out_dir, "flow_red_%06d_%06d" % (self.q_high, self.q_low))
        except:
            self.q_high = self.q_low = None
        fGl.chk_dir(self.out_dir)
        # these directories depend on applied flow reduction
        self.shortest_paths_dir = os.path.join(self.out_dir, "shortest_paths\\")
        fGl.chk_dir(self.shortest_paths_dir)
        self.areas_dir = os.path.join(self.out_dir, "areas\\")
        fGl.chk_dir(self.areas_dir)
        self.disc_areas_dir = os.path.join(self.out_dir, "disc_areas\\")
        fGl.chk_dir(self.disc_areas_dir)
        # populated by self.get_hydraulic_rasters()
        self.discharges = []
        self.Q_h_dict = {}
        self.Q_u_dict = {}
        self.Q_va_dict = {}
        # populated by self.get_interpolated_rasters()
        self.Q_h_interp_dict = {}
        self.Q_u_interp_dict = {}
        self.Q_va_interp_dict = {}
        # populated by self.make_shortest_paths_map(Q)
        self.Q_escape_dict = {}
        # populated by self.disconnected_areas(Q)
        self.Q_disc_areas_dict = {}
        # populated by self.make_disconnect_Q_map()
        self.target = ''

        self.xlsx = os.path.join(self.out_dir, "disconnected_area.xlsx")
        self.xlsx_writer = cIO.Write(config.xlsx_connectivity)
        self.xlsx_writer.write_cell("E", 4, self.species)
        self.xlsx_writer.write_cell("E", 5, self.lifestage)
        self.xlsx_writer.write_cell("E", 6, self.h_min)
        self.xlsx_writer.write_cell("E", 7, self.u_max)

        self.get_hydraulic_rasters()
        self.get_interpolated_rasters()
        self.get_target_raster()

    def get_hydraulic_rasters(self):
        self.logger.info("Retrieving hydraulic rasters...")
        try:
            mkt = cMkT.MakeFlowTable(self.condition, "", unit=self.units)
            self.discharges = sorted(mkt.discharges)
            # use subset of flows for analysis if q_low and q_high are provided
            if (self.q_low is not None) and (self.q_high is not None):
                self.discharges = [q for q in self.discharges if self.q_low <= q <= self.q_high]
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
            dem_path = self.dir2condition + "dem.tif"
            # check if interpolated depth already exists and uses selected interpolation method
            if self.check_interp_ras(h_interp_path):
                    h_ras = Raster(h_interp_path)
            else:
                # create interpolated depth raster
                h_path = self.Q_h_dict[Q]
                wle = cWL.WLE(h_path, dem_path, self.h_interp_dir, unique_id=True, method=self.method)
                wle.calculate_h()
                h_ras = Raster(h_interp_path)
                self.logger.info("OK")
            # in new interpolated area set velocity and velocity angle = 0
            arcpy.env.cellSize = dem_path  # make all interpolated rasters have DEM cell size
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

    def check_interp_ras(self, h_interp_path):
        # checks if interpolated raster already exists using selected interpolation method
        if os.path.exists(h_interp_path):
            info_path = h_interp_path.replace(".tif", ".info.txt")
            try:
                with open(info_path) as f:
                    method_line = f.readlines()[0]
                    method = method_line.split(": ")[1]
                    method = method.replace("\n", "")
                    if method == self.method:
                        return True
                    else:
                        self.logger.info("Existing raster %s uses different interpolation method than selected. Re-interpolating..." % h_interp_path)
                        return False
            except:
                return False
        else:
            self.logger.info("Existing %s not found. Creating..." % h_interp_path)
            return False


    @fGl.err_info
    def get_target_raster(self):
        """
        Produces the target to be used for finding shortest paths (largest polygon at low flow)
        """
        self.logger.info("Creating target area raster...")
        Q_min = min(self.discharges)
        self.logger.info("Using Q = %i %s for target" % (Q_min, self.q_units))
        # get interpolated depth raster
        h_ras = Raster(self.Q_h_interp_dict[Q_min])
        self.logger.info("Masking depth raster with threshold...")
        # mask according to fish data
        mask_h = Con(h_ras > self.h_min, h_ras)
        # integer type masked raster for polygon conversion
        bin_h = Con(h_ras > self.h_min, 1)
        self.logger.info("OK")
        # raster to polygon conversion
        self.logger.info("Converting raster to polygon...")
        areas_shp_path = os.path.join(self.cache, "areas%06d.shp" % int(Q_min))
        arcpy.RasterToPolygon_conversion(bin_h,
                                         areas_shp_path,
                                         "NO_SIMPLIFY"
                                         )
        self.logger.info("OK")
        self.logger.info("Calculating areas...")
        arcpy.AddField_management(areas_shp_path, "Area", "DOUBLE")
        if self.units == "us":
            exp = "!SHAPE.AREA@SQUAREFEET!"
        elif self.units == "si":
            exp = "!SHAPE.AREA@SQUAREMETERS!"
        arcpy.CalculateField_management(areas_shp_path, "Area", exp)
        self.logger.info("OK")
        # make copy of areas and remove mainstem
        all_areas = areas_shp_path
        disconnected_areas = os.path.join(self.cache, "disc_area%06d.shp" % int(Q_min))
        arcpy.CopyFeatures_management(all_areas, disconnected_areas)
        max_area = max([value for (key, value) in arcpy.da.SearchCursor(all_areas, ['OID@', 'Area'])])
        exp = "Area = %f" % max_area
        disconnected_layer = os.path.join(self.cache, "disc_area%06d" % int(Q_min))
        # convert shp to feature layer
        arcpy.MakeFeatureLayer_management(disconnected_areas, disconnected_layer)
        # select largest area (mainstem)
        arcpy.SelectLayerByAttribute_management(disconnected_layer, "NEW_SELECTION", exp)
        arcpy.env.extent = Raster(self.Q_h_interp_dict[Q_min])  # target needs matching extent so matrices align
        target_lyr = os.path.join(self.cache, "target")
        self.target = os.path.join(self.out_dir, "target.tif")
        arcpy.MakeFeatureLayer_management(disconnected_layer, target_lyr, exp)
        # convert target feature layer to raster
        cell_size = arcpy.GetRasterProperties_management(self.Q_h_interp_dict[Q_min], 'CELLSIZEX').getOutput(0)
        arcpy.FeatureToRaster_conversion(target_lyr, 'gridcode', self.target, cell_size)
        # delete intermediate products (no longer needed, also removes schema lock issue)
        arcpy.Delete_management(disconnected_layer)
        arcpy.Delete_management(disconnected_areas)
        self.logger.info("OK.")

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
        shortest_paths_ras = cg.find_shortest_paths()
        self.logger.info("Saving shortest paths raster...")
        out_ras_name = os.path.join(self.shortest_paths_dir, "path_lengths%06d.tif" % int(Q))
        shortest_paths_ras.save(out_ras_name)
        self.Q_escape_dict[Q] = out_ras_name
        self.logger.info("OK")

    def disconnected_areas(self, Q):
        self.logger.info("Computing disconnected areas...")
        self.logger.info("Discharge: %i %s" % (int(Q), self.q_units))

        # get interpolated depth raster
        self.logger.info("Retrieving interpolated depth raster...")
        h_interp_ras = Raster(self.Q_h_interp_dict[Q])
        # get escape route raster
        self.logger.info("Retrieving escape route raster...")
        escape_ras = Raster(self.Q_escape_dict[Q])
        self.logger.info("Retrieving maximum wetted area raster...")
        h_max_ras = Raster(self.Q_h_dict[max(self.discharges)])

        # get disconnected area raster
        self.logger.info("Computing disconnected area raster...")
        # total area = total interpolated area that is wetted at Q_max
        total_ras = Con((~IsNull(h_interp_ras)) & (~IsNull(h_max_ras)), 1)
        # disconnected area = portion of total area with null escape route
        disc_ras = Con(IsNull(escape_ras) & ~IsNull(total_ras), 1)

        self.logger.info("Converting rasters to polygons...")
        disc_area_path = os.path.join(self.disc_areas_dir, "disc_area%06d.shp" % int(Q))
        total_area_path = os.path.join(self.areas_dir, "area%06d.shp" % int(Q))
        arcpy.RasterToPolygon_conversion(disc_ras, disc_area_path, "NO_SIMPLIFY")
        arcpy.RasterToPolygon_conversion(total_ras, total_area_path, "NO_SIMPLIFY")
        self.Q_disc_areas_dict[Q] = disc_area_path

        self.logger.info("Calculating areas...")
        arcpy.AddField_management(disc_area_path, "Area", "DOUBLE")
        arcpy.AddField_management(total_area_path, "Area", "DOUBLE")

        if self.units == "us":
            exp = "!SHAPE.AREA@SQUAREFEET!"
        elif self.units == "si":
            exp = "!SHAPE.AREA@SQUAREMETERS!"

        arcpy.CalculateField_management(disc_area_path, "Area", exp)
        arcpy.CalculateField_management(total_area_path, "Area", exp)

        disc_areas = arcpy.da.TableToNumPyArray(disc_area_path, ("Area"))
        total_areas = arcpy.da.TableToNumPyArray(total_area_path, ("Area"))
        disc_areas = [area[0] for area in disc_areas]
        total_areas = [area[0] for area in total_areas]

        disc_area = sum(disc_areas)
        total_area = sum(total_areas)

        row_num = sorted(self.discharges).index(Q) + 3
        self.xlsx_writer.write_cell("A", row_num, Q)
        self.xlsx_writer.write_cell("B", row_num, disc_area)
        self.logger.info("Disconnected wetted area: %.2f %s" % (disc_area, self.area_units))
        percent_disconnected = disc_area / total_area * 100
        self.logger.info("Percent of area disconnected: %.2f" % percent_disconnected)

    def make_disconnect_Q_map(self):
        """
        Produces a raster where each cell value is the discharge at which disconnection occurs.
        If the cell is never in a disconnected area polygon, it assumes a default value of 0.
        """
        self.logger.info("Making Q_disconnect map...")
        arcpy.env.workspace = self.cache
        out_ras_path = os.path.join(self.out_dir, "Q_disconnect.tif")
        # start with highest Q raster, assign all wetted values to default of 0.
        out_ras = Raster(self.Q_h_dict[max(self.discharges)])
        out_ras = Con(~IsNull(out_ras), 0)
        # starting from lowest Q and working up, assign cell value Q to cells in disconnected areas
        for Q in self.discharges:
            disconnected_areas = self.Q_disc_areas_dict[Q]
            # assign Q as value within disconnected area
            temp_ras = arcpy.sa.ExtractByMask(out_ras, disconnected_areas)
            out_ras = Con(~IsNull(temp_ras), Q, out_ras)

        out_ras.save(out_ras_path)
        self.logger.info("Saved Q_disconnect raster: %s" % out_ras_path)

    def get_total_disc_area(self):
        """Uses Q_disconnect map to create a list of cumulative stranded area as flows are reduced"""
        q_disc_ras = Raster(os.path.join(self.out_dir, "Q_disconnect.tif"))
        cell_size = float(arcpy.GetRasterProperties_management(q_disc_ras, 'CELLSIZEX').getOutput(0))
        disc_areas_dict = {}
        for Q in sorted(self.discharges, reverse=True):
            # cumulative disconnected area
            cum_disc_area = Con(q_disc_ras >= Q, 1)
            mat = arcpy.RasterToNumPyArray(cum_disc_area, nodata_to_value=0)
            disc_areas_dict[Q] = np.sum(mat) * (cell_size**2)
        return disc_areas_dict

    @fGl.err_info
    def apply_flow_reduction(self):
        """
        Analyzes effects of a reduction in flows from Q_high to Q_low.

        *** make new target for Q_low, only interpolate needed rasters when initializing CA object

        Outputs:
            -shortest path rasters for Q_high and Q_low (and all model discharges in between)
            -disconnected area: the wetted area which is connected at Q_high but disconnected at Q_low
             (or disconnected at any model discharge in between)
        """

        self.logger.info("Applying flow reduction...")
        self.logger.info("Reducing flow from %i to %i %s" % (self.q_high, self.q_low, self.q_units))
        self.logger.info("Available discharges: %s (%s)" % (self.discharges, self.q_units))

        self.logger.info("Identifying area disconnected by flow reduction...")

        # make shortest escape route length map
        for Q in sorted(self.discharges, reverse=True):
            self.make_shortest_paths_map(Q)
            self.disconnected_areas(Q)
        # close disconnected area workbook
        self.xlsx_writer.save_close_wb(self.xlsx)

        # make map of Qs where areas disconnect
        self.make_disconnect_Q_map()

        total_disc_area = self.get_total_disc_area()
        disc_area = total_disc_area[min(self.discharges)]
        self.logger.info("Cumulative area disconnected by flow reduction: %.2f %s" % (disc_area, self.area_units))

        # create .info.txt file with run information
        self.flow_red_info(disc_area)
        self.clean_up()
        self.logger.info("Finished.")
        self.logger.info("Output stored in: %s" % self.out_dir)

    def flow_red_info(self, disc_area):
        # creates info file for flow reduction run
        # outputs: time of run, Q_high, Q_low, species/lifestage, disconnected area

        info_path = os.path.join(self.out_dir, 'run.info.txt')
        with open(info_path, "w") as info_file:
            info_file.write("Time created: %s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            info_file.write("\nQ_high: %06d %s" % (self.q_high, self.q_units))
            info_file.write("\nQ_low: %06d %s" % (self.q_low, self.q_units))
            info_file.write("\nApplied species: %s" % self.species)
            info_file.write("\nApplied lifestage: %s" % self.lifestage)
            info_file.write("\nCumulative disconnected area: %i %s" % (disc_area, self.area_units))
        self.logger.info("Saved info file: %s " % info_path)

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
