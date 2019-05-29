# logs to logfile.log
try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    import arcpy
    from arcpy.sa import *
except:
    print("ExceptionERROR: No valid ARCPY found.")

try:
    import fFunctions as ff
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: fFunctions).")


class SHArC:
    def __init__(self, unit, reach, stn, version):
        self.path2geodata = os.path.dirname(os.path.realpath(__file__)) + "\\" + str(reach).upper() + "_" + str(stn).lower() + "_" + str(version) + "\\Geodata\\"
        self.cache = self.path2geodata + ".cache\\"
        self.cache_count = 0
        ff.chk_dir(self.cache)
        self.extents = [0, 0, 0, 0]
        self.logger = logging.getLogger("logfile")
        self.ras_project = ""
        self.unit = unit
        if self.unit == "us":
            self.area_unit = "SQUARE_FEET_US"
            self.ft2ac = 1 / 43560
        else:
            self.area_unit = "SQUARE_METERS"
            self.ft2ac = 1

        self.xlsx_out = ""

    def calculate_wua(self, exceedance_pr, usable_area):
        # exceedance_pr = LIST of discharge exceedance probabilities
        # usable_area =  LIST of usable habitat area corresponding to exceedance_pr
        aua = []
        for e in range(0, exceedance_pr.__len__()):
            if not (e == (exceedance_pr.__len__() - 1)):
                pr = exceedance_pr[e]
            else:
                pr = 100 - sum(exceedance_pr[0: e])
            aua.append(pr / 100 * usable_area[e])
        return sum(aua)

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
            ff.rm_dir(self.cache)
            self.cache_count = 0
            if recreate_cache:
                ff.chk_dir(self.cache)
            self.logger.info("   * ok")
        except:
            self.logger.info("WARNING: .cache folder will be removed by package controls.")

    def get_usable_area(self, csi_raster, target_dir):
        # wua_threshold =  FLOAT -- value between 0.0 and 1.0
        self.set_env()
        arcpy.CheckOutExtension('Spatial')
        arcpy.env.workspace = self.cache

        try:
            ras_csi = arcpy.Raster(csi_raster + ".tif")
        except:
            ras_csi = arcpy.Raster(csi_raster)
        dsc = arcpy.Describe(ras_csi)
        coord_sys = dsc.SpatialReference

        self.logger.info("   * snapping to relevant are of CHSI raster ...")
        ras4shp = Con((~IsNull(ras_csi) & ~IsNull(self.ras_project)), 1)

        self.logger.info("   * converting CHSI raster to shapefile ...")
        try:
            shp_name = self.cache + str(self.cache_count) + "aua.shp"
            arcpy.RasterToPolygon_conversion(ras4shp, shp_name, "NO_SIMPLIFY")
            arcpy.DefineProjection_management(shp_name, coord_sys)
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy) in RasterToPolygon_conversion.")
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy) in RasterToPolygon_conversion.")
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
        except:
            self.logger.info("ERROR: Shapefile conversion failed.")

        self.logger.info("   * calculating usable habitat area and ")
        area = 0.0
        try:
            self.logger.info("     saving project CHSI shapefile of raster " + str(csi_raster) + ".tif to:")
            self.logger.info("     " + target_dir + str(shp_name))
            arcpy.AddField_management(shp_name, "F_AREA", "FLOAT", 9)
            arcpy.CalculateGeometryAttributes_management(shp_name, geometry_property=[["F_AREA", "AREA"]],
                                                         area_unit=self.area_unit)
            self.logger.info("   * summing area ...")
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
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy) in CalculateGeometryAttributes_management.")
            self.logger.info(e.args[0])
            arcpy.AddError(e.args[0])
        except:
            self.logger.info("ERROR: Area calculation failed.")

        self.cache_count += 1
        return float(area * self.ft2ac)

    def get_extents(self, template_feature, fields):
        # template feature = shapefile (full path)
        # fields = list: ["SHAPE@", look_for_entry]
        self.logger.info("   * reading project area extents ...")
        for row in arcpy.da.SearchCursor(template_feature, fields):
            if row[1] == 1:
                try:
                    self.extents = row[0].extent
                    self.logger.info("     ok")
                except:
                    self.logger.info("WARNING: Could not read project area extents (" + str(row) + ").")

    def set_env(self):
        arcpy.env.overwriteOutput = True
        try:
            arcpy.env.extent = arcpy.Extent(self.extents.XMin, self.extents.YMin, self.extents.XMax, self.extents.YMax)
        except:
            arcpy.env.extent = "MAXOF"
            self.logger.info("WARNING: Could not set project area extents (set to MAXOF).")

    def set_project_area(self, geofile_name, *field):
        # geofile_name = STR of either project area shapefile or TIF raster (DO NOT PROVIDE ANY FILE ENDING [SHP / TIF])
        try:
            field_name = field[0]  # should be provided if there's not yet a project raster
        except:
            field_name = "Id"

        self.logger.info("   * looking up project area geofile (" + str(geofile_name) + ") ...")

        self.set_env()
        arcpy.env.workspace = self.path2geodata + "Rasters\\"
        raster_list = arcpy.ListRasters()

        project_raster_exists = False
        for ras in raster_list:
            if geofile_name.lower() == str(ras).lower():
                try:
                    self.ras_project = arcpy.Raster(self.path2geodata + "Rasters\\" + str(ras))
                    project_raster_exists = True
                    self.logger.info("   * found project area Raster: " + str(ras))
                except:
                    self.logger.info("ERROR: Could not load existing Raster of the project area.")

        if not project_raster_exists:
            self.logger.info("   * Polygon to Raster conversion required.")
            shp_project = self.path2geodata + "Shapefiles\\" + geofile_name + ".shp"
            try:
                self.logger.info("   * converting project area Polygon to Raster ... ")
                arcpy.PolygonToRaster_conversion(shp_project, field_name, self.path2geodata + "Rasters\\" + geofile_name + ".tif")
                self.logger.info("     ok")
            except:
                self.logger.info("ERROR: Could not create Raster of the project area.")
            try:
                self.ras_project = arcpy.Raster(self.path2geodata + "Rasters\\" + str(geofile_name) + ".tif")
            except:
                try:
                    self.ras_project = arcpy.Raster(self.path2geodata + "Rasters\\" + str(geofile_name).lower() + ".tif")
                except:
                    self.logger.info("ERROR: Could not load newly created Raster of the project area.")

        arcpy.env.workspace = self.cache

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = CAUA (ProjectProposal)")
