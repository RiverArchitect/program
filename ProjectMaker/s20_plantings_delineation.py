# !/usr/bin/python
import arcpy
import webbrowser
from fFunctions import *
logger = logging_start("logfile_20")
try:
    from arcpy.sa import *
except:
    logger.info("ArcGIS ERROR: No SpatialAnalyst extension available.")
try:
    # load RiverArchitects own packages
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cDefinitions as cdef
except:
    print("ExceptionError: Could not find own packages (./site_packages/riverpy/)")


def main(action_dir, reach, stn, unit, version):
    # required input variables:
    # reach = "TBR"  #  (corresponding to folder name)
    # site_name = "BartonsBar" (for example)
    # stn = "brb"
    # unit = "us" or "si"
    # version = "v10"  # type() =  3-char str: vII
    error = False
    features = cdef.Features(False)  # read feature IDs (required to identify plants)

    if unit == "us":
        area_units = "SQUARE_FEET_US"
        ft2_to_acres = float(1 / (3 * 3 * 4840))  # 3*3 is ft2 to yd2 and 4840 yd2 to ac
    else:
        area_units = "SQUARE_METERS"
        ft2_to_acres = 1.0
    arcpy.CheckOutExtension('Spatial')
    arcpy.gp.overwriteOutput = True

    path2PP = os.path.dirname(os.path.realpath(__file__)) + "\\" + reach + "_" + stn + "_" + version + "\\"

    # folder settings 
    ras_dir = path2PP + "Geodata\\Rasters\\"
    shp_dir = path2PP + "Geodata\\Shapefiles\\"
    quant_dir = path2PP + "Quantities\\"
    del_ovr_files(path2PP)  # Delete temporary raster calculator files

    # file settings
    xlsx_target = path2PP + str(reach.upper()) + "_" + stn + "_assessment_" + version + ".xlsx"

    # LOOK UP ACTION RASTERS
    action_ras = {}
    try:
        logger.info("Looking up Action Rasters ...")
        arcpy.env.workspace = action_dir
        action_ras_all = arcpy.ListRasters()
        logger.info(" >> Source directory: " + action_dir)
        arcpy.env.workspace = path2PP + "Geodata\\"
        for aras in action_ras_all:
            for plant in features.id_list_plants:
                if plant in str(aras):
                    logger.info("   -- found: " + action_dir + str(aras))
                    action_ras.update({aras: arcpy.Raster(action_dir + aras)})
            if ("max" in str(aras)) and ("plant" in str(aras)):
                max_lf_plants = arcpy.Raster(action_dir + aras)
        logger.info(" -- OK (Action raster read)\n")
    except:
        logger.info("ERROR: Could not find action Rasters.")

    # CONVERT PROJECT SHAPEFILE TO RASTER
    try:
        logger.info("Converting Project Shapefile to Raster ...")
        arcpy.env.workspace = shp_dir
        arcpy.PolygonToRaster_conversion("ProjectArea.shp", "AreaCode", ras_dir + "ProjectArea.tif",
                                         cell_assignment="CELL_CENTER", priority_field="NONE", cellsize=1)
        logger.info(" -- OK. Loading Project raster ...")
        arcpy.env.workspace = path2PP + "Geodata\\"
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

    # RETAIN RELEVANT PLANTINGS ONLY
    shp_4_stats = {}
    try:
        logger.info("Analyzing optimum plant types in project area ...")
        logger.info(" >> Cropping maximum lifespans (action) raster ... ")
        max_lf_crop = Con((~IsNull(prj_area) & ~IsNull(max_lf_plants)), Float(max_lf_plants))
        logger.info(" >> Saving crop ... ")
        max_lf_crop.save(ras_dir + "max_lf_pl_c.tif")
        logger.info(" -- OK ")
        for aras in action_ras.keys():
            plant_ras = action_ras[aras]
            if not('.tif' in str(aras)):
                aras_tif = str(aras) + '.tif'
                aras_no_end = aras
            else:
                aras_tif = aras
                aras_no_end = aras.split('.tif')[0]
            logger.info(" >> Plant action raster: " + str(plant_ras))
            __temp_ras__ = Con((~IsNull(prj_area) & ~IsNull(plant_ras)), Con((Float(max_lf_plants) >= 2.5), (max_lf_plants * plant_ras)))
            logger.info(" >> Saving raster ... ")
            __temp_ras__.save(ras_dir + aras_tif)
            logger.info(" >> Converting to shapefile (polygon for area statistics) ... ")
            try:
                shp_ras = Con(~IsNull(__temp_ras__), 1, 0)
                arcpy.RasterToPolygon_conversion(shp_ras, shp_dir + aras_no_end + ".shp", "NO_SIMPLIFY")
            except:
                logger.info("     !! " + aras_tif + " is not suitable for this project.")
            arcpy.env.workspace = action_dir
            logger.info(" >> Calculating area statistics ... ")
            try:
                arcpy.AddField_management(shp_dir + aras_no_end + ".shp", "F_AREA", "FLOAT", 9)
                arcpy.CalculateGeometryAttributes_management(shp_dir + aras_no_end + ".shp",
                                                             geometry_property=[["F_AREA", "AREA"]],
                                                             area_unit=area_units)
                shp_4_stats.update({aras: shp_dir + aras_no_end + ".shp"})
            except:
                logger.info("     !! Omitting (not applicable) ...")
                error = True
            arcpy.env.workspace = path2PP + "Geodata\\"
        logger.info(" -- OK (Shapefile and raster analyses)\n")
        logger.info("Calculating area statistics of plants to be cleared for construction ...")
        arcpy.AddField_management(shp_dir + "PlantDelineation.shp", "F_AREA", "FLOAT", 9)
        arcpy.CalculateGeometryAttributes_management(shp_dir + "PlantDelineation.shp",
                                                     geometry_property=[["F_AREA", "AREA"]],
                                                     area_unit=area_units)
        shp_4_stats.update({"clearing": shp_dir + "PlantDelineation.shp"})
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
    arcpy.env.workspace = path2PP + "Geodata\\"
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
        stat_data = read_txt(stat_files[sf], logger)
        logger.info("     --> Extracting relevant area ...")
        polygon_count = 0
        total_area_ft2 = 0.0
        for row in stat_data:
            if row[0] == 1:
                total_area_ft2 += row[1]
                polygon_count += 1
        write_dict.update({sf: total_area_ft2 * float(ft2_to_acres)})
        logger.info("     --> OK")
    logger.info(" -- OK (Area extraction finished)\n")

    # WRITE AREA DATA TO EXCEL FILE
    logger.info("Writing results ...")
    write_dict2xlsx(write_dict, xlsx_target, "B", "C", 4, logger)

    logger.info(" -- OK (PLANT DELINEATION FINISHED)\n")

    # RELEASE LOGGER AND OPEN LOGFILE
    logging_stop(logger)
    try:
        logfile = os.getcwd() + "\\logfile_20.log"
        try:
            if not error:
                webbrowser.open(xlsx_target)
        except:
            pass
        webbrowser.open(logfile)
    except:
        pass


if __name__ == "__main__":
    dir2AP = str(input('Please enter the path to the RiverArchitect module (e.g., "D:/RiverArchitect/MaxLifespan/Products/Rasters/condition_rrr_lyr20_plants/") >> '))
    reach = str(input('Please enter a reach abbreviation ("RRR") >> ')).upper()
    stn = str(input('Please enter a site name abbreviation ("stn") >> ')).lower()
    unit = str(input('Please enter a unit system ("us" or "si") >> '))
    version = str(input('Please enter a version number ("vii") >> '))
    main(dir2AP, reach, stn, unit, version)
