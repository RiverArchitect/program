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
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg
    # load routines from LifespanDesign
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find riverpy.")


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 580  # window width
        self.wh = 650  # window height
        self.title = "Connectivity"
        self.set_geometry(self.ww, self.wh, self.title)
        try:
            import rasterio
            import gdal

            self.bound_shp = ""  # full path of a boundary shapefile
            self.a_method = "use_me"
            self.criterion = False
            self.dir2co = os.path.dirname(os.path.abspath(__file__))
            self.dir_conditions = self.dir2co + "01_Conditions\\"
            self.max_columnspan = 4
            self.condition_list = fGl.get_subdir_names(self.dir_conditions)

            msg0 = "UNDER CONSTRUCTION\n\n"

            # LABELS
            self.l_1 = tk.Label(self, fg="snow4", text=msg0)
            self.l_1.grid(sticky=tk.EW, row=2, rowspan=1, column=1, columnspan=4, padx=self.xd, pady=self.yd)
            self.l_2 = tk.Label(self, fg="blue", text=msg0, cursor="hand2")
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
            # self.b_1 = tk.Button(self, width=15, fGl="RoyalBlue3", bg="white", text="Click", command=lambda: print("button works"))
            # self.b_1.grid(sticky=tk.W, row=0, rowspan=2, column=self.max_columnspan, padx=self.xd, pady=self.yd)

        except:
            msg0 = "Under construction."
            # LABELS
            self.l_1 = tk.Label(self, fg="snow4", text=msg0)
            self.l_1.grid(sticky=tk.EW, row=2, rowspan=1, column=1, columnspan=4, padx=self.xd, pady=self.yd)
            self.l_2 = tk.Label(self, fg="blue", text="Wiki pages", cursor="hand2")
            self.l_2.grid(sticky=tk.EW, row=4, rowspan=1, column=1, columnspan=4, padx=self.xd, pady=self.yd)
            self.l_2.bind("<Button-1>", self.callback)

        self.complete_menus()

    def callback(self, event):
        webbrowser.open_new(r"https://github.com/sschwindt/RiverArchitect/wiki/Connectivity")

    def complete_menus(self):
        # DROP DOWN MENU
        # UNIT SYSTEM DROP DOWN
        self.cxmenu = tk.Menu(self.mbar, tearoff=0)  # create new menu
        self.mbar.add_cascade(label="Connect", menu=self.cxmenu)  # attach it to the menubar
        self.cxmenu.add_command(label="Option 1", command=lambda: showinfo("Hi", "Connective greetings."))
        self.cxmenu.add_command(label="Option 2", command=lambda: showinfo("Hi", "Connective greetings."))

    def activate_button(self, button):
        button["state"] = "normal"
        if self.criterion:
            self.b_1.config(fg="red")

    def select_boundary_shp(self):
        self.bound_shp = askopenfilename(initialdir=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\01_Conditions\\",
                                         title="Select boundary shapefile containing a rectangular polygon",
                                         filetypes=[("Shapefiles", "*.shp")])

    def shout_dict(self, the_dict):
        msg = "Selected:"
        for k in the_dict.keys():
            msg = msg + "\n\n > " + str(k) + " entries:\n   -- " + "\n   -- ".join(the_dict[k])
        showinfo("INFO", msg)

    def __call__(self):
        self.mainloop()
