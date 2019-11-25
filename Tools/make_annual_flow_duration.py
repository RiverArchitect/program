try:
    import webbrowser, os
    import numpy as np
    import calendar
    import fTools as ft
    import cInputOutput as cio
except:
    print("ERROR: Could not load numpy.")


def make_flow_duration():
    # requires csv file with
    # col1 = dates
    # col2 = mean daily discharge

    station_name = "AFLA"                   # CHANGE
    start_year = 1969                       # CHANGE
    end_year = 2009                         # CHANGE
    observation_period = "1969-2010"        # CHANGE
    path2csv = "D:\\Python\\Discharge\\"    # CHANGE
    csv_name = "AFLA_1969_2010_series.csv"  # CHANGE

    print("Reading discharge series ...")
    dates = ft.read_csv(path2csv + csv_name, True, 0)
    discharges = ft.read_csv(path2csv + csv_name, True, 1)
    n_days = 365


    print("Classifying mean daily discharge ...")
    # get length of months (ignore leap years)
    days_per_month = []
    for m in range(1, 12 + 1):
        days_per_month.append(calendar.monthrange(int(end_year), m)[1])

    # prepare day-discharge dict
    day_discharge_dict = {}
    for d in range(1, n_days + 1):
        # add one discharge entry per year
        day_discharge_dict.update({d: []})

    # add discharges per day of the year
    i_file_read = 0
    for y in range(start_year, end_year + 1):
        year_day = 1
        for m in range(1, 12 + 1):
            month = dates[i_file_read].month
            for d in range(1, days_per_month[m - 1] + 1):
                day = dates[i_file_read].day
                # ensure that date count matches filecount
                if m == month:
                    if d == day:
                        try:
                            val = float(discharges[i_file_read])
                        except:
                            val = np.nan
                        day_discharge_dict[year_day].append(val)

                # check leap years
                if (month == 2) and (dates[i_file_read + 1].day == 29):
                    i_file_read += 2
                else:
                    i_file_read += 1
                year_day += 1

    print("Averaging mean daily discharges ...")
    discharge_per_day = []
    for d in day_discharge_dict.keys():
        discharge_per_day.append(np.nanmean(day_discharge_dict[d], axis=0))
    discharge_per_day.sort(reverse=True)

    day_discharge_sorted = {}
    for d in day_discharge_dict.keys():
        day_discharge_sorted.update({d: discharge_per_day[d - 1]})

    print("Writing results to flow_duration_" + station_name + ".xlsx")
    xlsx_write = cio.Write("flow_duration_" + station_name + ".xlsx")
    xlsx_write.open_wb("flow_duration_template.xlsx", 0)
    xlsx_write.write_cell("G", 3, station_name)
    xlsx_write.write_cell("G", 4, observation_period)
    xlsx_write.write_dict2xlsx(day_discharge_sorted, "C", "B", 2)
    xlsx_write.save_close_wb()
    webbrowser.open(os.path.dirname(os.path.abspath(__file__)) + "\\flow_duration_" + station_name + ".xlsx")


if __name__ == "__main__":
    make_flow_duration()
