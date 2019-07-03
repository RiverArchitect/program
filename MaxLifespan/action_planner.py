# !/usr/bin/python
try:
    import sys, os, logging, random
    # add folder containing package routines to the system path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cActionAssessment as cAA
    import cFeatureActions as cFA

    # load classes files from riverpy
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cMapper as cMp
    import fGlobal as fGl
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging, random, riverpy).")


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
        fGl.open_folder(mapper.output_dir)


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

    feature_assessment = cAA.ArcPyContainer(condition, feature_type, dir_base_ras, unit_system, alternate_inpath)
    feature_assessment()  # call data processing

    try:
        cache_dir = str(feature_assessment.cache)
        del feature_assessment
        fGl.cool_down(5)
        fGl.rm_dir(cache_dir)  # dump cache after feature analysis
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
        print("Bad input.")
