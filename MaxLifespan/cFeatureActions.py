# !/usr/bin/python
try:
    import arcpy, sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: arcpy, os, sys, logging")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cDefinitions as cdef
except:
    print("ExceptionERROR: Cannot find package files (RP/cDefinitions.py).")


class Director:
    def __init__(self, condition, *args):
        # args[0] is an optional input path
        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.logger = logging.getLogger("max_lifespan")
        try:
            self.raster_input_path = args[0]
        except:
            self.path2fa = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\LifespanDesign\\"
            self.raster_input_path = r"" + self.path2fa + "Products\\Rasters\\" + str(self.condition) + "\\"

        arcpy.env.workspace = self.raster_input_path
        self.all_rasters = arcpy.ListRasters()
        arcpy.env.workspace = self.path

    def append_ds_rasters(self, feature_list):
        raster_list = []
        for feat in feature_list:
            for ras_name in self.all_rasters:
                if feat in ras_name:
                    if ras_name[0:2] == "ds":
                        ras_act = self.raster_input_path + ras_name
                        if os.path.isfile(ras_act + '.aux.xml') or os.path.isfile(ras_act) or os.path.isfile(ras_act + '.tif'):
                            raster_list.append(arcpy.Raster(ras_act))
                        else:
                            raster_list.append("")
        return raster_list

    def append_lf_rasters(self, feature_list):
        raster_list = []
        for feat in feature_list:
            for ras_name in self.all_rasters:
                if feat in ras_name:
                    if ras_name[0:2] == "lf":
                        ras_act = self.raster_input_path + ras_name
                        if os.path.isfile(ras_act + '.aux.xml') or os.path.isfile(ras_act) or os.path.isfile(ras_act + '.tif'):
                            raster_list.append(arcpy.Raster(ras_act))
                        else:
                            raster_list.append("")
        return raster_list


class FrameworkFeatures(Director):
    # This class stores all information about Framework features
    def __init__(self, condition, *args):
        try:
            # check if args[0] = alternative input path exists
            Director.__init__(self, condition, args[0])
        except:
            Director.__init__(self, condition)
        self.features = cdef.Features()
        self.names = self.features.name_list_framework
        self.shortnames = self.features.id_list_framework
        self.ds_rasters = self.append_ds_rasters(self.shortnames)
        self.lf_rasters = self.append_lf_rasters(self.shortnames)


class PlantFeatures(Director):
    # This class stores all information about Toolbox features
    def __init__(self, condition, *args):
        try:
            # check if args[0] = alternative input path exists
            Director.__init__(self, condition, args[0])
        except:
            Director.__init__(self, condition)
        self.features = cdef.Features()
        self.names = self.features.name_list_plants
        self.shortnames = self.features.id_list_plants
        self.ds_rasters = self.append_ds_rasters(self.shortnames)
        self.lf_rasters = self.append_lf_rasters(self.shortnames)


class ToolboxFeatures(Director):
    # This class stores all information about Toolbox features
    def __init__(self, condition, *args):
        try:
            # check if args[0] = alternative input path exists
            Director.__init__(self, condition, args[0])
        except:
            Director.__init__(self, condition)
        self.features = cdef.Features()
        self.names = self.features.name_list_toolbox
        self.shortnames = self.features.id_list_toolbox
        self.ds_rasters = self.append_ds_rasters(self.shortnames)
        self.lf_rasters = self.append_lf_rasters(self.shortnames)


class ComplementaryFeatures(Director):
    # This class stores all information about Complementary features
    def __init__(self, condition, *args):
        try:
            # check if args[0] = alternative input path exists
            Director.__init__(self, condition, args[0])
        except:
            Director.__init__(self, condition)
        self.features = cdef.Features()
        self.names = self.features.name_list_complement
        self.shortnames = self.features.id_list_complement
        self.ds_rasters = self.append_ds_rasters(self.shortnames)
        self.lf_rasters = self.append_lf_rasters(self.shortnames)


class Manager(FrameworkFeatures, PlantFeatures, ToolboxFeatures, ComplementaryFeatures):
    # Manages feature layer assignments
    def __init__(self, condition, feature_type, *args):

        acceptable_types = ["terraforming", "plantings", "bioengineering", "maintenance"]

        if feature_type in acceptable_types:
            if feature_type == "terraforming":
                try:
                    # check if args[0] = alternative input path exists
                    FrameworkFeatures.__init__(self, condition, args[0])
                except:
                    FrameworkFeatures.__init__(self, condition)

            if feature_type == "plantings":
                try:
                    # check if args[0] = alternative input path exists
                    PlantFeatures.__init__(self, condition, args[0])
                except:
                    PlantFeatures.__init__(self, condition)

            if feature_type == "bioengineering":
                try:
                    # check if args[0] = alternative input path exists
                    ToolboxFeatures.__init__(self, condition, args[0])
                except:
                    ToolboxFeatures.__init__(self, condition)

            if feature_type == "maintenance":
                try:
                    # check if args[0] = alternative input path exists
                    ComplementaryFeatures.__init__(self, condition, args[0])
                except:
                    ComplementaryFeatures.__init__(self, condition)

                self.logger.info("*** feature_type: " + str(feature_type))

        else:
            self.logger.info("ERROR: Invalid keyword for feature type.")
