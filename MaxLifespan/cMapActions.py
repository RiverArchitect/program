# !/usr/bin/python
# Desc.: Provides classes
try:
    # load relevant files from LifespanDesign
    import os, sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
    from cReadActionInput import *
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py, cReadActionInput.py).")

try:
    import arcpy
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy).")


class Mapper:
    def __init__(self, condition):
        # get and make directories
        self.condition = condition
        self.mxd_templates_dir = os.path.dirname(os.path.realpath(__file__)) + "\\.templates\\layouts\\"
        self.output_map_dir = os.path.dirname(os.path.realpath(__file__)) + "\\Output\\Maps\\" + self.condition + "\\"
        self.output_mxd_dir = os.path.dirname(os.path.realpath(__file__)) + "\\Output\\Layouts\\" + self.condition + "\\"
        fg.chk_dir(self.output_map_dir)
        fg.chk_dir(self.output_mxd_dir)

        info = Info()  # gets information from spatial input file
        # define xy map center point s in feet according to mapping_details.xlsx
        self.xy_center_points = info.coordinates_read()

        self.map_no = self.xy_center_points.__len__()
        self.scale = info.get_map_scale()   # (--) format specific
        self.dx = info.get_map_extent("x")  # 7000.00   # (ft) frame width
        self.dy = info.get_map_extent("y")  # 5333.33   # (ft) frame height

        self.error = False

    def choose_ref_layout(self, feature_type):
        # type(feature_type) == str
        if type(feature_type) == str:
            if feature_type == "terraforming":
                ref_layout_name = "terraforming.mxd"
            if feature_type == "plantings":
                ref_layout_name = "plantings.mxd"
            if feature_type == "bioengineering":
                ref_layout_name = "bioengineering.mxd"
            if feature_type == "maintenance":
                ref_layout_name = "maintenance.mxd"

        if not('ref_layout_name' in locals()):
            # ensure that at least some layout is used
            ref_layout_name = "terraforming.mxd"
            self.error = True
            self.logger.info("ERROR: Feature identification failed. Using default layout.")
            ref_layout_name = ""
        return ref_layout_name

    def make_pdf_maps(self, *args):
        # accepts args[0] as alternative directory for input layouts (mxd_dir)
        self.start_logging()
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("PDF - MAPPING")
        self.logger.info("Map format: ANSI E landscape (w = 44in, h = 34in)")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("                                                     ")

        try:
            length = args[0].__len__()
            if length > 3:
                self.output_mxd_dir = args[0]
                # fg.chk_dir(self.input_ras_dir)
        except:
            pass

        arcpy.env.workspace = self.output_mxd_dir
        arcpy.env.overwriteOutput = True

        mxd_list = arcpy.ListFiles("*.mxd")  # gets all layout in arcpy.env.workspace

        for layout in mxd_list:
            self.logger.info(" >> Preparing map assembly: " + str(layout[:-4]) + ".pdf (takes a while) ...")
            try:
                __outputPDF__ = arcpy.mapping.PDFDocumentCreate(self.output_map_dir + str(layout[:-4]) + ".pdf")
                # Instantiate mxd and df -- both need to be global variables here!!
                self.mxd = arcpy.mapping.MapDocument(self.output_mxd_dir + layout)
                self.df = arcpy.mapping.ListDataFrames(self.mxd)[0]

                __tempPDFs__ = []
                __count__ = 0
                for xy in self.xy_center_points:
                    __count__ += 1
                    try:
                        self.zoom2map(xy)
                    except:
                        self.logger.info("ERROR: Invalid x-y coordinates in mapping.inp")
                    fig_name = "fig_"+ str(layout) + "_" + "%02d" % (__count__,)
                    __PDFpath__ = self.output_map_dir + fig_name + "_temp.pdf"
                    try:
                        arcpy.mapping.ExportToPDF(self.mxd, __PDFpath__, image_compression = "ADAPTIVE", resolution = 96)
                    except:
                        self.error = True
                        self.logger.info("ERROR: Could not export PDF page no. " + str(__count__))
                    # arcpy.mapping.ExportToJPEG(self.mxd, __PDFpath__)
                    try:
                        __outputPDF__.appendPages(str(__PDFpath__))
                        __tempPDFs__.append(__PDFpath__) # remember temp names to remove later on
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

                del self.mxd

                self.logger.info(" >> Done. Map-PDF prepared in:")
                self.logger.info("    " + self.output_map_dir)

            except arcpy.ExecuteError:
                self.logger.info(arcpy.GetMessages(2))
                arcpy.AddError(arcpy.GetMessages(2))
                self.logger.info("ERROR: Mapping failed.")
                self.error = True
            except:
                self.logger.info("ERROR: Mapping failed.")
                self.error = True

    def prepare_layout(self, feature_type):
        self.start_logging()
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("PREPARE MAPPING")
        self.logger.info("Map format: ANSI E landscape (w = 44in, h = 34in)")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
        self.logger.info("                                                     ")

        self.logger.info(" >> Preparing map layout: " + self.output_mxd_dir + str(feature_type) + ".mxd")
        arcpy.env.overwriteOutput = True
        try:
            ref_layout_name = self.choose_ref_layout(str(feature_type))
            mxd = arcpy.mapping.MapDocument(self.mxd_templates_dir + ref_layout_name)
            arcpy.RefreshActiveView()
            arcpy.RefreshTOC()
            if os.path.isfile(os.path.join(self.output_mxd_dir, ref_layout_name)):
                self.logger.info("WARNING: Overwriting existing version of " + str(ref_layout_name))
            mxd.saveACopy(self.output_mxd_dir + ref_layout_name)

        except arcpy.ExecuteError:
            self.logger.info(arcpy.GetMessages(2))
            self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            self.logger.info("ERROR: Map layout preparation failed.")
            self.error = True
        except:
            self.logger.info("ERROR: Map layout preparation failed.")
            self.error = True

    def start_logging(self):
        self.logger = logging.getLogger("mapper")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        logfilenames = ["error.log", "logfile.log"]
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
        self.logger.info("max_lifespan.Mapper() initiated.")

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

    def zoom2map(self, xy):
        # type(xy) = list
        try:
            x = float(xy[0])
            y = float(xy[1])
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
        print("Class Info: <type> = Mapper (Module: MaxLifespan)")

