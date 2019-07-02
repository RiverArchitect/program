# !/usr/bin/python
try:
    import sys, os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")

try:
    # add folder containing package routines to the system path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cLifespanDesignAnalysis as cLDA
    # add riverpy routines
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cMapper as cMp
    import cDefinitions as cDef
    import cReachManager as cRM
    import fGlobal as fGl
    import cFeatures as cFe
except:
    print("ExceptionERROR: Cannot find RiverArchitect/.site_packages/riverpy.")


def analysis_call(parameter_name, feature, feature_analysis):
    logger = logging.getLogger("logfile")
    # NOTE: if not type(...) statements exclude empty values from thresholds workbook

    try:
        # invoke design raster creation
        if feature.ds:
            if parameter_name == "ds_compare_slopes":
                feature_analysis.design_energy_slope()
            if parameter_name == "ds_filter":
                if not type(feature.threshold_Dmaxf) is list:
                    feature_analysis.design_filter(feature.threshold_Dmaxf)
            if parameter_name == "ds_stable_grains":
                if not type(feature.threshold_taux) is list:
                    feature_analysis.design_stable_grains(feature.threshold_taux)
                else:
                    logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
            if parameter_name == "ds_wood":
                feature_analysis.design_wood()
            if parameter_name == "sidech":
                feature_analysis.design_side_channel()
        else:
            logger.info("      * Design mapping is off.")

        # invoke lifespan raster creation
        if parameter_name == "d2w":
            if not (type(feature.threshold_d2w_low) is list) and not (type(feature.threshold_d2w_up) is list):
                feature_analysis.analyse_d2w(feature.threshold_d2w_low, feature.threshold_d2w_up)
        if parameter_name == "det":
            if not (type(feature.threshold_det_low) is list) and not (type(feature.threshold_det_up) is list):
                feature_analysis.analyse_det(feature.threshold_det_low, feature.threshold_det_up)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "Fr":
            if not type(feature.threshold_Fr) is list:
                feature_analysis.analyse_Fr(feature.threshold_Fr)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "fill":
            if not type(feature.threshold_fill) is list:
                feature_analysis.analyse_fill(feature.threshold_fill)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "fine_grains":
            if not (type(feature.threshold_taux) is list) and not (type(feature.threshold_Dmaxf) is list):
                feature_analysis.analyse_fine_grains(feature.threshold_taux, feature.threshold_Dmaxf)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "h":
            if not type(feature.threshold_h) is list:
                feature_analysis.analyse_h(feature.threshold_h)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "mobile_grains":
            if not type(feature.threshold_taux) is list:
                feature_analysis.analyse_mobile_grains(feature.threshold_taux)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "mu":
            if (0 in feature.mu_method) or (1 in feature.mu_method):
                feature_analysis.analyse_mu(feature.mu_bad, feature.mu_good, feature.mu_method)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "scour":
            if not type(feature.threshold_scour) is list:
                feature_analysis.analyse_scour(feature.threshold_scour)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "taux":
            if not type(feature.threshold_taux) is list:
                feature_analysis.analyse_taux(feature.threshold_taux)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "tcd":
            run = False
            if not (type(feature.threshold_fill) is list) and not (type(feature.threshold_scour) is list):
                feature_analysis.analyse_tcd(feature.threshold_fill, feature.threshold_scour)
                run = True
            if (type(feature.threshold_fill) is list) and not (type(feature.threshold_scour) is list):
                feature_analysis.analyse_scour(feature.threshold_scour)
                run = True
            if not (type(feature.threshold_fill) is list) and (type(feature.threshold_scour) is list):
                feature_analysis.analyse_fill(feature.threshold_fill)
                run = True
            if not run:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "u":
            if not type(feature.threshold_u) is list:
                feature_analysis.analyse_u(feature.threshold_u)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
        if parameter_name == "lf_bioengineering":
            if not (type(feature.threshold_S0) is list) and not (type(feature.threshold_d2w_up) is list):
                feature_analysis.analyze_bio(feature.threshold_S0, feature.threshold_d2w_up)
            else:
                logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
    except:
        logger.info("      * Negative: No thresholds provided for %s." % parameter_name)
    return feature_analysis


def analysis(feature, condition, reach_extents, habitat, output_dir, unit_system, wildcard, manning_n, extent_type):
    logger = logging.getLogger("logfile")
    pot_err_msg = "FUNDAMENTAL APPLICATION ERROR - Revise River Architect usage instructions"
    try:
        try:
            fGl.clean_dir(os.getcwd() + "\\.cache\\")  # ensure that the cache is empty
            pass
        except:
            logger.info("ERROR: .cache folder in use.")

        # instantiate GIS Analysis Object
        pot_err_msg = "ArcPyAnalysis"
        feature_analysis = cLDA.ArcPyAnalysis(condition, reach_extents, habitat, output_dir, unit_system, manning_n)  # arcpy class
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
                logger.info("   >> Checking if %s applies ... " % par)
                feature_analysis = analysis_call(par, feature, feature_analysis)
            except:
                logger.info("ERROR: Failed checking " + par + " of " + feature.name + ".")

        pot_err_msg = "habitat join"
        if habitat:
            feature_analysis.join_with_habitat()
        pot_err_msg = "wildcard join"
        if wildcard:
            feature_analysis.join_with_wildcard()
        pot_err_msg = "non applicable feature: saving an empty results-Raster"
        feature_analysis.save_manager(feature.ds, feature.lf, feature.id)

    except:
        logger.info("ERROR: Analysis stopped (" + pot_err_msg + " failed).")


def map_maker(*args, **kwargs):
    # prepares layout of all available rasters in Output folder
    # *args[0] = LIST with (optional) directory for input rasters
    #  args[1] = LIST of reach_IDs
    logger = logging.getLogger("logfile")
    try:
        raster_dirs = args[0]
        logger.info("Raster input directories provided:")
        logger.info("\n ".join(raster_dirs))
    except:
        raster_dirs = [config.dir2map_templates + "rasters\\"]
    reaches = None
    try:
        for k in kwargs.items():
            if "reach_ids" in k[0].lower():
                reach_IDs = k[1]
                reaches = cDef.ReachDefinitions()
                reach_names = []
                [reach_names.append(reaches.dict_id_names[rid]) for rid in reach_IDs]
                logger.info("Mapping reach(es):")
                logger.info("\n ".join(reach_names))
    except:
        pass

    for rd in raster_dirs:
        try:
            if "\\" in str(rd):
                condition_new = rd.split("\\")[-2]
            else:
                condition_new = rd.split("/")[-2]
            logger.info("* identified condition = " + str(condition_new))
        except:
            logger.info("WARNING: Invalid raster directory: " + str(rd))
        mapper = cMp.Mapper(condition_new, "lf")
        mapper.prepare_layout(False)

        if reaches:
            reach_reader = cRM.Read()  # define xy map center point s in feet according to mapping_details.xlsx
            for rid in reach_IDs:
                try:
                    reach_extents = reach_reader.get_reach_coordinates(reaches.dict_id_int_id[rid])
                except:
                    reach_extents = "MAXOF"
                for ras in mapper.map_list:
                    mapper.make_pdf_maps(str(ras).split(".tif")[0], extent=reach_extents)
        else:
            for ras in mapper.map_list:
                mapper.make_pdf_maps(str(ras).split(".tif")[0], extent='raster')

    try:
        if not mapper.error:
            fGl.open_folder(mapper.output_dir)
    except:
        pass

    return config.dir2map + condition_new + "\\"


def raster_maker(condition, reach_ids, *args):
    # args[0] = feature_list (list from threshold_values.xlsx)
    # args[1] = mapping (True/False)
    # args[2] = habitat analysis (True/False)
    # args[3] = unit system ("us" or "si")
    # args[4] = wildcard raster application
    # args[5] = FLOAT manning n in s/m^(1/3)
    # args[6] = STR extent_type either "standard" (reaches) or "raster" (background raster)
    features = cDef.FeatureDefinitions(False)
    logger = logging.getLogger("logfile")
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
            logger.info("Integrated mapping (layout creation) activated.")
        except:
            mapping = False
            logger.info("Integrated mapping deactivated.")
        try:
            habitat_analysis = args[2]
        except:
            habitat_analysis = False
            logger.info("Physical feature stability analysis only.")
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

    logger.info("lifespan_design.raster_maker initiated with feature list = " + str(feature_list) + "\nUnit system: " +
                str(unit_system))

    # set environment settings
    temp_path = os.getcwd() + "\\.cache\\"
    fGl.chk_dir(temp_path)

    reach_reader = cRM.Read()
    reaches = cDef.ReachDefinitions()

    outputs = []

    for r in reach_ids:
        if reach_ids.__len__() < 8:
            reach_extents = reach_reader.get_reach_coordinates(reaches.dict_id_int_id[r])
        else:
            reach_extents = "MAXOF"
        if r == reach_ids[0]:
            output_dir = fGl.make_output_dir(condition, reach_ids, habitat_analysis, feature_list)
            outputs.append(output_dir)
        # fGl.clean_dir(output_dir)
        for f in feature_list:
            logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
            if reach_extents == "MAXOF":
                logger.info("FEATURE: " + str(f))
            else:
                logger.info("FEATURE (REACH: " + reaches.dict_id_names[r] + "): " + str(f))
            logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")
            feature = cFe.FeatureContainer(f)  # instantiate object containing all restoration feature attributes

            if not feature.sub:
                analysis(feature.feature, condition, reach_extents, habitat_analysis, output_dir, unit_system, wildcard,
                         manning_n, extent_type)
            else:
                sub_feature = cFe.FeatureContainer(f, feature.sub)
                analysis(sub_feature.feature, condition, reach_extents, habitat_analysis, output_dir, unit_system,
                         wildcard, manning_n, extent_type)
        if reach_extents == "MAXOF":
            break

    try:
        fGl.rm_dir(temp_path)  # dump cache after feature analysis
    except:
        logger.info("WARNING: Package could not remove .cache folder.")
    logger.info("RASTERS FINISHED.")

    if mapping:
        outputs = map_maker(outputs)

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

