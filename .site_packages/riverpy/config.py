try:
    import os, sys
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys).")

code_icon = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\templates\\code_icon.ico"

dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\"
dir2co = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\StrandingRisk\\"
dir2rp = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\RiparianRecruitment\\"
dir2conditions = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\01_Conditions\\"
dir2flows = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\00_Flows\\"
dir2gs = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\GetStarted\\"
dir2lf = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\LifespanDesign\\"
dir2map = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\\..")) + "\\02_Maps\\"
dir2map_templates = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\\..")) + "\\02_Maps\\templates\\"
dir2ml = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\MaxLifespan\\"
dir2mt = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\ModifyTerrain\\"
dir2oxl = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\openpyxl\\"
dir2pm = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\ProjectMaker\\"
dir2rb = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\ModifyTerrain\\RiverBuilder\\"
dir2ripy = os.path.dirname(__file__) + "\\"
dir2templates = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\templates\\"
dir2sh = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\SHArC\\"
dir2va = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\VolumeAssessment\\"

ft2ac = float(1 / 43560)
m2ft = 0.3048

empty_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\templates\\oups.txt"
xlsx_aqua = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\templates\\Fish.xlsx"
xlsx_dummy = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\templates\\empty.xlsx"
xlsx_mu = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\templates\\morphological_units.xlsx"
xlsx_reaches = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\ModifyTerrain\\.templates\\computation_extents.xlsx"
xlsx_thresholds = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\LifespanDesign\\.templates\\threshold_values.xlsx"
xlsx_volumes = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\VolumeAssessment\\.templates\\volumes_template.xlsx"
xlsx_connectivity = os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\StrandingRisk\\.templates\\disconnected_area_template.xlsx"
