try:
    import os, sys
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    import cConditionCreator as cCC
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find riverpy.")


class PopulateCondition(object):
    def __init__(self, master):
        top = self.top = tk.Toplevel(master)
        self.condition_list = fGl.get_subdir_names(config.dir2conditions)
        self.dir2condition_act = '.'
        self.dir2dem = ''
        self.dir2h = ''
        self.dir2u = ''
        self.unit = "us"
        self.unit_dict = {"us": "U.S. customary", "si": "SI (metric)"}

        # define analysis type identifiers (default = False)
        self.bool_var = tk.BooleanVar()
        self.top.iconbitmap(config.code_icon)

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 650
        wh = 570
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Populate Condition")  # window title

        self.col_0_width = 25

        # Set Condition
        self.l_name = tk.Label(top, text="Select condition: ")
        self.l_name.grid(sticky=tk.W, row=0, rowspan=3, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=0, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_condition.set)
        for ce in self.condition_list:
            self.lb_condition.insert(tk.END, ce)
        self.lb_condition.grid(sticky=tk.EW, row=0, column=1, padx=0, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)
        self.b_sc = tk.Button(top, width=self.col_0_width-5, fg="firebrick3", bg="white", text="Validate",
                              command=lambda: self.set_condition())
        self.b_sc.grid(sticky=tk.E, row=0, rowspan=3, column=2, padx=self.xd, pady=self.yd)
        self.l_c_dir = tk.Label(top, fg="firebrick3", text="Select a condition.")
        self.l_c_dir.grid(sticky=tk.W, row=3, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=4, column=0)  # dummy

        # 02 Make d2w
        self.l_d2w = tk.Label(top, text="Create Depth to Groundwater Raster (d2w.tif)")
        self.l_d2w.grid(sticky=tk.W, row=5, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.b_sd2w = tk.Button(top, width=self.col_0_width*2, bg="white", text="Select minimum flow depth raster",
                                command=lambda: self.select_h())        
        self.b_sd2w.grid(sticky=tk.EW, row=6, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_d2w = tk.Button(top, width=self.col_0_width, bg="white", text="Run d2w creation",
                               command=lambda: self.run_d2w())
        self.b_d2w.grid(sticky=tk.EW, row=6, column=2, padx=self.xd, pady=self.yd)
        self.l_interp = tk.Label(top, text="Interpolation method:")
        self.l_interp.grid(sticky=tk.W, row=7, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.c_interp = ttk.Combobox(top, state='readonly')
        self.c_interp.grid(sticky=tk.W, row=7, column=1, padx=self.xd, pady=self.yd)
        self.c_interp["values"] = ("IDW", "Kriging", "Nearest Neighbor")
        self.c_interp.current(0)
        self.l_d2w_dem = tk.Label(top, text="")
        self.l_d2w_dem.grid(sticky=tk.W, row=8, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=9, column=0)  # dummy

        # 03 Make detDEM
        self.l_det = tk.Label(top, text="Create detrended DEM Raster (dem_detrend.tif)")
        self.l_det.grid(sticky=tk.W, row=9, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.b_sdet = tk.Button(top, width=self.col_0_width*2, bg="white", text="Select minimum flow depth raster",
                                command=lambda: self.select_h())
        self.b_sdet.grid(sticky=tk.EW, row=10, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_det = tk.Button(top, width=self.col_0_width, bg="white", text="Run detrended DEM creation",
                               command=lambda: self.run_det())
        self.b_det.grid(sticky=tk.EW, row=10, column=2, padx=self.xd, pady=self.yd)
        self.l_det_dem = tk.Label(top, text="")
        self.l_det_dem.grid(sticky=tk.W, row=11, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=12, column=0)  # dummy

        # 04 Make MU
        self.l_mu = tk.Label(top, text="Create Morphological Unit Raster (mu.tif)")
        self.l_mu.grid(sticky=tk.W, row=13, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        self.b_smuh = tk.Button(top, width=self.col_0_width, bg="white",
                                text="Select depth raster",
                                command=lambda: self.select_h())
        self.b_smuh.grid(sticky=tk.EW, row=14, column=0, padx=self.xd, pady=self.yd)
        self.b_smuu = tk.Button(top, width=self.col_0_width, bg="white",
                                text="Select velocity raster",
                                command=lambda: self.select_u())
        self.b_smuu.grid(sticky=tk.EW, row=14, column=1, padx=self.xd, pady=self.yd)
        self.b_chg_mu = tk.Button(top, width=self.col_0_width * 2 + self.xd * 2, bg="white",
                                  text="View / change MU definitions",
                                  command=lambda: self.open_mu_xlsx())
        self.b_chg_mu.grid(sticky=tk.EW, row=15, column=0, columnspan=2, padx=self.xd, pady=self.yd)
        self.b_mu = tk.Button(top, width=self.col_0_width, bg="white", text="Run MU\ncreation",
                              command=lambda: self.run_mu())
        self.b_mu.grid(sticky=tk.EW, row=14, rowspan=2, column=2, padx=self.xd, pady=self.yd)
        self.l_mu_unit = tk.Label(top, fg="dodger blue",
                                  text="Currently selected Raster unit system: % s" % self.unit_dict[self.unit])
        self.l_mu_unit.grid(sticky=tk.W, row=16, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        # tk.Label(top, text="").grid(sticky=tk.W, row=15, column=0)  # dummy

        self.b_return = tk.Button(top, width=self.col_0_width, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW",
                                  command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=17, column=2, padx=self.xd, pady=self.yd)

        # add units-menu
        self.mbar = tk.Menu(self.top, foreground="dodger blue")  # create new menubar
        self.top.config(menu=self.mbar)  # attach it to the root window
        self.unitmenu = tk.Menu(self.mbar, tearoff=0, foreground="dodger blue")  # create new menu
        self.mbar.add_cascade(label="Units", menu=self.unitmenu, foreground="dodger blue")  # attach it to the menubar
        self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
        self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())

        self.b_d2w["state"] = "disabled"
        self.b_det["state"] = "disabled"
        self.b_mu["state"] = "disabled"
        self.b_sd2w["state"] = "disabled"
        self.c_interp["state"] = "disabled"
        self.b_sdet["state"] = "disabled"
        self.b_smuh["state"] = "disabled"
        self.b_smuu["state"] = "disabled"
        try:
            fGl.clean_dir(config.dir2gs + ".cache\\")
            fGl.rm_dir(config.dir2gs + ".cache\\")
        except:
            pass

    def gui_quit(self):
        self.top.destroy()

    def open_mu_xlsx(self):
        showinfo("INFO", "Do not forget to save changes ...")
        try:
            webbrowser.open(config.xlsx_mu)
        except:
            showinfo("ERROR", "Could not find %s." % config.xlsx_mu)

    def run_d2w(self):
        condition = cCC.ConditionCreator(self.dir2condition_act)
        condition.make_d2w(self.dir2h, self.dir2dem, method=self.c_interp.get())
        self.top.bell()
        try:
            if not condition.error:
                fGl.open_folder(self.dir2condition_act)
                self.b_d2w.config(fg="forest green", text="d2w.tif created.")
            else:
                self.b_d2w.config(fg="red", text="d2w.tif creation failed.")
        except:
            pass

    def run_det(self):
        condition = cCC.ConditionCreator(self.dir2condition_act)
        condition.make_det(self.dir2h, self.dir2dem)
        self.top.bell()
        try:
            if not condition.error:
                fGl.open_folder(self.dir2condition_act)
                self.b_det.config(fg="forest green", text="dem_detrend.tif created.")
            else:
                self.b_det.config(fg="red", text="dem_detrend.tif creation failed.")
        except:
            pass

    def run_mu(self):
        condition = cCC.ConditionCreator(self.dir2condition_act)
        condition.make_mu(self.unit, self.dir2h, self.dir2u)
        self.top.bell()
        try:
            if not condition.error:
                fGl.open_folder(self.dir2condition_act)
                self.b_mu.config(fg="forest green", text="mu.tif created.")
            else:
                self.b_mu.config(fg="red", text="mu.tif creation failed.")
        except:
            pass

    def select_dem(self):
        showinfo("INFO", "Select a DEM Raster file (if this is a GRID Raster, select the corresponding .aux.xml file).")
        self.dir2dem = askopenfilename(initialdir=".", title="Select DEM raster")

    def select_h(self):
        msg = "Select the flow depth raster corresponding to the required discharge / baseflow (?)."
        showinfo("INFO", msg)
        self.dir2h = askopenfilename(initialdir=self.dir2condition_act, title="Select baseflow depth raster",
                                     filetypes=[('GeoTIFF', '*.tif;*.tiff')])
        self.b_d2w["state"] = "normal"
        self.c_interp["state"] = "readonly"
        self.b_det["state"] = "normal"
        if self.dir2u.__len__() > 0:
            self.b_mu["state"] = "normal"

    def select_u(self):
        msg = "Select the flow velocity raster corresponding to baseflow."
        showinfo("INFO", msg)
        self.dir2u = askopenfilename(initialdir=self.dir2condition_act, title="Select baseflow velocity raster",
                                     filetypes=[('GeoTIFF', '*.tif;*.tiff')])
        if self.dir2h.__len__() > 0:
            self.b_mu["state"] = "normal"

    def set_condition(self):
        items = self.lb_condition.curselection()
        self.dir2condition_act = config.dir2conditions + str([self.condition_list[int(item)] for item in items][0])
        self.l_c_dir.config(fg="forest green", text="Selected: " + self.dir2condition_act)
        self.b_sc.config(fg="forest green")
        self.dir2dem = self.dir2condition_act + "\\dem.tif"
        if not os.path.isfile(self.dir2dem):
            showinfo("WARNING", self.dir2dem + " does not exist.")
            self.l_d2w_dem.config(fg="firebrick3", text=self.dir2dem + " does not exist.")
            self.l_det_dem.config(fg="firebrick3", text=self.dir2dem + " does not exist.")
        else:
            self.l_d2w_dem.config(fg="forest green", text="Using DEM: %s" % self.dir2dem)
            self.l_det_dem.config(fg="forest green", text="Using DEM: %s" % self.dir2dem)
            self.b_sd2w["state"] = "normal"
            self.b_sdet["state"] = "normal"
            self.b_smuh["state"] = "normal"
            self.b_smuu["state"] = "normal"

    def unit_change(self):
        self.unitmenu.delete(0, 1)
        if self.unit == "si":
            new_unit = "us"
            self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
            self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())
        else:
            new_unit = "si"
            self.unitmenu.add_command(label="[             ]  U.S. customary", command=lambda: self.unit_change())
            self.unitmenu.add_command(label="[current]  SI (metric)", background="pale green")
        self.top.bell()
        self.unit = new_unit
        self.l_mu_unit.config(text="Currently selected Raster unit system: % s" % self.unit_dict[self.unit])

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

