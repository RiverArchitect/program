# !/usr/bin/python
# Desc.: Provides classes
try:
    import sys, os
    # add folder containing package routines to the system path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cActionAssessment as ca
    import cMapActions as cm
    import cFeatureActions as cf

    # load relevant files from lifespan_design
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
    import logging

except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")
    print(
        "       PACKAGE requirement: cMapActions, cFeatureActions, cActionAssessment, /.site_packages/riverpy/fGlobal.")


def logging_start(logfile_name):
    logfilenames = ["error.log", logfile_name + ".log", "logfile.log"]
    for fn in logfilenames:
        fn_full = os.path.join(os.getcwd(), fn)
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
    return(logger)


def logging_stop(logger):
    # stop logging and release logfile
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)


def layout_maker(condition, feature_type):
    # prepares layout of all available rasters in OutputRasters/condition folder
    fn_full = os.path.join(os.getcwd(), "mxd_logfile.log")
    if os.path.isfile(fn_full):
        try:
            os.remove(fn_full)
            print("Overwriting old mxd_logfile.log")
        except:
            print("WARNING: Old logfiles is locked (mxd).")

    mapper = cm.Mapper(condition)
    mapper.prepare_layout(feature_type)
    mapper.stop_logging("layout")


def map_maker(condition, *args):
    # maps all available layouts (.mxd files) in OutputMaps/condition/Layouts folder
    # *args[0] = optional: alternative path for input layouts
    fn_full = os.path.join(os.getcwd(), "map_logfile.log")
    if os.path.isfile(fn_full):
        try:
            os.remove(fn_full)
            print("Overwriting old map_logfile.log")
        except:
            print("WARNING: Old logfile is locked (mapping).")
    mapper = cm.Mapper(condition)
    try:
        mapper.make_pdf_maps(args[0])
        print("Alternative layout input directory provided:")
        print(args[0])
    except:
        mapper.make_pdf_maps()

    mapper.stop_logging()
    if not mapper.error:
        fg.open_folder(mapper.output_map_dir)


def geo_file_maker(condition, feature_type, *args):
    # type is either "terraforming", "plantings", "bioengineering" or "maintenance"
    allowed_feature_types = ["terraforming", "plantings", "bioengineering", "maintenance"]
    try:
        arguments = True
    except:
        arguments = False

    if not arguments:
        mapping = False
        unit_system = "us"
    else:
        try:
            mapping = args[0]
            if mapping:
                print("Integrated mapping (layout creation) activated.")
            else:
                print("Integrated mapping deactivated.")
        except:
            mapping = False
            print("Integrated mapping deactivated.")
        try:
            unit_system = args[1]
        except:
            unit_system = "us"

    logger = logging_start("max_lifespan")
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

    try:
        alternate_inpath = args[2]
        feature_assessment = ca.ArcPyContainer(condition, feature_type, unit_system, alternate_inpath)
    except:
        feature_assessment = ca.ArcPyContainer(condition, feature_type, unit_system)
    feature_assessment()  # call data processing

    if mapping:
        layout_maker(condition, feature_type)
        map_maker(condition)

    try:
        # erase traces
        del feature_assessment
        fg.rm_dir(temp_path)  # dump cache after feature analysis
    except:
        logger.info("WARNING: Could not remove .cache.")

    logging_stop(logger)


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

