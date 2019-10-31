try:
    import webbrowser
    import glob, sys, os, logging
    from operator import itemgetter
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
except:
    print("ExceptionERROR: Missing fundamental packages (required: webbrowser, glob, operator, logging).")
try:
    import fGlobal as fGl
    import config
    import cInputOutput as cIO
    import cSHArC
except:
    print("ExceptionERROR: Missing own packages (riverpy).")


def main(condition_initial=str(), condition_project=str(), cover_pre=bool(), cover_post=bool(), fish={}, prj_name=str(), unit=str(), version=str(), apply_wua=bool()):
    """ calculates pre- and post implementation SHArea
    version = "v10"             # type() =  3-char str: vII
    prj_name = "MyProject"               # (corresponding to folder name)
    condition_initial = "2008"
    condition_project = "2008_tbr_lyr10"
    cover_app_pre = False
    fish = {"Chinook salmon": ["juvenile"]}
    """
    logger = logging.getLogger("logfile")
    error = False
    sys.path.append(config.dir2oxl)

    # set directories
    if cover_pre:
        pre_ext = "cover"
    else:
        pre_ext = "no_cover"
    if cover_post:
        post_ext = "cover"
    else:
        post_ext = "no_cover"

    dir2pp = os.path.dirname(os.path.realpath(__file__)) + "\\" + prj_name + "_" + version + "\\"
    dir2ras_chsi = [config.dir2sh + "SHArea\\Rasters_" + condition_initial + "\\" + pre_ext + "\\",
                    config.dir2sh + "SHArea\\Rasters_" + condition_project + "\\" + post_ext + "\\"]
    dir2ras_tar = [dir2pp + "Geodata\\Rasters\\" + condition_initial + "\\" + pre_ext + "\\",
                   dir2pp + "Geodata\\Rasters\\" + condition_project + "\\" + post_ext + "\\"]
    fGl.chk_dir(dir2ras_tar[0])
    fGl.chk_dir(dir2ras_tar[1])
    xlsx_out_name = config.empty_file

    shp_dir = dir2pp + "Geodata\\Shapefiles\\"

    # file and variable settings
    xlsx_tar_costs = dir2pp + prj_name + "_assessment_" + version + ".xlsx"
    if unit == "us":
        unit_q = "cfs"
        xlsx_sha_template = dir2pp + "Geodata\\SHArea_evaluation_template_us.xlsx"
    else:
        unit_q = "m3/s"
        xlsx_sha_template = dir2pp + "Geodata\\SHArea_evaluation_template_si.xlsx"

    # INSTANTIATE SHArea CLASS OBJECT:
    sha = cSHArC.SHArC(unit, prj_name, version)

    # RUN SHArea ANALYSIS
    try:
        logger.info("Starting SHArea analysis ...")
        project_area = shp_dir + "ProjectArea.shp"
        fields = ["SHAPE@", "gridcode"]
        sha.get_extents(project_area, fields[0])
        sha.set_project_area("ProjectArea")
        for species, lifestages in fish.items():
            for ls in lifestages:
                logger.info("SHArea ANALYSIS FOR " + str(species).upper() + " - " + str(ls).upper())
                fili = str(species).lower()[0:2] + str(ls)[0:2]
                xlsx_conditions = [condition_initial + "_sharea_" + fili + ".xlsx",
                                   condition_project + "_sharea_" + fili + ".xlsx"]
                xlsx_sha = cIO.Write(xlsx_sha_template, worksheet_no=0)
                xlsx_sha_name = dir2pp + "Geodata\\SHArea_" + fili + ".xlsx"
                conditions_sha = []

                xc_count = 0
                start_write_col = "B"
                for xc in xlsx_conditions:
                    # instantiate dict for results writing (entry types are {Q: [Probability, Usable Area]})
                    result_matrix = []
                    try:
                        logger.info(" >> Condition: " + str(xc).split("_sharea_")[0])
                        xlsx_info = cIO.Read(config.dir2sh + "SHArea\\" + xc)
                    except:
                        xlsx_info = ""
                        logger.info("ERROR: Could not access " + str(xc))
                        error = True
                    try:
                        logger.info("    -> Looking up discharge information (RiverArchitect/SHArC/SHArea/)...")
                        discharges = xlsx_info.read_float_column_short("B", 4)
                        exceedance_pr = xlsx_info.read_float_column_short("E", 4)

                        discharge_dict = dict(zip(discharges, exceedance_pr))
                        raster_list = glob.glob(dir2ras_chsi[xc_count] + "*.tif")
                        logger.info("    -> Matching CHSI rasters with discharge information ...")
                        for q in discharges:
                            test_ras = dir2ras_chsi[xc_count] + "csi_" + fili + str(int(q)) + ".tif"
                            ras = [r for r in raster_list if (r == test_ras)][0]
                            logger.info("    ---> Calculating habitat area from {0} for Q = {1}".format(ras, str(q) + unit_q))
                            try:
                                sha.get_usable_area(ras.split(".tif")[0])
                                result_matrix.append([q, discharge_dict[q], sha.result])
                            except:
                                logger.info("         * empty sluice for " + str(q))
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
                        logger.info("ERROR: Could not write SHArea data for " + str(species) + " - " + str(ls))
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
                                sha.calculate_sha([pr for pr in ex_pr_pdf], [res[2] for res in result_matrix]))
                    except:
                        logger.info("ERROR: Could not transfer SHArea data for " + str(species) + " - " + str(ls))
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
                    xlsx_out_name = prj_name + "_assessment_" + version + "_" + fili + ".xlsx"
                    xlsx_costs.save_close_wb(dir2pp + xlsx_out_name)
                    logger.info(" >> CHECK RESULTS IN: " + dir2pp + xlsx_out_name)
                except:
                    logger.info("ERROR: Could not transfer net SHArea gain.")
                    error = True

        sha.clear_cache()
    except:
        logger.info("ERROR: Could not run SHArea analysis.")
        return -1

    if not error:
        fGl.open_file(dir2pp + xlsx_out_name)
        
    return sha.cache
