try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    import cConditionCreator as ccc
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fg
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py).")


class CreateCondition(object):
    def __init__(self, master):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path_lvl_up = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.dir2condition = '.'
        self.dir2dem = '.'
        self.dir2back = '.'
        self.dir2fill = '.'
        self.dir2grains = '.'
        self.dir2h = '.'
        self.dir2scour = '.'
        self.dir2u = '.'

        self.new_condition_name = tk.StringVar()
        self.str_h = tk.StringVar()
        self.str_u = tk.StringVar()
        self.top.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 400
        wh = 790
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Create New Condition (from scratch)")  # window title

        self.col_0_width = 25

        # Set New Condition
        self.l_name = tk.Label(top, text="Condition name: ")
        self.l_name.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.e_condition = tk.Entry(top, textvariable=self.new_condition_name)
        self.e_condition.grid(sticky=tk.EW, row=0, column=1, columnspan=2, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=1, column=0)  # dummy

        # 02 Velocity raster folder
        self.b_su = tk.Button(top, width=self.col_0_width, bg="white", text="Select velocity (u) folder",
                              command=lambda: self.select_u())
        self.b_su.grid(sticky=tk.EW, row=2, column=0, padx=self.xd, pady=self.yd)
        self.l_u_str = tk.Label(top,text="Raster string: ")
        self.l_u_str.grid(sticky=tk.W, row=2, column=1, padx=self.xd, pady=self.yd)
        self.e_u = tk.Entry(top, width=6, textvariable=self.str_u)
        self.e_u.grid(sticky=tk.EW, row=2, column=2, padx=self.xd, pady=self.yd)
        self.b_u_info = tk.Button(top, width=5, bg="white", text="Help", command=lambda: self.user_info('u'))
        self.b_u_info.grid(sticky=tk.EW, row=2, column=3, padx=self.xd, pady=self.yd)
        self.l_u_folder = tk.Label(top, fg="red", text="No u-folder defined.")
        self.l_u_folder.grid(sticky=tk.W, row=3, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=4, column=0)  # dummy

        # 03 Depth raster folder
        self.b_sh = tk.Button(top, width=self.col_0_width, bg="white", text="Select depth (h) folder",
                              command=lambda: self.select_h())
        self.b_sh.grid(sticky=tk.EW, row=5, column=0, padx=self.xd, pady=self.yd)
        self.l_h_str = tk.Label(top, text="Raster string: ")
        self.l_h_str.grid(sticky=tk.W, row=5, column=1, padx=self.xd, pady=self.yd)
        self.e_h = tk.Entry(top, width=6, textvariable=self.str_h)
        self.e_h.grid(sticky=tk.EW, row=5, column=2, padx=self.xd, pady=self.yd)
        self.b_h_info = tk.Button(top, width=5, bg="white", text="Help", command=lambda: self.user_info('h'))
        self.b_h_info.grid(sticky=tk.EW, row=5, column=3, padx=self.xd, pady=self.yd)
        self.l_h_folder = tk.Label(top, fg="red", text="No h-folder defined.")
        self.l_h_folder.grid(sticky=tk.W, row=6, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=7, column=0)  # dummy

        # 04 DEM raster
        self.b_sdem = tk.Button(top, width=self.col_0_width, bg="white", text="Select DEM Raster",
                                command=lambda: self.select_dem())
        self.b_sdem.grid(sticky=tk.EW, row=8, column=0, padx=self.xd, pady=self.yd)
        self.l_dem = tk.Label(top, fg="red", text="No DEM Raster defined.")
        self.l_dem.grid(sticky=tk.W, row=9, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=10, column=0)  # dummy

        # 05 Grain size raster
        self.b_sgrain = tk.Button(top, width=self.col_0_width, bg="white", text="Select Grain size Raster",
                                  command=lambda: self.select_grains())
        self.b_sgrain.grid(sticky=tk.EW, row=11, column=0, padx=self.xd, pady=self.yd)
        self.l_grain = tk.Label(top, fg="red", text="No Grain size Raster defined.")
        self.l_grain.grid(sticky=tk.W, row=12, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=13, column=0)  # dummy

        # 06 Scour raster
        self.b_sscour = tk.Button(top, width=self.col_0_width, bg="white", text="Select Scour Raster",
                                  command=lambda: self.select_scour())
        self.b_sscour.grid(sticky=tk.EW, row=14, column=0, padx=self.xd, pady=self.yd)
        self.l_scour_info = tk.Label(top, fg="gray35", text="(optional)")
        self.l_scour_info.grid(sticky=tk.W, row=14, column=1, padx=self.xd, pady=self.yd)
        self.l_scour = tk.Label(top, fg="red", text="No Scour Raster defined.")
        self.l_scour.grid(sticky=tk.W, row=15, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=16, column=0)  # dummy

        # 07 Fill raster
        self.b_sfill = tk.Button(top, width=self.col_0_width, bg="white", text="Select Fill Raster",
                                 command=lambda: self.select_fill())
        self.b_sfill.grid(sticky=tk.EW, row=17, column=0, padx=self.xd, pady=self.yd)
        self.l_fill_info = tk.Label(top, fg="gray35", text="(optional)")
        self.l_fill_info.grid(sticky=tk.W, row=17, column=1, padx=self.xd, pady=self.yd)
        self.l_fill = tk.Label(top, fg="red", text="No Fill Raster defined.")
        self.l_fill.grid(sticky=tk.W, row=18, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=19, column=0)  # dummy

        # 08 Background raster
        self.b_sback = tk.Button(top, width=self.col_0_width, bg="white", text="Select Background Raster",
                                 command=lambda: self.select_back())
        self.b_sback.grid(sticky=tk.EW, row=20, column=0, padx=self.xd, pady=self.yd)
        self.l_back_info = tk.Label(top, fg="gray35", text="(optional)")
        self.l_back_info.grid(sticky=tk.W, row=20, column=1, padx=self.xd, pady=self.yd)
        self.l_back = tk.Label(top, fg="red", text="No Background Raster defined.")
        self.l_back.grid(sticky=tk.W, row=21, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=22, column=0)  # dummy

        # 09 CREATE CONDITION
        self.b_create_c = tk.Button(top, width=self.col_0_width, bg="white", text="CREATE CONDITION",
                                    command=lambda: self.run_creation())
        self.b_create_c.grid(sticky=tk.EW, row=23, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.l_run_info = tk.Label(top, fg="forest green", text="")
        self.l_run_info.grid(sticky=tk.W, row=24, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        self.b_return = tk.Button(top, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW",
                                  command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=25, column=0, columnspan=5, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        self.top.destroy()

    def run_creation(self):
        self.dir2condition = self.dir2ra + "01_Conditions\\" + str(self.new_condition_name.get()) + "\\"
        if not os.path.exists(self.dir2condition):
            os.makedirs(self.dir2condition)
        else:
            showinfo("WARNING", "The defined condition already exists and files may be overwritten. Make sure to SAVE IMPORTANT FILE from the existing condition BEFORE CLICKING OK.")
        new_condition = ccc.ConditionCreator(self.dir2condition)
        new_condition.transfer_rasters_from_folder(self.dir2h, "h", str(self.str_h.get()))
        new_condition.transfer_rasters_from_folder(self.dir2u, "u", str(self.str_u.get()))
        new_condition.save_tif(self.dir2dem, "dem")
        new_condition.save_tif(self.dir2grains, "dmean")
        new_condition.save_tif(self.dir2back, "scour")
        new_condition.save_tif(self.dir2back, "fill")
        new_condition.save_tif(self.dir2back, "back")
        self.top.bell()
        try:
            if not new_condition.error:
                fg.open_folder(self.dir2condition)
                self.l_run_info.config(fg="forest green", text="Condition successfully created.")
            else:
                self.l_run_info.config(fg="red", text="Condition creation failed.")
        except:
            pass
        msg0 = "Condition created. Next:\n (1) Return to the Main Window and\n (2) Use \'Populate Condition\' to create geomorphic unit, depth to groundwater and detrended DEM rasters."
        msg1 = "\n\nEnsure that the Rasters are correctly defined in LifespanDesign/.templates/input_definitions.inp."
        showinfo("INFO", msg0 + msg1)

    def select_back(self):
        showinfo("INFO", "Select a Background Raster file (if this is a GRID Raster, select the corresponding .aux.xml file).")
        self.dir2back = askopenfilename(initialdir=self.dir2grains, title="Select Background raster")
        self.l_back.config(fg="forest green", text=self.dir2back)

    def select_dem(self):
        showinfo("INFO", "Select a DEM Raster file (if this is a GRID Raster, select the corresponding .aux.xml file).")
        self.dir2dem = askopenfilename(initialdir=self.dir2u, title="Select DEM raster")
        self.l_dem.config(fg="forest green", text=self.dir2dem)

    def select_fill(self):
        msg0 = "Select a FILL Raster file (if this is a GRID Raster, select the corresponding .aux.xml file)."
        msg1 = "\n\nU.S. costomary: in FEET.\n S.I. metric: METERS."
        showinfo("INFO", msg0 + msg1)
        self.dir2fill = askopenfilename(initialdir=self.dir2scour, title="Select FILL raster")
        self.l_fill.config(fg="forest green", text=self.dir2fill)

    def select_grains(self):
        msg0 = "Select a Grain size Raster file (if this is a GRID Raster, select the corresponding .aux.xml file)."
        msg1 = "\n\nS.I. (metric): Grain sizes must be in METERS."
        msg2 = "\n\nU.S. customary units: Grain sizes must be in FEET (US)."
        showinfo("INFO", msg0 + msg1 + msg2)
        self.dir2grains = askopenfilename(initialdir=self.dir2dem, title="Select Grain size raster")
        self.l_grain.config(fg="forest green", text=self.dir2grains)

    def select_h(self):
        msg = self.user_raster_info()
        showinfo("INFO", msg)
        self.dir2h = askdirectory(initialdir=self.dir2u) + "/"
        self.l_h_folder.config(fg="forest green", text=str(self.dir2h))

    def select_scour(self):
        msg0 = "Select a SCOUR Raster file (if this is a GRID Raster, select the corresponding .aux.xml file)."
        msg1 = "\n\nU.S. costomary: in FEET.\n S.I. metric: METERS."
        showinfo("INFO", msg0 + msg1)
        self.dir2scour = askopenfilename(initialdir=self.dir2grains, title="Select SCOUR raster")
        self.l_scour.config(fg="forest green", text=self.dir2scour)

    def select_u(self):
        msg = self.user_raster_info()
        showinfo("INFO", msg)
        self.dir2u = askdirectory(initialdir=self.dir2h) + "/"
        self.l_u_folder.config(fg="forest green", text=str(self.dir2u))

    def user_info(self, variable_name):
        msg = ''
        if (variable_name == 'h') or (variable_name == 'u'):
            msg0 = "Only Rasters containing the entered string will be copied to the new condition folder."
            msg1 = "\n\n" + self.user_raster_info()
            msg = msg0 + msg1
        showinfo("INFO", msg)

    def user_raster_info(self):
        msg0 = "Select folder with hydrodynamic (depth/velocity) Rasters containing a defined string.\n"
        msg1 = "Make sure to adapt the Raster names according to the RA name-convention (this code cannot do this job automatically).\n"
        msg2 = "Read more about name conventions: https://github.com/sschwindt/RiverArchitect/wiki/Signposts#terms"
        return msg0 + msg1 + msg2

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

