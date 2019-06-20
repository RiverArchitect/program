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
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\")
    import slave_gui as sg
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    import cInputOutput as cIO
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find package files (riverpy).")


class SubFrame(tk.Frame):
    def __init__(self, master=None, sub_title=str(), max_columns=3, **options):
        Frame.__init__(self, master, **options)

        self.config(width=150, height=400)
        self.grid_propagate(False)
        self.px = 5
        self.py = 5
        b_width = 45

        self.l_title = tk.Label(self, fg="dark slate gray", text=sub_title.upper())
        self.l_title.grid(sticky=tk.EW, row=0, column=0, columnspan=max_columns, padx=self.px, pady=self.py)

        self.b_1 = tk.Button(self, bg="white", width=b_width, text="Button1")
        self.b_1.grid(sticky=tk.EW, row=1, column=0, columnspan=max_columns, padx=self.px, pady=self.py)

        self.l_1 = tk.Label(self, text="Label 1%s" % "None")
        self.l_1.grid(sticky=tk.W, row=2, rowspan=2, column=0, columnspan=max_columns, padx=self.px, pady=self.py)

        self.set_widget_state("disabled")

    def set_widget_state(self, state):
        # mode = STR (either "normal" or "disabled")
        for wid in self.winfo_children():
            wid["state"] = state


class GraphicFrame(tk.Frame):
    def __init__(self, master=None, graph_dir=str(), **options):
        Frame.__init__(self, master, **options)

        self.config(width=900, height=392)
        self.grid_propagate(False)
        graphic = tk.PhotoImage(file=graph_dir)
        graphic = graphic.subsample(2, 2)
        self.l_img = tk.Label(self, image=graphic)
        self.l_img.image = graphic
        self.l_img.pack()#grid(sticky=tk.E, row=3, column=2, rowspan=7, columnspan=2, padx=5, pady=5)


class CreateInput(object):
    def __init__(self, master):
        top = self.top = tk.Toplevel(master)
        self.top.iconbitmap(config.code_icon)

        ww = 925
        wh = 900
        self.xd = 5  # distance holder in x-direction (pixel)
        self.yd = 5  # distance holder in y-direction (pixel)
        # height and location
        wx = (self.top.winfo_screenwidth() - ww) / 2
        wy = (self.top.winfo_screenheight() - wh) / 2
        self.top.geometry("%dx%d+%d+%d" % (ww, wh, wx, wy))
        self.top.title("Create a River Builder Input File")  # window title
        self.max_columns = 2

        self.l_fn = tk.Label(top, text="New file name: ")
        self.l_fn.grid(sticky=tk.W, row=0, column=0, padx=self.xd, pady=self.yd)
        self.e_fn = tk.Entry(top, width=35)
        self.e_fn.grid(sticky=tk.W, row=0, column=1, padx=self.xd, pady=self.yd)
        self.l_fn_ext = tk.Label(top, text=".txt")
        self.l_fn_ext.grid(sticky=tk.W, row=0, column=2, padx=self.xd, pady=self.yd)

        self.f_req = SubFrame(top, "REQUIRED PARAMETERS", relief=tk.RAISED)
        self.f_req.grid(sticky=tk.EW, row=1, column=0, columnspan=3, padx=self.xd, pady=self.yd)
        sg.RaModuleGui.set_bg_color(self.f_req, "white")

        self.f_opt = SubFrame(top, sub_title="OPTIONAL PARAMETERS")
        self.f_opt.grid(sticky=tk.EW, row=1, column=3, columnspan=2, padx=self.xd, pady=self.yd)
        sg.RaModuleGui.set_bg_color(self.f_opt, "LightBlue1")

        self.illu = GraphicFrame(top, graph_dir=config.dir2mt+".templates\\chnl_xs_parameters.gif")
        self.illu.grid(sticky=tk.EW, row=2, column=0, columnspan=5, padx=self.xd, pady=self.yd)

        self.l_run_info = tk.Label(top, text="")
        self.l_run_info.grid(sticky=tk.W, row=8, column=0, columnspan=self.max_columns, padx=self.xd, pady=self.yd)



        self.b_return = tk.Button(top, fg="RoyalBlue3", bg="white", text="RETURN to MAIN WINDOW",
                                  command=lambda: self.gui_quit())
        self.b_return.grid(sticky=tk.E, row=9, column=4, padx=self.xd, pady=self.yd)




    def gui_quit(self):
        self.top.destroy()

    def open_files(self, f_list):
        for _f in f_list:
            self.user_message("Do not forget to save files after editing ...")
            fGl.open_file(_f)


    def run_file_maker(self):
        file_name = self.e_fn.get()


    def user_message(self, msg):
        showinfo("INFO", msg)

    def __call__(self, *args, **kwargs):
        self.top.mainloop()

