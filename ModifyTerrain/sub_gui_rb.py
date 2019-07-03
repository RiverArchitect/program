try:
    import os, sys
    from functools import partial
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import askokcancel, askyesno, showinfo
    from tkinter.filedialog import *
    import webbrowser
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, tkinter, webbrowser).")

try:
    import cRiverBuilderConstruct as cRBC
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cInputOutput as cIO
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class PopUpUserFunction(object):
    def __init__(self, master, user_function_count_dict):
        # defined_user_functions = TUPLE
        # top =
        self.top = tk.Toplevel(master)
        self.defined_user_functions = ()
        self.input_file = cRBC.InputFile()
        self.user_function_count_dict = user_function_count_dict
        self.widget_dict = {}
        self.top.title = "Define User functions"
        self.top.iconbitmap(config.code_icon)

        row = 0
        for k in self.input_file.user_function_dict.keys():
            self.add_fun_interface(k, row)
            tk.Label(self.top, text="                         ").grid(row=row+2, column=0)  # dummy row separator
            row += 3

        self.b = tk.Button(self.top, text='FINISH (Return Input File Creator)', command=self.return2main)
        self.b.grid(sticky=tk.E, row=row, column=0, columnspan=4, padx=1, pady=5)

    def add_fun_interface(self, fun_name, row):
        tk.Label(self.top, text="Add %s function: " % fun_name).grid(sticky=tk.W, row=row, column=0,
                                                                     columnspan=4, padx=1, pady=5)
        self.widget_dict.update({fun_name: []})
        if ("sin" in fun_name.lower()) or ("cos" in fun_name.lower()):
            self.widget_dict[fun_name].append(tk.Label(self.top, text="     a ="))
            self.widget_dict[fun_name].append(tk.Entry(self.top, width=10))
            self.widget_dict[fun_name].append(tk.Label(self.top, text="     f ="))
            self.widget_dict[fun_name].append(tk.Entry(self.top, width=10))
            self.widget_dict[fun_name].append(tk.Label(self.top, text="     ps ="))
            self.widget_dict[fun_name].append(tk.Entry(self.top, width=10))
        if "line" in fun_name.lower():
            self.widget_dict[fun_name].append(tk.Label(self.top, text="     s ="))
            self.widget_dict[fun_name].append(tk.Entry(self.top, width=10))
            self.widget_dict[fun_name].append(tk.Label(self.top, text="     dy ="))
            self.widget_dict[fun_name].append(tk.Entry(self.top, width=10))
        if "perl" in fun_name.lower():
            self.widget_dict[fun_name].append(tk.Label(self.top, text="     a ="))
            self.widget_dict[fun_name].append(tk.Entry(self.top, width=10))
            self.widget_dict[fun_name].append(tk.Label(self.top, text="     lam ="))
            self.widget_dict[fun_name].append(tk.Entry(self.top, width=10))
        col = 0
        row += 1
        for wid in self.widget_dict[fun_name]:
            wid.grid(sticky=tk.W, row=row, column=col, padx=2, pady=5)
            col += 1
            
        tk.Button(self.top, text="ADD", command=partial(self.add_user_function, fun_name)).grid(sticky=tk.W, row=row,
                                                                                                column=col, padx=1, pady=5)

    def add_user_function(self, fun_name):
        self.user_function_count_dict[fun_name] += 1  # set function counter
        par_list = []  # dummy required for line functions
        for wid in self.widget_dict[fun_name]:
            if type(wid) == tk.Entry:
                try:
                    par_list.append(float(wid.get()))
                except:
                    showinfo("ERROR", "Values must be FLOAT types (numeric).")
        try:
            self.input_file.user_function_dict[fun_name](self.user_function_count_dict[fun_name], par_list)
            showinfo("INFO", "Added new function:\n %s" % self.input_file.user_functions[-1])
        except:
            showinfo("CONTRIBUTOR WARNING", "The selected user function is not implemented.")

    def return2main(self):
        self.defined_user_functions = tuple(self.input_file.user_functions)
        self.top.destroy()


class SubFrame(tk.Frame):
    def __init__(self, master=None, **options):
        Frame.__init__(self, master, **options)
        tk.Label(self, text="       ").grid(row=0, column=3)  # column separator dummy
        self.config(width=880, height=500)
        self.input_file = cRBC.InputFile()
        self.grid_propagate(False)
        self.add_variability_fun_dict = {}
        self.tko_dict = {}
        self.tko_spec_dict = {}
        self.par_tko_dict = {}
        self.label_dict = {}
        self.msg_b_dict = {}
        self.occupied_rows = []
        self.px = 5
        self.py = 5
        self.sub_fun_dict = {}
        self.user_functions_applied = ()
        self.user_function_count_dict = {}
        [self.user_function_count_dict.update({k: 0}) for k in self.input_file.user_function_dict.keys()]

        self.make_widgets()

    def add_sub_function(self, par=str()):
        # par = STR of sub-reach type (e.g., sub_curvature)
        # fun_str = STR of user function
        fun_str = str(self.tko_dict[par].get()).split("=")[0]
        success = False
        try:
            self.sub_fun_dict[par].append(fun_str)
            success = True
        except:
            self.sub_fun_dict.update({par: [fun_str]})
            success = True
        if success:
            self.add_variability_fun_dict[par].config(fg="forest green")
            showinfo("INFO", "Added {0} as {1}".format(fun_str, self.input_file.par_name_dict[par].split("*")[0]))
        else:
            showinfo("ERROR", "Could not append function.")

    def make_user_functions(self):
        sub_frame = PopUpUserFunction(self, self.user_function_count_dict)
        self.master.wait_window(sub_frame.top)
        self.user_functions_applied += sub_frame.defined_user_functions
        self.user_function_count_dict = sub_frame.user_function_count_dict
        self.update_subreach_opts()

    def make_widgets(self):
        row = 0
        col0 = 0
        for par_class, par_list in self.input_file.par_dict.items():
            self.label_dict.update({par_class: tk.Label(self, text=par_class)})
            self.label_dict[par_class].grid(sticky=tk.W, row=row, column=col0, columnspan=3)
            row += 1
            for par in par_list:
                if not (row in self.occupied_rows) or (col0 == 4):
                    self.label_dict.update({par: tk.Label(self, text=self.input_file.par_name_dict[par])})
                    self.label_dict[par].grid(sticky=tk.W, row=row, column=col0)
                    self.tko_dict.update({par: self.input_file.par_tk_dict[par](self, 20, self.user_functions_applied, row, col0+1)})
                    self.tko_dict[par].grid(sticky=tk.EW, row=row, column=col0+1)
                    # self.par_tko_dict.update({par: [row, col0+1]})
                    self.msg_b_dict.update({par: tk.Button(self, text="Info", width=5,
                                                           command=partial(self.show_msg, par))})
                    self.msg_b_dict[par].grid(sticky=tk.EW, row=row, column=col0+2)
                    if ("xs_shape" in par) or ("user_functions" in par) or ("sub_" in par):
                        self.make_widget_specifier(row=row, col=col0+3, par=par)
                    self.occupied_rows.append(row)
                row += 1
            if row > 18:
                # make second column if too many entries
                row = 1
                col0 = 4
        msg0 = "\n** Optional variables\n"
        msg1 = "*** Required if Cross-Sectional Shape = AU\n"
        msg2 = "**** Set all values to zero to deactivate floodplain"
        tk.Label(self, text=msg0+msg1+msg2).grid(sticky=tk.W, row=row, rowspan=4, column=col0, columnspan=4)

        sg.RaModuleGui.set_bg_color(self, "white")

    def make_widget_specifier(self, row=int(), col=int(), par=str()):
        # row, col = INT of first spec entry position
        # par = STR
        if "xs_shape" in par:
            self.tko_spec_dict.update({par: [tk.Label(self, text="If TZ: n = ")]})
            self.tko_spec_dict[par].append(ttk.Combobox(self, values=tuple(range(0, 31)), width=5))
            self.tko_spec_dict[par][0].grid(sticky=tk.W, row=row, column=col)
            self.tko_spec_dict[par][1].grid(sticky=tk.W, row=row, column=col+1)
        if "user_functions" in par:
            self.tko_dict.update({par: tk.Button(self, width=20, text="Create",
                                                 command=lambda: self.make_user_functions()).grid(sticky=tk.EW, row=row, column=col-2)})
            self.tko_spec_dict.update({par: [tk.Button(self, text="Reset", command=lambda: self.reset_user_functions())]})
            self.tko_spec_dict[par][0].grid(sticky=tk.W, row=row, column=col)
        if "sub_" in par:
            self.add_variability_fun_dict.update({par: tk.Button(self, text="ADD", fg="orchid4",
                                                                 command=partial(self.add_sub_function, par))})
            self.add_variability_fun_dict[par].grid(sticky=tk.W, row=row, column=col)
            tk.Button(self, text="Show/Clear",  command=partial(self.show_clear_sub, par)).grid(sticky=tk.W, row=row, column=col+1)

    def reset_user_functions(self):
        answer = askyesno("Reset defined functions", "This will delete all defined user functions. Are you sure?")
        if answer:
            self.user_functions_applied = ()

    def show_clear_sub(self, par):
        msg0 = "The currently applied sub-reach variability functions for %s are:\n - " % self.input_file.par_name_dict[par].split("*")[0]
        try:
            msg1 = "\n - ".join(self.sub_fun_dict[par])
        except:
            msg1 = "\nNONE"
        qes = "\n\nDo you want to clear all user-function definitions for %s?" % self.input_file.par_name_dict[par].split("*")[0]
        answer = askyesno("Sub-Reach Function", msg0 + msg1 + qes)
        if answer:
            del self.sub_fun_dict[par]
            self.add_variability_fun_dict[par].config(fg="orchid4")

    def show_msg(self, par):
        _f = open(config.dir2rb + "messages\\" + par + ".txt", "r")
        msg = str(_f.read().splitlines()[0])
        _f.close()
        showinfo(self.input_file.par_name_dict[par], msg)

    def update_subreach_opts(self):
        self.make_widgets()


class GraphicFrame(tk.Frame):
    def __init__(self, master=None, graph_dir=str(), **options):
        Frame.__init__(self, master, **options)

        self.config(width=600, height=261)  # orig: w = 1800, h = 784
        self.grid_propagate(False)
        graphic = tk.PhotoImage(file=graph_dir)
        graphic = graphic.subsample(3, 3)
        self.l_img = tk.Label(self, image=graphic)
        self.l_img.image = graphic
        self.l_img.pack()


class CreateInput(object):
    def __init__(self, master):
        top = self.top = tk.Toplevel(master)
        self.top.iconbitmap(config.code_icon)
        ww = 900
        wh = 1000
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Create a River Builder Input File")  # window title
        self.user_input = {}

        self.max_columns = 2

        self.l_fn = tk.Label(top, text="New file name: ".upper())
        self.l_fn.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.e_fn = tk.Entry(top, width=35)
        self.e_fn.grid(sticky=tk.E, row=0, column=1, padx=self.xd, pady=self.yd)
        self.l_fn_ext = tk.Label(top, text=".txt")
        self.l_fn_ext.grid(sticky=tk.W, row=0, column=2, padx=self.xd, pady=self.yd)

        self.f_req = SubFrame(top)
        self.f_req.grid(sticky=tk.EW, row=1, column=0, columnspan=4, padx=self.xd, pady=self.yd)

        self.illu = GraphicFrame(top, graph_dir=config.dir2mt+".templates\\chnl_xs_parameters.gif")
        self.illu.grid(sticky=tk.EW, row=2, column=0, columnspan=4, padx=self.xd, pady=self.yd)

        self.b_run = tk.Button(top, bg="lemon chiffon", text="CREATE INPUT FILE", command=lambda: self.run_file_maker())
        self.b_run.grid(sticky=tk.EW, row=8, column=0, columnspan=4, padx=self.xd, pady=self.yd)

        self.b_return = tk.Button(top, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW",
                                  command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=9, column=3, padx=self.xd, pady=self.yd)

    def gui_quit(self):
        answer = askyesno("Cancel ?", "This will quit the Input File Creator. Are you sure?")
        if answer:
            self.top.destroy()

    def get_user_input(self):
        for par, tko in self.f_req.tko_dict.items():
            try:
                if not ("sub_" in par):
                    self.user_input.update({par: str(tko.get())})
                else:
                    try:
                        self.user_input.update({par: str("\n%s=" % self.f_req.input_file.par_name_dict[par].split("*")[0]).join(self.f_req.sub_fun_dict[par])})
                    except:
                        pass
                if "TZ" in str(tko.get()):
                    try:
                        self.user_input[par] = "TZ(%s)" % str(self.f_req.tko_spec_dict[par][1].get())
                    except:
                        showinfo("WARNING", "Cross-sectional shape = TZ but no n value is selected.")
            except:
                if "user_functions" in par:
                    self.user_input.update({par: "\n".join([str(s) for s in list(self.f_req.user_functions_applied)])})
                else:
                    showinfo("WARNING", "Could not read input for %s." % str(self.f_req.input_file.par_name_dict[par]))

    def run_file_maker(self):
        file_name = self.e_fn.get()
        if file_name.__len__() < 1:
            showinfo("INFO", "Enter NEW FILE NAME.")
            return -1
        if file_name + ".txt" in fGl.file_names_in_dir(config.dir2rb):
            showinfo("INFO", "File already exists. Choose different name or delete existing file from %s." % config.dir2rb)
            return -1
        self.get_user_input()
        self.f_req.input_file.make_file(file_name, self.user_input)
        self.user_input = {}
        self.b_run.config(text="CREATE ANOTHER INPUT FILE")
        showinfo("Finished", "Created %s." % str(config.dir2rb + file_name + ".txt"))
        webbrowser.open(config.dir2rb + file_name + ".txt")

    def __call__(self, *args, **kwargs):
        self.top.mainloop()
