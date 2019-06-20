try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    # load routines from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cInputOutput as cIO
    import fGlobal as fG
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class SubFrame(tk.Frame):
    def __init__(self, master=None, title=str(), max_columns=3, **options):
        Frame.__init__(self, master, **options)

        self.config(width=200, height=400)
        self.grid_propagate(False)
        self.rb_inp_file = config.dir2mt + "Input.txt"
        self.px = 5
        self.py = 5
        b_width = 45

        self.l_title = tk.Label(self, fg="dark slate gray", text=title.upper())
        self.l_title.grid(sticky=tk.EW, row=0, column=0, columnspan=max_columns, padx=self.px, pady=self.py)

        self.b_1 = tk.Button(self, bg="white", width=b_width, text="Create RB Input.txt File")
        self.b_1.grid(sticky=tk.EW, row=1, column=0, columnspan=max_columns, padx=self.px, pady=self.py)

        self.l_inp_rb = tk.Label(self, text="Selected Input.txt file:\n%s" % "None")
        self.l_inp_rb.grid(sticky=tk.W, row=3, rowspan=2, column=0, columnspan=max_columns, padx=self.px, pady=self.py)

        self.set_widget_state("disabled")

    def set_widget_state(self, state):
        # mode = STR (either "normal" or "disabled")
        for wid in self.winfo_children():
            wid["state"] = state


class GraphicFrame(tk.Frame):
    def __init__(self, master=None, graph_dir=str(), **options):
        Frame.__init__(self, master, **options)

        self.config(width=200, height=400)
        graphic = tk.PhotoImage(file=graph_dir)
        graphic = graphic.subsample(6, 6)
        self.l_img = tk.Label(self, image=graphic)
        self.l_img.image = graphic
        self.l_img.pack()#grid(sticky=tk.E, row=3, column=2, rowspan=7, columnspan=2, padx=5, pady=5)


class CreateInput(object):
    def __init__(self, master):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.top.iconbitmap(config.code_icon)



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


    def remake_buttons(self):
        pass


    def user_message(self, msg):
        showinfo("INFO", msg)

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

