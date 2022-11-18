try:
    import os, sys
    import tkinter as tk
    from tkinter.messagebox import askokcancel, askyesno, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import child_gui as sg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import fGlobal as fGl
    import cConditionCreator as cCC
    import config
except:
    print("ExceptionERROR: Cannot find package files (RP/fGlobal.py).")


class MainGui(sg.RaModuleGui):
    def __init__(self, from_master):
        sg.RaModuleGui.__init__(self, from_master)
        self.ww = 700
        self.wh = 490
        self.title = "Get Started"
        self.set_geometry(self.ww, self.wh, self.title)

        # GUI OBJECT VARIABLES
        self.gui_condition = tk.StringVar()
        self.gui_interpreter = tk.StringVar()
        self.extent_type = tk.StringVar()

        # BUTTONS
        self.b_create_c = tk.Button(self, width=30, bg="white", text="Create New Condition", command=lambda: self.create_c())
        self.b_create_c.grid(sticky=tk.EW, row=0, column=0, columnspan=2, padx=self.xd, pady=self.yd*2)

        self.b_populate_c = tk.Button(self, width=30, bg="white", text="Populate Condition",
                                      command=lambda: self.populate_c())
        self.b_populate_c.grid(sticky=tk.EW, row=1, column=0, columnspan=2, padx=self.xd, pady=self.yd * 2)

        self.b_create_sub_c = tk.Button(self, width=30, bg="white", text="Create a spatial subset of a Condition",
                                        command=lambda: self.create_c_sub())
        self.b_create_sub_c.grid(sticky=tk.EW, row=2, column=0, columnspan=2, padx=self.xd, pady=self.yd*2)

        self.b_analyze_Q = tk.Button(self, width=30, bg="white", text="Analyze Flows", command=lambda: self.analyze_Q())
        self.b_analyze_Q.grid(sticky=tk.EW, row=3, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_make_inp = tk.Button(self, width=30, bg="white", text="Make Input File", command=lambda: self.make_inp())
        self.b_make_inp.grid(sticky=tk.EW, row=4, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        self.b_align = tk.Button(self, width=30, bg="white", text="Align Input Rasters", command=lambda: self.align_inp())
        self.b_align.grid(sticky=tk.EW, row=5, column=0, columnspan=2, padx=self.xd, pady=self.yd)

        # MAKE PLACEHOLDER FILL
        logo = tk.PhotoImage(file=os.path.dirname(os.path.abspath(__file__))+"\\.templates\\welcome.gif")
        logo = logo.subsample(6, 6)
        self.l_img = tk.Label(self, image=logo)
        self.l_img.image = logo
        self.l_img.grid(sticky=tk.E, row=3, column=2, rowspan=7, columnspan=2, padx=self.xd*10, pady=self.yd)

        # Add credits
        self.l_credits = tk.Label(self, fg="gray50", text=fGl.get_credits(), justify=tk.LEFT)
        self.l_credits.grid(sticky=tk.E, row=8, column=0, rowspan=3, columnspan=2, padx=self.xd, pady=self.yd)

    def analyze_Q(self):
        try:
            import popup_analyze_q as pcq
        except:
            showinfo("Oups ...", "Cannot find discharge analysis routines -  check RA installation.", parent=self)
            return -1
        new_window = pcq.FlowAnalysis(self.master)
        self.b_analyze_Q["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_analyze_Q["state"] = "normal"

    def create_c(self):
        try:
            import popup_create_c as pcc
        except:
            showinfo("Oups ...", "Cannot find condition creation routines -  check RA installation.", parent=self)
            return -1
        new_window = pcc.CreateCondition(self.master)
        self.b_create_c["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_create_c["state"] = "normal"
        self.gui_quit()

    def create_c_sub(self):
        try:
            import popup_create_c_sub as pccs
        except:
            showinfo("Oups ...", "Cannot find sub-condition creation routines -  check RA installation.", parent=self)
            return -1
        new_window = pccs.CreateSubCondition(self.master)
        self.b_create_sub_c["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_create_sub_c["state"] = "normal"
        self.gui_quit()

    def make_inp(self):
        try:
            import popup_make_inp as pmi
        except:
            showinfo("Oups ...", "Cannot find discharge analysis routines -  check RA installation.")
            return -1
        new_window = pmi.InpFrame(self.master)
        self.b_make_inp["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_make_inp["state"] = "normal"
        del new_window

    def align_inp(self):
        try:
            import popup_align_rasters as par
        except:
            showinfo("Oups ...", "Cannot find discharge analysis routines -  check RA installation.")
            return -1
        new_window = par.AlignRasters(self.master)
        self.b_align["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_align["state"] = "normal"

    def gui_quit(self):
        answer = askyesno("Info", "River Architect must be restarted in order to finalize register dataset.\nPlease confirm closing River Architect?")
        if answer:
            self.master.destroy()

    def populate_c(self):
        try:
            import popup_populate_c as ppc
        except:
            showinfo("Oups ...", "Cannot find condition population routines -  check RA installation.", parent=self)
            return -1
        new_window = ppc.PopulateCondition(self.master)
        self.b_populate_c["state"] = "disabled"
        self.master.wait_window(new_window.top)
        self.b_populate_c["state"] = "normal"

    def __call__(self):
        self.mainloop()
