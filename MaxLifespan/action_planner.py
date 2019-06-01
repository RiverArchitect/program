# !/usr/bin/python
try:
    import sys, os, logging
    # add folder containing package routines to the system path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cActionAssessment as cAA
    import cFeatureActions as cFA

    # load classes files from riverpy
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cMapper as cMp
    import fGlobal as fG
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")
    print(
        "       PACKAGE requirement: cFeatureActions, cActionAssessment, /.site_packages/riverpy/fGlobal+cMapper.")


def map_maker(condition, feature_groups, *args):
    # condition = STR for identifying feature input dir
    # feature_group = LIST of feature groups
    # args[0] = alternative input dir
    try:
        mapper = cMp.Mapper(condition, "mlf", args[0])
    except:
        mapper = cMp.Mapper(condition, "mlf")
    mapper.prepare_layout(True, map_items=feature_groups)

    if not mapper.error:
        fG.open_folder(mapper.output_dir)


def geo_file_maker(condition, feature_type, dir_base_ras, *args, **kwargs):
    # feature_type = STR - either "terraforming", "plantings", "bioengineering" or "maintenance"
    # kwargs: unit_system ("us" or "si"), alternate_inpath (STR)

    allowed_feature_types = ["terraforming", "plantings", "bioengineering", "maintenance"]
    unit_system = "us"
    alternate_inpath = None
    try:
        for k in kwargs.items():
            if "unit_system" in k[0].lower():
                unit_system = str(k[1]).lower()
            if "alternate_inpath" in k[0].lower():
                alternate_inpath = k[1]
    except:
        pass

    logger = logging.getLogger("logfile")
    logger.info("*** unit system: " + str(unit_system))
    logger.info("*** condition: " + str(condition))
    if not(feature_type in allowed_feature_types):
        feature_type = "terraforming"
        logger.info("Bad argument type. Applying: " + str(feature_type))

    # set environment
    temp_path = os.getcwd() + "\\.cache\\"
    if os.path.exists(temp_path):
        fG.rm_dir(temp_path)  # delete cache if there are remainders from previous analysis
        logger.info("Found and deleted old .cache folder.")
    fG.chk_dir(temp_path)

    feature_assessment = cAA.ArcPyContainer(condition, feature_type, dir_base_ras, unit_system, alternate_inpath)
    feature_assessment()  # call data processing

    try:
        # erase traces
        del feature_assessment
        fG.rm_dir(temp_path)  # dump cache after feature analysis
    except:
        logger.info("WARNING: Could not remove .cache.")


# enable script to run stand-alone
if __name__ == "__main__":
    # query condition
    condition = str(input('Enter condition (shape: >> XXXX, e.g., >> 2008 ) \n>> '))
    # try query feature_type
    feature_type = str(input('Enter feature type (e.g.: >> \'terraforming\') \n>> '))

    # launch raster maker for lifespan and design rasters
    try:
        geo_file_maker(condition, feature_type, os.getcwd())
    except:
        print("Bad input. Using default condition (2008) and feature_type (terraforming).")
        geo_file_maker(condition="2008", feature_type="terraforming")
