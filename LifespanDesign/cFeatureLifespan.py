# !/usr/bin/python
try:
    import logging
except:
    print("ExceptionERROR: Cannot find logging package.")

try:
    from cThresholdDirector import *
    # add special routines
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cDefinitions as cdef
    from cPlants import *
    from cGravel import *
except:
    print("ExceptionERROR: Cannot find package files (RP/cPlants.py, RP/cGravel.py, cThresholdDirector.py, RP/cDefinitions).")


class Backwater:
    # This is the Backwater feature class.

    def __init__(self, feat_id):
        self.lf = True  # needed to identify if lifespan map applies
        self.parameter_list = ["u", "mobile_grains", "tcd", "mu"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.mu_bad = thresh.get_thresh_value("mu_bad")         # []
        self.mu_good = thresh.get_thresh_value("mu_good")
        self.mu_method = int(thresh.get_thresh_value("mu_method"))
        self.threshold_fill = thresh.get_thresh_value("fill")   # 0.1*6 * ft2m  # (ft * m/ft)
        self.threshold_freq = thresh.get_thresh_value("freq")   # 4.7           # (years)
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_taux = thresh.get_thresh_value("taux")   # 0.047         # (--) if too low, needed
        self.threshold_u = thresh.get_thresh_value("u")         # 0.1 * ft2m       # (ft * m/ft *1/s)
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Backwater")


class Bioengineering:
    # This is the Backwater feature class.

    def __init__(self, feat_id):
        self.ds = True   # needed to identify if design map applies
        self.lf = True  # needed to identify if lifespan map applies
        self.parameter_list = ["lf_bioengineering"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.threshold_S0 = thresh.get_thresh_value("S0")  # terrain slope
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Soil-bioengineering")


class Finesediment:
    # This is the Finesediment feature class.

    def __init__(self, feat_id):
        # IDEA: only makes sense where plantings may require this?
        self.ds = True  # needed to identify if design map applies
        self.lf = True  # needed to identify if lifespan map applies
        self.parameter_list = ["taux", "fine_grains", "tcd", "d2w", "ds_filter"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.threshold_d2w_low = thresh.get_thresh_value("d2w_low")
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        self.threshold_Dmaxf = thresh.get_thresh_value("D")
        self.threshold_fill = thresh.get_thresh_value("fill")
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_taux = thresh.get_thresh_value("taux")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Finesediment")


class Grading:
    # This is the Bar and Floodplain lowering feature class.

    def __init__(self, feat_id):
        self.ds = False # needed to identify if design map applies
        self.lf = True  # needed to identify if lifespan map applies
        self.inverse_tcd = True     # if True: inverse use of tcd thresholds
        self.parameter_list = ["mobile_grains", "taux", "scour", "mu", "d2w"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.mu_bad = thresh.get_thresh_value("mu_bad")
        self.mu_good = thresh.get_thresh_value("mu_good")
        self.mu_method = int(thresh.get_thresh_value("mu_method"))
        self.threshold_d2w_low = thresh.get_thresh_value("d2w_low")
        self.threshold_d2w_up = thresh.get_thresh_value("d2w_up")
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_taux = thresh.get_thresh_value("taux")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Grading")


class Gravel(GravelInStream, GravelOutStream):
    # This is the Sediment replenishment feature class.

    def __init__(self, type, feat_id):
        self.ds = True  # needed to identify if design map applies
        self.lf = True  # needed to identify if lifespan map applies
        if type == 'in':
            GravelInStream.__init__(self, feat_id)
        if type == 'out':
            GravelOutStream.__init__(self, feat_id)

    def __call__(self):
        print("Class Info: <type> = Feature: Gravel augmentation (super class)")


class Plantings(Plant1, Plant2, Plant3, Plant4):
    # This is the Vegetation Plantings feature class.

    def __init__(self, species, feat_id):
        self.lf = True  # needed to identify if lifespan map applies
        self.ds = False  # needed to identify if design map applies
        if species == 'plant1':
            Plant1.__init__(self, feat_id)
        if species == 'plant2':
            Plant2.__init__(self, feat_id)
        if species == 'plant3':
            Plant3.__init__(self, feat_id)
        if species == 'plant4':
            Plant4.__init__(self, feat_id)

    def __call__(self):
        print("Class Info: <type> = Feature: Plantings (super class)")


class Rocks:
    # This is the Boulder/rocks feature class.

    def __init__(self, feat_id):
        self.ds = True  # needed to identify if design map applies
        self.lf = True  # needed to identify if lifespan map applies
        self.parameter_list = ["taux", "scour", "ds_stable_grains"]
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.sf = thresh.get_thresh_value("sf")
        self.threshold_freq = thresh.get_thresh_value("freq")
        self.threshold_scour = thresh.get_thresh_value("scour")
        self.threshold_taux = thresh.get_thresh_value("taux")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Boulders/rocks")


class Sidecavity:
    # This is the Sidecavity feature class.

    def __init__(self, feat_id):
        self.ds = True  # needed to identify if design map applies
        self.lf = False # needed to identify if lifespan map applies
        self.parameter_list = ["fill", "mu"]
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.inverse_tcd = thresh.get_thresh_value("inverse_tcd")
        self.mu_bad = thresh.get_thresh_value("mu_bad")
        self.mu_good = thresh.get_thresh_value("mu_good")
        self.mu_method = int(thresh.get_thresh_value("mu_method"))
        self.threshold_fill = thresh.get_thresh_value("fill")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Sidecavity")


class Sidechannel:
    # This is the Sidechannel feature class.

    def __init__(self, feat_id):
        self.ds = False  # needed to identify if design map applies
        self.lf = True  # needed to identify if lifespan map applies
        self.parameter_list = ["taux", "fill", "sidech"]  # , "ds_compare_slopes"]
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.inverse_tcd = thresh.get_thresh_value("inverse_tcd")
        self.threshold_taux = thresh.get_thresh_value("taux")
        self.threshold_fill = thresh.get_thresh_value("fill")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Sidechannel")


class Widen:
    # This is the Berm setback / widening feature class.

    def __init__(self, feat_id):
        self.ds = True     # needed to identify if design map applies
        self.lf = False    # needed to identify if lifespan map applies
        self.parameter_list = ["mu", "det"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.mu_bad = thresh.get_thresh_value("mu_bad")
        self.mu_good = thresh.get_thresh_value("mu_good")
        self.mu_method = int(thresh.get_thresh_value("mu_method"))
        self.threshold_det_low = thresh.get_thresh_value("det_low")
        self.threshold_det_up = thresh.get_thresh_value("det_up")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Widen")


class Wood:
    # This is the Wood feature class.

    def __init__(self, feat_id):
        self.ds = True  # needed to identify if design map applies
        self.lf = True  # needed to identify if lifespan map applies
        self.parameter_list = ["h", "Fr", "mu", "ds_wood"]  # governs analysis HIERARCHY!
        self.id = feat_id

        thresh = ThresholdDirector(feat_id)
        self.mu_bad = thresh.get_thresh_value("mu_bad")
        self.mu_good = thresh.get_thresh_value("mu_good")
        self.mu_method = int(thresh.get_thresh_value("mu_method"))
        self.threshold_Fr = thresh.get_thresh_value("Fr")
        self.threshold_freq = thresh.get_thresh_value("freq")
        self.threshold_h = thresh.get_thresh_value("h")
        thresh.close_wb()

    def __call__(self):
        print("Class Info: <type> = Feature: Wood")


class RestorationFeature:
    # This class builds up on above feature classes.
    # Instantiate an object by: features = RestorationFeatures()

    def __init__(self, feature_name, *sub_feature):
        # sub_feature = BOOL (optional)
        self.feats = cdef.Features(False)
        self.sub = False
        self.name = feature_name
        self.id = self.feats.name_dict[feature_name]
        self.feat_lyr_type = self.set_feat_layer_type()

        if not sub_feature:
            if self.feats.col_name_dict[feature_name] == "E":
                self.feature = Backwater(self.id)

            if self.feats.col_name_dict[feature_name] == "P":
                self.feature = Bioengineering(self.id)

            if self.feats.col_name_dict[feature_name] == "F":
                self.feature = Widen(self.id)

            if self.feats.col_name_dict[feature_name] == "G":
                self.feature = Grading(self.id)

            if self.feats.col_name_dict[feature_name] == "N":
                self.feature = Wood(self.id)

            if self.feats.col_name_dict[feature_name] == "S":
                self.feature = Finesediment(self.id)

            if self.feats.col_name_dict[feature_name] == "O":
                self.feature = Rocks(self.id)

            if self.feats.col_name_dict[feature_name] == "H":
                self.feature = Sidecavity(self.id)

            if self.feats.col_name_dict[feature_name] == "I":
                self.feature = Sidechannel(self.id)

            if self.feats.col_name_dict[feature_name] in ["Q", "R"]:
                self.sub = True

            if self.feats.col_name_dict[feature_name] in ["J", "K", "L", "M"]:
                self.sub = True

        else:
            # subfeature containing features (called only in second iteration in feature_analysis.py)
            if (self.feats.col_name_dict[feature_name] in ["Q", "R"]) and sub_feature:
                col_dict = dict(zip(["Q", "R"], ["in", "out"]))
                sub_feature = col_dict[self.feats.col_name_dict[feature_name]]
                self.feature = Gravel(sub_feature, self.id)

            if (self.feats.col_name_dict[feature_name] in ["J", "K", "L", "M"]) and sub_feature:
                col_dict = dict(zip(["J", "K", "L", "M"], ["plant1", "plant2", "plant3", "plant4"]))
                sub_feature = col_dict[self.feats.col_name_dict[feature_name]]
                self.feature = Plantings(sub_feature, self.id)

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

    def __call__(self):
        print("Class Info: <type> = RestorationFeature (super class)")



