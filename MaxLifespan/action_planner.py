# !/usr/bin/python
try:
    import sys, os, logging
    # add folder containing package routines to the system path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cActionAssessment as ca
    import cFeatureActions as cf

    # load classes files from riverpy
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cMapper as cm
    import fGlobal as fg
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")
    print(
        "       PACKAGE requirement: cFeatureActions, cActionAssessment, /.site_packages/riverpy/fGlobal+cMapper.")


def logging_start(logfile_name):
    try:
        logging_stop(logfile_name)
    except:
        pass
    logfilenames = ["error.log", logfile_name + ".log", "logfile.log"]
    for fn in logfilenames:
        fn_full = os.path.dirname(os.path.abspath(__file__)) + "\\" + fn
        if os.path.isfile(fn_full):
            try:
                os.remove(fn_full)
                print("Overwriting old logfiles (" + fn + ").")
            except:
                print("WARNING: Old logfile is locked (geo_file_maker).")
    # start logging
    logger = logging.getLogger(logfile_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(message)s")

    # create console handler and set level to info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # create error file handler and set level to error
    err_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[0]), "w", encoding=None, delay="true")
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)
    logger.addHandler(err_handler)
    # create debug file handler and set level to debug
    debug_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[1]), "w")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)
    logger.info(logfile_name + ".max_lifespan initiated")
    return logger


def logging_stop(logger):
    # stop logging and release logfile
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)


def map_maker(condition, feature_groups, *args):
    # condition = STR for identifying feature input dir
    # feature_group = LIST of feature groups
    # args[0] = alternative input dir
    try:
        mapper = cm.Mapper(condition, "mlf", args[0])
    except:
        mapper = cm.Mapper(condition, "mlf")
    mapper.prepare_layout(True, map_items=feature_groups)

    if not mapper.error:
        fg.open_folder(mapper.output_dir)


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

    logger = logging_start("logfile")
    logger.info("*** unit system: " + str(unit_system))
    logger.info("*** condition: " + str(condition))
    if not(feature_type in allowed_feature_types):
        feature_type = "terraforming"
        logger.info("Bad argument type. Applying: " + str(feature_type))

    # set environment
    temp_path = os.getcwd() + "\\.cache\\"
    if os.path.exists(temp_path):
        fg.rm_dir(temp_path)  # delete cache if there are remainders from previous analysis
        logger.info("Found and deleted old .cache folder.")
    fg.chk_dir(temp_path)

    feature_assessment = ca.ArcPyContainer(condition, feature_type, dir_base_ras, unit_system, alternate_inpath)
    feature_assessment()  # call data processing

    try:
        # erase traces
        del feature_assessment
        fg.rm_dir(temp_path)  # dump cache after feature analysis
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
        geo_file_maker(condition, feature_type)
    except:
        print("Bad input. Using default condition (2008) and feature_type (terraforming).")
        geo_file_maker(condition="2008", feature_type="terraforming")
