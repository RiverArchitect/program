import webbrowser
import glob
from operator import itemgetter
from fFunctions import *
logger = logging_start("logfile_40")
import cIO
import cWUA

def main(condition_initial, condition_project, cover_pre, cover_post, dir2SR, fish, reach, stn, unit, version):
    # version = "v10"             # CHANGE: type() =  3-char str: vII
    # reach = "TBR"               # CHANGE (corresponding to folder name)
    # stn = "brb"                 # CHANGE
    # condition_initial = "2008"  # CHANGE
    # condition_project = "2008_tbr_lyr10"  # CHANGE
    # cover_app_pre = False       # CHANGE
    # fish = {"Chinook salmon": ["juvenile"]}  # CHANGE
    error = False
    sys.path.append(dir2SR + ".site_packages\\openpyxl\\")

    # set directories
    if cover_pre:
        pre_ext = "cover"
    else:
        pre_ext = "no_cover"
    if cover_post:
        post_ext = "cover"
    else:
        post_ext = "no_cover"

    dir2PP = os.path.dirname(os.path.realpath(__file__)) + "\\" + reach + "_" + stn + "_" + version + "\\"
    dir2ras_chsi = [dir2SR + "HabitatEvaluation\\WUA\\Rasters\\" + condition_initial + "\\" + pre_ext + "\\",
                    dir2SR + "HabitatEvaluation\\WUA\\Rasters\\" + condition_project + "\\" + post_ext + "\\"]
    dir2ras_tar = [dir2PP + "Geodata\\Rasters\\" + condition_initial + "\\" + pre_ext + "\\",
                   dir2PP + "Geodata\\Rasters\\" + condition_project + "\\" + post_ext + "\\"]
    chk_dir(dir2ras_tar[0])
    chk_dir(dir2ras_tar[1])

    shp_dir = dir2PP + "Geodata\\Shapefiles\\"

    # file and variable settings
    xlsx_tar_costs = dir2PP + reach.upper() + "_" + stn + "_assessment_" + version + ".xlsx"
    if unit == "us":
        u_mass_flux = "cfs"
        xlsx_wua_template = dir2PP + "Geodata\\WUA_evaluation_template_us.xlsx"
    else:
        u_mass_flux = "m3/s"
        xlsx_wua_template = dir2PP + "Geodata\\WUA_evaluation_template_si.xlsx"

    # INSTANTIATE WUA CLASS OBJECT:
    wua = cWUA.CWUA(unit, reach, stn, version)

    # RUN WUA ANALYSIS
    try:
        logger.info("Starting WUA analysis ...")
        project_area = shp_dir + "ProjectArea.shp"
        fields = ["SHAPE@", "gridcode"]
        wua.get_extents(project_area, fields)
        wua.set_project_area("ProjectArea", fields[1])
        for species in fish.keys():
            for ls in fish[species]:
                logger.info("WUA ANALYSIS FOR " + str(species).upper() + " - " + str(ls).upper())
                fish_sn = str(species).lower()[0:2] + str(ls[0])
                xlsx_conditions = [condition_initial + "_" + fish_sn + ".xlsx",
                                   condition_project + "_" + fish_sn + ".xlsx"]
                xlsx_wua = cIO.Write(xlsx_wua_template)
                xlsx_wua_name = dir2PP + "Geodata\\WUA_evaluation_" + fish_sn + ".xlsx"
                conditions_wua = []

                xc_count = 0
                start_write_col = "B"
                for xc in xlsx_conditions:
                    # instantiate dict for results writing (entry types are {Q: [Probability, Usable Area]})
                    result_matrix = []
                    try:
                        logger.info(" >> Condition: " + str(xc).split(".xlsx")[0])
                        xlsx_info = cIO.Read(dir2SR + "HabitatEvaluation\\WUA\\" + xc)
                    except:
                        xlsx_info = ""
                        logger.info("ERROR: Could not access " + str(xc))
                        error = True
                    try:
                        logger.info("    -> Looking up discharge information (SR/HabitatEvaluation)...")
                        discharges = xlsx_info.read_column("B", 4)
                        exceedance_pr = xlsx_info.read_column("E", 4)

                        discharge_dict = dict(zip(discharges, exceedance_pr))
                        raster_list = glob.glob(dir2ras_chsi[xc_count] + "*.aux.xml")
                        logger.info("    -> Matching CHSI rasters with discharge information ...")
                        for q in discharges:
                            test_ras = dir2ras_chsi[xc_count] + "csi_" + fish_sn + str(int(q)) + ".aux.xml"
                            ras = [r for r in raster_list if (r == test_ras)][0]
                            logger.info("    ---> Usable habitat area assessment for Q = " + str(q) + u_mass_flux)
                            result_matrix.append([q, discharge_dict[q], wua.get_usable_area(ras.split(".aux.xml")[0], dir2ras_tar[xc_count])])
                            logger.info("         ok")
                    except:
                        logger.info("ERROR: Could not process information from " + str(xc))
                        error = True

                    try:
                        logger.info("    -> Writing discharges and usable area to " + xlsx_wua_name + " ...")
                        result_matrix.sort(key=itemgetter(0), reverse=True)
                        write_row = 9
                        for res in result_matrix:
                            xlsx_wua.write_row(start_write_col, write_row, [res[0], res[1], res[2]])  # q, pr, area
                            write_row += 1
                        logger.info("    -> ok")
                    except:
                        logger.info("ERROR: Could not write WUA data for  " + str(species) + " - " + str(ls))
                        error = True

                    # calculate WUA for transfer independent from xlsx calculation
                    try:
                        ex_pr_pdf = [float(exceedance_pr[0])]
                        for i_pr in range(1, exceedance_pr.__len__()):
                            if not((float(exceedance_pr[i_pr - 1]) >= 100.0) or (exceedance_pr[i_pr] == 0)):
                                ex_pr_pdf.append(float(exceedance_pr[i_pr] - exceedance_pr[i_pr - 1]))
                            else:
                                ex_pr_pdf.append(0.0)
                        conditions_wua.append(
                                wua.calculate_wua([pr for pr in ex_pr_pdf], [l[2] for l in result_matrix]))
                    except:
                        logger.info("ERROR: Could not transfer WUA data for  " + str(species) + " - " + str(ls))
                        error = True

                    xc_count += 1
                    start_write_col = cIO.Read.col_num_to_name(cIO.Read.col_name_to_num(start_write_col) + 5)
                    xlsx_info.close_wb()

                logger.info(" >> Saving and closing " + xlsx_wua_name + " ...")
                try:
                    xlsx_wua.save_close_wb(xlsx_wua_name)
                except:
                    logger.info("ERROR: Could not save " + xlsx_wua_name)
                del xlsx_wua

                wua.clear_cache(True)  # limit cache size

                try:
                    logger.info(" >> Transferring results (net WUA gain) to cost table ...")
                    xlsx_costs = cIO.Write(xlsx_tar_costs)
                    xlsx_costs.write_cell("G", 3, float(conditions_wua[1] - conditions_wua[0]))
                    xlsx_out_name = reach.upper() + "_" + stn + "_assessment_" + version + "_" + fish_sn + ".xlsx"
                    xlsx_costs.save_close_wb(dir2PP + xlsx_out_name)
                    logger.info(" >> CHECK RESULTS IN: " + dir2PP + xlsx_out_name)
                except:
                    logger.info("ERROR: Could not transfer net WUA gain.")
                    error = True

        wua.clear_cache()

    except:
        logger.info("ERROR: Could not run WUA analysis.")
        error = True

    # RELEASE LOGGER AND OPEN LOGFILE
    logging_stop(logger)
    try:
        logfile = os.getcwd() + "\\logfile_40.log"
        try:
            if not error:
                webbrowser.open(dir2PP + xlsx_out_name)
        except:
            pass
        webbrowser.open(logfile)
    except:
        pass


