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


class AlignRasters(object):
    def __init__(self, master):
        top = self.top = tk.Toplevel(master)
        self.condition_list = fGl.get_subdir_names(config.dir2conditions)
        self.condition = ''
        self.dir2snap = ''

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 500
        wh = 200
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Align Input Rasters")  # window title
        self.top.iconbitmap(config.code_icon)

        row = 0

        # select condition
        self.l_condition = tk.Label(top, text="Select condition:")
        self.l_condition.grid(sticky=tk.W, row=row, column=0, padx=self.xd, pady=self.yd)
        self.combo_c = ttk.Combobox(top)
        self.combo_c.grid(sticky=tk.W, row=row, column=1)
        self.combo_c['values'] = tuple(fGl.get_subdir_names(config.dir2conditions))
        self.combo_c['state'] = 'readonly'
        self.b_s_condition = tk.Button(top, fg="red", text="Select",
                                       command=lambda: self.select_condition())
        self.b_s_condition.grid(sticky=tk.W, row=row, column=2, columnspan=2)
        row += 1

        self.l_inpath_curr = tk.Label(top, fg="gray60", text="Source: " + config.dir2conditions)
        self.l_inpath_curr.grid(sticky=tk.W, row=row, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        row += 1

        self.b_snap_ras = tk.Button(top, width=30, text="Select alignment raster", command=lambda: self.select_snap_ras())
        self.b_snap_ras.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1
        self.l_snap_ras = tk.Label(top, fg="red", text="No alignment raster selected.")
        self.l_snap_ras.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        row += 1
        self.b_align = tk.Button(top, width=30, text="Align Rasters", command=lambda: self.align_rasters())
        self.b_align.grid(sticky=tk.W, row=row, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.b_align["state"] = "disabled"

    def select_condition(self):
        try:
            self.condition = self.combo_c.get()
            input_dir = config.dir2conditions + str(self.condition)
            if os.path.exists(input_dir):
                self.b_s_condition.config(fg="forest green", text="Selected: " + self.condition)
                if self.dir2snap != '':
                    self.b_align["state"] = "normal"
                return ""
            else:
                self.b_align["state"] = "disabled"
                self.b_s_condition.config(fg="red", text="ERROR")
                return "Invalid file structure (non-existent directory /01_Conditions/CONDITION/)."
        except:
            self.b_align["state"] = "disabled"
            return "Invalid entry for \'Condition\'."

    def select_snap_ras(self):
        showinfo("INFO",
                 "Select an alignment raster for setting universal alignment, cell size, and coordinate system.",
                 parent=self.top)
        self.dir2snap = askopenfilename(initialdir=config.dir2conditions, title="Select alignment raster",
                                        parent=self.top)
        self.l_snap_ras.config(fg="forest green", text=self.dir2snap)
        if self.condition != '' and self.dir2snap != '':
            self.b_align["state"] = "normal"
        else:
            self.b_align["state"] = "disabled"

    def align_rasters(self):
        ccc = cCC.ConditionCreator(os.path.join(config.dir2conditions, self.condition))
        code = ccc.fix_alignment(self.dir2snap)
        if code == 0:
            showinfo("INFO",
                     "Rasters aligned successfully.",
                     parent=self.top)
        else:
            showinfo("ERROR",
                     "Errors occurred during raster alignment. See logfile for details.",
                     parent=self.top)

    def __call__(self, *args, **kwargs):
        self.top.mainloop()
