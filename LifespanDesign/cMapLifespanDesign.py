# !/usr/bin/python
try:
    from cReadInpLifespan import *
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/fGlobal.py, cReadInpLifespan.py).")

try:
    import arcpy
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy).")


class Mapper:
    def __init__(self, condition, *args):
        # condition = [str] state of planning situation, e.g., "2008"
        # args[0] alternative raster input directory - if empty: uses standard output
        # args[1] alternative layout input directory - if empty: uses standard lyt-input

        # get and make directories
        self.condition = condition
        try:
            if not(args[0].__len__() < 2):
                self.ras_input_dir = args[0]
            else:
                self.ras_input_dir = os.path.dirname(
                    os.path.realpath(__file__)) + "\\Output\\Rasters\\" + self.condition + "\\"
            fg.chk_dir(self.ras_input_dir)
        except:
            self.ras_input_dir = os.path.dirname(
                os.path.realpath(__file__)) + "\\Output\\Rasters\\" + self.condition + "\\"

        try:
            self.output_mxd_dir = args[1]
        except:
            self.output_mxd_dir = os.path.dirname(
                os.path.realpath(__file__)) + "\\Output\\Mapping\\" + self.condition + "\\Layouts\\"
        self.ref_lyt_dir = os.path.dirname(os.path.realpath(__file__)) + "\\Output\\Mapping\\.ReferenceLayouts\\"
        self.output_dir = os.path.dirname(os.path.realpath(__file__)) + "\\Output\\Mapping\\" + self.condition + "\\"

        fg.chk_dir(self.output_dir)
        fg.chk_dir(self.output_mxd_dir)

        info = Info()  # gets information from spatial input file
        # define xy map center point s in feet according to mapping_details.xlsx
        self.xy_center_points = info.coordinates_read()

        self.map_no = self.xy_center_points.__len__()
        self.scale = info.get_map_scale()   # (--) format specific
        self.dx = info.get_map_extent("x")  # 7000.00   # (ft) frame width
        self.dy = info.get_map_extent("y")  # 5333.33   # (ft) frame height
        self.resolution = 96  # px/in -- value increases automatically if map extents are modified

        self.error = False

    def choose_ref_layer(self, feature_type):
        # feature_type is either a raster or an mxd file name
        # type(feature_type) == str
        if type(feature_type) == str:
            if feature_type[0:2] == 'lf':
                ref_layer_name = "lf_sym"
            if feature_type[0:2] == 'ds':
                ref_layer_name = "ds_sym"

        if not('ref_layer_name' in locals()):
            # ensure that at least some source layer is used
            self.logger.info("WARNING: Raster / layout identification failed. Using lifespan layer layout (default).")
            ref_layer_name = "lf_sym"

        return ref_layer_name

    def choose_ref_layout(self, raster_name):
        # type(raster_name) == str
        if type(raster_name) == str:
            if raster_name[0:2] == "lf":
                ref_layout_name = "layout_lf.mxd"
            if raster_name[0:2] == "ds":
                if "bio" in raster_name.lower():
                    ref_layout_name = "layout_ds_bio.mxd"
                if ("dcf" in raster_name.lower()) or ("dcr" in raster_name.lower()) or ("dst" in
                        raster_name.lower()) or ("grav" in raster_name.lower()) or ("rocks" in raster_name.lower()):
                    ref_layout_name = "layout_ds_Dcr.mxd"
                if "fines" in raster_name.lower():
                    if "15" in raster_name.lower():
                        ref_layout_name = "layout_ds_FS_D15.mxd"
                    if "85" in raster_name.lower():
                        ref_layout_name = "layout_ds_FS_D85.mxd"
                    if not ('ref_layout_name' in locals()):
                        # ensure assignment (habitat would not recognize)
                        ref_layout_name = "layout_ds_FS_D85.mxd"
                if "sidech" in raster_name.lower():
                    ref_layout_name = "layout_ds_SeS0.mxd"
                if "sideca" in raster_name.lower():
                    ref_layout_name = "layout_ds_sideca.mxd"
                if "widen" in raster_name.lower():
                    ref_layout_name = "layout_ds_widen.mxd"
                if "wood" in raster_name.lower():
                    ref_layout_name = "layout_ds_Dw.mxd"

        if not('ref_layout_name' in locals()):
            # ensure that at least some layout is used
            try:
                raster_name = str(raster_name)
            except:
                raster_name = "ERROR: Bad Raster type."
            self.error = True
            self.logger.info("ERROR: Raster identification failed. Omitting layout creation of " + str(raster_name) + ".")
            ref_layout_name = ""

        return ref_layout_name

    def make_pdf_maps(self, *args, **kwargs):
        # accepts args[0] as alternative directory for input layouts (mxd_dir)
        self.start_logging()
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("PDF - MAPPING")
        self.logger.info("Map format: ANSI E landscape (w = 44in, h = 34in)")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("                                                     ")
        self.logger.info(" >> Mapping layouts from:")
        self.logger.info("    " + str(self.output_mxd_dir))

        try:
            length = args[0].__len__()
            if length > 3:
                self.output_mxd_dir = args[0]
                fg.chk_dir(self.ras_input_dir)
        except:
            pass

        try:
            for k in kwargs.items():
                if "extent" in k[0]:
                    if not (k[1] == "MAXOF"):
                        self.logger.info(" >> Special reach extents provided..")
                        self.logger.info("    -->> Overwriting mapping.inp center point definitions.")
                        self.make_xy_centerpoints(k[1])
        except:
            pass

        arcpy.env.workspace = self.output_mxd_dir
        arcpy.env.overwriteOutput = True

        mxd_list = arcpy.ListFiles("*.mxd")    # gets all layout in arcpy.env.workspace

        for layout in mxd_list:
            self.logger.info(" >> Preparing map assembly: " + str(layout[:-4]) + ".pdf (takes a while) ...")
            try:
                __outputPDF__ = arcpy.mapping.PDFDocumentCreate(self.output_dir + str(layout[:-4]) + ".pdf")
                # Instantiate mxd and df -- both need to be global variables here!!
                self.mxd = arcpy.mapping.MapDocument(self.output_mxd_dir + layout)
                self.df = arcpy.mapping.ListDataFrames(self.mxd)[0]

                # handle legend
                styleItem = arcpy.mapping.ListStyleItems(self.ref_lyt_dir + "legend.ServerStyle", "Legend Items")
                legend = arcpy.mapping.ListLayoutElements(self.mxd, "LEGEND_ELEMENT", "Legend")[0]
                legend.autoAdd = True
                ref_lyr_name = self.choose_ref_layer(str(self.mxd.title[:-4]))  # cf definition in prepare_maps
                sym_lyr = arcpy.mapping.ListLayers(self.mxd, ref_lyr_name, self.df)[0]
                arcpy.mapping.RemoveLayer(self.df, sym_lyr)
                act_lyr = arcpy.mapping.ListLayers(self.mxd, str(legend.items[0]), self.df)[0]
                legend.updateItem(act_lyr, styleItem[0])  # deactivate for external mapping

                arcpy.RefreshActiveView()
                # self.mxd.save()
                # legend.removeItem(leg.items[1])

                __tempPDFs__ = []
                __count__ = 0
                for xy in self.xy_center_points:
                    __count__ += 1
                    self.zoom2map(xy)
                    fig_name = "fig_"+ str(layout) + "_" + "%02d" % (__count__,)
                    __PDFpath__ = self.output_dir + fig_name + "_temp.pdf"
                    arcpy.mapping.ExportToPDF(self.mxd, __PDFpath__, image_compression="ADAPTIVE",
                                              resolution=self.resolution)
                    # arcpy.mapping.ExportToJPEG(self.mxd, __PDFpath__)
                    __outputPDF__.appendPages(str(__PDFpath__))
                    __tempPDFs__.append(__PDFpath__)  # remember temp names to remove later on
                __outputPDF__.saveAndClose()

                for deletePDF in __tempPDFs__:
                    try:
                        os.remove(deletePDF)
                    except:
                        self.logger.info("WARNING: Could not clean up PDF map temp_pages.")

                del self.mxd, self.df

                self.logger.info(" >> Done. Map-PDF prepared in:")
                self.logger.info("    " + self.output_dir)

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
        self.logger.info("    --   New X center: " + str(self.xy_center_points[0][0]))
        self.logger.info("    --   New Y center: " + str(self.xy_center_points[0][1]))
        self.logger.info("    --   New map width: " + str(self.dx))
        self.logger.info("    --   New map height: " + str(self.dy))
        self.resolution = 192  # improve resolution of single maps

    def prepare_layout(self):
        self.start_logging()
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("PREPARE MAPPING")
        self.logger.info("Map format: ANSI E landscape (w = 44in, h = 34in)")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("                                                     ")

        arcpy.env.workspace = self.ras_input_dir
        arcpy.env.overwriteOutput = True

        rasterlist = arcpy.ListRasters("*", "GRID")  # gets all rasters in arcpy.env. workspace
        if rasterlist.__len__() < 1:
            rasterlist = arcpy.ListRasters("*", "tif")

        for raster in rasterlist:
            self.logger.info(" >> Preparing map layout: " + self.output_dir + str(raster).split(".tif")[0] + ".mxd")

            # choose layout
            ref_layout_name = self.choose_ref_layout(str(raster))
            ref_lyr_name = self.choose_ref_layer(str(raster))
            try:
                mxd = arcpy.mapping.MapDocument(self.ref_lyt_dir + ref_layout_name)
                df = arcpy.mapping.ListDataFrames(mxd)[0]

                lf_sourceLayer = arcpy.mapping.ListLayers(mxd, ref_lyr_name, df)[0]
                __ras_lyr_name__ = "temp.lyr"
                full_ras = arcpy.Raster(self.ras_input_dir + str(raster))

                __ras_lyr__ = arcpy.MakeRasterLayer_management(full_ras, __ras_lyr_name__[:-4], "#", "", "#")
                arcpy.SaveToLayerFile_management(__ras_lyr__, self.ref_lyt_dir + __ras_lyr_name__)
                __lyr_file__ = arcpy.mapping.Layer(self.ref_lyt_dir + __ras_lyr_name__)
                arcpy.mapping.InsertLayer(df, lf_sourceLayer, __lyr_file__, "BEFORE")  # Insert New

                arcpy.mapping.UpdateLayer(df, __lyr_file__, lf_sourceLayer)  # Update symbology with example lyr-file
                arcpy.RefreshActiveView()
                arcpy.RefreshTOC()
                mxd.title = str(raster)  # necessary for later identification of make_maps
                if os.path.isfile(os.path.join(self.output_mxd_dir, str(raster).split(".tif")[0] + ".mxd")):
                    self.logger.info("WARNING: Overwriting existing version of " + str(raster).split(".tif")[0] + ".mxd")
                mxd.saveACopy(self.output_mxd_dir + str(raster).split(".tif")[0] + ".mxd")
                del mxd, df,  __lyr_file__, __ras_lyr__

            except arcpy.ExecuteError:
                self.logger.info(arcpy.GetMessages(2))
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
                self.logger.info("ERROR: Map layout preparation failed.")
                self.error = True
            except:
                self.logger.info("ERROR: Map layout preparation failed.")
                self.error = True
            try:
                # arcpy.Delete_management(__ras_lyr_name__)
                arcpy.Delete_management(self.ref_lyt_dir + __ras_lyr_name__)
                self.logger.info(" >> Clearing temp.lyr (arcpy.Delete_management).")
                self.logger.info(" >> Done.")

            except:
                self.logger.info("WARNING: Could not clear temp.lyr")
                self.error = True

    def start_logging(self):
        self.logger = logging.getLogger("mapper")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        logfilenames=["mapper.log"]
        # create console handler and set level to info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        # create error file handler and set level to error
        err_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[0]), "w", encoding=None, delay="true")
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(formatter)
        self.logger.addHandler(err_handler)
        # create debug file handler and set level to debug
        debug_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[0]), "w")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)
        self.logger.info("LifespanDesign.Mapper() initiated.")

    def stop_logging(self, *args):
        # takes optional arguments args[0] that activates instruction print for layout handling
        try:
            if args[0]:
                layout = True
            else:
                layout = False
        except:
            layout = False

        if layout and not self.error:
            self.logger.info("   ")
            self.logger.info(" >> Layouts (.mxd files) prepared in:")
            self.logger.info("      " + self.output_mxd_dir)
            self.logger.info("   ")
            self.logger.info(" >> For obtaining PDF maps do the following:")
            self.logger.info("      1) Open layouts (mxd) in ArcMap Desktop and adapt symbology of sym layer.")
            self.logger.info("      2) Save layouts (overwrite existing) without committing any other change.")
            self.logger.info("      3) Back in Python console: Run feature_analysis.map_making(condition).")
            self.logger.info("      ")
            self.logger.info(" >> See you soon!")
        if layout and self.error:
            self.logger.info(" >> Invalid files. Review layout template, error and warning messages.")

        # stop logging and release logfile
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def zoom2map(self, xy):
        # type(xy) = list
        try:
            x = float(xy[0])
            y = float(xy[1])
        except:
            self.logger.info("ERROR: Mapping could not assign xy-values. Undefined zoom.")
            x = 6719978.531
            y = 2203223.401

        newExtent = self.df.extent
        newExtent.XMin, newExtent.YMin = x - 0.5 * self.dx, y - 0.5 * self.dy
        newExtent.XMax, newExtent.YMax = x + 0.5 * self.dx, y + 0.5 * self.dy
        self.df.extent = newExtent
        arcpy.RefreshActiveView()

    def __call__(self):
        pass

