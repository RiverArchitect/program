try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    import cConditionCreator as cCC
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py).")


class CreateSubCondition(object):
    def __init__(self, master):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.condition_list = fGl.get_subdir_names(self.dir2ra + "01_Conditions\\")
        self.dir2src_condition = '.'
        self.dir2sub_condition = '.'
        self.dir2bound = '.'

        self.sub_condition_name = tk.StringVar()
        self.top.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 455
        wh = 370
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Create Sub Condition")  # window title

        self.col_0_width = 25

        # 01 Select source Condition
        self.l_name = tk.Label(top, text="Select source condition: ")
        self.l_name.grid(sticky=tk.W, row=0, rowspan=3, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=0, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_condition.set)
        for ce in self.condition_list:
            self.lb_condition.insert(tk.END, ce)
        self.lb_condition.grid(sticky=tk.EW, row=0, column=1, padx=0, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)
        self.b_sc = tk.Button(top, width=self.col_0_width-5, fg="firebrick3", bg="white", text="Validate",
                              command=lambda: self.select_src_condition())
        self.b_sc.grid(sticky=tk.E, row=0, rowspan=3, column=2, padx=self.xd, pady=self.yd)
        self.l_c_dir = tk.Label(top, fg="firebrick3", text="Select a condition.")
        self.l_c_dir.grid(sticky=tk.W, row=3, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=4, column=0)  # dummy

        # 02 Define sub condition name
        self.l_name = tk.Label(top, text="Sub-Condition name: ")
        self.l_name.grid(sticky=tk.W, row=5, column=0, padx=self.xd, pady=self.yd)
        self.e_condition = tk.Entry(top, textvariable=self.sub_condition_name)
        self.e_condition.grid(sticky=tk.EW, row=5, column=1, columnspan=2, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=6, column=0)  # dummy

        # 03 Define spatial boundary raster
        self.b_bound = tk.Button(top, bg="white", text="Select spatial boundary Raster",
                                 command=lambda: self.select_boundary())
        self.b_bound.grid(sticky=tk.EW, row=7, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.l_bound = tk.Label(top, fg="red", text="No spatial boundary Raster defined.", width=self.col_0_width*2)
        self.l_bound.grid(sticky=tk.W, row=8, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=9, column=0)  # dummy

        # 04 CREATE SUB-CONDITION
        self.b_create_c = tk.Button(top, bg="white", text="CREATE SUB-CONDITION",
                                    command=lambda: self.run_sub_c())
        self.b_create_c.grid(sticky=tk.EW, row=10, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.l_run_info = tk.Label(top, fg="forest green", text="")
        self.l_run_info.grid(sticky=tk.W, row=11, column=0, columnspan=3, padx=self.xd, pady=self.yd)

        self.b_return = tk.Button(top, width=self.col_0_width, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW",
                                  command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=12, column=2, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        self.top.destroy()

    def run_sub_c(self):
        self.dir2sub_condition = self.dir2ra + "01_Conditions\\" + str(self.sub_condition_name.get()) + "\\"
        if not os.path.exists(self.dir2sub_condition):
            os.makedirs(self.dir2sub_condition)
        else:
            showinfo("WARNING",
                     "The defined condition already exists and files may be overwritten. Make sure to SAVE IMPORTANT FILE from the existing condition BEFORE CLICKING OK.")
        condition = cCC.ConditionCreator(self.dir2sub_condition)
        condition.create_sub_condition(self.dir2src_condition, self.dir2bound)
        self.top.bell()
        try:
            if not condition.error:
                fGl.open_folder(self.dir2sub_condition)
                self.b_create_c.config(fg="forest green", text="Sub-Condition created.")
                self.l_run_info.config(text="New condition: %s" % self.dir2sub_condition)
            else:
                self.b_create_c.config(fg="red", text="Sub-Condition creation failed.")
        except:
            pass

    def select_boundary(self):
        msg0 = "Select a Boundary Raster file (if this is a GRID Raster, select the corresponding .aux.xml file)."
        msg1 = "Ensure that the boundary Raster only contains On-Off Integers, where 0=Outside and 1=Inside boundary."
        showinfo("INFO", msg0 + msg1)
        self.dir2bound = askopenfilename(initialdir=self.dir2src_condition, title="Select Boundary raster")
        self.l_bound.config(fg="forest green", text=self.dir2bound)

    def select_src_condition(self):
        items = self.lb_condition.curselection()
        self.dir2src_condition = self.dir2ra + "01_Conditions\\" + str([self.condition_list[int(item)] for item in items][0]) + "\\"
        self.l_c_dir.config(fg="forest green", text="Selected: " + self.dir2src_condition)
        self.b_sc.config(fg="forest green")

    def __call__(self, *args, **kwargs):
        self.top.mainloop()
