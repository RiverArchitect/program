try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    import arcpy
    from arcpy.sa import *
except:
    print("ExceptionERROR: No valid arcpy found.")

try:
    # import own module classes
    import cFish as cf
    import cMakeTable as cmkt

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cInputOutput as cio
    import fGlobal as fg

except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: cHabitatIO, RP/fGlobal).")


class CHSI:
    def __init__(self, hab_condition, cover_applies, unit):
        self.cache = os.path.dirname(os.path.abspath(__file__)) + "\\.cache\\"
        self.condition = hab_condition
        self.combine_method = "geometric_mean"
        self.cover_applies = cover_applies  # BOOL
        self.logger = logging.getLogger("logfile")

        self.path_condition = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\" + self.condition + "\\"
        self.path_hsi = os.path.dirname(os.path.abspath(__file__)) + "\\HSI\\" + str(self.condition) + "\\"
        if self.cover_applies:
            p_ext = "cover"
        else:
            p_ext = "no_cover"
        self.path_csi = os.path.dirname(os.path.abspath(__file__)) + "\\CHSI\\" + str(self.condition) + "\\" + p_ext + "\\"
        self.path_wua_ras = os.path.dirname(os.path.abspath(__file__)) + "\\AUA\\Rasters\\" + str(self.condition) + "\\" + p_ext + "\\"
        fg.chk_dir(self.cache)
        fg.chk_dir(self.path_csi)
        fg.chk_dir(self.path_wua_ras)

        self.unit = unit
        if self.unit == "us":
            self.area_unit = "SQUARE_FEET_US"
            self.u_length = "ft"
            self.u_discharge = "cfs"
            self.ft2ac = 1 / 43560
        else:
            self.area_unit = "SQUARE_METERS"
            self.u_length = "m"
            self.u_discharge = "m3"
            self.ft2ac = 1

        self.xlsx_out = ""

    def calculate_wua(self, wua_threshold, fish):
        # aua_threshold =  FLOAT -- value between 0.0 and 1.0
        # fish = DICT -- fish.keys()==species_names; fish.values()==lifestages
        arcpy.CheckOutExtension('Spatial')
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.path_csi
        arcpy.env.extent = "MAXOF"
        self.logger.info(" >> Retrieving CHSI rasters ...")
        csi_list = arcpy.ListRasters()
        cc = 0  # appended in cache to avoid overwriting problems
        for species in fish.keys():
            for ls in fish[species]:
                self.logger.info(" -- Usable Area FOR " + str(species).upper() + " - " + str(ls).upper())
                fish_shortname = str(species).lower()[0:2] + str(ls[0])
                if self.cover_applies:
                    xsn = self.condition + "_" + fish_shortname + "_cov.xlsx"
                else:
                    xsn = self.condition + "_" + fish_shortname + ".xlsx"

                xlsx_name = os.path.dirname(os.path.abspath(__file__)) + "\\AUA\\" + xsn
                xlsx = cmkt.MakeFishFlowTable()
                xlsx.open_wb(xlsx_name, 0)

                Q = xlsx.read_float_column_short("B", 4)
                self.logger.info(" >> Reducing CHSI rasters to AUA threshold (" + str(wua_threshold) + ") ...")
                for csi in csi_list:
                    self.logger.info("    -- CHSI raster: " + str(csi))
                    if fish_shortname in str(csi):
                        ras_csi = arcpy.Raster(self.path_csi + str(csi))
                    else:
                        continue
                    dsc = arcpy.Describe(ras_csi)
                    coord_sys = dsc.SpatialReference
                    rel_ras = Con(Float(ras_csi) >= float(wua_threshold), Float(ras_csi))
                    self.logger.info("       * saving AUA-CHSI raster: " + self.path_wua_ras + str(csi))
                    try:
                        rel_ras.save(self.path_wua_ras + str(csi))
                    except:
                        self.logger.info("ERROR: Could not save AUA-CHSI raster.")

                    ras4shp = Con(~IsNull(rel_ras), 1)

                    self.logger.info("       * converting AUA-CHSI raster to shapefile ...")
                    try:
                        shp_name = self.cache + str(cc) + "aua.shp"
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

                    self.logger.info("       * calculating area ...")
                    area = 0.0
                    try:
                        arcpy.AddField_management(shp_name, "F_AREA", "FLOAT", 9)
                        arcpy.CalculateGeometryAttributes_management(shp_name, geometry_property=[["F_AREA", "AREA"]],
                                                                     area_unit=self.area_unit)
                        self.logger.info("         summing up area ...")
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

                    self.logger.info("       * writing Usable Area to workbook:")
                    for q in Q.keys():
                        try:
                            q_str = str(csi).split(fish_shortname)[1].split('.tif')[0]
                        except:
                            q_str = str(csi).split(fish_shortname)[1]
                        if str(int(q)) == q_str:
                            self.logger.info(
                                "         Discharge: " + str(q) + self.u_discharge + " and Usable Area: " + str(
                                    area) + " square " + self.u_length)
                            row = int("".join([str(s) for s in str(Q[q]) if s.isdigit()]))
                            xlsx.write_data_cell("F", row, (area * self.ft2ac))
                    cc += 1

                try:
                    xlsx.save_close_wb(xlsx_name)
                    self.xlsx_out = xlsx_name
                except:
                    self.logger.info("ERROR: Failed to save " + str(xlsx_name))
        arcpy.CheckInExtension('Spatial')
        if cc > 0:
            return "OK"
        else:
            return "NoMatch"

    def clear_cache(self, *args):
        # if args[0]==False: the cache folder itself is not deleted
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.cache
        ras_list = arcpy.ListRasters()
        shp_list = arcpy.ListFeatureClasses()
        try:
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
            try:
                arcpy.env.workspace = os.path.dirname(os.path.abspath(__file__))  # temporary workspace
                fg.rm_dir(self.cache)
                if not args[0]:
                    self.logger.info("        * restoring cache ...")
                    fg.chk_dir(self.cache)
                    arcpy.env.workspace = self.cache
            except:
                self.logger.info("   >> Cleared .cache folder (arcpy.Delete_management) ...")

        except:
            self.logger.info("WARNING: .cache folder will be removed by package controls.")

    def launch_chsi_maker(self, fish, combine_method, boundary_shp):
        try:
            self.combine_method = combine_method
        except:
            self.combine_method = "geometric_mean"

        return self.make_chsi(fish, boundary_shp)

    def make_boundary_ras(self, shapef):
        if not arcpy.Exists(self.path_hsi + "boundras.tif"):
            self.logger.info("    * Converting to raster ...")
            try:
                arcpy.PolygonToRaster_conversion(in_features=shapef, value_field="Id",
                                                 out_rasterdataset=self.path_hsi + "boundras.tif",
                                                 cell_assignment="CELL_CENTER", cellsize=1.0)
            except:
                self.logger.info(
                    "ERROR: Boundary shapefile in arcpy.PolygonToRaster_conversion. Check boundary shapefile.")
                self.logger.info(Exception.args[0])
                self.logger.info(arcpy.GetMessages())
        try:
            return arcpy.Raster(self.path_hsi + "boundras.tif")
        except:
            return -1

    def make_chsi(self, fish, boundary_shp):
        # habitat suitability curves from Fish.xlsx
        # fish is a dictionary with fish species listed in Fish.xlsx
        # boundary_shp is either a full path of a shape file or an empty string for using "MAXOF"

        self.logger.info(" >> Raster combination method: " + str(self.combine_method))
        arcpy.CheckOutExtension('Spatial')
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.cache
        arcpy.env.extent = "MAXOF"

        if boundary_shp.__len__() > 0:
            self.logger.info(" >> Applying boundary shapefile ... ")
            boundary_ras = self.make_boundary_ras(boundary_shp)
            try:
                if boundary_ras == -1:
                    self.logger.info("ERROR: Boundary shapefile provided but raster conversion failed.")
                    return -1
            except:
                pass

        self.logger.info(" >> Retrieving hydraulic HSI rasters from:")
        self.logger.info("      " + self.path_hsi)
        arcpy.env.workspace = self.path_hsi
        __temp_list__ = arcpy.ListRasters()
        hsi_list = []
        [hsi_list.append(item) for item in __temp_list__]  # ensures that hsi_list is not a pointer but a real list
        del __temp_list__
        arcpy.env.workspace = self.cache

        cc = 0
        for species in fish.keys():
            for ls in fish[species]:
                self.logger.info(" -- Usable Area for " + str(species).upper() + " - " + str(ls).upper())
                fish_shortname = str(species).lower()[0:2] + str(ls[0])
                for ras in hsi_list:
                    if not (fish_shortname in str(ras)):
                        continue
                    cc += 1
                    # find dsi-rasters and match according velocity rasters
                    if str(ras)[0:3] == "dsi":
                        try:
                            q = int(str(ras).split(fish_shortname)[-1])
                        except:
                            q = int(str(ras).split(fish_shortname)[-1].split('.tif')[0])
                        self.logger.info("    --- combining rasters for Q = " + str(q) + " (" + self.combine_method + ") ...")

                        # load inundation area Raster (wetted area)
                        try:
                            self.logger.info("        * loading innundated area raster ...")
                            if q >= 1000:
                                h_ras_name = "h%003dk.tif" % int(q/1000)
                            else:
                                h_ras_name = "h%003d.tif" % q
                            if boundary_shp.__len__() > 0:
                                self.logger.info("        * clipping to boundary ...")
                                inundation_ras = Con(~IsNull(boundary_ras), arcpy.Raster(self.path_condition + h_ras_name))
                            else:
                                inundation_ras = arcpy.Raster(self.path_condition + h_ras_name)
                        except:
                            self.logger.info("ERROR: Cannot find flow depth raster for Q = " + str(q))
                            try:
                                self.logger.info("       -raster name: " + str(self.path_condition) + str(h_ras_name))
                            except:
                                pass
                            continue

                        if self.cover_applies:
                            try:
                                # use higher hsi pixels if cover indicates relevance
                                cover_types = ["substrate", "boulders", "cobbles", "wood", "plants"]
                                arcpy.env.extent = arcpy.Extent(inundation_ras.extent.XMin, inundation_ras.extent.YMin,
                                                                inundation_ras.extent.XMax, inundation_ras.extent.YMax)
                                relevant_cov = []
                                for covt in cover_types:
                                    if arcpy.Exists(self.path_hsi + covt + "_hsi"):
                                        self.logger.info("        * adding cover: " + covt + "_hsi")
                                        relevant_cov.append(Float(arcpy.Raster(self.path_hsi + covt + "_hsi")))
                                    if arcpy.Exists(self.path_hsi + covt + "_hsi.tif"):
                                        self.logger.info("        * adding cover: " + covt + "_hsi.tif")
                                        relevant_cov.append(Float(arcpy.Raster(self.path_hsi + covt + "_hsi.tif")))
                                self.logger.info("        * calculating cell statistics (maximum HSI values) ...")
                                cov_hsi = Float(CellStatistics(relevant_cov, "MAXIMUM", "DATA"))
                            except:
                                self.logger.info("ERROR: Could not add cover HSI.")
                                continue
                        try:
                            self.logger.info("        * reading hydraulic HSI rasters ...")
                            try:
                                dsi = Float(arcpy.Raster(self.path_hsi + str(ras)))
                            except:
                                dsi = Float(arcpy.Raster(self.path_hsi + str(ras) + ".tif"))
                            try:
                                vsi = Float(arcpy.Raster(self.path_hsi + "vsi" + str(ras).strip("dsi")))
                            except:
                                vsi = Float(arcpy.Raster(self.path_hsi + "vsi" + str(ras).strip("dsi") + ".tif"))
                            if self.cover_applies:
                                if self.combine_method == "geometric_mean":
                                    self.logger.info("        * combining hydraulic and cover HSI rasters (geometric mean)...")
                                    chsi = Con(~IsNull(inundation_ras), Con(Float(inundation_ras) > 0.0, Float(Float(dsi * vsi * cov_hsi) ** Float(1/3))))
                                if self.combine_method == "product":
                                    self.logger.info("        * combining hydraulic and cover HSI rasters (product)...")
                                    chsi = Con(~IsNull(inundation_ras), Con(Float(inundation_ras) > 0.0, Float(dsi * vsi * cov_hsi)))
                            else:
                                if self.combine_method == "geometric_mean":
                                    self.logger.info("        * combining hydraulic HSI rasters (geometric mean)...")
                                    chsi = Con(~IsNull(inundation_ras), Con(Float(inundation_ras) > 0.0, Float(SquareRoot(dsi * vsi))))
                                if self.combine_method == "product":
                                    self.logger.info("        * combining hydraulic HSI rasters (product)...")
                                    chsi = Con(~IsNull(inundation_ras), Con(Float(inundation_ras) > 0.0, Float(dsi * vsi)))

                            if not ('.tif' in str(ras)):
                                self.logger.info("        * saving as: " + str(ras).strip("dsi") + ".tif")
                                chsi.save(self.path_csi + "csi" + str(ras).strip("dsi") + ".tif")
                            else:
                                self.logger.info("        * saving as: " + str(ras).strip("dsi"))
                                chsi.save(self.path_csi + "csi" + str(ras).strip("dsi"))

                            self.logger.info("        * clearing cache buffer ...")
                            del chsi, dsi, vsi
                            self.clear_cache(False)
                            self.logger.info("        * ok ...")
                        except:
                            self.logger.info("ERROR: Could not save CSI raster associated with " + str(ras) + ".")
                            continue
                self.logger.info(" >> OK")
                arcpy.CheckOutExtension('Spatial')
        if cc > 0:
            return "OK"
        else:
            return "NoMatch"

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = CHSI (Module: Habitat Evaluation)")


class HHSI:
    def __init__(self, geo_input_path, condition, *unit_system):

        # general directories and parameters
        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        self.condition = condition
        self.dir_in_geo = geo_input_path
        self.path_hsi = os.path.dirname(os.path.realpath(__file__)) + "\\HSI\\" + str(condition) + "\\"
        self.error = False
        self.flow_dict_h = {}
        self.flow_dict_u = {}
        self.fish = cf.Fish()
        self.logger = logging.getLogger("habitat_evaluation")
        self.raster_dict = {}
        self.ras_h = []
        self.ras_u = []

        fg.chk_dir(self.cache)
        fg.clean_dir(self.cache)
        fg.chk_dir(self.path_hsi)
        fg.chk_dir(self.dir_in_geo)

        # set unit system variables
        try:
            self.units = unit_system[0]
        except:
            self.units = "us"
            print("WARNING: Invalid unit_system identifier. unit_system must be either \'us\' or \'si\'.")
            print("         Setting unit_system default to \'us\'.")

    def clear_cache(self, *args):
        # if args[0]==False: the cache folder itself is not deleted
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.cache
        ras_list = arcpy.ListRasters()
        shp_list = arcpy.ListFeatureClasses()
        try:
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
            try:
                arcpy.env.workspace = os.path.dirname(os.path.abspath(__file__))  # temporary workspace
                fg.rm_dir(self.cache)
                if not args[0]:
                    self.logger.info("        * restoring cache ...")
                    fg.chk_dir(self.cache)
                    arcpy.env.workspace = self.cache
            except:
                self.logger.info(" >> Cleared .cache folder (arcpy.Delete_management) ...")

        except:
            self.logger.info("WARNING: .cache folder will be removed by package controls.")

    def make_boundary_ras(self, shapef):
        if not arcpy.Exists(self.path_hsi + "boundras.tif"):
            self.logger.info("    * Converting to raster ...")
            try:
                arcpy.PolygonToRaster_conversion(in_features=shapef, value_field="Id",
                                                 out_rasterdataset=self.path_hsi + "boundras.tif",
                                                 cell_assignment="CELL_CENTER", cellsize=1.0)
            except:
                self.logger.info(
                    "ERROR: Boundary shapefile in arcpy.PolygonToRaster_conversion. Check boundary shapefile.")
                self.logger.info(Exception.args[0])
                self.logger.info(arcpy.GetMessages())
        try:
            return arcpy.Raster(self.path_hsi + "boundras.tif")
        except:
            return -1

    def make_hhsi(self, fish_applied, boundary_shp):
        # habitat suitability curves from Fish.xlsx
        # fish_applied is a dictionary with fish species listed in Fish.xlsx
        # boundary_shp is either a full path of a shape file or an empty string for using "MAXOF"

        self.read_hyd_rasters()

        arcpy.CheckOutExtension('Spatial')
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.cache
        arcpy.env.extent = "MAXOF"

        if boundary_shp.__len__() > 0:
            boundary_ras = self.make_boundary_ras(boundary_shp)
            try:
                if boundary_ras == -1:
                    self.logger.info("ERROR: Boundary shapefile provided but raster conversion failed.")
                    return -1
            except:
                pass

        for species in fish_applied.keys():
            self.logger.info(" >> FISH SPECIES  : " + str(species))
            for ls in fish_applied[species]:
                self.logger.info("         LIFESTAGE: " + str(ls))
                self.logger.info("   >> Calculating DEPTH HSI (DSI)")
                self.logger.info("    > Retrieving hhsi curve from Fish.xlsx ...")
                curve_data = self.fish.get_hsi_curve(species, ls, "h")
                self.logger.info("      - OK")
                for rh in self.ras_h:
                    self.logger.info("   -> DISCHARGE: " + str(self.flow_dict_h[str(rh)]))
                    rh_ras = arcpy.Raster(self.dir_in_geo + rh)

                    self.logger.info("    > Raster calculation: Depth HSI ...")
                    if boundary_shp.__len__() > 0:
                        __temp_h_ras__ = Con(~IsNull(boundary_ras), Float(rh_ras))
                        rh_ras = __temp_h_ras__
                    ras_out = self.nested_con_raster_calc(rh_ras, curve_data)
                    self.logger.info("      - OK")
                    ras_name = "dsi_" + str(species[0:2]).lower() + str(ls)[0] + str(self.flow_dict_h[str(rh)]) + ".tif"
                    self.logger.info("    > Saving: " + self.path_hsi + ras_name + " ...")
                    try:
                        ras_out.save(self.path_hsi + ras_name)
                        self.logger.info("      - OK")
                    except:
                        self.logger.info("ERROR: Could not save HHSI (depth) raster (corrupted data?).")

                self.logger.info("   >> Calculating VELOCITY HSI")
                self.logger.info("    > Reading hhsi curve from Fish.xlsx ...")
                curve_data = self.fish.get_hsi_curve(species, ls, "u")
                self.logger.info("      - OK")
                for ru in self.ras_u:
                    self.logger.info("   -> DISCHARGE: " + str(self.flow_dict_u[str(ru)]))
                    rh_ras = arcpy.Raster(self.dir_in_geo + ru)
                    self.logger.info("    > Raster calculation: Velocity HSI  ... ")
                    if boundary_shp.__len__() > 0:
                        __temp_h_ras__ = Con(~IsNull(boundary_ras), Float(rh_ras))
                        rh_ras = __temp_h_ras__
                    ras_out = self.nested_con_raster_calc(rh_ras, curve_data)
                    self.logger.info("      - OK")
                    ras_name = "vsi_" + str(species[0:2]).lower() + str(ls)[0] + str(self.flow_dict_u[str(ru)]) + ".tif"
                    self.logger.info(
                        "    > Saving: " + self.path_hsi + ras_name + " ...")
                    try:
                        ras_out.save(self.path_hsi + ras_name)
                        self.logger.info("      - OK")
                    except:
                        self.logger.info("ERROR: Could not save HHSI (velocity) raster (corrupted data?).")

            self.logger.info(" >> FISH SPECIES " + str(species).upper() + " COMPLETE.")
        arcpy.env.workspace = self.cache
        arcpy.CheckInExtension('Spatial')

    def nested_con_raster_calc(self, ras, curve_data):
        arcpy.env.extent = "MAXOF"
        # curve_data = [[x-values], [y-values(hsi)]]
        __ras__ = [ras * 0]  # initial raster assignment
        index = 0
        i_par_prev = 0.0
        i_hsi_prev = curve_data[1][0]
        for i_par in curve_data[0]:
            __ras__.append(Float(Con((Float(ras) >= Float(i_par_prev)) & (Float(ras) < Float(i_par)), (
                                     Float(i_hsi_prev) + (
                                      (Float(ras) - Float(i_par_prev)) / (Float(i_par) - Float(i_par_prev)) * Float(
                                        curve_data[1][index] - i_hsi_prev))), Float(0.0))))
            i_hsi_prev = curve_data[1][index]
            i_par_prev = i_par
            index += 1

        return Float(CellStatistics(__ras__, "SUM", "DATA"))

    def read_hyd_rasters(self):
        # uses negotiated HHSI script
        arcpy.CheckOutExtension('Spatial')
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.dir_in_geo
        arcpy.env.extent = "MAXOF"

        # obtain just the depth files
        self.logger.info(" >> Retrieving rasters for hydraulic HSI calculation.")
        all_rasters = arcpy.ListRasters()
        arcpy.env.workspace = self.cache

        for rn in all_rasters:
            if (rn[0] == "h") or (rn[0] == "u"):
                try:
                    if str(rn).endswith("k") or str(rn).endswith("k.tif"):
                        # multiply "k"-raster name discharges with 1000
                        thousand = 1000.0
                    else:
                        thousand = 1.0
                    if rn[0] == "h":
                        self.logger.info("     -- Adding flow depth raster: " + str(rn))
                        _Q_ = float(str(rn).split("h")[1].split(".tif")[0].split("k")[0]) * thousand
                        self.flow_dict_h.update({str(rn): int(_Q_)})
                        self.ras_h.append(str(rn))
                    if rn[0] == "u":
                        self.logger.info("     -- Adding flow velocity raster: " + str(rn))
                        _Q_ = float(str(rn).split("u")[1].split(".tif")[0].split("k")[0]) * thousand
                        self.flow_dict_u.update({str(rn): int(_Q_)})
                        self.ras_u.append(str(rn))
                except:
                    self.logger.info("ERROR: Failed to add raster.")

        arcpy.env.workspace = self.cache
        arcpy.CheckInExtension('Spatial')

    def __call__(self, *args):
        print("Class Info: <type> = HHSI (Module: Habitat Evaluation)")


class CovHSI(HHSI):
    def __init__(self, raster_input_path, condition, geofile_name, *unit_system):
        try:
            HHSI.__init__(self, raster_input_path, condition, unit_system[0])
        except:
            # if no unit_system is provided
            HHSI.__init__(self, raster_input_path, condition)

        self.cover_type = str(geofile_name).split(".")[0]
        self.cell_size = float()  # initialization for points to raster export variable
        if self.units == "us":
            self.geofile_dict = {"substrate": "dmean_ft.tif", "boulders": "boulders.shp", "cobbles": "dmean_ft.tif",
                                 "wood": "wood.shp", "plants": "plants.shp"}
        else:
            self.geofile_dict = {"substrate": "dmean.tif", "boulders": "boulders.shp", "cobbles": "dmean.tif",
                                 "wood": "wood.shp", "plants": "plants.shp"}

        if not (self.geofile_dict[self.cover_type][-4:-1] == ".sh"):
            try:
                self.logger.info(" >> Identified cover type (input raster): " + self.geofile_dict[self.cover_type])
                self.input_raster = arcpy.Raster(raster_input_path + self.geofile_dict[self.cover_type])
            except:
                self.logger.info("ERROR: Could not find the cover input geofile (" + self.geofile_dict[self.cover_type] + ").")
        else:
            self.logger.info(" >> Identified cover type (input shapefile): " + self.geofile_dict[self.cover_type])
            self.input_raster = self.convert_shp2raster(self.dir_in_geo + self.geofile_dict[self.cover_type])

    def call_analysis(self, curve_data):
        if self.cover_type == "substrate":
            return self.nested_con_raster_calc(self.input_raster, curve_data)
        if (self.cover_type == "plants") or (self.cover_type == "wood") or (self.cover_type == "boulders"):
            return self.spatial_join_analysis(self.input_raster, curve_data)
        if self.cover_type == "cobbles":
            return self.substrate_size_analysis(self.input_raster, curve_data)

    def convert_shp2raster(self, shapefile):
        cov_raster = "cov_ras.tif"  # name of the temporarily used cover raster
        arcpy.PolygonToRaster_conversion(shapefile, "cover.tif", self.cache + cov_raster,
                                         cell_assignment="CELL_CENTER", priority_field="NONE", cellsize=1)
        return arcpy.Raster(self.cache + cov_raster)

    def crop_input_raster(self, fish_species, fish_lifestage, depth_raster_path):
        # crop (cover) input_raster to the minimum flow depth defined in Fish.xlsx, associated with a given dsicharge
        try:
            curve_data = self.fish.get_hsi_curve(fish_species, fish_lifestage, "h")
            h_min = curve_data[0][0]
        except:
            self.logger.info(
                "WARNING: Could not get minimum flow depth for defined fish species/lifestage. Setting h min to 0.1 (default).")
            h_min = 0.1
        try:
            h_raster = arcpy.Raster(depth_raster_path)
            __temp__ = Con((Float(h_raster) >= h_min), self.input_raster)
            self.input_raster = __temp__
        except:
            self.logger.info("ERROR: Could not crop raster to defined flow depth.")
        # assign relevant cell_size for point to raster conversion
        try:
            self.cell_size = float(arcpy.GetRasterProperties_management(h_raster, property_type="CELLSIZEX")[0])
        except:
            self.logger.info("WARNING: Could not get flow depth raster properties. Setting output cell size to 3.0 (default).")
            self.cell_size = 3.0  # default assignment

    def define_grain_size(self, grain_type):
        if "cobbles" in grain_type:
            metric_size = [0.064, 0.256]  # cobble min and max size in meters
        if "boulders" in grain_type:
            metric_size = [0.256, 100]  # boulder min and max (fictive) size in meters

        try:
            if self.units == "us":
                return [uss / 0.3047992 for uss in metric_size]
            if self.units == "si":
                return metric_size
        except:
            pass

    def make_covhsi(self, fish_applied, depth_raster_path):
        # habitat suitability curves from Fish.xlsx
        # fish_applied is a dictionary with fish species listed in Fish.xlsx
        arcpy.CheckOutExtension('Spatial')
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.cache
        arcpy.env.extent = "MAXOF"
        self.logger.info("* * * CREATING " + str(self.cover_type).upper() + " COVER RASTER * * *")
        for species in fish_applied.keys():
            self.logger.info(" >> FISH SPECIES  : " + str(species))
            for ls in fish_applied[species]:
                self.logger.info("         LIFESTAGE: " + str(ls))
                self.logger.info("   -> Retrieving " + self.cover_type + " curve from Fish.xlsx ...")
                curve_data = self.fish.get_hsi_curve(species, ls, self.cover_type)
                if depth_raster_path.__len__() > 0:
                    self.logger.info("   -> Cropping to relevant depth regions ...")
                    self.crop_input_raster(species, ls, depth_raster_path)
                else:
                    try:
                        self.cell_size = float(arcpy.GetRasterProperties_management(self.input_raster, property_type="CELLSIZEX")[0])
                    except:
                        self.cell_size = 1.0
                self.logger.info("   -> Calculating cover HSI raster ...")
                try:
                    ras_out = self.call_analysis(curve_data)
                except:
                    self.logger.info("ERROR: Cover raster calculation (check input data).")
                    arcpy.CheckInExtension('Spatial')
                    self.error = True

                self.logger.info("      - OK")
                ras_name = self.cover_type + "_hsi.tif"
                self.logger.info(
                    "   -> Saving: " + self.path_hsi + ras_name + " ...")
                try:
                    ras_out.save(self.path_hsi + ras_name)
                    self.logger.info("      - OK")
                except:
                    self.logger.info("ERROR: Could not save " + self.cover_type + " HSI raster (corrupted data?).")
                    self.error = True

            if not self.error:
                self.logger.info(" >> " + self.cover_type + " cover HSI raster creation " + str(species).upper() + " complete.")
            else:
                self.logger.info(" >> Could not create cover HSI raster. Check error messages.")

        arcpy.CheckInExtension('Spatial')

    def spatial_join_analysis(self, raster, curve_data):
        # uses curve radius data and to mark all points within this radius of the input raster

        self.logger.info("   -> Converting raster to points ...")
        try:
            cov_points = self.cache + "cov_points.shp"
            arcpy.RasterToPoint_conversion(raster, cov_points)
            zero_raster = Con((IsNull(raster) == 1), (IsNull(raster) * 1), 1)
            all_points = self.cache + "all_points.shp"
            arcpy.RasterToPoint_conversion(zero_raster, all_points)
        except:
            self.error = True
            self.logger.info("ERROR: Could not perform spatial radius operations (RasterToPoint_conversion).")
        self.logger.info("   -> Delineating " + self.cover_type + " effect radius (spatial join radius: " + str(curve_data[0][0]) + ") ...")
        try:
            out_points = self.cache + "spatjoin.shp"
            rad = float(curve_data[0][0])
            arcpy.SpatialJoin_analysis(target_features=all_points, join_features=cov_points,
                                       out_feature_class=out_points, join_operation="JOIN_ONE_TO_MANY",
                                       join_type="KEEP_COMMON", field_mapping="", match_option="CLOSEST",
                                       search_radius=rad, distance_field_name="")
        except:
            self.error = True
            self.logger.info("ERROR: Could not perform spatial radius operations (SpatialJoin_analysis).")
        self.logger.info("   -> Converting points back to raster ...")
        try:
            arcpy.PointToRaster_conversion(in_features=out_points, value_field="grid_code",
                                           out_rasterdataset=self.cache + "cov_points",
                                           cell_assignment="MEAN", cellsize=self.cell_size)
            __temp_ras__ = arcpy.Raster(self.cache + "cov_points.tif")
            self.logger.info("   -> Assigning spatial HSI value (" + str(curve_data[1][0]) + ") where applies (raster calculator) ...")
            __ras__ = Con(__temp_ras__ > 0, curve_data[1][0])  # assign HSI value
        except:
            self.error = True
            self.logger.info("ERROR: Could not perform spatial radius operations (back conversion).")
        if not self.error:
            return Float(CellStatistics([__ras__], "SUM", "DATA"))
        else:
            return -1

    def substrate_size_analysis(self, raster, curve_data):
        self.logger.info("   -> Sorting out relevant grain sizes ...")
        # retain only values of interest
        __ras__ = Con(Float(raster) >= self.define_grain_size(self.cover_type)[0],
                      Con(Float(raster) < self.define_grain_size(self.cover_type)[1], 1.0))
        return self.spatial_join_analysis(__ras__, curve_data)

    def __call__(self, *args):
        print("Class Info: <type> = CovHSI (Module: Habitat Evaluation)")
