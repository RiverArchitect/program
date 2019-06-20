try:
    import sys, os, logging, datetime
    import numpy as np
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, datetime, logging, numpy).")

try:
    import config
    import cFish as cFi
    import cInputOutput as cIO
    import fGlobal as fG
    import cMakeTable as cMT
except:
    print("ExceptionERROR: Missing RiverArchitect packages (riverpy).")


class FlowAssessment:
    def __init__(self):
        self.flows_2d = []  # 2D-modeled discharges available in a condition folder
        self.Q_flowdur = []
        self.exceedance_abs = []  # absolute exceedance duration in days
        self.exceedance_rel = []  # relative exceedance duration in percent
        self.logger = logging.getLogger("logfile")

    def get_flow_duration_data_from_list(self, flow_duration_matrix):
        # flow_duration_matrix = NESTED LIST with [Q, Exceed. Prob in percent]
        self.Q_flowdur = flow_duration_matrix[0]  # cfs or m3
        self.exceedance_rel = flow_duration_matrix[1]  # percent

    def get_flow_duration_data_from_xlsx(self, flow_duration_xlsx):
        # flow_duration_xlsx = STR containing the absolute workbook path with flow duration curve data
        #     --> anyway, the workbook must have Q_flowdur data in col B and exceed. percenmt in col C (start_row=3)
        self.logger.info("   * retrieving flow duration curve (%s) ..." % str(flow_duration_xlsx))
        try:
            data_reader = cIO.Read(flow_duration_xlsx)
            self.Q_flowdur = data_reader.read_column("A", 3)  # cfs or m3-col = "B"+1 because read_col considers colA=0
            self.exceedance_rel = data_reader.read_column("B", 3)  # percent-col = "C"+1 because read_col considers colA=0
            data_reader.close_wb()
        except:
            self.logger.info("ERROR: Could not read flow duration curve data")
            return -1
        try:
            [self.Q_flowdur, self.exceedance_rel] = fG.eliminate_nan_from_list(self.Q_flowdur, self.exceedance_rel)
        except:
            pass

    def get_flow_model_data(self, condition):
        # condition = STR of CONDITION
        self.logger.info("   * retrieving 2D-modeled flows (%s) ..." % str(condition))
        try:
            flow_data = cMT.MakeFlowTable(condition, "*")
            self.flows_2d = flow_data.discharges
            self.logger.info("   * OK")
        except:
            self.logger.info("Internal Error: Cannot access condition folder.")

    def harmonize_flow_duration(self, Q_extrema):
        # Q_extrema = FLOAT that may be inserted at the beginning of the flow series
        __ex__ = []
        for iq in range(0, self.Q_flowdur.__len__()):
            try:
                __ex__.append(self.exceedance_rel[iq])
            except:
                self.Q_flowdur.insert(0, Q_extrema)
                self.logger.info(
                    "WARNING: Flow_duration[...].xlsx has different lengths of \'Q_flowdur\' and \'exceedance days\' columns.")
        self.exceedance_rel = __ex__

    def interpolate_flow_exceedance(self, Q_value):
        # Q_value is a FLOAT discharge in cfs or m3s
        self.logger.info("   * Interpolating exceedance probability for Q = " + str(Q_value))
        try:
            Q_value = float(Q_value)
        except:
            self.logger.info("ERROR: Invalid interpolation data type (type(Q) == " + type(Q_value) + ").")

        if Q_value <= float(max(self.Q_flowdur)):
            if not(Q_value <= float(min(self.Q_flowdur))):
                # find closest smaller and higher discharge
                iq = 0
                for qq in sorted(self.Q_flowdur, reverse=True):
                    # iterate Q_flowdur list (start from lowest)
                    if iq == 0:
                        Q_lower = float(self.Q_flowdur[iq])
                        ex_lower = 100.0
                    else:
                        Q_lower = float(self.Q_flowdur[iq - 1])
                        ex_lower = float(self.exceedance_rel[iq - 1])
                    Q_higher = self.Q_flowdur[iq]
                    ex_higher = self.exceedance_rel[iq]
                    if Q_value > qq:
                        # self.logger.info(" -->> qq: " + str(qq))
                        # self.logger.info(" -->> Q_value: " + str(Q_value))
                        continue
                    iq += 1
            else:
                Q_lower = Q_value
                ex_lower = 100.0
                Q_higher = min(self.Q_flowdur)
                ex_higher = 100.0
        else:
            self.logger.info("   * HIGH DISCHARGE. Annual exceedance probability close to zero.")
            Q_lower = max(self.Q_flowdur)
            ex_lower = 0.0
            Q_higher = Q_value
            ex_higher = 0.0
        try:
            pr_exceedance = ex_lower + ((Q_value - Q_lower) / (Q_higher - Q_lower)) * (ex_higher - ex_lower)
            self.logger.info(" -->> Expected exceedance duration (per year): " + str(pr_exceedance) + "%")
            return pr_exceedance
        except:
            self.logger.info("ERROR: Could not interpolate exceedance probability of Q = " + str(Q_value) + ".")
            return 0.0

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = FlowAssessment (%s)" % os.path.dirname(__file__))
        print(dir(self))


class SeasonalFlowProcessor:
    def __init__(self, input_xlsx, *args, **kwargs):
        # input_xlsx = STR full path of an input xlsx file
        # functionality:
        # 1) instantiate object
        # 2) assign fish species with self.get_fish_seasons and run self.make_flow_duration() for each species/lifestage
        self.export_dict = {}
        self.fish = cFi.Fish()
        self.fish_seasons = {}
        self.date_column = []
        self.flow_column = []
        self.flow_matrix = []  # rows=n-days, cols=m-years
        self.logger = logging.getLogger("logfile")
        self.min_year = 9999
        self.max_year = 1
        self.season_years = int()
        self.xlsx_template = config.dir2ra + "00_Flows\\templates\\flow_duration_template.xlsx"
        self.read_flow_series(input_xlsx)

    def add_years(self, curr_date, number_of_years):
        try:
            return curr_date.replace(year=curr_date.year + number_of_years)
        except ValueError:
            return curr_date + (datetime.date(curr_date.year + number_of_years, 3, 1) - datetime.date(curr_date.year, 3, 1))

    def assign_years(self):
        for e in self.date_column:
            try:
                if int(e.year) < int(self.min_year):
                    self.min_year = int(e.year)
                if int(e.year) > int(self.max_year):
                    self.max_year = int(e.year)
            except:
                self.logger.info("ERROR: The source discharge file contains non-detectable formats (dates in col. A).")
                return -1

    def build_flow_duration_data(self):
        self.season_years = self.max_year - self.min_year + 1
        for fish in self.fish_seasons.keys():
            # identify relevant dates
            self.logger.info("   * building flow duration data for %s." % str(fish))
            try:
                start_date = datetime.datetime(self.fish_seasons[fish]["start"]["year"],
                                               self.fish_seasons[fish]["start"]["month"],
                                               self.fish_seasons[fish]["start"]["day"])
                end_date = datetime.datetime(self.fish_seasons[fish]["end"]["year"],
                                             self.fish_seasons[fish]["end"]["month"],
                                             self.fish_seasons[fish]["end"]["day"])
            except:
                self.logger.info("ERROR: Invalid date assignment (Fish.xlsx).")
                continue
            try:
                data4export = self.make_flow_season_data(start_date, end_date)
                self.export_dict.update({fish: data4export})
            except:
                self.logger.info("ERROR: Could not process flow series.")

    def date2id(self, curr_date):
        # curr_date = datetime.datetime object
        try:
            return int(str(curr_date.month) + str("%02i" % curr_date.day))
        except:
            return -1

    def get_fish_seasons(self, fish_species, fish_lifestage):
        # fish_species = STR as used in cFish.Fish()
        # fish_lifestage = STR as used in cFish.Fish()
        self.logger.info("   * reading season dates for {0} - {1}.".format(fish_species, fish_lifestage))
        fish_sn = str(fish_species).lower()[0:2] + str(fish_lifestage).lower()[0:2]
        try:
            self.fish_seasons.update({fish_sn: self.fish.get_season_dates(fish_species, fish_lifestage)})
        except:
            self.logger.info("ERROR: Could not read parameter type (for {0} - {1}) from Fish.xlsx.".format(fish_species, fish_lifestage))

    def make_flow_duration(self, condition):
        self.logger.info("   * generating flow duration curve (%s)." % condition)
        try:
            self.build_flow_duration_data()
        except:
            self.logger.info("ERROR: Flow series analysis failed.")
            return -1
        try:
            return self.write_flow_duration2xlsx(condition)
        except:
            self.logger.info("ERROR: Could not write flow duration curve data (flow series).")
            return -1

    def make_condition_flow2d_duration(self, condition):
        # condition = STR of CONDITION
        for fish in self.export_dict.keys():
            xlsx_name = config.dir2ra + "00_Flows\\" + condition + "\\flow_duration_" + str(fish) + ".xlsx"
            flows = FlowAssessment()
            Q = []
            pr = []
            for l in self.export_dict[fish]:
                Q.append(l[0])
                pr.append(l[1])
            flows.get_flow_duration_data_from_list([Q, pr])
            flows.get_flow_model_data(condition)
            result = []
            for q in flows.flows_2d:
                result.append([q, flows.interpolate_flow_exceedance(q)])
            try:
                self.write_flow2d_duration2xlsx(xlsx_name, result)
            except:
                self.logger.info("ERROR: Could not write flow duration curve data (2D flows).")
                continue

    def make_flow_season_data(self, start_date, end_date, **kwargs):
        # start_date = datetime.datetime(YEAR, MONTH, DAY) of season start
        # end_date = datetime.datetime(YEAR, MONTH, DAY) of season end
        # **kwargs: mean_daily = False (default) - applies daily averages rather than all flows
        mean_daily = False
        # parse optional keyword arguments
        try:
            for k in kwargs.items():
                if "mean_daily" in k[0]:
                    mean_daily = k[1]
        except:
            pass

        date_integers = []  # convert dates to id type DDMM

        if not self.date2id(end_date) > self.date2id(start_date):
            end_date = self.add_years(end_date, 1)

        for dy in range(int((end_date - start_date).days) + 1):
            date_id = self.date2id(start_date + datetime.timedelta(days=dy))
            if not date_id == 229:
                # exclude leap year day
                date_integers.append(date_id)
        n_dates = date_integers.__len__()
        season_flows = np.ones((n_dates, self.season_years + 1)) * np.nan

        __row_source__ = 0
        __col_tar__ = 0
        for dy in self.date_column:
            date_id = self.date2id(dy)
            if date_id in date_integers:
                positions = []
                try:
                    [positions.append(i) for i, x in enumerate(date_integers) if x == date_id]
                    season_flows[positions[-1], __col_tar__] = self.flow_column[__row_source__]
                except:
                    self.logger.info("ERROR: Invalid date and / or flow ranges in discharge series.")
                try:
                    if positions[-1] == n_dates - 1:
                        __col_tar__ += 1
                except:
                    pass
            __row_source__ += 1

        season_flow_list = []
        if mean_daily:
            mean_flows = []
            __row_tar__ = 0
            for id in date_integers:
                try:
                    mean_flows.append(np.nanmean(season_flows[__row_tar__, :]))
                except:
                    pass
                __row_tar__ += 1
            season_flow_list = mean_flows
        else:
            for season in season_flows:
                for flow in season:
                    try:
                        if float(flow) > 0.0:
                            season_flow_list.append(float(flow))
                    except:
                        self.logger.info("WARNING: %s is not a number." % str(flow))
        season_flow_list.sort(reverse=True)

        data4export = []
        __row_tar__ = 1
        n_flows = season_flow_list.__len__()
        for flow in season_flow_list:
            try:
                data4export.append([flow, float(__row_tar__ / n_flows * 100)])
            except:
                pass
            __row_tar__ += 1
        return data4export

    def read_flow_series(self, input_xlsx):
        try:
            input_xlsx_f = cIO.Read(input_xlsx)
            self.date_column = input_xlsx_f.read_column('A', 3)
            self.flow_column = input_xlsx_f.read_column('B', 3)
            input_xlsx_f.close_wb()
            self.assign_years()
        except:
            self.logger.info("ERROR: The source discharge file contains non-detectable formats.")

    def write_flow_duration2xlsx(self, condition):
        fG.chk_dir(config.dir2ra + "00_Flows\\" + condition + "\\")
        for fish in self.export_dict.keys():
            export_xlsx_name = config.dir2ra + "00_Flows\\" + condition + "\\flow_duration_" + str(fish) + ".xlsx"
            self.logger.info("   * writing to " + export_xlsx_name)
            try:
                xlsx_write = cIO.Write(self.xlsx_template)
            except:
                self.logger.info("ERROR: Could not open workbook (%s)." % self.xlsx_template)
                continue
            # xlsx_write.open_wb(export_xlsx_name, 0)
            self.logger.info("   * writing data ...")
            try:
                xlsx_write.write_cell("E", 4, fish)
                xlsx_write.write_cell("E", 5, " Month:" + str(self.fish_seasons[fish]["start"]["month"]) + " Day:" + str(self.fish_seasons[fish]["start"]["day"]))
                xlsx_write.write_cell("E", 6, " Month:" + str(self.fish_seasons[fish]["end"]["month"]) + " Day:" + str(self.fish_seasons[fish]["end"]["day"]))
                xlsx_write.write_cell("E", 7, self.min_year)
                xlsx_write.write_cell("E", 8, self.max_year)
                xlsx_write.write_matrix("A", 3, self.export_dict[fish])
            except:
                self.logger.info("")

            try:
                self.logger.info("   * saving workbook ... ")
                xlsx_write.save_close_wb(export_xlsx_name)
            except:
                self.logger.info("ERROR: Failed to save %s" % export_xlsx_name)
        try:
            return export_xlsx_name
        except:
            return -1

    def write_flow2d_duration2xlsx(self, xlsx_name, export_list):
        # export_list = NESTED LIST with [Q_data, exceedance prob.]
        self.logger.info("   * writing 2D flows duration curve to " + xlsx_name)
        try:
            xlsx_write = cIO.Write(xlsx_name, worksheet_no=1)
        except:
            self.logger.info("ERROR: Could not open workbook (%s)." % xlsx_name)
            return -1
        # xlsx_write.open_wb(export_xlsx_name, 0)
        self.logger.info("   * writing data ...")
        try:
            xlsx_write.write_matrix("B", 3, export_list)
        except:
            self.logger.info("")

        try:
            self.logger.info("   * saving workbook ... ")
            xlsx_write.save_close_wb(xlsx_name)
        except:
            self.logger.info("ERROR: Failed to save %s" % xlsx_name)

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = SeasonalFlowProcessor (%s)" % os.path.dirname(__file__))
        print(dir(self))
