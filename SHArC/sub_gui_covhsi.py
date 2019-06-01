try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    # import own routines
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import cHSI as chsi

    # load routines from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\LifespanDesign\\")
    import cParameters as cPa

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fG
except:
    print("ExceptionERROR: Cannot find package files (riverpy/fGlobal.py).")


class CovHSIgui(object):
    def __init__(self, master, unit, fish_applied):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path_lvl_up = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cover_applies = False
        self.dir_conditions = self.path_lvl_up + "\\01_Conditions\\"
        self.dir_input_ras = ""
        self.condition = ""
        self.condition_list = fG.get_subdir_names(self.dir_conditions)
        self.flow_path = ""     # full path to whetted-region defining raster
        self.h_list = ["all terrain"]
        self.h_ras_path = ""
        self.max_columnspan = 5
        self.unit = unit
        self.fish_applied = fish_applied

        # define analysis type identifiers (default = False)
        self.substrate = tk.BooleanVar()
        self.boulders = tk.BooleanVar()
        self.cobbles = tk.BooleanVar()
        self.wood = tk.BooleanVar()
        self.plants = tk.BooleanVar()
        self.hsi_types = {"substrate": self.substrate, "boulders": self.boulders, "cobbles": self.cobbles,
                          "wood": self.wood, "plants": self.plants}

        self.top.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 570
        wh = 475
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Generate cover habitat condition rasters")  # window title

        act_row = 0

        # Select condition ROWs 0 - 3
        self.l_condition = tk.Label(top, text="1) Select condition:")
        self.l_condition.grid(sticky=tk.W, row=act_row, rowspan=3, column=0, padx=self.xd, pady=self.yd)

        self.l_dummy = tk.Label(top, text="                                                                          ")
        self.l_dummy.grid(sticky=tk.W, row=act_row, column=self.max_columnspan, padx=self.xd, pady=self.yd)
        self.sb_condition = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=act_row, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_condition.set)
        for e in self.condition_list:
            self.lb_condition.insert(tk.END, e)
        self.lb_condition.grid(sticky=tk.E, row=act_row, column=1, padx=self.xd, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)
        self.b_c_select = tk.Button(top, width=8, bg="white", text="Confirm\nselection", command=lambda: self.select_condition())
        self.b_c_select.grid(sticky=tk.W, row=act_row, rowspan=3, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        msg_hc1 = "Highlight one condition (located in the 01_Conditions folder)."
        self.b_h_con = tk.Button(top, fg="RoyalBlue3", bg="white", text="Help", command=lambda: self.user_message(msg_hc1))
        self.b_h_con.grid(sticky=tk.W, row=act_row, column=self.max_columnspan, padx=self.xd, pady=self.yd)
        act_row += 3
        self.l_inpath_curr = tk.Label(top, fg="gray60", text="Source: " + str(self.dir_conditions))
        self.l_inpath_curr.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan + 1,
                                padx=self.xd, pady=self.yd)
        act_row += 1

        # Select flow cover raster ROWs 4 - 7
        self.l_flow = tk.Label(top, text="2) Define flow region:")
        self.l_flow.grid(sticky=tk.W, row=act_row, rowspan=3, column=0, padx=self.xd, pady=self.yd)

        self.l_dummy2 = tk.Label(top, text="                                                                          ")
        self.l_dummy2.grid(sticky=tk.W, row=act_row, column=self.max_columnspan, padx=self.xd, pady=self.yd)
        self.sb_flow = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_flow.grid(sticky=tk.W, row=act_row, column=2, padx=0, pady=self.yd)
        self.lb_flow = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_flow.set)
        for e in self.h_list:
            self.lb_flow.insert(tk.END, e)
        self.lb_flow.grid(sticky=tk.E, row=act_row, column=1, padx=self.xd, pady=self.yd)
        self.sb_flow.config(command=self.lb_flow.yview)
        self.b_c_select = tk.Button(top, width=8, bg="white", text="Confirm\nselection",
                                    command=lambda: self.select_flow())
        self.b_c_select.grid(sticky=tk.W, row=act_row, rowspan=3, column=self.max_columnspan - 1, padx=self.xd,
                             pady=self.yd)
        msg_flow1 = "Once a condition was selected, the flow region box lists the available flow depth rasters in the condition\'s folder.\n"
        msg_flow2 = "The selected flow depth raster defines where cover applies and excludes areas where the flow depth is smaller than the smallest value defined in Fish.xlsx or NaN."
        self.b_h_flow = tk.Button(top, fg="RoyalBlue3", bg="white", text="Help",
                                  command=lambda: self.user_message(msg_flow1 + msg_flow2))
        self.b_h_flow.grid(sticky=tk.W, row=act_row, column=self.max_columnspan, padx=self.xd, pady=self.yd)
        act_row += 3
        self.l_inflow_curr = tk.Label(top, fg="gray60", text="Current: " + str(self.flow_path))
        self.l_inflow_curr.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan + 1,
                                padx=self.xd, pady=self.yd)
        act_row += 1

        # Select type ROW
        self.l_select_msg = tk.Label(top, text="3) Select (cover) type(s) ")
        self.l_select_msg.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        self.b_edit_hsc = tk.Button(top, fg="RoyalBlue3", bg="white", text="Edit HSCs",
                                    command=lambda: self.open_files([self.path + "\\.templates\\Fish.xlsx"]))
        self.b_edit_hsc.grid(sticky=tk.EW, row=act_row, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        act_row += 1

        msg_0 = "The applied Habitat Suitability Curves can be adapted by clicking on the Edit HSCs button."

        # SUBSTRATE ROW
        self.cb_substrate = tk.Checkbutton(top, text="Make substrate HSI raster", variable=self.substrate,
                                           onvalue=True, offvalue=False,
                                           command=lambda: self.print_msg("Substrate: " + str(self.substrate.get())))
        self.cb_substrate.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan - 1,
                               padx=self.xd, pady=self.yd)
        msg_s1 = "If this box is checked, a substrate_hsi raster is created in the HabitatEvaluation/HSI/" + self.condition + "folder.\n"
        msg_s2 = "A dmean raster is needed in the 01_Conditions/" + self.condition + " folder.\n"
        self.b_h_subs = tk.Button(top, fg="RoyalBlue3", bg="white", text="Help",
                                  command=lambda: self.user_message(msg_s1 + msg_s2 + msg_0))
        self.b_h_subs.grid(sticky=tk.EW, row=act_row, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        act_row += 1

        # BOULDER ROW
        self.cb_bou = tk.Checkbutton(top, text="Make boulder HSI raster", variable=self.boulders,
                                     onvalue=True, offvalue=False,
                                     command=lambda: self.print_msg("Boulders: " + str(self.boulders.get())))
        self.cb_bou.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan - 1,
                         padx=self.xd, pady=self.yd)
        msg_b1 = "If this box is checked, a boulder_hsi raster is created in the HabitatEvaluation/HSI/" + self.condition + "folder.\n"
        msg_b2 = "A boulders.shp delineation shapefile (polygon) is needed in the 01_Conditions/" + self.condition + " folder.\n"
        self.b_h_bou = tk.Button(top, fg="RoyalBlue3", bg="white", text="Help",
                                 command=lambda: self.user_message(msg_b1 + msg_b2 + msg_0))
        self.b_h_bou.grid(sticky=tk.EW, row=act_row, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        act_row += 1

        # COBBLE ROW
        self.cb_cob = tk.Checkbutton(top, text="Make cobble HSI raster", variable=self.cobbles,
                                     onvalue=True, offvalue=False,
                                     command=lambda: self.print_msg("Cobbles: " + str(self.cobbles.get())))
        self.cb_cob.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan - 1,
                         padx=self.xd, pady=self.yd)
        msg_c1 = "If this box is checked, a cobble_hsi raster is created in the HabitatEvaluation/HSI/" + self.condition + "folder.\n"
        msg_c2 = "A dmean raster is needed in the 01_Conditions/" + self.condition + " folder.\n"
        self.b_h_cob = tk.Button(top, fg="RoyalBlue3", bg="white", text="Help",
                                 command=lambda: self.user_message(msg_c1 + msg_c2 + msg_0))
        self.b_h_cob.grid(sticky=tk.EW, row=act_row, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        act_row += 1

        # STREAMWOOD ROW
        self.cb_wood = tk.Checkbutton(top, text="Make streamwood HSI raster", variable=self.wood,
                                      onvalue=True, offvalue=False,
                                      command=lambda: self.print_msg("Streamwood: " + str(self.wood.get())))
        self.cb_wood.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan - 1,
                          padx=self.xd, pady=self.yd)
        msg_w1 = "If this box is checked, a cobble_hsi raster is created in the HabitatEvaluation/HSI/" + self.condition + "folder.\n"
        msg_w2 = "A wood.shp delineation shapefile (polygon) is needed in the 01_Conditions/" + self.condition + " folder.\n"
        self.b_h_wood = tk.Button(top, fg="RoyalBlue3", bg="white", text="Help",
                                  command=lambda: self.user_message(msg_w1 + msg_w2 + msg_0))
        self.b_h_wood.grid(sticky=tk.EW, row=act_row, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        act_row += 1

        # PLANTS ROW
        self.cb_veg = tk.Checkbutton(top, text="Make vegetation (plants) HSI raster", variable=self.plants,
                                     onvalue=True, offvalue=False,
                                     command=lambda: self.print_msg("Plants: " + str(self.plants.get())))
        self.cb_veg.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan - 1,
                         padx=self.xd, pady=self.yd)
        msg_v1 = "If this box is checked, a plants_hsi raster is created in the HabitatEvaluation/HSI/" + self.condition + "folder.\n"
        msg_v2 = "A plants.shp delineation shapefile (polygon) is needed in the 01_Conditions/" + self.condition + " folder.\n"
        self.b_h_veg = tk.Button(top, fg="RoyalBlue3", bg="white", text="Help",
                                 command=lambda: self.user_message(msg_v1 + msg_v2 + msg_0))
        self.b_h_veg.grid(sticky=tk.EW, row=act_row, column=self.max_columnspan - 1, padx=self.xd, pady=self.yd)
        act_row += 1

        # RUN ROW
        self.b_run = tk.Button(top, bg="white", text="3) Run: Make cover HSI rasters",
                               anchor='w', command=lambda: self.run_raster_calc())
        self.b_run.grid(sticky=tk.EW, row=act_row, column=0, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)
        act_row += 1

        # ROW LAST
        self.l_run_info = tk.Label(top, text="")
        self.l_run_info.grid(sticky=tk.W, row=act_row, column=0, columnspan=self.max_columnspan - 1, padx=self.xd,
                             pady=self.yd)
        self.b_return = tk.Button(top, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW", command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=act_row, column=1, columnspan=self.max_columnspan, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        self.top.destroy()

    def open_files(self, f_list):
        for _f in f_list:
            print(str(_f))
            self.user_message("Do not forget to save files after editing ...")
            fG.open_file(_f)

    def print_msg(self, msg):
        print(str(msg))

    def run_raster_calc(self):
        relevant_types = []
        for rt in self.hsi_types.keys():
            if self.hsi_types[rt].get():
                relevant_types.append(rt)

        msg0 = "Analysis takes a while. \nPython windows seem unresponsive in the meanwhile. \nCheck console messages."
        msg1 = "\n\nThe following HSI types will be created:\n - "
        showinfo("INFORMATION ", msg0 + msg1 + "\n - ".join(relevant_types))
        error_occurred = False
        dir_out = ""
        for cov in relevant_types:
            cov_hsi = chsi.CovHSI(self.dir_input_ras, self.condition, cov, self.unit)
            cov_hsi.make_covhsi(self.fish_applied, self.h_ras_path)
            if cov_hsi.error:
                error_occurred = True
            else:
                dir_out = cov_hsi.path_hsi
            del cov_hsi
            try:
                fG.clean_dir(os.path.dirname(os.path.realpath(__file__)) + "\\.cache\\")
            except:
                print("WARNING: Could not clean up cache.")
        self.top.bell()
        try:
            if not error_occurred:
                fG.open_folder(dir_out)
                self.l_run_info.config(fg="forest green", text="HSI RASTERS SUCCESSFULLY CREATED")
                self.b_run.config(width=30, bg="pale green", text="RE-run (generate habitat condition)",
                                  command=lambda: self.run_raster_calc())
            else:
                self.l_run_info.config(fg="red", text="HSI RASTERS COMPILED WITH ERRORS")
                self.b_run.config(bg="salmon", text="RE-run (generate habitat condition)",
                                  command=lambda: self.run_raster_calc())
        except:
            pass

        showinfo("COMPUTATION FINISHED", "Check logfile (logfile.log).")

    def select_condition(self):
        items = self.lb_condition.curselection()
        self.condition = [self.condition_list[int(item)] for item in items][0]
        self.dir_input_ras = self.path_lvl_up + "\\01_Conditions\\" + self.condition + "\\"

        if os.path.exists(self.dir_input_ras):
            self.l_inpath_curr.config(fg="forest green", text="Selected: " + str(self.dir_input_ras))
            self.update_flows()
        else:
            self.l_inpath_curr.config(fg="red", text="SELECTION ERROR                                 ")

    def select_flow(self):
        items = self.lb_flow.curselection()
        __ras_name__ = [self.h_list[int(item)] for item in items][0]
        if not (__ras_name__ == "all terrain"):
            self.h_ras_path = self.path_lvl_up + "\\01_Conditions\\" + self.condition + "\\" + __ras_name__
            if os.path.exists(self.dir_input_ras):
                self.l_inflow_curr.config(fg="forest green", text="Current: " + str(self.h_ras_path))
            else:
                self.l_inflow_curr.config(fg="red", text="SELECTION ERROR                                 ")
        else:
            self.l_inflow_curr.config(fg="forest green", text="Current: All terrain")
            self.h_ras_path = ""

    def update_flows(self):
        try:
            self.lb_flow.delete(0, tk.END)  # try to empty listbox if currently filled
        except:
            pass

        # update depth raster file list from condition folder contents (raster has .aux.xml?)
        self.h_list = ["all terrain"]
        folder_names = fG.get_subdir_names(self.dir_input_ras)
        if folder_names.__len__() < 1:
            folder_names = [i for i in os.listdir(self.dir_input_ras) if i.endswith('.tif')]
        for fn in folder_names:
            if fn[0] == "h":
                if os.path.isdir(self.dir_input_ras + fn) or os.path.isfile(self.dir_input_ras + fn):
                    self.h_list.append(fn)

        for e in self.h_list:
            self.lb_flow.insert(tk.END, e)
        self.sb_flow.config(command=self.lb_flow.yview)

    def user_message(self, msg):
        showinfo("INFO", msg)

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

