try:
    import webbrowser, os
    import calendar
    import fTools as ft
    import cInputOutput as cio
except:
    print("ERROR: Could not load packages.")


def make_annual_peak():
    # requires csv file with
    # col1 = WaterYear (Integer)
    # col2 = Date (DD-MMM-YYYY)
    # col3 = mean daily discharge

    path2csv = "D:\\Python\\Discharge\\"    # CHANGE
    csv_name = "AFLA_flow_data.csv"   # CHANGE



    print("Reading discharge series ...")
    water_year = ft.read_csv(path2csv + csv_name, True, 0)
    dates = ft.read_csv(path2csv + csv_name, True, 1, True)
    discharges = ft.read_csv(path2csv + csv_name, True, 2)

    unique_wy = list(set(water_year))  # unique values for water_year

    annual_peaks = []

    for wy in unique_wy:
        start_y = water_year.index(wy)  # first row in csv file (start water year)
        end_y = ft.rindex(water_year, wy)  # last row in csv file (end water year)

        sub_q = discharges[start_y: end_y + 1]
        sub_date = dates[start_y: end_y + 1]

        # update peak discharge dict for water year
        annual_peaks.append([str(sub_date[sub_q.index(max(sub_q))]), max(sub_q)])

    fn = csv_name.split(".csv")[0] + ".xlsx"
    print("Writing results to " + fn)
    xlsx_write = cio.Write(fn)
    xlsx_write.open_wb("annual_peak_template.xlsx", 0)
    for it in range(0, annual_peaks[0].__len__()):
        lst = [item[it] for item in annual_peaks]
        xlsx_write.write_column(lst, chr(65 + it), 2)
    xlsx_write.save_close_wb()
    webbrowser.open(os.path.dirname(os.path.abspath(__file__)) + "\\" + fn)


if __name__ == "__main__":
    make_annual_peak()
