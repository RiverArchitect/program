import webbrowser
import glob
from operator import itemgetter
from fFunctions import *
logger = logging.getLogger("logfile")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
import cInputOutput as cIO
import cSHArC


def main(condition_initial, condition_project, cover_pre, cover_post, dir2ra, fish, reach, stn, unit, version):
    # version = "v10"             # type() =  3-char str: vII
    # reach = "TBR"               # (corresponding to folder name)
    # stn = "brb"                 
    # condition_initial = "2008"  
    # condition_project = "2008_tbr_lyr10"
    # cover_app_pre = False 
    # fish = {"Chinook salmon": ["juvenile"]}
    error = False
    sys.path.append(dir2ra + ".site_packages\\openpyxl\\")

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
    dir2ras_chsi = [dir2ra + "SHArC\\SHArea\\Rasters\\" + condition_initial + "\\" + pre_ext + "\\",
                    dir2ra + "SHArC\\SHArea\\Rasters\\" + condition_project + "\\" + post_ext + "\\"]
    dir2ras_tar = [dir2PP + "Geodata\\Rasters\\" + condition_initial + "\\" + pre_ext + "\\",
                   dir2PP + "Geodata\\Rasters\\" + condition_project + "\\" + post_ext + "\\"]
    chk_dir(dir2ras_tar[0])
    chk_dir(dir2ras_tar[1])

    shp_dir = dir2PP + "Geodata\\Shapefiles\\"

    # file and variable settings
    xlsx_tar_costs = dir2PP + reach.upper() + "_" + stn + "_assessment_" + version + ".xlsx"
    if unit == "us":
        u_mass_flux = "cfs"
        xlsx_sha_template = dir2PP + "Geodata\\SHArea_evaluation_template_us.xlsx"
    else:
        u_mass_flux = "m3/s"
        xlsx_sha_template = dir2PP + "Geodata\\SHArea_evaluation_template_si.xlsx"

    # INSTANTIATE SHArea CLASS OBJECT:
    sha = cSHArC.SHArC(unit, reach, stn, version)

    # RUN SHArea ANALYSIS
    try:
        logger.info("Starting SHArea analysis ...")
        project_area = shp_dir + "ProjectArea.shp"
        fields = ["SHAPE@", "gridcode"]
        sha.get_extents(project_area, fields)
        sha.set_project_area("ProjectArea", fields[1])
        for species in fish.keys():
            for ls in fish[species]:
                logger.info("SHArea ANALYSIS FOR " + str(species).upper() + " - " + str(ls).upper())
                fish_sn = str(species).lower()[0:2] + str(ls[0])
                xlsx_conditions = [condition_initial + "_" + fish_sn + ".xlsx",
                                   condition_project + "_" + fish_sn + ".xlsx"]
                xlsx_sha = cIO.Write(xlsx_sha_template)
                xlsx_sha_name = dir2PP + "Geodata\\SHArea_evaluation_" + fish_sn + ".xlsx"
                conditions_sha = []

                xc_count = 0
                start_write_col = "B"
                for xc in xlsx_conditions:
                    # instantiate dict for results writing (entry types are {Q: [Probability, Usable Area]})
                    result_matrix = []
                    try:
                        logger.info(" >> Condition: " + str(xc).split(".xlsx")[0])
                        xlsx_info = cIO.Read(dir2ra + "SHArC\\SHArea\\" + xc)
                    except:
                        xlsx_info = ""
                        logger.info("ERROR: Could not access " + str(xc))
                        error = True
                    try:
                        logger.info("    -> Looking up discharge information (RiverArchitect/SHArC)...")
                        discharges = xlsx_info.read_float_column_short("B", 4)
                        exceedance_pr = xlsx_info.read_float_column_short("E", 4)

                        discharge_dict = dict(zip(discharges, exceedance_pr))
                        raster_list = glob.glob(dir2ras_chsi[xc_count] + "*.tif")
                        logger.info("    -> Matching CHSI rasters with discharge information ...")
                        for q in discharges:
                            print(dir2ras_chsi[xc_count] + "csi_" + fish_sn + str(int(q)) + ".tif")
                            test_ras = dir2ras_chsi[xc_count] + "csi_" + fish_sn + str(int(q)) + ".tif"
                            print(str(raster_list))
                            ras = [r for r in raster_list if (r == test_ras)][0]
                            logger.info("    ---> Usable habitat area assessment for Q = " + str(q) + u_mass_flux)
                            result_matrix.append([q, discharge_dict[q], sha.get_usable_area(ras.split(".tif")[0], dir2ras_tar[xc_count])])
                            logger.info("         ok")
                    except:
                        logger.info("ERROR: Could not process information from " + str(xc))
                        error = True

                    try:
                        logger.info("    -> Writing discharges and usable area to " + xlsx_sha_name + " ...")
                        result_matrix.sort(key=itemgetter(0), reverse=True)
                        write_row = 9
                        for res in result_matrix:
                            xlsx_sha.write_row(start_write_col, write_row, [res[0], res[1], res[2]])  # q, pr, area
                            write_row += 1
                        logger.info("    -> ok")
                    except:
                        logger.info("ERROR: Could not write SHArea data for  " + str(species) + " - " + str(ls))
                        error = True

                    # calculate SHArea for transfer independent from xlsx calculation
                    try:
                        ex_pr_pdf = [float(exceedance_pr[0])]
                        for i_pr in range(1, exceedance_pr.__len__()):
                            if not((float(exceedance_pr[i_pr - 1]) >= 100.0) or (exceedance_pr[i_pr] == 0)):
                                ex_pr_pdf.append(float(exceedance_pr[i_pr] - exceedance_pr[i_pr - 1]))
                            else:
                                ex_pr_pdf.append(0.0)
                        conditions_sha.append(
                                sha.calculate_wua([pr for pr in ex_pr_pdf], [l[2] for l in result_matrix]))
                    except:
                        logger.info("ERROR: Could not transfer SHArea data for  " + str(species) + " - " + str(ls))
                        error = True

                    xc_count += 1
                    start_write_col = cIO.Read.col_num_to_name(cIO.Read.col_name_to_num(start_write_col) + 5)
                    xlsx_info.close_wb()

                logger.info(" >> Saving and closing " + xlsx_sha_name + " ...")
                try:
                    xlsx_sha.save_close_wb(xlsx_sha_name)
                except:
                    logger.info("ERROR: Could not save " + xlsx_sha_name)
                del xlsx_sha

                sha.clear_cache(True)  # limit cache size

                try:
                    logger.info(" >> Transferring results (net SHArea gain) to cost table ...")
                    xlsx_costs = cIO.Write(xlsx_tar_costs)
                    xlsx_costs.write_cell("G", 3, float(conditions_sha[1] - conditions_sha[0]))
                    xlsx_out_name = reach.upper() + "_" + stn + "_assessment_" + version + "_" + fish_sn + ".xlsx"
                    xlsx_costs.save_close_wb(dir2PP + xlsx_out_name)
                    logger.info(" >> CHECK RESULTS IN: " + dir2PP + xlsx_out_name)
                except:
                    logger.info("ERROR: Could not transfer net SHArea gain.")
                    error = True

        sha.clear_cache()

    except:
        logger.info("ERROR: Could not run SHArea analysis.")
        error = True

    # RELEASE LOGGER AND OPEN LOGFILE
    try:
        logfile = os.getcwd() + "\\logfile.log"
        try:
            if not error:
                webbrowser.open(dir2PP + xlsx_out_name)
        except:
            pass
        webbrowser.open(logfile)
    except:
        pass
