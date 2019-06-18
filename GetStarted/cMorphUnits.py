try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fGl
    import cInputOutput as cIO
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: RP/fGlobal).")


class MU:
    def __init__(self, unit_system, *args, **kwargs):
        # args[0] optional out_dir -- otherwise: out_dir = script_dir
        # kwargs
        self.logger = logging.getLogger("logfile")
        self.cache = os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\"
        self.mu_xlsx_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\templates\\morphological_units.xlsx"
        self.logger.info("->> Reading Morphological Units (%s)" % self.mu_xlsx_dir)
        fGl.chk_dir(self.cache)

        try:
            self.out_dir = args[0]
        except:
            self.out_dir = os.path.dirname(os.path.realpath(__file__)) + "\\"

        if unit_system == "us":
            self.logger.info(" * converting Rasters to U.S. customary units")
            self.uc = 3.2808399
        else:
            self.logger.info(" * using SI metric Raster units")
            self.uc = 1.0

        self.mu_dict = {}
        self.mu_h_lower = {}
        self.mu_h_upper = {}
        self.mu_u_lower = {}
        self.mu_u_upper = {}
        self.read_mus()
        self.raster_dict = {}
        self.ras_mu = 0

    def calculate_mu(self, path2h_ras, path2u_ras):
        try:
            arcpy.CheckOutExtension('Spatial')  # check out license
            arcpy.gp.overwriteOutput = True
            arcpy.env.workspace = self.cache
            arcpy.env.extent = "MAXOF"

            try:
                self.logger.info(" * Reading input Rasters ...")
                h = Float(arcpy.Raster(path2h_ras))
                u = Float(arcpy.Raster(path2u_ras))
                self.logger.info(" * OK")
            except:
                self.logger.info("ERROR: Could not find / access input Rasters\n{0}\n{1}.".format(path2h_ras, path2u_ras))
                return True
            try:
                arcpy.env.extent = u.extent
            except:
                pass

            try:
                self.logger.info(" * Evaluating morphological units ...")
                for mu, mu_id in self.mu_dict.items():
                    self.logger.info("   - {0} (ID={1})".format(str(mu), str(mu_id)))
                    self.raster_dict.update({mu: Con(h > 0, Con(((u >= self.mu_u_lower[mu]) & (u < self.mu_u_upper[mu]) & (h >= self.mu_h_lower[mu]) & (h < self.mu_h_upper[mu])), mu_id))})
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: MU calculation failed.")
                return True

            try:
                self.logger.info(" * superimposing single MU Rasters ...")
                self.ras_mu = CellStatistics(fGl.dict_values2list(self.raster_dict.values()), "MAXIMUM", "DATA")
                self.logger.info(" * OK")
            except arcpy.ExecuteError:
                self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
            except Exception as e:
                self.logger.info(arcpy.GetMessages(2))
            except:
                self.logger.info("ERROR: MU update failed.")
                return True

            # arcpy.CheckInExtension('Spatial')
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: MU calculation failed.")
            return True

    def clean_up(self):
        try:
            self.logger.info(" * Cleaning up ...")
            del self.ras_mu, self.raster_dict
            fGl.clean_dir(self.cache)
            fGl.rm_dir(self.cache)
            self.logger.info(" * OK")
        except:
            self.logger.info(" * Failed to clean up .cache folder.")

    def read_mus(self):
        mu_xlsx = cIO.Read(self.mu_xlsx_dir)
        for i in range(6, 44):
            # loop over all mu-rows
            if not (i == 23):
                # jump over floodplain table headers
                mu_type = str(mu_xlsx.ws["D" + str(i)].value)
                try:
                    mu_ID = int(mu_xlsx.ws["E" + str(i)].value)
                except:
                    continue
                if not (mu_type.lower() == "none"):
                    try:
                        self.mu_h_lower.update({mu_type: float(mu_xlsx.ws["F" + str(i)].value) * self.uc})  # add mu name and lower depth thresh.
                        self.mu_h_upper.update({mu_type: float(mu_xlsx.ws["G" + str(i)].value) * self.uc})  # add mu name and upper depth thresh.
                        self.mu_u_lower.update({mu_type: float(mu_xlsx.ws["H" + str(i)].value) * self.uc})  # add mu name and lower velocity thresh.
                        self.mu_u_upper.update({mu_type: float(mu_xlsx.ws["I" + str(i)].value) * self.uc})  # add mu name and upper velocity thresh.
                        self.mu_dict.update({mu_type: mu_ID})  # add mu name and ID to dict
                        self.logger.info(" * added %s." % str(mu_type))
                    except:
                        self.logger.info(" * omitted {0} (no depth / velocity thresholds provided in row {1}).".format(mu_type, str(i)))
        mu_xlsx.close_wb()

    def save_mu(self, *args):
        # args[0] can be an optional output directory
        try:
            self.out_dir = args[0]
        except:
            pass
        self.logger.info("")
        self.logger.info(" * SAVING ... ")
        arcpy.CheckOutExtension('Spatial')  # check out license
        arcpy.gp.overwriteOutput = True
        arcpy.env.workspace = self.cache
        arcpy.env.extent = "MAXOF"
        arcpy.CheckInExtension('Spatial')
        try:
            self.logger.info(" * Converting MU IDs to strings:")

            self.logger.info("   >> Converting raster to points ...")
            pts = arcpy.RasterToPoint_conversion(self.ras_mu, self.cache + "pts_del.shp")

            self.logger.info("   >> Converting numbers to strings ...")
            arcpy.AddField_management(pts, "MU", "TEXT")
            expression = "inverse_dict = " + fGl.dict2str(self.mu_dict, inverse_dict=True)
            arcpy.CalculateField_management(pts, "MU", "inverse_dict[!grid_code!]", "PYTHON", expression)

            self.logger.info("   >> OK")
            self.logger.info(" * Saving MU string raster as:")
            self.logger.info(str(self.out_dir) + "\\mu_str.tif")
            arcpy.PointToRaster_conversion(in_features=pts, value_field="MU",
                                           out_rasterdataset=self.out_dir + "\\mu_str.tif",
                                           cell_assignment="MOST_FREQUENT", cellsize=5)
            self.logger.info(" * OK")
        except arcpy.ExecuteError:
            self.logger.info("ExecuteERROR: (arcpy).")
            self.logger.info(arcpy.GetMessages(2))
        except Exception as e:
            self.logger.info("ExceptionERROR: (arcpy).")
            self.logger.info(e.args[0])
        except:
            self.logger.info("ERROR: Field assignment failed.")
            return True

        try:
            self.logger.info(" * Saving mu numeric raster as:")
            self.logger.info(str(self.out_dir) + "\\mu.tif")
            self.ras_mu.save(self.out_dir + "\\mu.tif")
            self.logger.info(" * OK")
        except arcpy.ExecuteError:
            self.logger.info(arcpy.AddError(arcpy.GetMessages(2)))
        except Exception as e:
            self.logger.info(arcpy.GetMessages(2))
        except:
            self.logger.info("ERROR: Saving failed.")
            return True

        try:
            self.clean_up()
        except:
            pass
        return False

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = MU (%s)" % os.path.dirname(__file__))
        print(dir(self))
