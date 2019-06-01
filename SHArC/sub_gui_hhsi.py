try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, Tkinter, webbrowser).")

try:
    # import own routines
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cHSI as chsi

    # load routines from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import cMakeTable as cMkT
    import cFlows as cFl
    import cInputOutput as cIO
    import fGlobal as fG
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class HHSIgui(object):
    def __init__(self, master, unit, fish_applied, *args):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.dir_conditions = self.dir2ra + "01_Conditions\\"
        self.dir_input_ras = ""
        self.condition = ""
        self.condition_list = fG.get_subdir_names(self.dir_conditions)
        self.max_columnspan = 5
        self.discharge_xlsx = []
        self.unit = unit
        self.fish_applied = fish_applied

        self.top.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

        try:
            # test if a boundary shapefile was provided
            self.boundary_shp = args[0]
        except:
            self.boundary_shp = ""

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 420
        wh = 307
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Generate hydraulic habitat condition (HSI) Rasters")  # window title

        self.l_condition = tk.Label(top, text="Select a hydraulic Condition:")
        self.l_condition.grid(sticky=tk.W, row=2, rowspan=3, column=0, padx=self.xd, pady=self.yd)
        self.l_inpath_curr = tk.Label(top, fg="gray60", text="Source: "+str(self.dir_conditions))
        self.l_inpath_curr.grid(sticky=tk.W, row=5, column=0, columnspan=self.max_columnspan + 1, padx=self.xd, pady=self.yd)

        self.l_dummy = tk.Label(top, text="                                                                          ")
        self.l_dummy.grid(sticky=tk.W, row=2, column=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.l_run_info = tk.Label(top, text="")
        self.l_run_info.grid(sticky=tk.W, row=8, column=0, columnspan=self.max_columnspan - 1, padx=self.xd,
                             pady=self.yd)

        # DROP DOWN ENTRIES (SCROLL BARS)
        self.sb_condition = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=2, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.E, row=2, column=1, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)

        # BUTTONS
        iflow = "Flow data are looked up from the selected Condition and Aquatic Ambiance"
        self.l_flowdur = tk.Label(top, bg="white", text=iflow)
        self.l_flowdur.grid(sticky=tk.EW, row=1, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.b_c_select = tk.Button(top, width=8, bg="white", text="Select", command=lambda: self.select_condition())
        self.b_c_select.grid(sticky=tk.W, row=2, rowspan=3, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)

        self.b_Q = tk.Button(top, fg="RoyalBlue3", width=30, bg="white",
                             text="    Optional: View discharge dependency file (xlsx workbook)", anchor='w',
                             command=lambda: self.user_message("Confirm hydraulic Condition first!"))
        self.b_Q.grid(sticky=tk.EW, row=6, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.b_HSC = tk.Button(top, width=30, bg="white",
                               text="    Optional: Edit Habitat Suitability Curves", anchor='w',
                               command=lambda: self.open_files([self.dir2ra + ".site_packages\\templates\\Fish.xlsx"]))
        self.b_HSC.grid(sticky=tk.EW, row=7, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

        self.b_run = tk.Button(top, width=30, bg="white", text="Run (generate habitat condition)",
                               anchor='w', command=lambda: self.run_raster_calc())
        self.b_run.grid(sticky=tk.EW, row=8, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)
        self.b_run["state"] = "disabled"

        self.b_return = tk.Button(top, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW", command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=9, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        self.top.destroy()

    def open_files(self, f_list):
        for _f in f_list:
            self.user_message("Do not forget to save files after editing ...")
            fG.open_file(_f)

    def prepare_discharge_file(self):
        for species in self.fish_applied.keys():
            for ls in self.fish_applied[species]:
                fsn = str(species).lower()[0:2] + str(ls[0:2])
                # copy spreadsheet with discharge dependencies (if not yet existent)
                spreadsheet_handle = cMkT.MakeFlowTable(self.condition, "sharc", unit=self.unit)
                self.discharge_xlsx.append(spreadsheet_handle.make_aquatic_condition_xlsx(fsn))
                # get discharge statistics and write them to workbook
                xlsx_flow_dur = self.dir2ra + "00_Flows\\" + self.condition + "\\flow_duration_" + str(fsn) + ".xlsx"
                Q_stats = cFl.FlowAssessment()
                Q_stats.get_flow_duration_data_from_xlsx(xlsx_flow_dur)
                exceedances = []
                error_msg = []
                for qq in spreadsheet_handle.discharges:
                    try:
                        exceedances.append(Q_stats.interpolate_flow_exceedance(float(qq)))  # in percent
                    except:
                        error_msg.append("Invalid exceedances found for Q = " + str(qq) + ".")
                        exceedances.append(0.0)

                spreadsheet_handle.write_data_column("E", 4, exceedances)
                spreadsheet_handle.save_close_wb()
                spreadsheet_handle.copy_wb(spreadsheet_handle.wb_out_name,
                                           spreadsheet_handle.wb_out_name.split(".xlsx")[0] + "_cov.xlsx")

                if error_msg.__len__() > 0:
                    showinfo("ERRORS FOUND", "\n".join(error_msg))

    def remake_buttons(self):
        self.b_c_select.config(bg="PaleGreen1")
        self.b_Q.config(fg="black", text="View discharge dependency file (xlsx workbook)",
                        command=lambda: self.open_files(self.discharge_xlsx), bg="PaleGreen1")
        self.b_run["state"] = "normal"

    def run_raster_calc(self):
        msg0 = "Analysis takes a while. \nPython windows seem unresponsive in the meanwhile. \nCheck console messages."
        msg1 = "\n\nClick OK to start DHSI and VHSI calculation."
        showinfo("INFORMATION ", msg0 + msg1)
        hhsi = chsi.HHSI(self.dir_input_ras, self.condition, self.unit)

        hhsi.make_hhsi(self.fish_applied, self.boundary_shp)
        self.top.bell()

        try:
            if not hhsi.error:
                fG.open_folder(hhsi.path_hsi)
                self.l_run_info.config(fg="forest green", text="RUN SUCCESSFULLY COMPLETED (close window)")
                self.b_run.config(width=30, bg="PaleGreen1", text="Re-run (generate habitat condition)")
            else:
                self.l_run_info.config(fg="red", text="RUN COMPLETED WITH ERRORS")
                self.b_run.config(bg="salmon", text="Re-run (generate habitat condition)")
        except:
            pass
        try:
            hhsi.clear_cache()
        except:
            pass
        showinfo("COMPUTATION FINISHED", "Check logfile (logfile.log).")

    def select_condition(self):
        items = self.lb_condition.curselection()
        self.condition = [self.condition_list[int(item)] for item in items][0]
        self.dir_input_ras = self.dir2ra + "01_Conditions\\" + self.condition + "\\"

        if os.path.exists(self.dir_input_ras):
            self.l_inpath_curr.config(fg="forest green", text="Selected: " + str(self.dir_input_ras))
        else:
            self.l_inpath_curr.config(fg="red", text="SELECTION ERROR                                 ")
        self.prepare_discharge_file()
        self.remake_buttons()

    # def select_flowdur_xlsx(self):
    #     self.xlsx_flow_dur = askopenfilename(initialdir=self.dir2ra + "\\00_Flows\\", title="Select xlsx file containing the discharge duration curve (Q_flowdur-days)")
    #     self.b_flowdur_select.config(
    #         text="i) Selected flow duration curve: " + str(self.xlsx_flow_dur).split("/")[-1].split("\\")[-1],
    #         fg="forest green")
    #     self.b_c_select["state"] = "normal"

    def user_message(self, msg):
        showinfo("INFO", msg)

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

