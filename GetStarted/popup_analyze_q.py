try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    import cConditionCreator as cCC
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cFish as cFi
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py).")


class FlowAnalysis(object):
    def __init__(self, master):
        top = self.top = tk.Toplevel(master)
        self.condition = ""
        self.condition_list = fGl.get_subdir_names(config.dir2conditions)
        self.dir2condition_act = '.'
        self.dir2dem = ''
        self.dir2h = ''
        self.dir2u = ''
        self.eco_flow_type = cFi.Fish()
        self.eco_flow_type_applied = {}
        self.eco_flow_type_list = []
        self.flows_xlsx = ''
        self.flow_series_xlsx = None
        self.logger = logging.getLogger("logfile")

        # define analysis type identifiers (default = False)
        self.bool_var = tk.BooleanVar()
        self.top.iconbitmap(config.code_icon)

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 590
        wh = 370
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Analyze Discharge")  # window title

        self.col_0_width = 25

        # Set Condition
        self.l_0 = tk.Label(top, text="1) Analyze a Condition")
        self.l_0.grid(sticky=tk.W, row=0, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.l_name = tk.Label(top, text="Select condition: ")
        self.l_name.grid(sticky=tk.W, row=1, rowspan=3, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=1, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_condition.set)
        for ce in self.condition_list:
            self.lb_condition.insert(tk.END, ce)
        self.lb_condition.grid(sticky=tk.EW, row=1, column=1, padx=0, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)
        self.b_sc = tk.Button(top, width=self.col_0_width-5, fg="firebrick3", bg="white", text="Analyze",
                              command=lambda: self.scan_condition())
        self.b_sc.grid(sticky=tk.E, row=1, rowspan=3, column=2, padx=self.xd, pady=self.yd)
        self.l_c_dir = tk.Label(top, fg="firebrick3", text="Select a condition and press \'Analyze\'.")
        self.l_c_dir.grid(sticky=tk.W, row=4, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=5, column=0)  # dummy

        # 02 Make input file for condition
        self.l_1 = tk.Label(top, text="2) Generate Flow Duration Curves")
        self.l_1.grid(sticky=tk.W, row=6, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_mod = tk.Button(top, bg="white", text="Modify Source",
                               command=lambda: self.modify_eco_flow_source())
        self.b_mod.grid(sticky=tk.E, row=6, column=2, padx=self.xd, pady=self.yd)
        self.l_s_type = tk.Label(top, text="Add season / target species: ")
        self.l_s_type.grid(sticky=tk.W, row=7, rowspan=3, column=0, padx=self.xd, pady=self.yd)
        self.sb_type = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_type.grid(sticky=tk.W, row=7, column=2, padx=0, pady=self.yd)
        self.lb_type = tk.Listbox(top, height=3, width=25, yscrollcommand=self.sb_type.set)
        self.lb_type.grid(sticky=tk.EW, row=7, column=1, padx=0, pady=self.yd)
        self.make_eco_type_list(rebuild=False)
        self.b_sct = tk.Button(top, fg="firebrick3", width=self.col_0_width - 5, bg="white", text="Add",
                               command=lambda: self.select_eco_type())
        self.b_sct.grid(sticky=tk.E, row=7, rowspan=3, column=2, padx=self.xd, pady=self.yd)
        self.l_ct_dir = tk.Label(top, text="Current selection: {0}".format(fGl.print_dict(self.eco_flow_type_applied)))
        self.l_ct_dir.grid(sticky=tk.W, row=10, column=0, columnspan=4, padx=self.xd, pady=self.yd)

        self.b_q_inp = tk.Button(top, width=self.col_0_width * 2, fg="firebrick3", bg="white",
                                 text="Select input Flow Series",
                                 command=lambda: self.select_flow_series_xlsx())
        self.b_q_inp.grid(sticky=tk.EW, row=11, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_q_dur = tk.Button(top, width=self.col_0_width * 2, fg="firebrick3", bg="white",
                                 text="Make flow duration curve(s)", command=lambda: self.make_flow_duration())
        self.b_q_dur.grid(sticky=tk.EW, row=12, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_sct["state"] = "disabled"
        self.b_q_inp["state"] = "disabled"
        self.b_q_dur["state"] = "disabled"

        self.b_return = tk.Button(top, width=self.col_0_width, fg="RoyalBlue3", bg="white", 
                                  text="RETURN to MAIN WINDOW", command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=12, column=2, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        self.top.destroy()

    def make_flow_duration(self):        
        condition4input = cCC.ConditionCreator(self.dir2condition_act)
        if not self.flow_series_xlsx:
            self.select_flow_series_xlsx()

        flow_duration_xlsx = condition4input.create_flow_duration_table(self.flow_series_xlsx, self.eco_flow_type_applied)
        try:
            if not condition4input.error:
                fGl.open_file(flow_duration_xlsx)
                self.b_q_dur.config(fg="forest green")
            else:
                showinfo("ERROR", "Review error messages (console / logfile.log).", parent=self.top)
                self.b_q_dur.config(fg="firebrick3", text="Re-try flow duration creation")
        except:
            pass

    def make_eco_type_list(self, rebuild):
        # if rebuild = True -> rebuilt reset lb_type entries and eco-type_applied dict
        if rebuild:
            self.eco_flow_type_applied = {}
            self.eco_flow_type_list = []
            e = 0
            for lbe in self.lb_type:
                self.lb_type.delete(e)
                e += 1

        for f_spec in self.eco_flow_type.species_dict.keys():
            lf_stages = self.eco_flow_type.species_dict[f_spec]
            for lfs in lf_stages:
                self.eco_flow_type_list.append("{0} - {1}".format(str(f_spec), str(lfs)))
                self.lb_type.insert(tk.END, self.eco_flow_type_list[-1])
        self.sb_type.config(command=self.lb_type.yview)

    def modify_eco_flow_source(self):
        self.eco_flow_type.edit_xlsx()
        self.b_mod.config(text="Refresh Window", command=self.make_eco_type_list(rebuild=True))

    def scan_condition(self):
        items = self.lb_condition.curselection()
        self.condition = str([self.condition_list[int(item)] for item in items][0])
        self.dir2condition_act = config.dir2conditions + self.condition  # INFO: dir2new_condition may not end with "\\"!
        if os.path.isfile(self.dir2condition_act + "\\flow_definitions.xlsx"):
            run = tk.messagebox.askyesno("Create new?",
                                         "%s already exists.\nDo you want to create another flow_definitions.xlsx?" % self.dir2condition_act,
                                         parent=self.top)
        else:
            run = True
        if run:
            condition4flows = cCC.ConditionCreator(self.dir2condition_act)
            self.flows_xlsx = condition4flows.create_discharge_table()

        self.l_c_dir.config(fg="forest green", text="Selected: " + self.dir2condition_act)
        self.b_sc.config(fg="forest green", text="Analyzed")
        self.b_sct["state"] = "normal"

        try:
            if run and not condition4flows.error:
                msg0 = "Analysis complete.\n"
                msg1 = "Complete discharge (flood) return periods in the discharges workbook."
                showinfo("INFO", msg0 + msg1, parent=self.top)
                fGl.open_file(self.flows_xlsx)
            if run and condition4flows.error:
                self.b_sc.config(fg="firebrick3", text="Analysis failed")
        except:
            pass

    def select_eco_type(self):
        items = self.lb_type.curselection()
        selected = [str(self.eco_flow_type_list[item]) for item in items][0]
        f_spec = selected.split(' - ')[0]
        lfs = selected.split(' - ')[-1]

        if not (f_spec in self.eco_flow_type_applied.keys()):
            self.eco_flow_type_applied.update({f_spec: []})
        self.eco_flow_type_applied[f_spec].append(lfs)
        self.logger.info(" > Added: " + str(f_spec) + " - " + str(lfs))
        self.l_ct_dir.config(text="Current selection: {0}".format(fGl.print_dict(self.eco_flow_type_applied)),
                             fg="forest green")
        self.b_sct.config(fg="forest green")
        self.b_q_inp["state"] = "normal"

    def select_flow_series_xlsx(self):
        self.flow_series_xlsx = askopenfilename(initialdir=config.dir2flows + "\\InputFlowSeries",
                                                title="Select flow series workbook (xlsx)",
                                                filetypes=[("Workbooks", "*.xlsx")], parent=self.top)
        b_text = str(self.flow_series_xlsx)
        if b_text.__len__() > 50:
            b_text = "... \\" + str(self.flow_series_xlsx).split("/")[-1].split("\\")[-1]
        self.b_q_inp.config(fg="forest green", text=str(b_text))
        self.b_q_dur["state"] = "normal"

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

