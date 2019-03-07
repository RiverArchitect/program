# !/usr/bin/python
# Desc.: Provides classes
try:
    # load relevant files from lifespan_design
    import os, sys, logging
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
    import cDefinitions as cdef
    import cTerrainIO as cio
    import cModifyTerrain as cmt
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/fGlobal.py, cReadActionInput.py).")

try:
    import arcpy
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy).")


class Mapper:
    def __init__(self, condition, feature_id):
        # initiate logger
        self.condition = condition
        self.start_logging("mapping")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("PDF - MAPPING")
        self.logger.info("Map format: ANSI E landscape (w = 44in, h = 34in)")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("                                                     ")

        # get and make directories
        self.mxd_templates_dir = os.path.dirname(
                            os.path.realpath(__file__)) + "\\Input\\Layouts\\" + self.condition + "\\"
        self.output_map_dir = os.path.dirname(os.path.realpath(__file__)) + "\\Output\\Maps\\" + self.condition + "\\"
        self.output_mxd_dir = os.path.dirname(
            os.path.realpath(__file__)) + "\\Output\\Layouts\\" + self.condition + "\\"
        fg.chk_dir(self.output_map_dir)
        fg.chk_dir(self.output_mxd_dir)
        
        self.feature_id = feature_id
        self.features = cdef.Features()

        self.reader = cio.Read()  # gets information from spatial input file
        self.reaches = cdef.Reaches()
        self.previous_run = False  # class sets this tu True if a Mapper object method is called in a loop
        self.tempPDFs = []

        self.dx = float()
        self.dy = float()
        self.error = False

    def assign_reach_row(self, internal_reach_id):
        digit0 = int(internal_reach_id[-2])
        digit1 = int(internal_reach_id[-1])
        if not(digit0 > 0):
            row_no = self.reader.row_start + digit1 - 0
        else:
            digit_str = str(digit0) + str(digit1)
            row_no = self.reader.row_start + int(digit_str)
        return row_no

    def choose_ref_layout(self, feature_id, volume_type):
        # type(feature_id) == str
        self.logger.info("  * Retrieving reference layout for feature ID: " + str(feature_id) + ".")
        if feature_id in self.features.id_list:
            if volume_type < 0:
                ref_layout_name = "volume_" + str(feature_id) + "_neg.mxd"
            else:
                ref_layout_name = "volume_" + str(feature_id) + "_pos.mxd"
            return ref_layout_name
        else:
            self.logger.info("ERROR: No layout template found (feature ID: " + str(feature_id) + ".")
            self.error = True
            return -1

    def finalize_map(self):
        try:
            self.outputPDF.saveAndClose()
        except:
            self.error = True
            self.logger.info("ERROR: Failed to save PDF map assembly.")

        for deletePDF in self.tempPDFs:
            try:
                os.remove(deletePDF)
            except:
                pass

        self.previous_run = False  # reset

        self.logger.info(" >> Map-PDF prepared in:")
        self.logger.info("    " + self.output_map_dir)
        self.logger.info("MAPPING FINISHED.")

        self.stop_logging()

    def map_custom(self, input_ras_dir, *args):
        # args[0] = -1 / +1 tells volume-difference maps whether volume is negative (excavation) or positive (fill)
        try:
            volume_type = int(args[0])
        except:
            # default is -1 (excavation)
            volume_type = -1
        if volume_type < 0:
            self.logger.info(" >> Mapping excavation area (custom).")
        else:
            self.logger.info(" >> Mapping fill area (custom).")

        # identifies the extent of a custom raster stored in input_ras_dir
        arcpy.env.workspace = input_ras_dir

        all_rasters = arcpy.ListRasters()
        for ras in all_rasters:
            if ("dem" in str(ras)) or ("cus" in str(ras)) or ("mod" in str(ras)):
                _temp_ras_ = arcpy.Raster(input_ras_dir + ras)
                xy_extents = [_temp_ras_.extent.XMin, _temp_ras_.extent.XMax, _temp_ras_.extent.YMin, _temp_ras_.extent.YMax]
                break
        if not("xy_extents" in locals()):
            self.logger.info("ERROR: No custom (DEM/feature) raster found.")
            xy_extents = 0

        try:
            # this is different from map_reach!
            center_point_x = (float(xy_extents[0]) + float(xy_extents[1])) / 2
            center_point_y = (float(xy_extents[2]) + float(xy_extents[3])) / 2
            self.dx = abs(float(xy_extents[0]) - float(xy_extents[1]))
            self.dy = abs(float(xy_extents[2]) - float(xy_extents[3]))
        except:
            self.error = True
            self.logger.info("ERROR: Invalid xy-extents.")

        arcpy.env.workspace = self.output_mxd_dir
        arcpy.env.overwriteOutput = True

        # assign layout
        mxd_name = self.choose_ref_layout("cust", volume_type)
        map_name = mxd_name.split(".")[0] + ".pdf"
        mxd_file, pdf_file = self.prepare_mapping(mxd_name, map_name)

        self.logger.info(" >> Preparing map: " + map_name + " (takes a while) ...")
        try:
            # __outputPDF__ = arcpy.mapping.PDFDocumentCreate(self.output_map_dir + map_name)
            # Instantiate mxd and df -- both need to be global variables here!!
            self.mxd = arcpy.mapping.MapDocument(mxd_file)
            self.df = arcpy.mapping.ListDataFrames(self.mxd)[0]

            try:
                self.zoom2map(center_point_x, center_point_y)
            except:
                self.error = True
                self.logger.info("ERROR: Invalid x-y coordinates in reach spreadsheet.")

            try:
                arcpy.mapping.ExportToPDF(self.mxd, self.output_map_dir + "temp_" + map_name,
                                          image_compression="ADAPTIVE", resolution=96)
            except:
                self.error = True
                self.logger.info("ERROR: Could not create " + str(map_name))
            # arcpy.mapping.ExportToJPEG(self.mxd, __PDFpath__)
            try:
                self.outputPDF.appendPages(self.output_map_dir + "temp_" + map_name)
                self.tempPDFs.append(self.output_map_dir + "temp_" + map_name) # remember temp names to remove later on
            except:
                self.error = True
                self.logger.info("ERROR: Could not append PDF page " + str(map_name) + " to map assembly.")

            del self.mxd

        except arcpy.ExecuteError:
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
            self.logger.info("ERROR: Mapping failed (" + map_name + ").")
            self.error = True

        except:
            self.logger.info("ERROR: Mapping failed (" + map_name + ").")
            self.error = True

    def map_reach(self, reach_id, feature_id, *args):
        # args[0] = -1 / +1 tells volume-difference maps whether volume is negative (excavation) or positive (fill)
        try:
            volume_type = int(args[0])
        except:
            # default is -1 (excavation)
            volume_type = -1
        if volume_type < 0:
            suffix = "_excv"
            self.logger.info(" >> Mapping excavation area (" + str(feature_id) + ").")
        else:
            suffix = "_fill"
            self.logger.info(" >> Mapping fill area (" + str(feature_id) + ").")
        # define xy map center point s in feet according to mapping_details.xlsx
        internal_reach_id = self.reaches.dict_id_int_id[reach_id]
        xy_extents = self.reader.get_reach_coordinates(internal_reach_id)
        # this is different than in map_custom!
        center_point_x = (float(xy_extents[0]) + float(xy_extents[2])) / 2
        center_point_y = (float(xy_extents[1]) + float(xy_extents[3])) / 2
        self.dx = abs(float(xy_extents[2]) - float(xy_extents[0]))
        self.dy = abs(float(xy_extents[3]) - float(xy_extents[1]))

        arcpy.env.workspace = self.output_mxd_dir
        arcpy.env.overwriteOutput = True

        # assign layout and pdf
        mxd_name = self.choose_ref_layout(feature_id, volume_type)
        map_name = str(feature_id) + suffix + ".pdf"
        mxd_file, pdf_file = self.prepare_mapping(mxd_name, map_name)
        __temp_pdf__ = self.output_map_dir + "temp_" + str(feature_id) + "_" + map_name

        self.logger.info(" >> Preparing map page: " + map_name + " -- reach: " + str(reach_id))
        try:
            # Instantiate mxd and df -- both need to be global variables here!!
            self.mxd = arcpy.mapping.MapDocument(mxd_file)
            self.df = arcpy.mapping.ListDataFrames(self.mxd)[0]

            try:
                self.logger.info(" >> Zooming to reach ...")
                self.zoom2map(center_point_x, center_point_y)
                arcpy.RefreshActiveView()
                arcpy.RefreshTOC()
            except:
                self.error = True
                self.logger.info("ERROR: Invalid x-y coordinates in reach spreadsheet.")

            try:
                self.logger.info(" >> Exporting page ...")
                arcpy.mapping.ExportToPDF(self.mxd, __temp_pdf__,
                                          image_compression="ADAPTIVE", resolution=96)

            except:
                self.error = True
                self.logger.info("ERROR: Could not create " + str(map_name))
            # arcpy.mapping.ExportToJPEG(self.mxd, __PDFpath__)

            try:
                self.outputPDF.appendPages(__temp_pdf__)
                self.tempPDFs.append(__temp_pdf__)  # remember temp names to remove later on

            except:
                self.error = True
                self.logger.info("ERROR: Could not append PDF page " + str(map_name) + " to map assembly.")

        except arcpy.ExecuteError:
            self.logger.info(arcpy.GetMessages(2))
            arcpy.AddError(arcpy.GetMessages(2))
            self.logger.info("ERROR: Mapping failed (" + map_name + ").")
            self.error = True

        except:
            self.logger.info("ERROR: Mapping failed (" + map_name + ").")
            self.error = True

        self.logger.info("OK.")
        self.logger.info("")

    def prepare_mapping(self, mxd_template, map_name):
        arcpy.env.overwriteOutput = True
        try:
            if not self.previous_run:
                if os.path.isfile(os.path.join(self.output_mxd_dir, mxd_template)):
                    self.logger.info("  * Using existing version of " + str(mxd_template))
                else:
                    mxd = arcpy.mapping.MapDocument(self.mxd_templates_dir + mxd_template)
                    mxd.saveACopy(self.output_mxd_dir + mxd_template)
                self.outputPDF = arcpy.mapping.PDFDocumentCreate(self.output_map_dir + map_name)
                self.previous_run = True
            self.logger.info(" >> Using map layout: " + self.output_mxd_dir + str(mxd_template))
            return self.output_mxd_dir + mxd_template, self.output_map_dir + map_name

        except arcpy.ExecuteError:
            self.logger.info(arcpy.GetMessages(2))
            self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            self.logger.info("ERROR: Map layout preparation failed.")
            self.error = True
            return "None", "None"

        except:
            self.logger.info("ERROR: Map layout preparation failed.")
            self.error = True
            return "None", "None"

    def start_logging(self, log_file_name):
        self.logger = logging.getLogger(log_file_name + ".log")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        logfilenames = ["error.log", "mapping.log"]
        for fn in logfilenames:
            if os.path.isfile(fn):
                print("Overwriting old logfiles.")
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
        debug_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[1]), "w")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)
        self.logger.info("modify_terrain.Mapper() initiated.")

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
        if layout and self.error:
            self.logger.info(" >> Invalid files. Review layout template, error and warning messages.")

        # stop logging and release logfile
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def zoom2map(self, x, y):
        # type(xy) = list
        try:
            x = float(x)
            y = float(y)
        except:
            self.logger.info("ERROR: Mapping could not assign xy-values. Undefined zoom.")
            x = 6719978.531
            y = 2203223.401

        new_extent = self.df.extent
        new_extent.XMin, new_extent.YMin = x - 0.5 * self.dx, y - 0.5 * self.dy
        new_extent.XMax, new_extent.YMax = x + 0.5 * self.dx, y + 0.5 * self.dy
        self.df.extent = new_extent
        arcpy.RefreshActiveView()

    def __call__(self):
        print("Class Info: <type> = Mapper (Module: ModifyTerrain)")

