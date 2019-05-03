try:
    import sys, os, logging
    import webbrowser
except:
    print("ExceptionERROR: cFish is missing fundamental packages (required: os, sys, logging, webbrowser).")


try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cInputOutput as cio
    import fGlobal as fg

except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: /.site_packages/riverpy/fGlobal).")


class Fish:
    def __init__(self):

        self.life_stages = []
        self.logger = logging.getLogger("logfile")
        self.ls_row = 5
        self.ls_col_add = {"spawning": 1, "fry": 3, "ammocoetes": 3, "juvenile": 5, "adult": 7}  # ASCII codes
        self.parameter_rows = {"u": 9, "h": 38, "substrate": 72, "cobbles": 81, "boulders": 82, "plants": 84,
                               "wood": 85, "start_date": 6, "end_date": 7}
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.reader = None
        self.species = []
        self.species_col = {}
        self.species_dict = {}
        self.species_row = 2
        self.assign_fish_names()

    def assign_fish_names(self):
        # reads fish names and lifestages from .templates/Fish.xlsx
        # check if Fish.xlsx is accessible
        try:
            self.open_fish_wb()
        except:
            self.logger.info(
                "ERROR: Multiple openings of Fish.xlsx. Close all office applications and restart this program.")

        start_col = "C"
        species_skip = 8

        species_names = self.reader.read_row_str(self.species_row, start_col, col_skip=species_skip)

        _col_ = start_col
        for sn in species_names:
            _end_ = self.reader.col_num_to_name(self.reader.col_name_to_num(_col_) + species_skip - 1)
            life_stages = self.reader.read_row_str(self.ls_row, _col_, col_skip=2, end_col=_end_,
                                                   if_row=self.parameter_rows["u"])
            self.species_col.update({sn: _col_})
            self.species_dict.update({sn: life_stages})
            _col_ = self.reader.col_num_to_name(self.reader.col_name_to_num(_col_) + species_skip)
        self.close_fish_wb()

    def edit_xlsx(self):
        try:
            try:
                self.reader.close_wb()
            except:
                pass
            webbrowser.open(self.path + "\\.templates\\Fish.xlsx")
        except:
            self.logger.info("ERROR: Failed to open Fish.xlsx. Ensure that the workbook is not open.")

    def get_hsi_curve(self, species, lifestage, par):
        # par is either "u" (velocity), "h" (depth), "substrate", "cobble", "boulder", "plants" or "wood" (see init)
        # returns curve data pairs curve_data = [[par-values], [hsi-values]]
        try:
            self.open_fish_wb()
        except:
            self.logger.info("ERROR: Could not access Fish.xlsx.")
        try:
            start_row = self.parameter_rows[par]
        except:
            self.logger.info("ERROR: No HSI curve assigned for parameter type " + str(par) + ".")
            try:
                self.close_fish_wb()
            except:
                pass
            return -1
        try:
            col_par = self.reader.col_num_to_name(
                self.reader.col_name_to_num(self.species_col[species]) + self.ls_col_add[lifestage] - 1)
            col_hsi = self.reader.col_num_to_name(
                self.reader.col_name_to_num(self.species_col[species]) + self.ls_col_add[lifestage])
            curve_data = [self.reader.read_float_column_short(col_par, start_row), self.reader.read_float_column_short(col_hsi, start_row)]
        except:
            self.logger.info("ERROR: Could not read parameter type " + str(par) + " from Fish.xlsx.")
            try:
                self.close_fish_wb()
            except:
                pass
            return -1
        try:
            self.close_fish_wb()
        except:
            self.logger.info("ERROR: Could not access Fish.xlsx (close workbook).")
        return curve_data

    def get_season_dates(self, species, lifestage):
        try:
            self.open_fish_wb()
        except:
            self.logger.info("ERROR: Could not access Fish.xlsx.")

        col_date = self.reader.col_num_to_name(self.reader.col_name_to_num(self.species_col[species]) + self.ls_col_add[lifestage])

        row_start = self.parameter_rows["start_date"]
        row_end = self.parameter_rows["end_date"]
        season_start_date = self.reader.read_date_from_cell(col_date, row_start)
        season_end_date = self.reader.read_date_from_cell(col_date, row_end)
        return {"start": season_start_date, "end": season_end_date}

    def open_fish_wb(self):
        self.reader = cio.Read(self.path + "\\.templates\\Fish.xlsx")

    def close_fish_wb(self):
        self.reader.close_wb()
        self.reader = None

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = Fish (Module: HabitatEvaluation)")

