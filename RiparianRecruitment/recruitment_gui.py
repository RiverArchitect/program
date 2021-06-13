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

        self.condition = ""
        self.out_dir = ""

        row = 0

        self.l_prompt = tk.Label(self, text="Select Condition and Flow Data")
        self.l_prompt.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Select condition label and button (dropdown)
        self.l_condition = tk.Label(self, text="Select condition:")
        self.l_condition.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.combo_c = ttk.Combobox(self)
        self.combo_c.grid(sticky=tk.W, row=row, column=1, padx=self.xd, pady=self.yd)
        self.combo_c['values'] = tuple(fGl.get_subdir_names(config.dir2conditions))
        self.combo_c['state'] = 'readonly'
        self.b_s_condition = tk.Button(self, fg="red", text="Select",
                                       command=lambda: self.select_condition())
        self.b_s_condition.grid(sticky=tk.W, row=row, column=2, columnspan=2, padx=self.xd, pady=self.yd)
        row += 1

        self.l_inpath_curr = tk.Label(self, fg="gray60", text="Source: " + config.dir2conditions)
        self.l_inpath_curr.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1

        # Upload flow data button
        self.b_flow_data = tk.Button(self, width=10, fg="RoyalBlue3", bg="white",
                                     text="Select Flow Data",
                                      command=lambda: self.select_flow_data())
        self.b_flow_data.grid(sticky=tk.EW, row=row, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        row += 1

        # Modify recruitment criteria button
        self.b_mod_cr = tk.Button(self, width=25, bg="white", text="Modify recruitment criteria", command=lambda:
        self.open_inp_file("recruitment_criteria"))
        self.b_mod_cr.grid(sticky=tk.EW, row=row, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        row += 1

        # Run riparian recruitment submodule
        self.b_run_rr = tk.Button(self, width=25, fg="RoyalBlue3", bg="white",
                                  text="Analyze Riparian Recruitment")
        self.b_run_rr.grid(sticky=tk.W, row=row, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.b_run_rr['state'] = 'disabled'


    def run_recruitment(self):
        if self.condition.get() == '':
            self.logger.info("ERROR: Select condition.")
            return
        if self.flow_data.get() == '':
            self.logger.info("ERROR: Select file with flow data.")
            return
        rp = cRP.RecruitmentPotential(self.condition, self.unit)
        rp.recruitment_potential()


    def select_condition(self):
        try:
            self.condition = self.combo_c.get()
            input_dir = config.dir2conditions + str(self.condition)
            if os.path.exists(input_dir):
                self.b_s_condition.config(fg="forest green", text="Selected: " + self.condition)
            else:
                self.b_s_condition.config(fg="red", text="ERROR")
                self.errors = True
                self.verified = False
                return "Invalid file structure (non-existent directory /01_Conditions/CONDITION/)."
        except:
            self.errors = True
            self.verified = False
            return "Invalid entry for \'Condition\'."


    def select_flow_data(self):
        self.flow_data = askopenfilename(initialdir=config.dir2flows,
                                         title="Select flow data for recession rate calculation",
                                         filetypes=[("Text file", ".csv .txt .xls .xlsx")])
        b_text = str(self.flow_data)
        if b_text.__len__() > 50:
            b_text = "... \\" + str(self.flow_data).split("/")[-1].split("\\")[-1]
        self.b_flow_data.config(fg="forest green", text=str(b_text))
        if self.select_flow_data != {}:
            self.b_run_rr["state"] = "normal"


    def activate_buttons(self, **kwargs):
        target_state = "normal"
        # parse optional arguments
        try:
            for k in kwargs.items():
                if "revert" in k[0]:
                    if k[1]:
                        # disable buttons if revert = True
                        target_state = "disabled"
        except:
            pass
        self.b_flow_data["state"] = target_state
        self.b_run_rr["state"] = target_state


    def open_inp_file(self, filename, *args):
        # args[0] = STR indicating other modules
        _f = None
        try:
            if "recruitment_criteria" in filename:
                _f = config.xlsx_recruitment
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

    def __call__(self):
        self.mainloop()
