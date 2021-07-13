try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo, showwarning
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
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py).")


class MandatoryFrame(tk.Frame):
    def __init__(self, master=None, **options):
        Frame.__init__(self, master, **options)
        self.config(width=350, height=400)

        self.xd = 5
        self.yd = 5
        self.col_0_width = 30

        # 02 Velocity raster folder
        self.b_su = tk.Button(self, width=self.col_0_width, bg="white", text="Select velocity (u) folder")
        self.b_su.grid(sticky=tk.EW, row=2, column=0, padx=self.xd, pady=self.yd)
        self.l_u_str = tk.Label(self, text="Raster string: ")
        self.l_u_str.grid(sticky=tk.W, row=2, column=1, padx=self.xd, pady=self.yd)
        self.e_u = tk.Entry(self, width=6)
        self.e_u.grid(sticky=tk.EW, row=2, column=2, padx=self.xd, pady=self.yd)
        self.b_u_info = tk.Button(self, width=5, bg="white", text="Help")
        self.b_u_info.grid(sticky=tk.EW, row=2, column=3, padx=self.xd, pady=self.yd)
        self.l_u_folder = tk.Label(self, fg="red", text="No u-folder defined.")
        self.l_u_folder.grid(sticky=tk.W, row=3, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="").grid(sticky=tk.W, row=4, column=0)  # dummy

        # 03 Depth raster folder
        self.b_sh = tk.Button(self, width=self.col_0_width, bg="white", text="Select depth (h) folder")
        self.b_sh.grid(sticky=tk.EW, row=5, column=0, padx=self.xd, pady=self.yd)
        self.l_h_str = tk.Label(self, text="Raster string: ")
        self.l_h_str.grid(sticky=tk.W, row=5, column=1, padx=self.xd, pady=self.yd)
        self.e_h = tk.Entry(self, width=6)
        self.e_h.grid(sticky=tk.EW, row=5, column=2, padx=self.xd, pady=self.yd)
        self.b_h_info = tk.Button(self, width=5, bg="white", text="Help")
        self.b_h_info.grid(sticky=tk.EW, row=5, column=3, padx=self.xd, pady=self.yd)
        self.l_h_folder = tk.Label(self, fg="red", text="No h-folder defined.")
        self.l_h_folder.grid(sticky=tk.W, row=6, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="").grid(sticky=tk.W, row=7, column=0)  # dummy

        # 04 DEM raster
        self.b_sdem = tk.Button(self, width=self.col_0_width, bg="white", text="Select DEM Raster")
        self.b_sdem.grid(sticky=tk.EW, row=8, column=0, padx=self.xd, pady=self.yd)
        self.l_dem = tk.Label(self, fg="red", text="No DEM Raster defined.")
        self.l_dem.grid(sticky=tk.W, row=9, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="").grid(sticky=tk.W, row=10, column=0)  # dummy

        # 05 Grain size raster
        self.b_sgrain = tk.Button(self, width=self.col_0_width, bg="white", text="Select Grain size Raster")
        self.b_sgrain.grid(sticky=tk.EW, row=11, column=0, padx=self.xd, pady=self.yd)
        self.l_grain = tk.Label(self, fg="red", text="No Grain size Raster defined.")
        self.l_grain.grid(sticky=tk.W, row=12, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="").grid(sticky=tk.W, row=13, column=0)  # dummy


class OptionalFrame(tk.Frame):
    def __init__(self, master=None, **options):
        Frame.__init__(self, master, **options)
        self.bg_color = "khaki"
        self.config(width=350, height=400, bg=self.bg_color)


        self.xd = 5
        self.yd = 5
        self.col_0_width = 30

        # Velocity Direction rasters
        self.b_sva = tk.Button(self, width=self.col_0_width, bg="white", text="Select velocity angle (va) folder")
        self.b_sva.grid(sticky=tk.EW, row=0, column=0, padx=self.xd, pady=self.yd)
        self.l_va_str = tk.Label(self, text="Raster string: ")
        self.l_va_str.grid(sticky=tk.W, row=0, column=1, padx=self.xd, pady=self.yd)
        self.e_va = tk.Entry(self, width=6)
        self.e_va.grid(sticky=tk.EW, row=0, column=2, padx=self.xd, pady=self.yd)
        self.b_va_info = tk.Button(self, width=5, bg="white", text="Help")
        self.b_va_info.grid(sticky=tk.EW, row=0, column=3, padx=self.xd, pady=self.yd)
        self.l_va_info = tk.Label(self, fg="gray35", text="(optional)")
        self.l_va_info.grid(sticky=tk.W, row=0, column=4, padx=self.xd, pady=self.yd)
        self.l_va_folder = tk.Label(self, fg="tan4", text="No va-folder defined.")

        self.l_va_folder.grid(sticky=tk.W, row=1, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="", bg="khaki").grid(sticky=tk.W, row=13, column=0)  # dummy

        # 06 Scour raster
        self.b_sscour = tk.Button(self, width=self.col_0_width, bg="white", text="Select Scour Raster")
        self.b_sscour.grid(sticky=tk.EW, row=14, column=0, padx=self.xd, pady=self.yd)
        self.l_scour_info = tk.Label(self, fg="gray35", text="(optional)")
        self.l_scour_info.grid(sticky=tk.W, row=14, column=1, padx=self.xd, pady=self.yd)
        self.l_scour = tk.Label(self, fg="tan4", text="No Scour Raster defined.")

        self.l_scour.grid(sticky=tk.W, row=15, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="", bg="khaki").grid(sticky=tk.W, row=16, column=0)  # dummy

        # 07 Fill raster
        self.b_sfill = tk.Button(self, width=self.col_0_width, bg="white", text="Select Fill Raster")
        self.b_sfill.grid(sticky=tk.EW, row=17, column=0, padx=self.xd, pady=self.yd)
        self.l_fill_info = tk.Label(self, fg="gray35", text="(optional)")
        self.l_fill_info.grid(sticky=tk.W, row=17, column=1, padx=self.xd, pady=self.yd)
        self.l_fill = tk.Label(self, fg="tan4", text="No Fill Raster defined.")

        self.l_fill.grid(sticky=tk.W, row=18, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="", bg="khaki").grid(sticky=tk.W, row=19, column=0)  # dummy

        # 08 Background raster
        self.b_sback = tk.Button(self, width=self.col_0_width, bg="white", text="Select Background Raster")
        self.b_sback.grid(sticky=tk.EW, row=20, column=0, padx=self.xd, pady=self.yd)
        self.l_back_info = tk.Label(self, fg="gray35", text="(optional)")
        self.l_back_info.grid(sticky=tk.W, row=20, column=1, padx=self.xd, pady=self.yd)
        self.c_back_align = tk.Checkbutton(self, text="Use to align input rasters")
        self.c_back_align.grid(sticky=tk.W, row=21, column=0, padx=self.xd, pady=self.yd)
        self.c_back_align["state"] = "disabled"
        self.l_back = tk.Label(self, fg="tan4", text="No Background Raster defined.")
        self.l_back.grid(sticky=tk.W, row=22, column=0, columnspan=5, padx=self.xd, pady=self.yd)
        tk.Label(self, text="", bg="khaki").grid(sticky=tk.W, row=23, column=0)  # dummy

        for wid in self.winfo_children():
            try:
                wid.configure(bg=self.bg_color)
            except:
                # some widget do not accept bg as kwarg
                pass


class CreateCondition(object):
    def __init__(self, master):
        config.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.dir2new_condition = '.'
        self.dir2dem = '.'
        self.dir2back = '.'
        self.dir2fill = '.'
        self.dir2grains = '.'
        self.dir2h = '.'
        self.dir2scour = '.'
        self.dir2u = '.'
        self.dir2va = '.'

        self.new_condition_name = tk.StringVar()
        self.str_h = tk.StringVar()
        self.str_u = tk.StringVar()
        self.str_va = tk.StringVar()
        self.align_rasters = tk.BooleanVar()
        self.top.iconbitmap(config.code_icon)

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 490
        wh = 890
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Create New Condition (from scratch)")  # window title

        self.col_0_width = 30

        # Set New Condition
        self.l_name = tk.Label(top, text="Condition name: ")
        self.l_name.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.e_condition = tk.Entry(top, textvariable=self.new_condition_name)
        self.e_condition.grid(sticky=tk.EW, row=0, column=1, columnspan=2, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=1, column=0)  # dummy

        # MANDATORY INPUTS FRAME
        self.mandatory = MandatoryFrame(self.top, relief=tk.RAISED)
        self.mandatory.grid(row=2, column=0, columnspan=3)
        self.mandatory.b_su.config(command=lambda: self.select_u())
        self.mandatory.e_u.config(textvariable=self.str_u)
        self.mandatory.b_u_info.config(command=lambda: self.user_info('u'))
        self.mandatory.b_sh.config(command=lambda: self.select_h())
        self.mandatory.e_h.config(textvariable=self.str_h)
        self.mandatory.b_h_info.config(command=lambda: self.user_info('h'))
        self.mandatory.b_sdem.config(command=lambda: self.select_dem())
        self.mandatory.b_sgrain.config(command=lambda: self.select_grains())

        # OPTIONAL INPUTS FRAME
        self.optional = OptionalFrame(self.top, relief=tk.RAISED)
        self.optional.config(bg="khaki")
        self.optional.grid(row=3, column=0, columnspan=3)
        self.optional.b_sva.config(command=lambda: self.select_va())
        self.optional.e_va.config(textvariable=self.str_va)
        self.optional.b_va_info.config(command=lambda: self.user_info('va'))
        self.optional.b_sscour.config(command=lambda: self.select_scour())
        self.optional.b_sfill.config(command=lambda: self.select_fill())
        self.optional.b_sback.config(command=lambda: self.select_back())
        self.optional.c_back_align.config(variable=self.align_rasters)

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
        self.dir2new_condition = config.dir2conditions + str(self.new_condition_name.get()) + "\\"
        if not os.path.exists(self.dir2new_condition):
            os.makedirs(self.dir2new_condition)
        else:
            showinfo("WARNING", "The defined condition already exists and files may be overwritten. Make sure to SAVE IMPORTANT FILES from the existing condition BEFORE CLICKING OK.")
        new_condition = cCC.ConditionCreator(self.dir2new_condition)
        new_condition.transfer_rasters_from_folder(self.dir2h, "h", str(self.str_h.get()))
        new_condition.transfer_rasters_from_folder(self.dir2u, "u", str(self.str_u.get()))
        new_condition.save_tif(self.dir2dem, "dem")
        new_condition.save_tif(self.dir2grains, "dmean")

        if str(self.dir2va).__len__() > 2:
            new_condition.transfer_rasters_from_folder(self.dir2va, "va", str(self.str_va.get()))
        if self.dir2scour.__len__() > 2:
            new_condition.save_tif(self.dir2scour, "scour")
        if self.dir2fill.__len__() > 2:
            new_condition.save_tif(self.dir2fill, "fill")
        if self.dir2back.__len__() > 2:
            new_condition.save_tif(self.dir2back, "back")

        if self.align_rasters.get():
            snap_ras = os.path.join(self.dir2new_condition, "back.tif")
            new_condition.fix_alignment(snap_ras)

        new_condition.check_alignment(self.dir2new_condition)

        self.top.bell()
        try:
            if new_condition.error:
                self.l_run_info.config(fg="red", text="Condition creation failed.")
            elif new_condition.warning:
                self.l_run_info.config(fg="gold4", text="Condition created with warnings (see logfile).")
                showwarning("WARNING", "Input rasters are not properly aligned (see logfile). Rasters can be aligned by inputting a background raster and selecting the checkbox \"Use to align input rasters\", or by using the \"Align Input Rasters\" tool from the GetStarted menu.")
            else:
                fGl.open_folder(self.dir2new_condition)
                self.l_run_info.config(fg="forest green", text="Condition successfully created.")

        except:
            pass
        msg0 = "Condition created. Next:\n (1) Return to the Main Window and\n (2) Use \'Populate Condition\' to create geomorphic unit, depth to water table and detrended DEM rasters."
        msg1 = "\n\nEnsure that the Rasters are correctly defined in LifespanDesign/.templates/input_definitions.inp."
        showinfo("INFO", msg0 + msg1, parent=self.top)

    def select_back(self):
        showinfo("INFO", "Select a Background Raster file (if this is a GRID Raster, select the corresponding .aux.xml file).", parent=self.top)
        self.dir2back = askopenfilename(initialdir=self.dir2grains, title="Select Background raster", parent=self.top)
        self.optional.l_back.config(fg="forest green", text=self.dir2back)
        if self.dir2back != '':
            self.optional.c_back_align["state"] = "normal"
        else:
            self.optional.c_back_align["state"] = "disabled"

    def select_dem(self):
        showinfo("INFO", "Select a DEM Raster file (if this is a GRID Raster, select the corresponding .aux.xml file).")
        self.dir2dem = askopenfilename(initialdir=self.dir2u, title="Select DEM raster", parent=self.top)
        self.mandatory.l_dem.config(fg="forest green", text=self.dir2dem)

    def select_fill(self):
        msg0 = "Select a FILL Raster file (if this is a GRID Raster, select the corresponding .aux.xml file)."
        msg1 = "\n\nU.S. costomary: in FEET.\n S.I. metric: METERS."
        showinfo("INFO", msg0 + msg1, parent=self.top)
        self.dir2fill = askopenfilename(initialdir=self.dir2scour, title="Select FILL raster", parent=self.top)
        self.optional.l_fill.config(fg="forest green", text=self.dir2fill)

    def select_grains(self):
        msg0 = "Select a Grain size Raster file (if this is a GRID Raster, select the corresponding .aux.xml file)."
        msg1 = "\n\nS.I. (metric): Grain sizes must be in METERS."
        msg2 = "\n\nU.S. customary units: Grain sizes must be in FEET (US)."
        showinfo("INFO", msg0 + msg1 + msg2, parent=self.top)
        self.dir2grains = askopenfilename(initialdir=self.dir2dem, title="Select Grain size raster", parent=self.top)
        self.mandatory.l_grain.config(fg="forest green", text=self.dir2grains)

    def select_h(self):
        msg = self.user_raster_info()
        showinfo("INFO", msg, parent=self.top)
        self.dir2h = askdirectory(initialdir=self.dir2u, parent=self.top) + "/"
        self.mandatory.l_h_folder.config(fg="forest green", text=str(self.dir2h))

    def select_scour(self):
        msg0 = "Select a SCOUR Raster file (if this is a GRID Raster, select the corresponding .aux.xml file)."
        msg1 = "\n\nU.S. customary: in FEET.\n S.I. metric: METERS."
        showinfo("INFO", msg0 + msg1, parent=self.top)
        self.dir2scour = askopenfilename(initialdir=self.dir2grains, title="Select SCOUR raster", parent=self.top)
        self.optional.l_scour.config(fg="forest green", text=self.dir2scour)

    def select_u(self):
        msg = self.user_raster_info()
        showinfo("INFO", msg, parent=self.top)
        self.dir2u = askdirectory(initialdir=self.dir2h, parent=self.top) + "/"
        self.mandatory.l_u_folder.config(fg="forest green", text=str(self.dir2u))

    def select_va(self):
        msg = self.user_raster_info()
        showinfo("INFO", msg, parent=self.top)
        self.dir2va = askdirectory(initialdir=self.dir2u, parent=self.top) + "/"
        self.optional.l_va_folder.config(fg="forest green", text=str(self.dir2va))

    def user_info(self, variable_name):
        msg = ''
        if (variable_name == 'h') or (variable_name == 'u') or (variable_name == 'va'):
            msg0 = "Only Rasters containing the entered string will be copied to the new condition folder."
            msg1 = "\n\n" + self.user_raster_info()
            msg = msg0 + msg1
        showinfo("INFO", msg, parent=self.top)

    def user_raster_info(self):
        msg0 = "Select folder with hydrodynamic (depth/velocity) Rasters containing a defined string.\n"
        msg1 = "Make sure to adapt the Raster names according to the RA name-convention (this code cannot do this job automatically).\n"
        msg2 = "Read more about name conventions: https://github.com/sschwindt/RiverArchitect/wiki/Signposts#terms"
        return msg0 + msg1 + msg2

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

