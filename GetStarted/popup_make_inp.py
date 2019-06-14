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


class InpFrame(object):
    def __init__(self, master):
        self.dir2ra = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\"
        top = self.top = tk.Toplevel(master)
        self.condition_list = fGl.get_subdir_names(self.dir2ra + "01_Conditions\\")
        self.dir2condition = '.'
        self.dir2dem = ''
        self.dir2h = ''
        self.dir2u = ''
        self.flows_xlsx = ''

        # define analysis type identifiers (default = False)
        self.bool_var = tk.BooleanVar()
        self.top.iconbitmap(self.dir2ra + ".site_packages\\templates\\code_icon.ico")

        # ARRANGE GEOMETRY
        # width and height of the window.
        ww = 400
        wh = 200
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Make Input File")  # window title

        self.col_0_width = 25

        # Set Condition
        self.l_info = tk.Label(top, text="Make sure to Analyze Flows before creating an input_definitions.inp file.")
        self.l_info.grid(sticky=tk.W, row=0, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        self.l_name = tk.Label(top, text="Select condition: ")
        self.l_name.grid(sticky=tk.W, row=1, rowspan=3, column=0, padx=self.xd, pady=self.yd)
        self.sb_condition = tk.Scrollbar(top, orient=tk.VERTICAL)
        self.sb_condition.grid(sticky=tk.W, row=1, column=2, padx=0, pady=self.yd)
        self.lb_condition = tk.Listbox(top, height=3, width=15, yscrollcommand=self.sb_condition.set)
        for ce in self.condition_list:
            self.lb_condition.insert(tk.END, ce)
        self.lb_condition.grid(sticky=tk.EW, row=1, column=1, padx=0, pady=self.yd)
        self.sb_condition.config(command=self.lb_condition.yview)
        self.b_sc = tk.Button(top, width=self.col_0_width-5, fg="firebrick3", bg="white", text="Generate file",
                              command=lambda: self.make_input_file())
        self.b_sc.grid(sticky=tk.E, row=1, rowspan=3, column=2, padx=self.xd, pady=self.yd)
        self.l_c_dir = tk.Label(top, fg="firebrick3", text="Make input definition (.inp) file.")
        self.l_c_dir.grid(sticky=tk.W, row=4, column=0, columnspan=4, padx=self.xd, pady=self.yd)
        tk.Label(top, text="").grid(sticky=tk.W, row=5, column=0)  # dummy

        self.b_return = tk.Button(top, width=self.col_0_width, fg="RoyalBlue3", bg="white", 
                                  text="RETURN to MAIN WINDOW", command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=6, column=2, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        self.top.destroy()

    def make_input_file(self):
        items = self.lb_condition.curselection()
        # INFO: dir2condition may not end with "\\"!
        condition = str([self.condition_list[int(item)] for item in items][0])
        condition4input = cCC.ConditionCreator(self.dir2ra + "01_Conditions\\" + condition)
        condition4input.generate_input_file(self.dir2ra + "01_Conditions\\" + condition + "\\flow_definitions.xlsx")
        try:
            if not condition4input.error:
                fGl.open_file(self.dir2condition + "\\input_definition.inp")
                self.b_sc.config(fg="forest green")
                self.l_c_dir.config(fg="forest green", text=self.dir2condition + "\\input_definition.inp")
            else:
                showinfo("INFO", "Make sure that the flow return periods are defined.")
                self.b_sc.config(fg="red", text="failed - try again")
        except:
            pass

    def __call__(self, *args, **kwargs):
        self.top.mainloop()
