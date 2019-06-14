# !/usr/bin/python
try:
    from cReadInpLifespan import *
except:
    print("ExceptionERROR: Cannot find package files (classes_read_inp.py).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?).")


class ParameterContainer:
    def __init__(self, condition, par_id):
        self.condition = condition  # [str] state of planning situation, .e.g., "2008"
        self.raster_path = r"" + os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\"
        input_info = Info(condition, par_id)
        self.raster_names = input_info.raster_read()
        self.flood_dependency_dict = {"chsi": False, "d2w": False, "dem": False, "det": False, "dod": False, "grains": False,
                                      "h": True, "mu": False, "sidech": False, "u": True, "wild": False}
        try:
            self.flood_dependent = self.flood_dependency_dict[par_id]
        except:
            self.flood_dependent = False


class CHSI(ParameterContainer):
    # This class stores all information about combined habitat suitability Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "chsi")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
        except:
            self.raster = ""


class DEM(ParameterContainer):
    # This class stores all information about DEM Rasters

    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "dem")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class DEMdet(ParameterContainer):
    # This class stores all information about detrended DEM Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "det")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class DoD(ParameterContainer):
    # This class stores all information about the topographic change Rasters
    # Instantiate an object by: myDoD = DoD() in feet

    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "dod")
        try:
            self.raster_scour = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster_scour = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster_scour = ""
        try:
            self.raster_fill = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster_fill = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster_fill = ""


class FlowDepth(ParameterContainer):
    # This class stores all information about flow depth Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "h")
        self.rasters = []
        for ras_name in self.raster_names:
            ras_act = self.raster_path + self.condition + "\\" + ras_name
            if arcpy.Exists(ras_act) or os.path.isfile(ras_act + '.tif'):
                try:
                    self.rasters.append(arcpy.Raster(ras_act + '.tif'))
                except:
                    self.rasters.append(arcpy.Raster(ras_act))
            else:
                self.rasters.append("")


class FlowVelocity(ParameterContainer):
    # This class stores all information about flow velocity Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "u")
        self.rasters = []
        for ras_name in self.raster_names:
            ras_act = self.raster_path + self.condition + "\\" + ras_name
            if arcpy.Exists(ras_act) or os.path.isfile(ras_act + '.tif'):
                try:
                    self.rasters.append(arcpy.Raster(ras_act + '.tif'))
                except:
                    self.rasters.append(arcpy.Raster(ras_act))
            else:
                self.rasters.append("")


class GrainSizes(ParameterContainer):
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "grains")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class MU(ParameterContainer):
    # This class stores all information about Morphological Units Rasters and thresholds.
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "mu")
        self.mu_dict = {"agriplain": 4, "backswamp": 5, "bank": 6, "chute": 8, "cutbank": 9, "fast glide": 10,
                        "flood runner": 11, "floodplain": 12, "high floodplain": 13, "hillside": 14, "bedrock": 14,
                        "island high floodplain": 15, "island-floodplain": 16, "lateral bar": 17, "levee": 18,
                        "medial bar": 19, "mining pit": 20, "point bar": 21, "pond": 22, "pool": 23, "riffle": 24,
                        "riffle transition": 25, "run": 26, "slackwater": 27, "slow glide": 28, "spur dike": 29,
                        "swale": 30, "tailings": 31, "terrace": 32, "tributary channel": 33, "tributary delta": 34,
                        "in-channel bar": 35}
        self.raster_names = ["mu"]  # overwrites ParameterContainer.raster_names
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class SideChannelDelineation(ParameterContainer):
    # This class stores all information about depth to groundwater table Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "sidech")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class WaterTable(ParameterContainer):
    # This class stores all information about depth to groundwater table Rasters
    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "d2w")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""


class Wildcard(ParameterContainer):
    # This class stores all information about depth to groundwater table Rasters

    def __init__(self, condition):
        ParameterContainer.__init__(self, condition, "wild")
        try:
            self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0] + ".tif")
        except:
            try:
                self.raster = arcpy.Raster(self.raster_path + self.condition + "\\" + self.raster_names[0])
            except:
                self.raster = ""
