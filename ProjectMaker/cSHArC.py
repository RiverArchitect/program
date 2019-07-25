# logs to logfile.log
try:
    import sys, os, logging, random
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random).")

try:
    import arcpy
    from arcpy.sa import *
except:
    print("ExceptionERROR: No valid ARCPY found.")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: riverpy).")


class SHArC:
    def __init__(self, unit=str(), prj_name=str(), version=str()):
        self.dir2geo = config.dir2pm + prj_name + "_" + version + "\\Geodata\\"
        self.cache = self.dir2geo + ".cache%s\\" % str(random.randint(1000000, 9999999))
        self.cache_count = 0
        fGl.chk_dir(self.cache)
        self.extents = [0, 0, 0, 0]
        self.logger = logging.getLogger("logfile")
        self.ras_project = None
        self.result = 0.0
        self.unit = unit
        if self.unit == "us":
            self.area_unit = "SQUARE_FEET_US"
            self.unit_str = "acres"
            self.ft2ac = config.ft2ac
        else:
            self.area_unit = "SQUARE_METERS"
            self.unit_str = "m2"
            self.ft2ac = 1.0

        self.xlsx_out = ""

    def calculate_wua(self, exceedance_pr, usable_area):
        # exceedance_pr = LIST of discharge exceedance probabilities
        # usable_area =  LIST of usable habitat area corresponding to exceedance_pr
        area = []
        for e in range(0, exceedance_pr.__len__()):
            if not (e == (exceedance_pr.__len__() - 1)):
                pr = exceedance_pr[e]
            else:
                pr = 100 - sum(exceedance_pr[0: e])
            area.append(pr / 100 * usable_area[e])
        return sum(area)

    def clear_cache(self, *args):
        try:
            # check for optional BOOL argument to restore cache
            recreate_cache = args[0]
        except:
            recreate_cache = False
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.cache
        ras_list = arcpy.ListRasters()
        shp_list = arcpy.ListFeatureClasses()
        try:
            if not recreate_cache:
                self.logger.info("   * clearing .cache (arcpy.Delete_management) ...")
            else:
                self.logger.info("   * resetting .cache (arcpy.Delete_management) ...")
            for ras in ras_list:
                try:
                    arcpy.Delete_management(str(ras))
                except:
                    pass
            for shp in shp_list:
                try:
                    arcpy.Delete_management(str(shp))
                except:
                    pass
            fGl.rm_dir(self.cache)
            self.cache_count = 0
            if recreate_cache:
                fGl.chk_dir(self.cache)
            self.logger.info("   * ok")
        except:
            self.logger.info("       .cache folder will be removed by package controls.")

    @fGl.spatial_license
    def get_usable_area(self, csi_raster=str()):
        # wua_threshold =  FLOAT -- value between 0.0 and 1.0
        self.set_env()
        arcpy.env.workspace = self.cache

        try:
            ras_csi = arcpy.Raster(csi_raster + ".tif")
        except:
            ras_csi = arcpy.Raster(csi_raster)

        self.logger.info("   * snapping to ProjectArea.shp within CHSI raster (%s)..." % csi_raster)
        ras4shp = Con(~IsNull(self.ras_project), Con(~IsNull(ras_csi), Int(1)))

        self.logger.info("   * converting snapped CHSI raster to Polygon shapefile:")
        try:
            shp_name = self.cache + "aua%s.shp" % str(self.cache_count)
            self.logger.info("     " + shp_name)
            arcpy.RasterToPolygon_conversion(ras4shp, shp_name, "NO_SIMPLIFY")
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy) in RasterToPolygon_conversion.")
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
            return -1
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy) in RasterToPolygon_conversion.")
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
            return -1
        except:
            self.logger.info("ERROR: Shapefile conversion failed.")
            return -1

        self.logger.info("   * calculating usable habitat area ... ")
        try:
            arcpy.AddField_management(shp_name, "F_AREA", "FLOAT", 9)
        except:
            pass
        try:
            arcpy.CalculateGeometryAttributes_management(shp_name, geometry_property=[["F_AREA", "AREA"]],
                                                         area_unit=self.area_unit)
            self.logger.info("   * summing up area ...")
            area = 0.0
            with arcpy.da.UpdateCursor(shp_name, "F_AREA") as cursor:
                for row in cursor:
                    try:
                        area += float(row[0])
                    except:
                        self.logger.info("       WARNING: Bad value (" + str(row) + ")")
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy) in CalculateGeometryAttributes_management.")
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
            return -1
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy) in CalculateGeometryAttributes_management.")
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
            return -1
        except:
            self.logger.info("ERROR: Area calculation failed.")
            return -1

        self.cache_count += 1
        self.result = area * self.ft2ac
        self.logger.info("   * result: " + str(area * self.ft2ac) + " " + self.unit_str)

    @fGl.err_info
    @fGl.spatial_license
    def get_extents(self, template_feature, field=str()):
        # template feature = shapefile (full path)
        # fields = str
        self.logger.info("   * reading project area extents ...")
        with arcpy.da.UpdateCursor(template_feature, field) as cursor:
            for row in cursor:
                try:
                    self.extents = row[0].extent
                    self.logger.info("     ok")
                    break
                except:
                    self.logger.info("WARNING: Could not read project area extents (" + str(row) + ").")

    def set_env(self):
        arcpy.env.overwriteOutput = True
        try:
            arcpy.env.extent = arcpy.Extent(self.extents.XMin, self.extents.YMin, self.extents.XMax, self.extents.YMax)
        except:
            try:
                arcpy.env.extent = self.ras_project.extent
            except:
                arcpy.env.extent = "MAXOF"
                self.logger.info("WARNING: Could not set project area extents (set to MAXOF).")

    def set_project_area(self, geofile_name):
        # geofile_name = STR of either project area shapefile or TIF raster (DO NOT PROVIDE ANY FILE ENDING [SHP / TIF])
        self.logger.info("   * looking up project area polygon from " + str(geofile_name) + " ...")

        self.set_env()
        arcpy.env.workspace = self.dir2geo + "Rasters\\"
        raster_list = arcpy.ListRasters()

        project_raster_exists = False
        for ras in raster_list:
            if geofile_name.lower() in str(ras).lower():
                try:
                    self.ras_project = arcpy.Raster(self.dir2geo + "Rasters\\" + str(ras).lower())
                    project_raster_exists = True
                    self.logger.info("   * found project area Raster: " + str(ras).lower())
                except:
                    self.logger.info("ERROR: Could not load existing Raster of the project area.")

        if not project_raster_exists:
            self.logger.info("   * Polygon to Raster conversion required.")
            shp_project = self.dir2geo + "Shapefiles\\" + geofile_name.lower() + ".shp"
            try:
                self.logger.info("   * converting project area Polygon (%s) to Raster ... " % shp_project)
                try:
                    arcpy.PolygonToRaster_conversion(shp_project, "gridcode", self.dir2geo + "Rasters\\" + geofile_name.lower() + ".tif")
                except:
                    arcpy.PolygonToRaster_conversion(shp_project, "AreaCode",
                                                     self.dir2geo + "Rasters\\" + geofile_name.lower() + ".tif")
                self.logger.info("     ok")
            except:
                self.logger.info("ERROR: Could not create Raster of the project area.")
            try:
                self.ras_project = arcpy.Raster(self.dir2geo + "Rasters\\" + str(geofile_name) + ".tif")
            except:
                try:
                    self.ras_project = arcpy.Raster(self.dir2geo + "Rasters\\" + str(geofile_name).lower() + ".tif")
                except:
                    self.logger.info("ERROR: Could not load newly created Raster of the project area.")

        arcpy.env.workspace = self.cache

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = cSHArC (ProjectMaker)")
