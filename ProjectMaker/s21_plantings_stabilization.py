# !/usr/bin/python
try:
    import sys, os, logging
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionError: Could not import packages (sys, os, logging, riverpy)")

try:
    import arcpy
    from arcpy.sa import *
except:
    print("ArcGIS ERROR: No SpatialAnalyst extension available.")


def main(best_plant_dir=str(), lf_dir=str(), crit_lf=float(), prj_name=str(), unit=str(), version=str()):
    """ derive and draw stabilizing features for vegetation plantings
    crit_lf = 2.5               # years of minimum plant survival without stabilization
    prj_name = "TBR"             # corresponding to folder name
    unit = "us" or "si"
    version = "v10"             # type() =  3-char str: vII
    """
    logger = logging.getLogger("logfile")
    logger.info("STABILIZING PLANTS ----- ----- ----- -----")
    error = False
    if unit == "us":
        area_units = "SQUARE_FEET_US"
        ft2_to_acres = config.ft2ac 
    else:
        area_units = "SQUARE_METERS"
        ft2_to_acres = 1.0

    arcpy.CheckOutExtension('Spatial')
    arcpy.gp.overwriteOutput = True

    dir2pp = config.dir2pm + prj_name + "_" + version + "\\"

    # folder settings
    ras_dir = dir2pp + "Geodata\\Rasters\\"
    shp_dir = dir2pp + "Geodata\\Shapefiles\\"
    quant_dir = dir2pp + "Quantities\\"

    # file and variable settings
    xlsx_target = dir2pp + prj_name + "_assessment_" + version + ".xlsx"
    feature_dict = {"Large wood": 211,
                    "ELJs (plantings)": 212,
                    "Bioengineering (veget.)": 213,
                    "Bioengineering (mineral)": 214,
                    "Angular boulders (instream)": 215}

    # LOOK UP INPUT RASTERS
    try:
        logger.info("Looking up maximum lifespan rasters ...")
        max_lf_plants = arcpy.Raster(ras_dir + "max_lf_pl_c.tif")
        logger.info(" >> Vegetation plantings OK.")
        logger.info(" -- OK (MaxLifespan raster read)\n")
    except:
        logger.info("ERROR: Could not find MaxLifespan Rasters.")
        return -1
    try:
        logger.info("Looking up specific bioengineering lifespan rasters ...")
        logger.info(best_plant_dir + "lf_wood.tif")
        try:
            lf_wood = arcpy.Raster(lf_dir + "lf_wood.tif")
        except:
            lf_wood = arcpy.Raster(lf_dir + "lf_wood")
        logger.info(" >> Added Streamwood.")
        try:
            lf_bio = arcpy.Raster(lf_dir + "lf_bio.tif")
        except:
            lf_bio = arcpy.Raster(lf_dir + "lf_bio")
        logger.info(" >> Added Other bioengineering.")
        logger.info(" -- OK (Bioengineering raster read)\n")
    except:
        logger.info("ERROR: Could not find Bioengineering (other) Rasters (%s)." % lf_dir)
        return -1

    # EVALUATE BEST STABILIZATION FEATURES
    try:
        logger.info("Assessing best features for plant stabilization.")
        arcpy.env.extent = max_lf_plants.extent
        best_stab = Con(max_lf_plants <= crit_lf, Con(~IsNull(lf_wood), Con(lf_wood > crit_lf,
                                                                            Int(feature_dict["Large wood"]),
                                                                            Int(feature_dict["ELJs (plantings)"])),
                                                      Con(~IsNull(lf_bio), Con(lf_bio > crit_lf,
                                                                               Int(feature_dict["Bioengineering (veget.)"]),
                                                                               Int(feature_dict["Bioengineering (mineral)"])),
                                                          Int(feature_dict["Angular boulders (instream)"]))))
        logger.info(" -- OK (Stabilization assessment.)\n")
    except:
        logger.info("ERROR: Best stabilization assessment failed.")
        return -1

    # SAVE RASTERS
    try:
        logger.info("Saving results raster as " + ras_dir + "plant_stab.tif")
        best_stab.save(ras_dir + "plant_stab.tif")
        logger.info(" -- OK (Raster saved.)\n")
    except:
        logger.info("ERROR: Result geofile saving failed.")
        return -1

    # SHAPEFILE CONVERSION AND STATS
    try:
        logger.info("Extracting quantities from geodata ...")
        logger.info(" >> Converting results raster to polygon shapefile ...")
        p_stab_shp = shp_dir + "Plant_stab.shp"
        try:
            arcpy.RasterToPolygon_conversion(Int(best_stab), p_stab_shp, "NO_SIMPLIFY")
            if not fGl.verify_shp_file(p_stab_shp):
                logger.info("NO STABILIZATION MEASURE IDENTIFIED (EMPTY: %s)." % p_stab_shp)
                logger.info(fGl.open_file(xlsx_target))
                return -1
        except:
            logger.info("NOTHING TO DO. Consider to increase the critical lifespan threshold.")
        logger.info(" >> Calculating area statistics ... ")
        try:
            arcpy.AddField_management(p_stab_shp, "F_AREA", "FLOAT", 9)
        except:
            logger.info("    * field F_AREA already exists or the dataset is opened by another software.")
        try:
            arcpy.CalculateGeometryAttributes_management(p_stab_shp, geometry_property=[["F_AREA", "AREA"]],
                                                         area_unit=area_units)
        except:
            logger.info("    * no plant stabilization applicable ")

        logger.info(" >> Adding field (stabilizing feature) ... ")
        try:
            arcpy.AddField_management(p_stab_shp, "Stab_feat", "TEXT")
        except:
            logger.info("    * field Stab_feat already exists ")
        logger.info(" >> Evaluating field (stabilizing feature) ... ")
        inv_feature_dict = {v: k for k, v in feature_dict.items()}
        code_block = "inv_feature_dict = " + str(inv_feature_dict)
        try:
            arcpy.CalculateField_management(p_stab_shp, "Stab_feat", "inv_feature_dict[!gridcode!]", "PYTHON", code_block)
        except:
            logger.info("    * no plant stabilization added ... ")
        logger.info(" >> Exporting tables ...")
        arcpy.TableToTable_conversion(p_stab_shp, quant_dir, "plant_stab.txt")
        logger.info(" -- OK (Quantity export)\n")
    except:
        logger.info("ERROR: Shapefile operations failed.")
        return -1

    # PREPARE AREA DATA (QUANTITIES)
    logger.info("Processing table statistics ...")
    write_dict = {}
    for k in feature_dict.keys():
        write_dict.update({k: 0.0})  # set to zero for surface count

    stat_data = fGl.read_txt(quant_dir + "plant_stab.txt")
    logger.info(" >> Extracting relevant area sizes ...")

    for row in stat_data:
        try:
            write_dict[inv_feature_dict[int(row[0])]] += row[1]
        except:
            logger.info("      --- Unknown key: " + str(int(row[0])))
            error = True

    if unit == "us":
        logger.info(" >> Converting ft2 to acres ...")
        for k in write_dict.keys():
            write_dict[k] = write_dict[k] * float(ft2_to_acres)
    logger.info(" -- OK (Area extraction finished)\n")

    # WRITE AREA DATA TO EXCEL FILE
    logger.info("Writing results to costs workbook (sheet: from_geodata) ...")
    fGl.write_dict2xlsx(write_dict, xlsx_target, "B", "C", 12)

    # CLEAN UP useless shapefiles
    logger.info("Cleaning up redundant shapefiles ...")
    arcpy.env.workspace = shp_dir
    all_shps = arcpy.ListFeatureClasses()
    for shp in all_shps:
        if "_del" in str(shp):
            try:
                arcpy.Delete_management(shp)
            except:
                logger.info(str(shp) + " is locked. Remove manually to avoid confusion.")
    arcpy.env.workspace = dir2pp + "Geodata\\"
    logger.info(" -- OK (Clean up)\n")

    if not error:
        fGl.open_file(xlsx_target)


if __name__ == "__main__":
    crit_lf = float(input('Please enter a minimum survival duration for plantings in years (e.g., 2.5) >> '))
    prj_name = str(input('Please enter a Project Name ("ProjectName") >> '))
    unit = str(input('Please enter a unit system ("us" or "si") >> '))
    version = str(input('Please enter a version number ("vii") >> '))
    main(config.dir2ml, crit_lf, prj_name, unit, version)
