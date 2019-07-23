# !/usr/bin/python
import os, sys, logging
try:
    import config
    import fGlobal as fGl
    from shutil import copyfile
    sys.path.append(config.dir2lf)
    from cReadInpLifespan import Info
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/fGlobal.py, cReadInpLifespan.py).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?).")


class Mapper:
    def __init__(self, condition, map_type, *args):
        # condition = [str] state of planning situation, e.g., "2008"
        # map_type = [str] options: "lf", "ds", "mlf", "mt"
        # args[0] alternative raster input directory - if empty: uses standard output
        # args[1] alternative output directory - if empty: 02_Maps/CONDITION/
        self.logger = logging.getLogger("logfile")

        # get and make directories
        self.condition = condition
        self.dir_map_shp = ""
        self.error = False
        self.legend = None  # tar: aprx.listLayouts()[0].listElements("mapframe_element")[0].listElements("legend_element")[0]
        self.m = None  # will be an aprx.listMaps(STR)[0] object
        self.map_frame = None  # will be an aprx.listLayouts()[0].listElements("mapframe_element)[0] object
        self.map_layout = None  # will be an aprx.listLayouts()[0] object
        self.map_type = map_type
        self.map_string = ""  # will be assigned as a function of map_type in self.assign_directories
        self.raster_extent = None  # tar: arcpy.Raster().extent
        self.map_list = []
        self.ras4map_list = []
        self.resolution = 96  # dpi
        self.xy_center_points = []

        try:
            if not(args[0].__len__() < 2):
                self.dir_map_ras = args[0]
            else:
                self.dir_map_ras = str(self.get_input_ras_dir(map_type))
            fGl.chk_dir(self.dir_map_ras)
        except:
            try:
                self.dir_map_ras = str(self.get_input_ras_dir(map_type))
            except:
                self.logger.info("WARNING: The provided path to rasters for mapping is invalid. Using templates instead.")
                self.dir_map_ras = config.dir2map_templates + "rasters"

        try:
            self.output_dir = args[1]
        except:
            self.output_dir = config.dir2map + self.condition + "\\"
        fGl.chk_dir(self.output_dir)
        fGl.chk_dir(self.output_dir + "layers\\")

        try:
            self.aprx = self.copy_template_project()  # returns an arcpy.mp.ArcGISProject() object
        except:
            self.logger.info("ERROR: Could read source project (ensure that " + config.dir2map_templates + "river_template.aprx exists).")

    def choose_ref_layer(self, raster_type):
        # raster_type =  STR of mxd or raster name
        try:
            if 'lf' in str(raster_type):
                return "lf_sym"
            if 'ds' in str(raster_type):
                return "ds_sym"
        except ValueError:
            return ""

    def choose_ref_layout(self, map_lyr_name=str()):
        if "lf" in map_lyr_name:
            if not ("mlf" in map_lyr_name):
                return "layout_lf"
            else:
                if "bio" in map_lyr_name.lower():
                    return "layout_mlf_bioeng"
                if "maint" in map_lyr_name.lower():
                    return "layout_mlf_maintenance"
                if "plant" in map_lyr_name.lower():
                    return "layout_mlf_plants"
                if "terra" in map_lyr_name.lower():
                    return "layout_mlf_terraforming"
        if "ds" in map_lyr_name:
            if "bio" in map_lyr_name.lower():
                return "layout_ds_bio"
            if ("dcf" in map_lyr_name.lower()) or ("dcr" in map_lyr_name.lower()) or ("dst" in map_lyr_name.lower()) or ("grav" in map_lyr_name.lower()) or ("rocks" in map_lyr_name.lower()):
                return "layout_ds_Dcr"
            if "fines" in map_lyr_name.lower():
                if "15" in map_lyr_name.lower():
                    return "layout_ds_FS_D15"
                if "85" in map_lyr_name.lower():
                    return "layout_ds_FS_D85"
            if "sidech" in map_lyr_name.lower():
                return "layout_ds_SeS0"
            if "sideca" in map_lyr_name.lower():
                return "layout_ds_sideca"
            if "widen" in map_lyr_name.lower():
                return "layout_ds_widen"
            if ("wood" in map_lyr_name.lower()) or ("Dw" in map_lyr_name.lower()):
                return "layout_ds_Dw"
        if "volume_" in map_lyr_name:
            return map_lyr_name
        if "exc" in map_lyr_name:
            return "volume_cust_neg"
        if "fil" in map_lyr_name:
            return "volume_cust_pos"
        # if no map_lyr_name could be identified > return lifespan layout
        return "layout_lf"

    def choose_map_layer(self, map_name=str()):
        if "lf" in map_name:
            if not ("mlf" in map_name):
                return "layer_lf"
            else:
                if "bio" in map_name.lower():
                    return "layer_mlf_bioeng"
                if "maint" in map_name.lower():
                    return "layer_mlf_connectivity"
                if "plant" in map_name.lower():
                    return "layer_mlf_plants"
                if "terra" in map_name.lower():
                    return "layer_mlf_terraforming"
        if "ds_" in map_name:
            if "bio" in map_name.lower():
                return "layer_ds_bio"
            if ("dcf" in map_name.lower()) or ("dcr" in map_name.lower()) or ("dst" in map_name.lower()) or ("grav" in map_name.lower()) or ("grain" in map_name.lower()):
                return "layer_ds_Dcr"
            if "fines" in map_name.lower():
                if "15" in map_name.lower():
                    return "layer_ds_FS_D15"
                if "85" in map_name.lower():
                    return "layer_ds_FS_D85"
            if "sidech" in map_name.lower():
                return "layer_ds_SeS0"
            if "sideca" in map_name.lower():
                return "layer_ds_sideca"
            if "widen" in map_name.lower():
                return "layer_ds_widen"
            if "wood" in map_name.lower():
                return "layer_ds_Dw"
        if "volume_" in map_name:
            return map_name
        if "exc" in map_name:
            return "volume_cust_neg"
        if "fil" in map_name:
            return "volume_cust_pos"
        # if no map_name could be identified > return lifespan layer
        return "layer_lf"

    def copy_template_project(self):
        try:
            if not os.path.isfile(self.output_dir + "maps_" + self.condition + "_design.aprx"):
                arcpy.mp.ArcGISProject(config.dir2map_templates + "river_template.aprx").saveACopy(self.output_dir + "maps_" + self.condition + "_design.aprx")
        except:
            self.logger.info(" >> Using existing project: " + self.output_dir + "maps_" + self.condition + "_design.aprx")
        try:
            return arcpy.mp.ArcGISProject(self.output_dir + "maps_" + self.condition + "_design.aprx")
        except:
            self.logger.info(
                "ERROR: Could not create new project (check write permissions for " + self.output_dir + ").")
            return -1

    def get_input_ras_dir(self, map_type):
        if (map_type == "lf") or (map_type == "ds"):
            return config.dir2lf + "Output\\Rasters\\" + self.condition + "\\"
        if map_type == "mlf":
            self.dir_map_shp = config.dir2ml + "Output\\Shapefiles\\" + self.condition + "\\"
            return config.dir2ml + "Output\\Rasters\\" + self.condition + "\\"
        if map_type == "mt":
            return config.dir2mt + "Output\\Rasters\\" + self.condition + "\\"

    def get_raster_extent(self, path2raster):
        # path2raster = STR of full raster directory (e.g., D:/temp/raster.tif)
        raster = arcpy.Raster(path2raster)
        return raster.extent

    def make_pdf_maps(self, map_name, *args, **kwargs):
        # map_name = STR of pdf name
        # args[0] =  STR of alternative output directory for PDFs
        # optional kwarg "extent": overwrite mapping extent
        # optional kwarg "map_layout": alternative aprx.listLayouts()[] object
        try:
            length = args[0].__len__()
            if length > 3:
                self.output_dir = args[0]
                fGl.chk_dir(self.output_dir)
                self.logger.info(" >> Alternative output directory provided: " + str(self.output_dir))
        except:
            pass

        try:
            for k in kwargs.items():
                if "extent" in str(k[0]).lower():
                    if k[1] == "raster":
                        self.logger.info(" >> Using Raster coordinates for mapping.")
                        self.make_xy_centerpoints(
                            [self.raster_extent.XMin, self.raster_extent.YMin, self.raster_extent.XMax,
                             self.raster_extent.YMax])
                    else:
                        if not (k[1] == "MAXOF"):
                            self.make_xy_centerpoints(k[1])
                            self.logger.info(" >> Special reach extents provided.")
                            self.logger.info("    --> Overwriting mapping.inp center point definitions.")
                if "map_layout" in k[0]:
                    self.logger.info(" >> External map layout provided - using: " + str(k[1]))
                    self.map_layout = k[1]
        except:
            pass

        self.logger.info(" >> Starting PDF creation for: " + str(self.map_layout.name))
        self.logger.info("    * Map format: ANSI E landscape (w = %0.1f in, h = %0.1f in)" % (self.map_layout.pageWidth, self.map_layout.pageHeight))
        map_name = map_name.split("\\")[-1].split("/")[-1]
        if self.map_type == "lf":
            for lyr in self.m.listLayers():
                if not ((str(map_name).split(".pdf")[0] in lyr.name) or ("background" in lyr.name)):
                    lyr.visible = False
                else:
                    lyr.visible = True
        self.aprx.save()

        arcpy.env.workspace = self.output_dir
        arcpy.env.overwriteOutput = True
        pdf_name = self.output_dir + map_name.split(".pdf")[0] + ".pdf"
        self.logger.info("    * Creating PDF %s ..." % pdf_name)
        try:
            os.remove(pdf_name) if os.path.isfile(pdf_name) else print()
            __outputPDF__ = arcpy.mp.PDFDocumentCreate(pdf_name)
            __tempPDFs__ = []
            __count__ = 0
            for xy in self.xy_center_points:
                __count__ += 1
                self.logger.info("      - zooming to " + str(xy))
                try:
                    self.zoom2map(xy)
                except:
                    self.logger.info("ERROR: Invalid x-y coordinates in extent source [mapping.inp / reaches].")
                fig_name = "fig_" + "%02d" % (__count__,)
                __PDFpath__ = self.output_dir + fig_name + "_temp.pdf"
                self.logger.info("      - exporting PDF page ... ")
                try:
                    self.map_layout.exportToPDF(__PDFpath__, image_compression="ADAPTIVE", resolution=self.resolution,
                                                clip_to_elements=True)
                except:
                    self.error = True
                    self.logger.info("ERROR: Could not export PDF page no. " + str(__count__))
                self.logger.info("      - appending PDF page ... ")
                try:
                    __outputPDF__.appendPages(str(__PDFpath__))
                    __tempPDFs__.append(__PDFpath__)  # remember temp names to remove later on
                    self.logger.info("      - page complete.")
                except:
                    self.error = True
                    self.logger.info("ERROR: Could not append PDF page no." + str(__count__) + " to map assembly.")
            try:
                __outputPDF__.saveAndClose()
            except:
                self.error = True
                self.logger.info("ERROR: Failed to save PDF map assembly.")

            for deletePDF in __tempPDFs__:
                try:
                    os.remove(deletePDF)
                except:
                    self.logger.info("WARNING: Could not clean up PDF map temp_pages.")
            self.logger.info("    * Finished map: " + self.output_dir + map_name.split(".pdf")[0] + ".pdf")

        except arcpy.ExecuteError:
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
            self.logger.info("ERROR: Mapping failed.")
            self.error = True
        except:
            self.logger.info("ERROR: Mapping failed.")
            self.error = True

    def make_xy_centerpoints(self, new_extents):
        # shape(new_extents) = [XMin, YMin, XMax, YMax]
        self.xy_center_points = []
        self.xy_center_points.append(
            [float((new_extents[0] + new_extents[2]) / 2.), float((new_extents[1] + new_extents[3]) / 2.)])
        self.dx = float(new_extents[2] - new_extents[0])
        self.dy = float(new_extents[3] - new_extents[1])
        self.logger.info("      - New X center: " + str(self.xy_center_points[0][0]))
        self.logger.info("      - New Y center: " + str(self.xy_center_points[0][1]))
        self.logger.info("      - New map width: " + str(self.dx))
        self.logger.info("      - New map height: " + str(self.dy))
        self.resolution = 192  # improve resolution of single maps

    def prepare_layout(self, *args, **kwargs):
        # prepares map layouts in the project file (self.aprx) and starts mapping if not args[0]
        # kwargs: - map_items=LIST of items for mapping (default: all rasters in dir_map_ras folder)
        try:
            direct_mapping = args[0]
        except:
            direct_mapping = True

        arcpy.env.workspace = self.dir_map_ras
        arcpy.env.overwriteOutput = True
        self.ras4map_list = fGl.list_file_type_in_dir(self.dir_map_ras, ".tif")
        if self.ras4map_list.__len__() < 1:
            self.ras4map_list = fGl.list_file_type_in_dir(self.dir_map_ras, ".aux.xml")
        try:
            for k in kwargs.items():
                if "map_items" in str(k[0]).lower():
                    self.map_list = k[1]
        except:
            pass
        if self.map_list.__len__() < 1:
            self.map_list = self.ras4map_list

        self.logger.info("\n\nMAPPING")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")

        for map_item in self.map_list:
            map_name = map_item.split("\\")[-1].split("/")[-1]
            map_name = str(map_name).lower().split(".tif")[0].split("_mlf")[0]
            self.logger.info(" >> Preparing map: " + self.output_dir + map_name + ".pdf")

            # choose layout
            self.map_string = self.choose_map_layer(str(map_name).lower().split(".tif")[0])
            if self.map_string.__len__() < 1:
                self.logger.info("ERROR: No reference map found for %s (skipping)." % str(map_item))
                continue
            self.logger.info("    * source map layer: " + self.map_string)
            try:
                self.m = self.aprx.listMaps(self.map_string)[0]
                self.logger.info("    * source map layout: " + self.choose_ref_layout(self.map_string))
                if self.choose_ref_layout(self.map_string).__len__() < 1:
                    self.logger.info("ERROR: No reference layer found for %s (skipping)." % str(self.map_string))
                    continue
            except:
                self.logger.info("ERROR: Invalid reference map for %s (skipping)." % str(self.map_string))
                continue
            self.map_layout = self.aprx.listLayouts(self.choose_ref_layout(self.map_string))[0]
            self.logger.info("    * setting legend ...")
            self.legend = self.map_layout.listElements("legend_element", "legend")[0]
            self.legend.syncLayerOrder = False
            self.legend.syncLayerVisibility = False
            self.legend.syncNewLayer = False
            self.legend.syncReferenceScale = False
            self.logger.info("    * saving updates ...")
            self.aprx.save()

            try:
                if self.map_type == "lf":
                    try:
                        self.map_frame = self.map_layout.listElements("mapframe_element")[0]
                    except:
                        pass
                    self.logger.info("    * creating new layer ...")
                    lf_source_layer = self.m.listLayers(self.choose_ref_layer(map_name))[0]  # lf_sym
                    __new_ras_lyr_name__ = map_name + ".lyrx"
                    __new_ras__ = arcpy.Raster(str(map_item))
                    self.raster_extent = __new_ras__.extent
                    __new_ras_lyr__ = arcpy.MakeRasterLayer_management(__new_ras__, map_name, "#", "", "#")
                    arcpy.SaveToLayerFile_management(__new_ras_lyr__, self.output_dir + "layers\\" + map_name)
                    __new_lyr_file__ = arcpy.mp.LayerFile(self.output_dir + "layers\\" + __new_ras_lyr_name__)
                    self.m.insertLayer(lf_source_layer, __new_lyr_file__, "BEFORE")
                    self.logger.info("    * updating symbology ...")
                    self.m.listLayers(map_name)[0].symbology = lf_source_layer.symbology
                if self.map_type == "mlf":
                    self.logger.info("    * retrieving symbology ...")
                    try:
                        sym_lyr_f = arcpy.mp.LayerFile(config.dir2map_templates + "symbology\\LifespanRasterSymbology.lyrx")
                        sym_lyr = sym_lyr_f.listLayers()[0]
                    except:
                        self.logger.info("WARNING: Cannot load " + config.dir2map_templates + "symbology\\LifespanRasterSymbology.lyrx")
                    self.logger.info("    * updating layer sources ...")
                    for lyr in self.m.listLayers():
                        visibility = True
                        if not ("background" in lyr.name.lower()):
                            self.logger.info("      - layer source " + lyr.connectionProperties['dataset'])
                            dir_old = lyr.connectionProperties['connection_info']['database']
                            if str(lyr.connectionProperties['dataset']).endswith(".shp"):
                                dir_new = self.dir_map_shp
                            else:
                                dir_new = self.dir_map_ras
                                visibility = False
                                if "max_lf" in lyr.connectionProperties['dataset']:
                                    visibility = True  # only activate max lf raster visibility
                                    try:
                                        lyr.symbology = sym_lyr.symbology
                                    except:
                                        print("Invalid symbology")
                                    __temp_ras__ = arcpy.Raster(dir_new + lyr.connectionProperties['dataset'])
                                    self.raster_extent = __temp_ras__.extent
                                    del __temp_ras__
                                    self.logger.info("        * will be used for mapping extent")
                            lyr.updateConnectionProperties({'connection_info': {'database': dir_old}},
                                                           {'connection_info': {'database': dir_new}},
                                                           auto_update_joins_and_relates=True, validate=False)
                        lyr.visible = visibility
                if self.map_type == "mt":
                    extent_set = False
                    for lyr in self.m.listLayers():
                        if not ("background" in lyr.name.lower()):
                            dir_old = lyr.connectionProperties['connection_info']['database']
                            ras_connection = lyr.connectionProperties['dataset']
                            lyr.updateConnectionProperties({'connection_info': {'database': dir_old}},
                                                           {'connection_info': {'database': self.dir_map_ras}},
                                                           auto_update_joins_and_relates=True, validate=False)
                            for ras in self.map_list:
                                # if str(ras).split(".")[0] in str(ras_connection):
                                lyr.updateConnectionProperties({'dataset': str(ras_connection)},
                                                               {'dataset': str(ras)},
                                                               auto_update_joins_and_relates=True, validate=False)
                                if not extent_set:
                                    self.raster_extent = self.get_raster_extent(self.dir_map_ras + ras)
                                    self.logger.info("        * %s will be used for mapping extent" % str(ras))
                                    extent_set = True
                        lyr.visible = True

                self.aprx.save()

                if direct_mapping:
                    self.logger.info("    * Calling PDF map creator ...")
                    self.make_pdf_maps(map_name, extent="raster")

            except arcpy.ExecuteError:
                self.logger.info(arcpy.GetMessages(2))
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                self.logger.info("ERROR: Map layout preparation failed.")
                self.error = True
            except:
                self.logger.info("ERROR: Map layout preparation failed.")
                self.error = True

    def zoom2map(self, xy):
        # type(xy) = list
        try:
            x = float(xy[0])
            y = float(xy[1])
        except:
            self.logger.info("ERROR: Mapping could not assign xy-values. Undefined zoom.")
            x = 6719978.531
            y = 2203223.401

        local_frame = self.map_layout.listElements("mapframe_element")[0]
        try:
            new_extent = local_frame.getLayerExtent(self.m.listLayers()[0])  # dummy extent assignment
        except:
            new_extent = self.raster_extent
        try:
            new_extent.XMin, new_extent.YMin = x - 0.5 * self.dx, y - 0.5 * self.dy
            new_extent.XMax, new_extent.YMax = x + 0.5 * self.dx, y + 0.5 * self.dy
            local_frame.camera.setExtent = new_extent
            local_frame.panToExtent(new_extent)
            self.aprx.save()
        except:
            self.logger.info("WARNING: Cannot zoom to defined extent.")

    def __call__(self):
        pass
