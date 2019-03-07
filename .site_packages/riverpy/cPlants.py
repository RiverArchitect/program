# !/usr/bin/python
try:
    import sys, os
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')) + "\\LifespanDesign\\")
    from cThresholdDirector import *
except:
    print("ExceptionERROR: cPlants cannot find cFeatureLifespan (need ThresholdDirector).")


class Plant1:
    # Refers to BoxElder
    # __call__()

    def __init__(self, feat_id):
        self.parameter_list = ["h", "taux", "d2w"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.threshold_d2w_low = thresh.get_thresh_value("d2w_low")
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        self.threshold_h = thresh.get_thresh_value("h")
        self.threshold_taux = thresh.get_thresh_value("taux")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Plantings (species ID: " + str(self.id) + ")")


class Plant2:
    # Refers to Cottonwood
    # __call__()

    def __init__(self, feat_id):
        self.parameter_list = ["h", "u", "tcd", "d2w"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.threshold_d2w_low = thresh.get_thresh_value("d2w_low")
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        self.threshold_fill = thresh.get_thresh_value("fill")
        self.threshold_h = thresh.get_thresh_value("h")
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_u = thresh.get_thresh_value("u")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Plantings (species ID: " + str(self.id) + ")")


class Plant3:
    # Refers to WhiteAlder
    # __call__()

    def __init__(self, feat_id):
        self.parameter_list = ["mobile_grains", "scour", "d2w"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.threshold_d2w_low = thresh.get_thresh_value("d2w_low")
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_taux = thresh.get_thresh_value("taux")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Plantings (species ID: " + str(self.id) + ")")


class Plant4:
    # Refers to Willows
    # __call__()

    def __init__(self, feat_id):
        self.parameter_list = ["h", "taux", "scour", "d2w"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.threshold_d2w_low = thresh.get_thresh_value("d2w_low")
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        self.threshold_h = thresh.get_thresh_value("h")
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_taux = thresh.get_thresh_value("taux")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Plantings (species ID: " + str(self.id) + ")")





