# !/usr/bin/python
try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    # add folder containing package routines to the system path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cFeatureLifespan as cf
    import cLifespanDesignAnalysis as ca
    # add riverpy routines
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cMapper as cm
    import cDefinitions as cdef
    import cTerrainIO as cmio
    import fGlobal as fg
except:
    print(
        "ExceptionERROR: Cannot find package files (fGlobal.py, cMapLifespanDesign, cFeatureLifespan, cLifespanDesignAnalysis, MT/cDefinitions.py, MT/cTerrainIO).")


def analysis_call(*args):
    logger = logging.getLogger("lifespan_design")

    try:
        parameter_name = args[0]
        feature = args[1]
        feature_analysis = args[2]

        # invoke design raster creation
        if parameter_name == "ds_compare_slopes":
            feature_analysis.design_energy_slope()
        if parameter_name == "ds_filter":
            feature_analysis.design_filter(feature.threshold_Dmaxf)
        if parameter_name == "ds_stable_grains":
            feature_analysis.design_stable_grains(feature.threshold_taux)
        if parameter_name == "ds_wood":
            feature_analysis.design_wood()
        if parameter_name == "sidech":
            feature_analysis.design_side_channel()

        # invoke lifespan raster creation
        if parameter_name == "d2w":
            feature_analysis.analyse_d2w(feature.threshold_d2w_low, feature.threshold_d2w_up)
        if parameter_name == "det":
            feature_analysis.analyse_det(feature.threshold_det_low, feature.threshold_det_up)
        if parameter_name == "Fr":
            feature_analysis.analyse_Fr(feature.threshold_Fr)
        if parameter_name == "fill":
            feature_analysis.analyse_fill(feature.threshold_fill)
        if parameter_name == "fine_grains":
            feature_analysis.analyse_fine_grains(feature.threshold_taux, feature.threshold_Dmaxf)
        if parameter_name == "h":
            feature_analysis.analyse_h(feature.threshold_h)
        if parameter_name == "mobile_grains":
            feature_analysis.analyse_mobile_grains(feature.threshold_taux)
        if parameter_name == "mu":
            feature_analysis.analyse_mu(feature.mu_bad, feature.mu_good, feature.mu_method)
        if parameter_name == "scour":
            feature_analysis.analyse_scour(feature.threshold_scour)
        if parameter_name == "taux":
            feature_analysis.analyse_taux(feature.threshold_taux)
        if parameter_name == "tcd":
            feature_analysis.analyse_tcd(feature.threshold_fill, feature.threshold_scour)
        if parameter_name == "u":
            feature_analysis.analyse_u(feature.threshold_u)
        if parameter_name == "lf_bioengineering":
            feature_analysis.analyze_bio(feature.threshold_S0, feature.threshold_d2w_up)
        return feature_analysis

    except:
        logger.info("ERROR: Function analysis_call received bad arguments.")


def analysis(feature, condition, reach_extents, habitat, output_dir, unit_system, wildcard, manning_n, extent_type):
    pot_err_msg = "logger initiation"  # a message that is printed in the case of a program crash
    try:
        logger = logging.getLogger("lifespan_design")

        try:
            fg.clean_dir(os.getcwd()+"\\.cache\\")  # ensure that the cache is empty
            pass
        except:
            logger.info("ERROR: .cache folder in use.")

        # instantiate GIS Analysis Object
        pot_err_msg = "ArcPyAnalysis"
        feature_analysis = ca.ArcPyAnalysis(condition, reach_extents, habitat, output_dir, unit_system, manning_n)  # arcpy class
        feature_analysis.extent_type = extent_type

        # assign analysis specific parameters if applies
        try:
            inverse_tcd = feature.inverse_tcd
            logger.info("   >> Inverse tcd analysis")
        except:
            inverse_tcd = False
        pot_err_msg = "inverse threshold verification"
        feature_analysis.verify_inverse_tcd(inverse_tcd)
        try:
            freq = feature.threshold_freq
            logger.info("   >> Customary frequency threshold = " + str(freq))
        except:
            freq = 0
        pot_err_msg = "frequence threshold verification"
        feature_analysis.verify_threshold_freq(freq)
        try:
            sf = feature.sf
            logger.info("   >> Customary safety factor (SF) = " + str(sf))
        except:
            sf = 1.0
        pot_err_msg = "safety factor verification"
        feature_analysis.verify_sf(sf)

        # call parameter analysis
        pot_err_msg = "parameter analysis"
        for par in feature.parameter_list:
            try:
                logger.info("   >> Calling parameter analysis (" + par + ").")
                feature_analysis = analysis_call(par, feature, feature_analysis)
            except:
                logger.info("ERROR: Failed calling " + par + " analysis of " + feature.name + ".")

        pot_err_msg = "habitat join"
        if habitat:
            feature_analysis.join_with_habitat()
        pot_err_msg = "wildcard join"
        if wildcard:
            feature_analysis.join_with_wildcard()
        pot_err_msg = "non applicable feature: saving an empty results-Raster"
        feature_analysis.save_manager(feature.ds, feature.lf, feature.id)

    except:
        try:
            logger.info("ERROR: Analysis stopped (" + pot_err_msg + " failed).")
        except:
            print("Call ERROR: Analysis stopped (" + pot_err_msg + " failed).")


def map_maker(*args, **kwargs):
    # prepares layout of all available rasters in Output folder
    # *args[0] = LIST with (optional) directory for input rasters
    #  args[1] = LIST of reach_IDs
    try:
        raster_dirs = args[0]
        print("Raster input directories provided:")
        print("\n ".join(raster_dirs))
    except:
        raster_dirs = [os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\02_Maps\\templates\\rasters\\"]
    reaches = None
    try:
        for k in kwargs.items():
            if "reach_ids" in k[0].lower():
                reach_IDs = k[1]
                reaches = cdef.Reaches()
                reach_names = []
                [reach_names.append(reaches.dict_id_names[rid]) for rid in reach_IDs]
                print("Mapping reach(es):")
                print("\n ".join(reach_names))
    except:
        pass

    for rd in raster_dirs:
        try:
            if "\\" in str(rd):
                condition_new = rd.split("\\")[-2]
            else:
                condition_new = rd.split("/")[-2]
            print("* identified condition = " + str(condition_new))
        except:
            print("WARNING: Invalid raster directory: " + str(rd))
        mapper = cm.Mapper(condition_new, "lf")
        mapper.prepare_layout(False)

        if reaches:
            reach_reader = cmio.Read()  # define xy map center point s in feet according to mapping_details.xlsx
            for rid in reach_IDs:
                try:
                    reach_extents = reach_reader.get_reach_coordinates(reaches.dict_id_int_id[rid])
                except:
                    reach_extents = "MAXOF"
                for ras in mapper.raster_list:
                    mapper.make_pdf_maps(str(ras).split(".tif")[0], extent=reach_extents)
        else:
            for ras in mapper.raster_list:
                mapper.make_pdf_maps(str(ras).split(".tif")[0], extent='raster')

    try:
        if not mapper.error:
            fg.open_folder(mapper.output_dir)
    except:
        pass

    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\02_Maps\\" + condition_new + "\\"


def raster_maker(condition, reach_ids, *args):
    # args[0] = feature_list (list from threshold_values.xlsx)
    # args[1] = mapping (True/False)
    # args[2] = habitat analysis (True/False)
    # args[3] = unit system ("us" or "si")
    # args[4] = wildcard raster application
    # args[5] = FLOAT manning n in s/m^(1/3)
    # args[6] = STR extent_type either "standard" (reaches) or "raster" (background raster)
    features = cdef.Features(False)
    if not args:
        # use general feature list and default settings if no arguments are provided
        feature_list = features.feature_name_list
        mapping = False
        habitat_analysis = False
        unit_system = "us"
        wildcard = False
    else:
        try:
            if args[0].__len__() > 0:
                feature_list = args[0]
            else:
                feature_list = features.feature_name_list
        except:
            # use simplified feature list
            feature_list = features.feature_name_list
        try:
            mapping = args[1]
            print("Integrated mapping (layout creation) activated.")
        except:
            mapping = False
            print("Integrated mapping deactivated.")
        try:
            habitat_analysis = args[2]
        except:
            habitat_analysis = False
            print("Physical feature stability analysis only.")
        try:
            unit_system = args[3]
        except:
            unit_system = "us"
        try:
            wildcard = args[4]
        except:
            wildcard = False
        try:
            manning_n = float(args[5])
        except:
            manning_n = 0.0473934
        try:
            extent_type = str(args[6])
        except:
            extent_type = "standard"

    # start logging
    logger = fg.initialize_logger(os.path.dirname(os.path.abspath(__file__)), "lifespan_design")
    logger.info("lifespan_design.raster_maker initiated with feature list = " + str(feature_list) + "\nUnit system: " +
                str(unit_system))

    # set environment settings
    temp_path = os.getcwd()+"\\.cache\\"
    fg.chk_dir(temp_path)

    reach_reader = cmio.Read()
    reaches = cdef.Reaches()

    outputs = []

    for r in reach_ids:
        if reach_ids.__len__() < 8:
            reach_extents = reach_reader.get_reach_coordinates(reaches.dict_id_int_id[r])
        else:
            reach_extents = "MAXOF"
        if r == reach_ids[0]:
            output_dir = fg.make_output_dir(condition, reach_ids, habitat_analysis, feature_list)
            outputs.append(output_dir)
        # fg.clean_dir(output_dir)
        for f in feature_list:
            logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
            if reach_extents == "MAXOF":
                logger.info("FEATURE (ALL REACHES): " + str(f))
            else:
                logger.info("FEATURE (REACH: " + reaches.dict_id_names[r] + "): " + str(f))
            logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
            feature = cf.RestorationFeature(f)  # instantiate object containing all restoration feature attributes

            if not feature.sub:
                analysis(feature.feature, condition, reach_extents, habitat_analysis, output_dir, unit_system, wildcard, manning_n, extent_type)
            else:
                sub_feature = cf.RestorationFeature(f, feature.sub)
                analysis(sub_feature.feature, condition, reach_extents, habitat_analysis, output_dir, unit_system, wildcard, manning_n, extent_type)
        if reach_extents == "MAXOF":
            break

    try:
        fg.rm_dir(temp_path)  # dump cache after feature analysis
    except:
        logger.info("WARNING: Package could not remove .cache folder.")
    logger.info("RASTERS FINISHED.")

    if mapping:
        outputs = map_maker(outputs)

    # stop logging and release logfile
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)
    return outputs


# enable script to run stand-alone
if __name__ == "__main__":
    # query condition
    condition = str(input('Enter the condition (shape: >> XXXX, e.g., >> 2008 ) \n>> '))
    # launch raster maker for lifespan and design rasters
    try:
        # try query feature_list
        feature_list = list(input(
            "Enter the condition (not mandatory; do not forget brackets! - example: >> [\'Featurename1\', \'Featurename2\']) \n>> "))
        raster_maker(condition, "all", feature_list)
    except:
        raster_maker(condition, "all")

