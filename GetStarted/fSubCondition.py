try:
    import os, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, logging).")

try:
    import arcpy
except:
    print("ExceptionERROR: arcpy is not available (check license connection?)")
try:
    from arcpy.sa import *
except:
    print("ExceptionERROR: Spatial Analyst (arcpy.sa) is not available (check license?)")


def make_sub_condition(source_condition, target_condition, base_ras_name):
    # source_condition =  STR of a source condition ("D:\\...\\RiverArchitect\\01_Conditions\\2017\\")
    # target_condition = STR of a target condition ("D:\\...\\RiverArchitect\\01_Conditions\\2017_confinement\\")
    # base_ras_name = STR of a full path and name of a raster that is used for limiting raster extents ("D:\\...\\Rasters\\projectarea")

    script_dir = os.path.dirname(os.path.realpath(__file__)) + "\\"
    logger = logging.getLogger('logfile.log')
    logger.info(" * Setting arcpy environment ...")
    
    try:
        arcpy.CheckOutExtension('Spatial')
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = script_dir        
    except:
        logger.info("ERROR: Could not set arcpy environment (permissions and licenses?).")
        return True

    try:
        logger.info(" * Loading boundary Raster ...")
        base_ras = arcpy.Raster(base_ras_name.split('.aux')[0])
        arcpy.env.extent = base_ras.extent
    except:
        logger.info("ERROR: Could not load boundary Raster: " + str(base_ras_name).split('.aux')[0])
        return True

    logger.info(" * Looking for source GeoTIFFs in %s ..." % source_condition)
    geotiff_names = [i for i in os.listdir(source_condition) if i.endswith('.tif')]

    for gtiff_full_name in geotiff_names:
        logger.info("  > Loading " + str(gtiff_full_name) + " ... ")
        try:
            gtiff_full = arcpy.Raster(source_condition + gtiff_full_name)
        except:
            logger.info("ERROR: Could not read source file (%s)." % str(source_condition + gtiff_full_name))
            continue
        logger.info("     * Cropping raster ... ")
        try:
            gtiff_cropped = Con(~IsNull(base_ras), Float(gtiff_full))
        except:
            logger.info("ERROR: Could not crop " + str(gtiff_full_name))
            continue
        logger.info("     * Saving cropped raster as " + target_condition + gtiff_full_name + " ... ")
        try:
            gtiff_cropped.save(target_condition + gtiff_full_name)
            logger.info("     * OK")
        except:
            logger.info("ERROR: Could not save " + str(target_condition + gtiff_full_name))

    arcpy.CheckInExtension('Spatial')
    logger.info(" * Spatial Sub-Condition creation complete..")

    # return Error=False after successful execution
    return False
