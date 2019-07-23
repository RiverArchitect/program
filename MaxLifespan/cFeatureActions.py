# !/usr/bin/python
try:
    import arcpy, sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy, os, sys, logging")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cDefinitions as cDef
except:
    print("ExceptionERROR: Cannot find riverpy.")


class Director:
    def __init__(self, condition, *args):
        # args[0] is an optional input path
        self.logger = logging.getLogger("logfile")
        try:
            self.raster_input_path = args[0]
            self.logger.info("*** input directory: " + str(self.raster_input_path))
        except:
            self.raster_input_path = config.dir2lf + "Output\\Rasters\\" + str(condition) + "\\"
        arcpy.env.workspace = self.raster_input_path
        self.all_rasters = arcpy.ListRasters()
        if not self.all_rasters:
            self.all_rasters = []
        arcpy.env.workspace = config.dir2ml

    def append_ds_rasters(self, feature_list):
        raster_list = []
        if str(self.all_rasters).__len__() < 1:
            return []
        for feat in feature_list:
            for ras_name in self.all_rasters:
                if feat in ras_name:
                    if "ds" in ras_name:
                        ras_act = self.raster_input_path + ras_name
                        if os.path.isfile(ras_act.split(".")[0] + '.aux.xml') or os.path.isfile(ras_act.split(".")[0] + '.tif'):
                            raster_list.append(arcpy.Raster(ras_act))
                        else:
                            raster_list.append("")
        if raster_list.__len__() < 1:
            self.logger.info("WARNING: No Lifespan / Design Raster found (%s)." % str(self.raster_input_path))
        return raster_list

    def append_lf_rasters(self, feature_list):
        raster_list = []
        if str(self.all_rasters).__len__() < 1:
            return []
        for feat in feature_list:
            for ras_name in self.all_rasters:
                if feat in ras_name:
                    if "lf" in ras_name:
                        ras_act = self.raster_input_path + ras_name
                        if os.path.isfile(ras_act.split(".")[0] + '.aux.xml') or os.path.isfile(ras_act.split(".")[0] + '.tif'):
                            raster_list.append(arcpy.Raster(ras_act))
                        else:
                            raster_list.append("")
        if raster_list.__len__() < 1:
            self.logger.info("WARNING: No Lifespan / Design Raster found (%s)." % str(self.raster_input_path))
        return raster_list


class Manager(Director):
    # Manages feature layer assignments
    def __init__(self, condition, feature_type, lf_dir):
        acceptable_types = ["terraforming", "plantings", "bioengineering", "connectivity"]
        if feature_type in acceptable_types:
            Director.__init__(self, condition,  lf_dir)
            self.logger.info("*** feature_type: " + str(feature_type))
            self.features = cDef.FeatureDefinitions()
            self.names = self.features.feat_class_name_dict[feature_type]
            self.shortnames = self.features.feat_class_id_dict[feature_type]
            self.ds_rasters = self.append_ds_rasters(self.shortnames)
            self.lf_rasters = self.append_lf_rasters(self.shortnames)
        else:
            self.logger.info("ERROR: Invalid keyword for feature type.")
