try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, showinfo
    from tkinter.filedialog import *
    import webbrowser
    import logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging tkinter, webbrowser).")

try:
    # import own routines
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # load routines from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fG
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py).")


class MainGui(tk.Frame):
    def __init__(self, master=None):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        tk.Frame.__init__(self, master)
        # if imported from master GUI, redefine master as highest level (ttk.Notebook tab container)
        if __name__ != '__main__':
            self.master = self.winfo_toplevel()
        self.set_geometry()
        try:
            import rasterio
            import gdal

            self.bound_shp = ""  # full path of a boundary shapefile
            self.a_method = "use_me"
            self.criterion = False
            self.dir = os.path.dirname(os.path.abspath(__file__))
            self.dir_conditions = self.dir
            self.max_columnspan = 4
            self.condition_list = fG.get_subdir_names(self.dir_conditions)
            self.unit = "us"

            msg0 = "UNDER CONSTRUCTION\n\n"

            # LABELS
            self.l_1 = tk.Label(self, fg="snow4", text=msg0 + msg1)
            self.l_1.grid(sticky=tk.EW, row=2, rowspan=1, column=1, columnspan=4, padx=self.xd, pady=self.yd)
            self.l_2 = tk.Label(self, fg="blue", text=msg2, cursor="hand2")
            self.l_2.grid(sticky=tk.EW, row=4, rowspan=1, column=1, columnspan=4, padx=self.xd, pady=self.yd)
            self.l_2.bind("<Button-1>", self.callback)


            # # DROP DOWN ENTRIES (SCROLL BARS)
            # self.sb_condition = tk.Scrollbar(self, orient=tk.VERTICAL)
            # self.sb_condition.grid(sticky=tk.W, row=3, column=3, padx=0, pady=self.yd)
            #
            #
            # # CHECK BUTTONS -- determine if geometric mean or product is used
            # self.cb_1 = tk.Checkbutton(self, text="Check", variable=self.a_method, onvalue="use_me", offvalue="use_other")
            # self.cb_1.grid(sticky=tk.W, row=2, column=2, padx=self.xd, pady=self.yd)
            # self.cb_1.select()
            #
            #
            # # BUTTONS
            # self.b_1 = tk.Button(self, width=15, fG="RoyalBlue3", bg="white", text="Click", command=lambda: print("button works"))
            # self.b_1.grid(sticky=tk.W, row=0, rowspan=2, column=self.max_columnspan, padx=self.xd, pady=self.yd)

        except:
            msg0 = "Cannot import GDAL and/or RASTERIO. Check requirements.\n\n"
            msg1 = "The Eco-Morphology module uses leogoesger\'s FFF connectors.\n"
            msg2 = "Find out more: https://github.com/leogoesger/FFF-connectors"

            # LABELS
            self.l_1 = tk.Label(self, fg="snow4", text=msg0 + msg1)
            self.l_1.grid(sticky=tk.EW, row=2, rowspan=1, column=1, columnspan=4, padx=self.xd, pady=self.yd)
            self.l_2 = tk.Label(self, fg="blue", text=msg2, cursor="hand2")
            self.l_2.grid(sticky=tk.EW, row=4, rowspan=1, column=1, columnspan=4, padx=self.xd, pady=self.yd)
            self.l_2.bind("<Button-1>", self.callback)

        self.make_menu()

    def callback(self, event):
        webbrowser.open_new(r"https://github.com/leogoesger/FFF-connectors")

    def set_geometry(self):
        # ARRANGE GEOMETRY
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # width and height of the window
        self.ww = 550
        self.wh = 495
        self.wx = (self.master.winfo_screenwidth() - self.ww) / 2
        self.wy = (self.master.winfo_screenheight() - self.wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (self.ww, self.wh, self.wx, self.wy))  # set height and location
        if __name__ == '__main__':
            self.master.title("Connectivity Assessment")  # window title
            self.master.iconbitmap(os.path.dirname(os.path.abspath(__file__)) + "\\.templates\\code_icon.ico")

    def make_menu(self):
        # DROP DOWN MENU
        self.mbar = tk.Menu(self)  # create new menubar
        self.master.config(menu=self.mbar)  # attach it to the root window

        # UNIT SYSTEM DROP DOWN
        self.unitmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Units", menu=self.unitmenu)  # attach it to the menubar
        self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
        self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())

        # CLOSE DROP DOWN
        self.closemenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Close", menu=self.closemenu)  # attach it to the menubar
        self.closemenu.add_command(label="Credits", command=lambda: self.show_credits())
        self.closemenu.add_command(label="Quit programm", command=lambda: self.myquit())

    def activate_button(self, button):
        button["state"] = "normal"
        if self.criterion:
            self.b_1.config(fg="red")

    def myquit(self):
        self.open_log_file()
        tk.Frame.quit(self)

    def open_log_file(self):
        logfilenames = ["error.log", "ecomy.log", "logfile.log", "map_logfile.log", "mxd_logfile.log"]
        for filename in logfilenames:
            _f = r'' + os.path.dirname(os.path.abspath(__file__)) + "\\" + filename
            if os.path.isfile(_f):
                try:
                    webbrowser.open(_f)
                except:
                    pass

    def select_boundary_shp(self):
        self.bound_shp = askopenfilename(initialdir=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\",
                                         title="Select boundary shapefile containing a rectangular polygon",
                                         filetypes=[("Shapefiles", "*.shp")])

    def shout_dict(self, the_dict):
        msg = "Selected:"
        for k in the_dict.keys():
            msg = msg + "\n\n > " + str(k) + " entries:\n   -- " + "\n   -- ".join(the_dict[k])
        showinfo("INFO", msg)



    def show_credits(self):
        showinfo("Credits", fG.get_credits())


    def unit_change(self):
        if self.unit == "si":
            new_unit = "us"
            self.unitmenu.delete(0, 1)
            self.unitmenu.add_command(label="[current]  U.S. customary", background="pale green")
            self.unitmenu.add_command(label="[             ]  SI (metric)", command=lambda: self.unit_change())
            self.master.bell()
            showinfo("UNIT CHANGE", "Unit system changed to U.S. customary.")
        else:
            new_unit = "si"
            self.unitmenu.delete(0, 1)
            self.unitmenu.add_command(label="[             ]  U.S. customary", command=lambda: self.unit_change())
            self.unitmenu.add_command(label="[current]  SI (metric)", background="pale green")
            self.master.bell()
            showinfo("UNIT CHANGE", "Unit system changed to SI (metric).")
        self.unit = new_unit

    def __call__(self):
        self.mainloop()


# enable script to run stand-alone
if __name__ == "__main__":
    MainGui().mainloop()
