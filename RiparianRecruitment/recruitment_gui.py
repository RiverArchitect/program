try:
    import os, sys
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging tkinter, webbrowser).")

try:
    # import own routines
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import cRecruitmentPotential as cRP
    import cRecruitmentCriteria as cRC
    # import child gui
    import child_gui as cg
    # load routines from riverpy
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    # ALSO: add the new module path to the \.site_packages\riverpy\config.py
    # All 'vital' packages and functions are loaded and stored, respectivel from \.site_packages\riverpy\fGlobal.py
    import config
    import cFlows as cFl
    import fGlobal as fGl
    import cMakeTable as cMkT
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class MainGui(cg.RaModuleGui):
    def __init__(self, from_master):
        cg.RaModuleGui.__init__(self, from_master)
        self.ww = 580  # window width
        self.wh = 650  # window height
        self.title = "Recruitment Potential"
        self.set_geometry(self.ww, self.wh, self.title)

        # Populated by self.select_condition()
        self.condition = ""
        #  Populated by self.select_species()
        self.species = ""
        # Populated by self.select_flow_data()
        self.flow_data = ""
        # Populated by self.select_year()
        self.selected_year = ""
        # Populated by self.select_ex_veg_ras()
        self.ex_veg_ras = ""
        # Populated by self.select_grading_ext_ras()
        self.grading_ext_ras = ""

        row = 0

        self.l_prompt = tk.Label(self, text="Select Condition and Species of Interest")
        self.l_prompt.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Select condition label and button (dropdown)
        self.l_condition = tk.Label(self, text="Select condition:")
        self.l_condition.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.combo_c = ttk.Combobox(self)
        self.combo_c.grid(sticky=tk.W, row=row, column=1, padx=self.xd, pady=self.yd)
        self.combo_c['values'] = tuple(fGl.get_subdir_names(config.dir2conditions))
        self.combo_c['state'] = 'readonly'
        self.b_s_condition = tk.Button(self, fg="red", text="Select", command=lambda: self.select_condition())
        self.b_s_condition.grid(sticky=tk.W, row=row, column=2, columnspan=2, padx=self.xd, pady=self.yd)
        row += 1

        self.l_inpath_curr = tk.Label(self, fg="gray60", text="Source: " + config.dir2conditions)
        self.l_inpath_curr.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Select species of interest label and button (dropdown)
        self.l_species = tk.Label(self, text="Select species: ")
        self.l_species.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.combo_s = ttk.Combobox(self)
        self.combo_s.grid(sticky=tk.W, row=row, column=1, padx=self.xd, pady=self.yd)
        self.combo_s['values'] = cRC.RecruitmentCriteria().common_name_list
        self.combo_s['state'] = 'readonly'
        self.b_s_species = tk.Button(self, fg="red", text="Select", command=lambda: self.select_species())
        self.b_s_species.grid(sticky=tk.W, row=row, column=2, columnspan=2, padx=self.xd, pady=self.yd)
        row += 1

        # Modify recruitment criteria button
        self.b_mod_cr = tk.Button(self, width=25, bg="white", text="Modify recruitment criteria", command=lambda:
        self.open_inp_file("recruitment_criteria"))
        self.b_mod_cr.grid(sticky=tk.W, row=row, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        row += 1

        self.l_prompt = tk.Label(self, text="Upload Flow Data and Select Year-of-Interest")
        self.l_prompt.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Upload flow data button
        self.l_flow_data = tk.Label(self, text="Upload flow data:")
        self.l_flow_data.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.b_flow_data = tk.Button(self, fg="RoyalBlue3", bg="white",
                                     text="Select Flow Data", command=lambda: self.select_flow_data())
        self.b_flow_data['state'] = 'disabled'
        self.b_flow_data.grid(sticky=tk.W, row=row, column=1, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Select year-of-interest button (dropdown)
        self.year_of_interest = tk.Label(self, text="Select year-of-interest:")
        self.year_of_interest.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.combo_y = ttk.Combobox(self)
        self.combo_y.grid(sticky=tk.W, row=row, column=1, padx=self.xd, pady=self.yd)
        self.combo_y['values'] = []
        self.combo_y['state'] = 'disabled'
        self.b_s_year = tk.Button(self, fg="red", text="Select", command=lambda: self.select_year())
        self.b_s_year['state'] = 'disabled'
        self.b_s_year.grid(sticky=tk.W, row=row, column=2, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        self.l_prompt = tk.Label(self, text="Upload Vegetation Raster and Grading Limits Raster")
        self.l_prompt.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Upload existing vegetation raster button
        self.ex_veg_ras = tk.Label(self, text="Upload vegetation raster:")
        self.ex_veg_ras.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.b_ex_veg_ras = tk.Button(self, fg="RoyalBlue3", bg="white",
                                   text="Select vegetation raster",
                                   command=lambda: self.select_ex_veg_ras())
        self.b_ex_veg_ras["state"] = 'disabled'
        self.b_ex_veg_ras.grid(sticky=tk.W, row=row, column=1, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Upload grading limits raster button
        self.grading_ext_ras = tk.Label(self, text="Upload grading limits raster:")
        self.grading_ext_ras.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.b_grading_ext_ras = tk.Button(self, fg="RoyalBlue3", bg="white",
                                               text="Select grading limits raster",
                                               command=lambda: self.select_grading_ext_ras())
        self.b_grading_ext_ras["state"] = 'disabled'
        self.b_grading_ext_ras.grid(sticky=tk.W, row=row, column=1, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Run Riparian SeedlingRecruitment submodule
        self.b_run_rr = tk.Button(self, width=40, fg="RoyalBlue3", bg="white",
                                  text="Analyze Riparian Seedling Recruitment", command=lambda: self.run_recruitment())
        self.b_run_rr.grid(sticky=tk.W, row=row, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.b_run_rr['state'] = 'disabled'

    def select_condition(self):
        try:
            self.condition = self.combo_c.get()
            input_dir = config.dir2conditions + str(self.condition)
            if os.path.exists(input_dir):
                self.b_s_condition.config(fg="forest green", text="Selected: " + self.condition)
                # activate vegetation and grading limits raster if condition is exists
                self.b_ex_veg_ras["state"] = 'normal'
                self.b_grading_ext_ras["state"] = 'normal'
            else:
                self.b_s_condition.config(fg="red", text="ERROR")
                self.errors = True
                self.verified = False
                return "Invalid file structure (non-existent directory /01_Conditions/CONDITION/)."
        except:
            self.errors = True
            self.verified = False
            return "Invalid entry for \'Condition\'."

    def select_species(self):
        try:
            self.species = self.combo_s.get()
            self.b_s_species.config(fg="forest green", text="Selected: " + self.species)
        except:
            self.errors = True
            self.verified = False
            return "Invalid entry for species."
        # activate flow data selection if species is selected
        if self.species != '':
            self.b_flow_data['state'] = 'normal'
            self.set_years_list()

    def select_flow_data(self):
        self.flow_data = askopenfilename(initialdir=config.dir2flows + "\\InputFlowSeries",
                                         title="Select flow data for recession rate calculation",
                                         filetypes=[("Text file", ".csv .xls .xlsx")])
        b_text = str(self.flow_data)
        if b_text.__len__() > 50:
            b_text = "Selected: ... \\" + os.path.basename(b_text)
        else:
            b_text = "Selected: " + b_text
        self.b_flow_data.config(fg="forest green", text=str(b_text))
        self.set_years_list()

    def set_years_list(self):
        # populate combobox for year selection if we have selected flow data
        if self.flow_data != '':
            years_list = cRP.RecruitmentPotential(self.condition, self.flow_data, self.species, self.selected_year, self.unit, self.ex_veg_ras, self.grading_ext_ras).years_list
            self.combo_y['values'] = years_list
            self.combo_y['state'] = 'readonly'
            self.b_s_year['state'] = 'normal'

    def select_year(self):
        self.selected_year = self.combo_y.get()
        if self.combo_y.get() != '':
            self.b_s_year.config(fg="forest green", text='Selected: ' + self.selected_year)
            self.b_run_rr["state"] = "normal"

    def select_ex_veg_ras(self):
        self.ex_veg_ras = askopenfilename(initialdir=config.dir2conditions + '\\' + self.condition,
                                       title="Select vegetation raster to subtract from bed preparation calculations",
                                       filetypes=[("Raster files", ".tif .tiff .flt .asc")])
        b_text = str(self.ex_veg_ras)
        if b_text.__len__() > 50:
            b_text = "Selected: ... \\" + os.path.basename(b_text)
        else:
            b_text = "Selected: " + b_text
        self.b_ex_veg_ras.config(fg="forest green", text=str(b_text))

    def select_grading_ext_ras(self):
        self.grading_ext_ras = askopenfilename(initialdir=config.dir2conditions + '\\' + self.condition,
                                               title="Select grading limits raster to consider as \"fully prepared\" bed",
                                               filetypes=[("Raster files", ".tif .tiff .flt .asc")])
        b_text = str(self.grading_ext_ras)
        if b_text.__len__() > 50:
            b_text = "Selected: ... \\" + os.path.basename(b_text)
        else:
            b_text = "Selected: " + b_text
        self.b_grading_ext_ras.config(fg="forest green", text=str(b_text))

    def open_inp_file(self, filename, *args):
        # args[0] = STR indicating other modules
        _f = None
        try:
            if "recruitment_criteria" in filename:
                _f = config.xlsx_recruitment_criteria
        except:
            pass
        if os.path.isfile(_f):
            try:
                webbrowser.open(_f)
            except:
                showinfo("ERROR ", "Cannot open " + str(_f) +
                         ".\nMake sure that the file was created (Get Started tab) and that your operating system has a standard application defined for *.inp-files.")
        else:
            showinfo("ERROR ",
                     "The file " + str(_f) + " does not exist.\nUse the Get Started tab to create and input file.")

    def run_recruitment(self):
        if self.condition == '':
            self.logger.info("ERROR: Select condition.")
            return
        if self.flow_data == '':
            self.logger.info("ERROR: Select flow data file (.csv, .txt, .xls, .xlsx).")
            return
        # passing arguments (users selections) to cRecruitmentPotential
        rp = cRP.RecruitmentPotential(self.condition, self.flow_data, self.species, self.selected_year, self.unit, self.ex_veg_ras, self.grading_ext_ras)
        rp.run_rp()

    def __call__(self):
        self.mainloop()
