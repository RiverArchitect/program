# !/usr/bin/python
try:
    import os, logging
except:
    print("ExceptionERROR: Cannot find logging package.")

try:
    import cThresholdDirector as cTD
    import cDefinitions as cDef
except:
    print("ExceptionERROR: Cannot find riverpy (.site_packages/).")


class Feature:
    def __init__(self, feat_id):
        # set analysis HIERARCHY with parameter list
        self.parameter_list = ["h", "u", "taux", "Fr", "mobile_grains", "fine_grains", "tcd", "mu", "sidech", "d2w",
                               "det", "lf_bioengineering", "ds_stable_grains", "ds_filter", "ds_wood"]
        self.id = feat_id

        thresh = cTD.ThresholdDirector(feat_id)
        self.ds = thresh.get_thresh_value("ds")  # needed to identify if design map applies
        self.lf = thresh.get_thresh_value("lf")  # needed to identify if lifespan map applies
        self.name = thresh.get_thresh_value("name")
        self.sf = thresh.get_thresh_value("sf")
        self.threshold_d2w_low = thresh.get_thresh_value("d2w_low")
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        self.threshold_det_low = thresh.get_thresh_value("det_low")
        self.threshold_det_up = thresh.get_thresh_value("det_up")
        self.threshold_fill = thresh.get_thresh_value("fill")
        self.threshold_Fr = thresh.get_thresh_value("Fr")
        self.threshold_freq = thresh.get_thresh_value("freq")
        self.threshold_h = thresh.get_thresh_value("h")
        self.threshold_S0 = thresh.get_thresh_value("S0")  # terrain slope
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_taux = thresh.get_thresh_value("taux")
        self.inverse_tcd = thresh.get_thresh_value("inverse_tcd")
        self.threshold_u = thresh.get_thresh_value("u")

        try:
            self.mu_bad = thresh.get_thresh_value("mu_bad")
        except:
            self.mu_bad = []
        try:
            self.mu_good = thresh.get_thresh_value("mu_good")
        except:
            self.mu_good = []
        try:
            self.mu_method = int(thresh.get_thresh_value("mu_method"))
        except:
            self.mu_method = -1
        try:
            if (self.mu_bad.__len__() == 0) and (self.mu_good.__len__() == 0):
                self.mu_method = -1
        except:
            pass
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: {0} ({1})".format(str(self.name), os.path.dirname(__file__)))
        print(dir(self))


class FeatureContainer:
    # This class builds up on above feature classes.
    # Instantiate an object by: features = RestorationFeatures()

    def __init__(self, feature_name, *sub_feature):
        # sub_feature = BOOL (optional)
        self.feats = cDef.FeatureDefinitions(False)
        self.sub = False
        self.name = feature_name
        self.id = self.feats.name_dict[feature_name]
        self.feat_lyr_type = self.set_feat_layer_type()

        if not sub_feature:
            if self.feats.col_name_dict[feature_name] in [24, 25, 11, 12, 13, 14]:
                self.sub = True
            else:
                self.feature = Feature(self.id)
        else:
            # sub_feature containing features (called in second iteration in feature_analysis.py)
            self.feature = Feature(self.id)

    def set_feat_layer_type(self):
        if self.feats.col_name_dict[self.name] in self.feats.threshold_cols_framework:
            __type__ = 1
        if self.feats.col_name_dict[self.name] in self.feats.threshold_cols_plants:
            __type__ = 2
        if self.feats.col_name_dict[self.name] in self.feats.threshold_cols_toolbox:
            __type__ = 2
        if self.feats.col_name_dict[self.name] in self.feats.threshold_cols_complement:
            __type__ = 3
        try:
            return __type__
        except:
            return 0

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = FeatureContainer (%s)" % os.path.dirname(__file__))
        print(dir(self))



