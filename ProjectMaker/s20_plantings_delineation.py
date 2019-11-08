# !/usr/bin/python
try:
    import sys, os, logging
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cDefinitions as cDef
    import config
    import fGlobal as fGl
except:
    print("ExceptionError: Could not find own packages (./site_packages/riverpy/)")

try:
    import arcpy
    from arcpy.sa import *
except:
    print("ArcGIS ERROR: No SpatialAnalyst extension available.")


def main(maxlf_dir=str(), min_lf=float(), prj_name=str(), unit=str(), version=str()):
    """ delineate optimum plantings
    required input variables:
    min_lf = minimum plant lifespan where plantings are considered
    prj_name = "TBR"  #  (corresponding to folder name)
    prj_name = "BartonsBar" (for example)
    unit = "us" or "si"
    version = "v10"  # type() =  3-char str: vII
    """
    logger = logging.getLogger("logfile")

    logger.info("PLACE OPTIMUM PLANT SPECIES ----- ----- ----- -----")
    features = cDef.FeatureDefinitions(False)  # read feature IDs (required to identify plants)

    if unit == "us":
        area_units = "SQUARE_FEET_US"
        ft2_to_acres = config.ft2ac
    else:
        area_units = "SQUARE_METERS"
        ft2_to_acres = 1.0
    arcpy.CheckOutExtension('Spatial')
    arcpy.gp.overwriteOutput = True

    path2pp = config.dir2pm + prj_name + "_" + version + "\\"

    # folder settings 
    ras_dir = path2pp + "Geodata\\Rasters\\"
    shp_dir = path2pp + "Geodata\\Shapefiles\\"
    quant_dir = path2pp + "Quantities\\"
    fGl.del_ovr_files(path2pp)  # Delete temporary raster calculator files

    # file settings
    xlsx_target = path2pp + prj_name + "_assessment_" + version + ".xlsx"

    action_ras = {}
    try:
        logger.info("Looking up MaxLifespan Rasters ...")
        arcpy.env.workspace = maxlf_dir
        action_ras_all = arcpy.ListRasters()
        logger.info(" >> Source directory: " + maxlf_dir)
        arcpy.env.workspace = path2pp + "Geodata\\"
        for aras in action_ras_all:
            for plant in features.id_list_plants:
                if plant in str(aras):
                    logger.info("   -- found: " + maxlf_dir + str(aras))
                    action_ras.update({aras: arcpy.Raster(maxlf_dir + aras)})
            if ("max" in str(aras)) and ("plant" in str(aras)):
                max_lf_plants = arcpy.Raster(maxlf_dir + aras)
        logger.info(" -- OK (read Rasters)\n")
    except:
        logger.info("ERROR: Could not find action Rasters.")
        return -1

    # CONVERT PROJECT SHAPEFILE TO RASTER
    try:
        logger.info("Converting Project Shapefile to Raster ...")
        arcpy.env.workspace = shp_dir
        arcpy.PolygonToRaster_conversion("ProjectArea.shp", "AreaCode", ras_dir + "ProjectArea.tif",
                                         cell_assignment="CELL_CENTER", priority_field="NONE", cellsize=1)
        logger.info(" -- OK. Loading project raster ...")
        arcpy.env.workspace = path2pp + "Geodata\\"
        prj_area = arcpy.Raster(ras_dir + "ProjectArea.tif")
        logger.info(" -- OK (Shapefile2Raster conversion)\n")
    except arcpy.ExecuteError:
        logger.info("ExecuteERROR: (arcpy).")
        logger.info(arcpy.GetMessages(2))
        arcpy.AddError(arcpy.GetMessages(2))
        return -1
    except Exception as e:
        logger.info("ExceptionERROR: (arcpy).")
        logger.info(e.args[0])
        arcpy.AddError(e.args[0])
        return -1
    except:
        logger.info("ExceptionERROR: (arcpy) Conversion failed.")
        return -1

    # CONVERT EXISTING PLANTS SHAPEFILE TO RASTER
    try:
        logger.info("Converting PlantExisting.shp Shapefile to Raster ...")
        arcpy.env.workspace = shp_dir
        arcpy.PolygonToRaster_conversion(shp_dir + "PlantExisting.shp", "gridcode", ras_dir + "PlantExisting.tif",
                                         cell_assignment="CELL_CENTER", priority_field="NONE", cellsize=1)
        arcpy.env.workspace = path2pp + "Geodata\\"
        logger.info(" -- OK (Shapefile2Raster conversion)\n")
    except arcpy.ExecuteError:
        logger.info("ExecuteERROR: (arcpy).")
        logger.info(arcpy.GetMessages(2))
        arcpy.AddError(arcpy.GetMessages(2))
        arcpy.CreateRasterDataset_management(ras_dir, "PlantExisting.tif", "1", "8_BIT_UNSIGNED", "World_Mercator.prj",
                                             "3", "", "PYRAMIDS -1 NEAREST JPEG",
                                             "128 128", "NONE", "")
    except Exception as e:
        logger.info("ExceptionERROR: (arcpy).")
        logger.info(e.args[0])
        arcpy.AddError(e.args[0])
    except:
        logger.info("WARNING: PlantExisting.shp is corrupted or non-existent.")
    logger.info(" >> Loading existing plant raster ...")
    existing_plants = arcpy.Raster(ras_dir + "PlantExisting.tif")

    # RETAIN RELEVANT PLANTINGS ONLY
    shp_4_stats = {}
    try:
        logger.info("Analyzing optimum plant types in project area ...")
        logger.info(" >> Cropping maximum lifespan Raster ... ")
        arcpy.env.extent = prj_area.extent
        max_lf_crop = Con((~IsNull(prj_area) & ~IsNull(max_lf_plants)), Con(IsNull(existing_plants), Float(max_lf_plants)))
        logger.info(" >> Saving crop ... ")
        max_lf_crop.save(ras_dir + "max_lf_pl_c.tif")
        logger.info(" -- OK ")
        occupied_px_ras = ""
        for aras in action_ras.keys():
            plant_ras = action_ras[aras]
            if not('.tif' in str(aras)):
                aras_tif = str(aras) + '.tif'
                aras_no_end = aras
            else:
                aras_tif = aras
                aras_no_end = aras.split('.tif')[0]
            logger.info(" >> Applying MaxLifespan Raster({}) where lifespan > {} years.".format(str(plant_ras), str(min_lf)))
            __temp_ras__ = Con((~IsNull(prj_area) & ~IsNull(plant_ras)), Con((Float(max_lf_plants) >= min_lf), (max_lf_plants * plant_ras)))
            if arcpy.Exists(occupied_px_ras):
                logger.info(" >> Reducing to relevant pixels only ... ")
                __temp_ras__ = Con((IsNull(occupied_px_ras) & IsNull(existing_plants)), __temp_ras__)
                occupied_px_ras = Con(~IsNull(occupied_px_ras), occupied_px_ras,  __temp_ras__)
            else:
                occupied_px_ras = __temp_ras__
                __temp_ras__ = Con(IsNull(existing_plants), __temp_ras__)
            logger.info(" >> Saving raster ... ")
            __temp_ras__.save(ras_dir + aras_tif)
            logger.info(" >> Converting to shapefile (polygon for area statistics) ... ")
            try:
                shp_ras = Con(~IsNull(__temp_ras__), 1, 0)
                arcpy.RasterToPolygon_conversion(shp_ras, shp_dir + aras_no_end + ".shp", "NO_SIMPLIFY")
            except:
                logger.info("     !! " + aras_tif + " is not suitable for this project.")
            arcpy.env.workspace = maxlf_dir
            logger.info(" >> Calculating area statistics ... ")
            try:
                arcpy.AddField_management(shp_dir + aras_no_end + ".shp", "F_AREA", "FLOAT", 9)
            except:
                logger.info("    * field F_AREA already exists ")
            try:
                arcpy.CalculateGeometryAttributes_management(shp_dir + aras_no_end + ".shp",
                                                             geometry_property=[["F_AREA", "AREA"]],
                                                             area_unit=area_units)
                shp_4_stats.update({aras: shp_dir + aras_no_end + ".shp"})
            except:
                shp_4_stats.update({aras: config.dir2pm + ".templates\\area_dummy.shp"})
                logger.info("     !! Omitting (not applicable) ...")
            arcpy.env.workspace = path2pp + "Geodata\\"
        logger.info(" -- OK (Shapefile and raster analyses)\n")
        logger.info("Calculating area statistics of plants to be cleared for construction ...")
        try:
            arcpy.AddField_management(shp_dir + "PlantClearing.shp", "F_AREA", "FLOAT", 9)
        except:
            logger.info("    * cannot add field F_AREA to %s (already exists?)" % str(shp_dir + "PlantClearing.shp"))
        try:
            arcpy.CalculateGeometryAttributes_management(shp_dir + "PlantClearing.shp",
                                                         geometry_property=[["F_AREA", "AREA"]],
                                                         area_unit=area_units)
            shp_4_stats.update({"clearing": shp_dir + "PlantClearing.shp"})
        except:
            shp_4_stats.update({"clearing": config.dir2pm + ".templates\\area_dummy.shp"})
            logger.info("    * no clearing applicable ")
        logger.info(" -- OK (Statistic calculation)\n")
    except arcpy.ExecuteError:
        logger.info("ExecuteERROR: (arcpy).")
        logger.info(arcpy.GetMessages(2))
        arcpy.AddError(arcpy.GetMessages(2))
        return -1
    except Exception as e:
        logger.info("ExceptionERROR: (arcpy).")
        logger.info(e.args[0])
        arcpy.AddError(e.args[0])
        return -1
    except:
        logger.info("ExceptionERROR: (arcpy) Conversion failed.")
        return -1

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
    arcpy.env.workspace = path2pp + "Geodata\\"
    logger.info(" -- OK (Clean up)\n")

    # EXPORT STATISTIC TABLES
    logger.info("Exporting table statistics ...")
    stat_files = {}
    for ts in shp_4_stats.keys():
        try:
            logger.info(" >> Exporting " + str(shp_4_stats[ts]) + " area ...")
            arcpy.TableToTable_conversion(shp_4_stats[ts], quant_dir, "plant_" + ts + ".txt")
            stat_files.update({ts: quant_dir + "plant_" + ts + ".txt"})
        except:
            logger.info("    !! EXPORT FAILED")
            return -1
    logger.info(" -- OK (Table export)\n")

    arcpy.CheckInExtension('Spatial')

    # PREPARE AREA DATA (QUANTITIES)
    logger.info("Processing table statistics ...")
    write_dict = {}
    for sf in stat_files.keys():
        stat_data = fGl.read_txt(stat_files[sf])
        logger.info("     --> Extracting relevant area ...")
        polygon_count = 0
        total_area_ft2 = 0.0
        for row in stat_data:
            if row[0] == 1:
                total_area_ft2 += row[1]
                polygon_count += 1
        write_dict.update({sf: total_area_ft2 * float(ft2_to_acres)})
        logger.info("     --> OK")
    logger.info(" -- OK (Area extraction finished).")

    # WRITE AREA DATA TO EXCEL FILE
    logger.info("Writing results ...")
    fGl.write_dict2xlsx(write_dict, xlsx_target, "B", "C", 4)

    logger.info(" -- OK (PLANT PLACEMENT FINISHED)\n")
    return ras_dir


if __name__ == "__main__":
    dir2AP = str(input('Please enter the path to the RiverArchitect module (e.g., "D:/RiverArchitect/MaxLifespan/Output/Rasters/condition_rrr_lyr20_plants/") >> '))
    prj_name = str(input('Please enter a Project name ("ProjectName") >> '))
    unit = str(input('Please enter a unit system ("us" or "si") >> '))
    version = str(input('Please enter a version number ("vii") >> '))
    main(dir2AP, prj_name, unit, version)
