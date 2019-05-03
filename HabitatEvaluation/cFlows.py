try:
    import sys, os, logging, datetime
    import numpy as np
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, datetime, logging, numpy).")

try:
    import cFish as cf
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cInputOutput as cio
    import fGlobal as fg

except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: cFish, RP/fGlobal).")


class FlowAssessment:
    def __init__(self):
        self.Q_flowdur = []
        self.exceedance_abs = []  # absolute exceedance duration in days
        self.exceedance_rel = []  # relative exceedance duration in percent
        self.logger = logging.getLogger("logfile")

    def calculate_relative_exceedance(self):
        self.logger.info(" >> Calculating relative flow exceedances ...")
        max_d = max(self.exceedance_abs)
        for val in self.exceedance_abs:
            try:
                self.exceedance_rel.append(float(val / max_d))
            except:
                self.exceedance_rel.append(0.0)
                self.logger.info("WARNING: Could not divide " + str(val) + " by " + str(max_d) + ".")
        self.logger.info(" >> OK")

    def get_flow_data(self, *alternative_flowdur):
        # *alternative_flowdur can be an optional alternative workbook  with flow duration curve data
        #     --> anyway, the alternative must have Q_flowdur data in col B and exceedance days in col C (start_row=2)
        self.logger.info(" >> Retrieving flow data ...")
        try:
            hydro_wb = alternative_flowdur[0]
        except:
            hydro_wb = os.path.dirname(os.path.realpath(__file__)) + "\\hydrograph.xlsx"
        self.logger.info(" >> Source: " + str(hydro_wb))
        data_reader = cio.Read(hydro_wb)
        self.Q_flowdur = data_reader.read_float_column_short("B", 2)  # cfs or m3
        self.exceedance_abs = data_reader.read_float_column_short("C", 2)  # days

        # interpolate zero-probability flow
        Q_max = float(self.Q_flowdur[-1] - (self.Q_flowdur[-2] - self.Q_flowdur[-1]) / float(self.exceedance_abs[-2] - self.exceedance_abs[-1]))
        self.Q_flowdur.append(Q_max)
        self.exceedance_abs.append(0)

        # add data consistency (ensure that self.Q_flowdur and self.exceedance are the same length)
        __ex__ = []
        for iq in range(0, self.Q_flowdur.__len__()):
            try:
                __ex__.append(self.exceedance_abs[iq])
            except:
                self.Q_flowdur.insert(0, Q_max)
                self.logger.info(
                    "WARNING: Flow_duration[...].xlsx has different lengths of \'Q_flowdur\' and \'exceedance days\' columns.")
        self.exceedance_abs = __ex__
        self.logger.info(" >> OK")
        self.calculate_relative_exceedance()

    def interpolate_flow_exceedance(self, Q_value):
        # Q_value is a FLOAT discharge in cfs or m3s
        self.logger.info(" >> Interpolating exceedance probability for Q_flowdur = " + str(Q_value))
        try:
            Q_value = float(Q_value)
        except:
            self.logger.info("ERROR: Invalid interpolation data type (type(Q_flowdur) == " + type(Q_value) + ").")

        if Q_value <= max(self.Q_flowdur):
            if not(Q_value <= min(self.Q_flowdur)):
                # find closest smaller and higher discharge
                iq = 0
                for qq in sorted(self.Q_flowdur, reverse=True):
                    # iterate Q_flowdur list (start from lowest)
                    if iq == 0:
                        Q_lower = self.Q_flowdur[iq]
                        ex_lower = 1.0
                    else:
                        Q_lower = self.Q_flowdur[iq - 1]
                        ex_lower = float(self.exceedance_rel[iq - 1])
                    Q_higher = self.Q_flowdur[iq]
                    ex_higher = self.exceedance_rel[iq]
                    if Q_value > qq:
                        self.logger.info(" -->> qq: " + str(qq))
                        self.logger.info(" -->> Q_value: " + str(Q_value))
                        break
                    iq += 1
            else:
                Q_lower = Q_value
                ex_lower = 1.0
                Q_higher = min(self.Q_flowdur)
                ex_higher = 1.0
        else:
            self.logger.info(" >> HIGH DISCHARGE. Annual exceedance probability close to zero.")
            Q_lower = max(self.Q_flowdur)
            ex_lower = 0.0
            Q_higher = Q_value
            ex_higher = 0.0
        try:
            self.logger.info(" -->> ex_low: " + str(ex_lower))
            self.logger.info(" -->> ex_high: " + str(ex_higher))
            self.logger.info(" -->> Q_low: " + str(Q_lower))
            self.logger.info(" -->> Q_high: " + str(Q_higher))
            pr_exceedance = ex_lower + ((Q_value - Q_lower) / (Q_higher - Q_lower)) * (ex_higher - ex_lower)
            self.logger.info(" -->> Expected exceedance duration (per year): " + str(pr_exceedance * 100) + "%")
            return pr_exceedance
        except:
            self.logger.info("ERROR: Could not interpolate exceedance probability of Q = " + str(Q_value) + ".")
            return 0.0

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = FlowAssessment (Module: Habitat Evaluation)")


class SeasonalFlowProcessor:
    def __init__(self, input_xlsx, *args, **kwargs):
        # input_xlsx = STR full path of an input xlsx file
        # functionality:
        # 1) instantiate object
        # 2) assign fish species with self.get_fish_seasons and run self.make_flow_duration() for each species/lifestage
        self.fish = cf.Fish()
        self.fish_seasons = {}
        self.date_column = []
        self.flow_column = []
        self.flow_matrix = []  # rows=n-days, cols=m-years
        self.logger = logging.getLogger("logfile")
        self.min_year = 9999
        self.max_year = 1
        self.xlsx_template = os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\flow_duration_template.xlsx"
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

    def build_export(self):
        m_years = self.max_year - self.min_year + 1
        export_dict = {}
        for fish in self.fish_seasons.keys():
            # identify relevant dates and convert to id type DDMM
            date_integers = []
            start_date = datetime.datetime(self.fish_seasons[fish]["start"]["year"],
                                           self.fish_seasons[fish]["start"]["month"],
                                           self.fish_seasons[fish]["start"]["day"])
            end_date = datetime.datetime(self.fish_seasons[fish]["end"]["year"],
                                         self.fish_seasons[fish]["end"]["month"],
                                         self.fish_seasons[fish]["end"]["day"])
            if not self.date2id(end_date) > self.date2id(start_date):
                end_date = self.add_years(end_date, 1)

            for dy in range(int((end_date - start_date).days) + 1):
                date_id = self.date2id(start_date + datetime.timedelta(days=dy))
                if not date_id == 229:
                    # exclude leap year day
                    date_integers.append(date_id)
            n_dates = date_integers.__len__()
            fish_flows = np.ones((n_dates, m_years + 1)) * np.nan

            __row_source__ = 0
            __col_tar__ = 0
            for dy in self.date_column:
                date_id = self.date2id(dy)
                if date_id in date_integers:
                    positions = []
                    [positions.append(i) for i, x in enumerate(date_integers) if x == date_id]
                    fish_flows[positions[-1], __col_tar__] = self.flow_column[__row_source__]
                    if positions[-1] == n_dates - 1:
                        __col_tar__ += 1
                __row_source__ += 1

            mean_flows = []
            __row_tar__ = 0
            for id in date_integers:
                mean_flows.append(np.nanmean(fish_flows[__row_tar__, :]))
                __row_tar__ += 1
            mean_flows.sort(reverse=True)

            data4export = []
            __row_tar__ = 0
            for flow in mean_flows:
                data4export.append([flow, __row_tar__ + 1])
                __row_tar__ += 1
            export_dict.update({fish: data4export})
        return export_dict

    def date2id(self, curr_date):
        # curr_date = datetime.datetime object
        try:
            return int(str(curr_date.month) + str("%02i" % curr_date.day))
        except:
            return -1

    def get_fish_seasons(self, fish_species, fish_lifestage):
        # fish_species = STR as used in cFish.Fish()
        # fish_lifestage = STR as used in cFish.Fish()
        self.fish_seasons.update({str(fish_species).lower()[0:2] + str(fish_lifestage[0]): self.fish.get_season_dates(
            fish_species, fish_lifestage)})

    def make_fish_flow_duration(self):
        export_dict = self.build_export()
        return self.write_flow_duration2xlsx(export_dict)

    def read_flow_series(self, input_xlsx):
        try:
            input_xlsx_f = cio.Read(input_xlsx)
            self.date_column = input_xlsx_f.read_column('A', 3)
            self.flow_column = input_xlsx_f.read_column('B', 3)
            input_xlsx_f.close_wb()
            self.assign_years()
        except:
            self.logger.info("ERROR: The source discharge file contains non-detectable formats.")

    def write_flow_duration2xlsx(self, export_dict):
        for fish in export_dict.keys():
            export_xlsx_name = os.path.dirname(os.path.abspath(__file__)) + "\\FlowDurationCurves\\flow_duration_" + str(fish) + ".xlsx"
            self.logger.info(" >> Writing " + export_xlsx_name)
            xlsx_write = cio.Write(self.xlsx_template)
            # xlsx_write.open_wb(export_xlsx_name, 0)
            xlsx_write.write_cell("F", 3, fish)
            xlsx_write.write_cell("F", 4, " Month:" + str(self.fish_seasons[fish]["start"]["month"]) + " Day:" + str(self.fish_seasons[fish]["start"]["day"]))
            xlsx_write.write_cell("F", 5, " Month:" + str(self.fish_seasons[fish]["end"]["month"]) + " Day:" + str(self.fish_seasons[fish]["end"]["day"]))
            xlsx_write.write_cell("F", 6, self.min_year)
            xlsx_write.write_cell("F", 7, self.max_year)
            xlsx_write.write_matrix("B", 2, export_dict[fish])
            xlsx_write.save_close_wb(export_xlsx_name)
        try:
            return export_xlsx_name
        except:
            pass

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = FlowGenerator (Module: Habitat Evaluation)")
        print(dir(self))
