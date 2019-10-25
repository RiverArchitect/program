# !/usr/bin/python
try:
    import sys, os, logging
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
    sys.path.append(config.dir2lf)
    import cParameters as cPa
    import cReadInpLifespan as cRIL
except:
    print("ExceptionError: Could not import packages (sys, os, logging, riverpy)")

try:
    import arcpy
    from arcpy.sa import *
except:
    print("ArcGIS ERROR: No SpatialAnalyst extension available.")


def main(lf_dir=str(), crit_lf=float(), prj_name=str(), unit=str(), version=str(), n_m=float(), txcr=float(), s_sed=2.68):
    """ derive and draw stabilizing features for vegetation plantings
    crit_lf = 2.5               # years of minimum plant survival without stabilization
    prj_name = "TBR"             # corresponding to folder name
    unit = "us" or "si"
    version = "v10"             # type() =  3-char str: vII
    n_m = Mannings n
    txcr = critical dimensionless bed shear stress for grain motion
    s_sed = grain
    """
    logger = logging.getLogger("logfile")
    logger.info("STABILIZING TERRAIN ----- ----- ----- -----")
    error = False
    if unit == "us":
        area_units = "SQUARE_FEET_US"
        ft2_to_acres = config.ft2ac
        n_m = n_m / 1.49  # (s/ft^(1/3)) global Manning's n where k =1.49 converts to US customary
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
                    "Bioengineering (veget.)": 213,
                    "Bioengineering (mineral)": 214,
                    "Angular boulders (instream)": 215}

    # LOOK UP INPUT RASTERS
    try:
        project_ras = arcpy.Raster(ras_dir + "ProjectArea.tif")
    except:
        try:
            project_ras = arcpy.Raster(ras_dir + "projectarea.tif")
        except:
            logger.info("ERROR: Could not create Raster of the project area.")
            return -1

    try:
        hy_condition = lf_dir.split("_lyr")[0].split("\\")[-1].split("/")[-1]
        logger.info("Looking up hydraulic Rasters for %s ..." % hy_condition)
    except:
        logger.info("ERROR: Could not find hydraulic Rasters (associated with %s)." % lf_dir)
        return -1
    try:
        h = cPa.FlowDepth(hy_condition)
        u = cPa.FlowVelocity(hy_condition)
        info = cRIL.Info(hy_condition)
        lifespans = info.lifespan_read()
    except:
        logger.info("ERROR: Could not find hydraulic Rasters (01_Conditions/%s)." % hy_condition)
        return -1

    try:
        logger.info("Looking up grain lifespan Raster ...")
        max_lf_grains = arcpy.Raster(lf_dir + "lf_grains.tif")
    except:
        logger.info("ERROR: Could not find Lifespan Raster (%slf_grains.tif)." % lf_dir)
        return -1

    logger.info("Retrieving wood lifespan Raster ...")
    try:
        lf_wood = arcpy.Raster(lf_dir + "lf_wood.tif")
    except:
        lf_wood = Float(0.0)
        logger.info("WARNING: Could not find Lifespan Raster (%slf_wood.tif) -- continue anyway using 0-wood-lifespans ..." % lf_dir)

    logger.info("Retrieving bioengineering lifespan Raster ...")
    try:
        lf_bio = arcpy.Raster(lf_dir + "lf_bio_v_bio.tif")
    except:
        lf_bio = Float(0.0)
        logger.info("WARNING: Could not find Lifespan Raster (%slf_bio.tif) -- continue anyway using 0-bio-lifespans ..." % lf_dir)
    logger.info(" -- OK (Lifespan Rasters read)\n")

    # EVALUATE BEST STABILIZATION FEATURES
    tar_lf = fGl.get_closest_val_in_list(lifespans, crit_lf)
    if int(tar_lf) != int(crit_lf):
        logger.info(
            "WARNING: Substituting user-defined crit. lifespan ({0}) with {1} (Condition: {2}).".format(str(crit_lf),
                                                                                                        str(tar_lf),
                                                                                                        hy_condition))
    try:
        logger.info("Calculating required stable grains sizes to yield a lifespan of %s years ..." % str(tar_lf))
        arcpy.env.extent = max_lf_grains.extent
        i = lifespans.index(int(tar_lf))
        stab_grain_ras = Con(~IsNull(project_ras), Float(Square(u.rasters[i] * Float(n_m)) / ((Float(s_sed) - 1.0) * Float(txcr) * Power(h.rasters[i], (1 / 3)))))
    except arcpy.ExecuteError:
        logging.info("ExecuteERROR: (arcpy).")
        logging.info(arcpy.GetMessages(2))
        arcpy.AddError(arcpy.GetMessages(2))
        return -1
    except Exception as e:
        logging.info("ExceptionERROR: (arcpy).")
        logging.info(e.args[0])
        arcpy.AddError(e.args[0])
        return -1
    except:
        logging.info("ERROR: Could not calculate stable grain size Raster for %s." % str(tar_lf))
        logging.info(arcpy.GetMessages())
        return -1

    try:
        logger.info("Assigning stabilization features (hierarchy: Streamwood -> Bioengineering (other) -> Boulder paving")
        arcpy.env.extent = max_lf_grains.extent
        best_stab_i = Con(max_lf_grains <= crit_lf, Con(~IsNull(lf_wood), Con(lf_wood > crit_lf,
                                                                              Int(feature_dict["Large wood"])),
                                                        Con(~IsNull(lf_bio), Con(lf_bio > crit_lf,
                                                                                 Int(feature_dict["Bioengineering (veget.)"]),
                                                                                 Int(feature_dict["Bioengineering (mineral)"])),
                                                            Int(feature_dict["Angular boulders (instream)"]))))
        best_boulders = Con(max_lf_grains <= crit_lf, Con(IsNull(best_stab_i), Float(stab_grain_ras)))
        best_stab = Con(IsNull(best_stab_i), Con(~IsNull(best_boulders), Int(feature_dict["Angular boulders (instream)"])), Int(best_stab_i))
        logger.info(" -- OK (Stabilization assessment)\n")
    except:
        logger.info("ERROR: Best stabilization assessment failed.")
        return -1

    # SAVE RASTERS
    try:
        logger.info("Saving results Raster " + ras_dir + "terrain_stab.tif")
        best_stab.save(ras_dir + "terrain_stab.tif")
        logger.info(" -- OK (Raster saved.)")
    except:
        logger.info("ERROR: Result geofile saving failed.")
    try:
        logger.info("Saving results Raster " + ras_dir + "terrain_boulder_stab.tif")
        best_boulders.save(ras_dir + "terrain_boulder_stab.tif")
        logger.info(" -- OK (Stabilization Rasters saved)\n")
    except:
        logger.info("ERROR: Result geofile saving failed.")

    # SHAPEFILE CONVERSION AND STATS
    try:
        logger.info("Extracting quantities from geodata ...")
        logger.info(" >> Converting terrain_stab.tif to polygon shapefile ...")
        t_stab_shp = shp_dir + "Terrain_stab.shp"
        conversion_success = True
        try:
            arcpy.RasterToPolygon_conversion(best_stab, t_stab_shp, "NO_SIMPLIFY")
            if not fGl.verify_shp_file(t_stab_shp):
                logger.info("NO BIOENGINEERING STABILIZATION MEASURE IDENTIFIED (EMPTY: %s)." % t_stab_shp)
        except:
            conversion_success = True

        logger.info(" >> Converting terrain_boulder_stab.tif to layer ...")
        t_boulder_shp = shp_dir + "Terrain_boulder_stab.shp"
        try:
            arcpy.RasterToPolygon_conversion(Int(best_boulders + 1.0), t_boulder_shp, "NO_SIMPLIFY")
            if not fGl.verify_shp_file(t_stab_shp):
                logger.info("NO BOULDER STABILIZATION MEASURE IDENTIFIED (EMPTY: %s)." % t_boulder_shp)
        except:
            if not conversion_success:
                logger.info("No stabilization requirement identified. Returning without action.")
                return -1

        logger.info(" >> Calculating area statistics ... ")
        try:
            arcpy.AddField_management(t_stab_shp, "F_AREA", "FLOAT", 9)
        except:
            logger.info("    * field F_AREA already exists or the dataset is opened by another software.")
        try:
            arcpy.CalculateGeometryAttributes_management(t_stab_shp, geometry_property=[["F_AREA", "AREA"]],
                                                         area_unit=area_units)
        except:
            logger.info("    * no terrain stabilization applicable ")

        logger.info(" >> Adding field (stabilizing feature) ... ")
        try:
            arcpy.AddField_management(t_stab_shp, "Stab_feat", "TEXT")
        except:
            logger.info("    * field Stab_feat already exists ")
        logger.info(" >> Evaluating field (stabilizing feature) ... ")
        inv_feature_dict = {v: k for k, v in feature_dict.items()}
        code_block = "inv_feature_dict = " + str(inv_feature_dict)
        try:
            arcpy.CalculateField_management(t_stab_shp, "Stab_feat", "inv_feature_dict[!gridcode!]", "PYTHON", code_block)
        except:
            logger.info("    * no plant stabilization added ... ")
        logger.info(" >> Exporting tables ...")
        arcpy.TableToTable_conversion(t_stab_shp, quant_dir, "terrain_stab.txt")
        logger.info(" -- OK (Quantity export)\n")
    except:
        logger.info("ERROR: Shapefile operations failed.")
        return -1

    # PREPARE AREA DATA (QUANTITIES)
    logger.info("Processing table statistics ...")
    write_dict = {}
    for k in feature_dict.keys():
        write_dict.update({k: 0.0})  # set to zero for surface count

    stat_data = fGl.read_txt(quant_dir + "terrain_stab.txt")
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
    fGl.write_dict2xlsx(write_dict, xlsx_target, "E", "F", 12)

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
