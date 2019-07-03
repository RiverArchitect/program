try:
    import os, logging, sys, glob
    from functools import partial
    import tkinter as tk
    from tkinter import ttk
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, glob, logging.")
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
except:
    print("ExceptionERROR: Missing fundamental packages (required: riverpy).")


# recurring variables:
# _f = TXT FILE  - input file (opened)
# par_name = STR - RiverBuilder Parameter Name
# write_list = list of lines that will eventually be written
class InputFile:
    def __init__(self):
        # processing variables
        self.logger = logging.getLogger("logfile")

        # RiverBuilder variables
        self.chnl_xs_pts = 21
        self.d50 = 0.01
        self.datum = 1
        self.dx = 1.0  # FLOAT of x-intercept
        self.dy = 1.0  # FLOAT of y-intercept
        self.floodplain_outer_height = 0.0
        self.h_bf = 0.0
        self.length = 1.0
        self.s_valley = 0.0
        self.sub_curvature = []
        self.sub_floodplain_l = []
        self.sub_floodplain_r = []
        self.sub_meander = []
        self.sub_thalweg = []
        self.sub_w_bf = []
        self.taux = 0.0
        self.terrace_outer_height = 0.0
        self.user_functions = []  #
        self.user_function_dict = {"SIN": lambda fun_id, par_list: self.add_user_function(fun="SIN", fun_id=fun_id, a=par_list[0], f=par_list[1], ps=par_list[2]),
                                   "COS": lambda fun_id, par_list: self.add_user_function(fun="COS", fun_id=fun_id, a=par_list[0], f=par_list[1], ps=par_list[2]),
                                   "SIN_SQ": lambda fun_id, par_list: self.add_user_function(fun="SIN_SQ", fun_id=fun_id, a=par_list[0], f=par_list[1], ps=par_list[2]),
                                   "LINE": lambda fun_id, par_list, *arg: self.add_user_function(fun="LINE", fun_id=fun_id, s0=par_list[0], dy=par_list[1]),
                                   "PERL": lambda fun_id, par_list, *arg: self.add_user_function(fun="PERL", fun_id=fun_id, a=par_list[0], lam=par_list[1])}
        self.w_bf = 0.0
        self.w_bf_min = 0.0
        self.w_boundary = 0.0
        self.w_floodplain = 0.0
        self.w_terrace = 0.0
        self.x_res = 1
        self.xs_shape = "AU"

        # make contents
        self.var_dict = self.get_var_names()
        self.msg_dict = {}
        self.par_dict = self.get_parameters()
        self.par_name_dict = self.get_par_names()
        self.par_tk_dict = self.make_par_tk_characteristics()
        self.par_defaults = self.get_par_defaults()

    def add_user_function(self, fun=str(), fun_id=int(), a=float(), f=float(), ps=float, lam=float(), s0=float(), dy=float()):
        # fun = STR  of SIN#, COS#, SIN_SQ# (sin-square), LINE#, PERL# (Perlin)
        # a = FLOAT - amplitude
        # f = FLOAT - frequency
        # ps = FLOAT - phase shift (multiple or fraction of PI)
        # lam = FLOAT - wavelength (originally in RiverBuilder denoted as "w"
        if ("sin" in fun.lower()) or ("cos" in fun.lower()):
            self.user_functions.append(self.make_trigonometric_string(fun, fun_id, a, f, ps))
        if "line" in fun.lower():
            self.user_functions.append("{0}{1}={0}({2}, {3})".format(fun, str(fun_id), "%3.4f" % s0, "%3.4f" % dy))
        if "perl" in fun.lower():
            self.user_functions.append("{0}{1}={0}({2}, {3})".format(fun, str(fun_id), "%3.4f" % a, "%3.4f" % lam))

    @staticmethod
    def get_par_defaults():
        return {"datum": 1.0, "length": 100.0, "x_res": 1.0,
                "chnl_xs_pts": 23.0, "s_valley": 0.001,
                "taux": 0.047,
                "w_bf": 10.0, "w_bf_min": 5.0, "h_bf": 1.0,
                "d50": 0.01, "w_floodplain": 0.0,
                "floodplain_outer_height": 0.0, "w_terrace": 0.0,
                "terrace_outer_height": 0.0, "w_boundary": 0.0,
                "xs_shape": 0.0, "user_functions": "SIN1=SIN(0, 1, 0)",
                "sub_curvature": "SIN1", "sub_floodplain_l": "",
                "sub_floodplain_r": "", "sub_meander": "",
                "sub_thalweg": "", "sub_w_bf": ""
                }


    @staticmethod
    def get_par_names():
        return {"datum": "Datum", "length": "Length", "x_res": "X Resolution",
                "chnl_xs_pts": "Channel XS Points", "s_valley": "Valley Slope (Sv)", "taux": "Critical Shields Stress (t*50)**",
                "w_bf": "Bankfull Width (Wbf)", "w_bf_min": "Bankfull Width Minimum", "h_bf": "Bankfull Depth (Hbf, A)",
                "d50": "Median Sediment Size (D50)", "w_floodplain": "Floodplain Width",
                "floodplain_outer_height": "Outer Floodplain Edge Height", "w_terrace": "Terrace Width",
                "terrace_outer_height": "Outer Terrace Edge Height", "w_boundary": "Boundary Width",
                "xs_shape": "Cross-Sectional Shape", "user_functions": "User Functions**",
                "sub_curvature": "Centerline Curvature Function***", "sub_floodplain_l": "Left Floodplain Function**",
                "sub_floodplain_r": "Right Floodplain Function**", "sub_meander": "Meandering Centerline Function**",
                "sub_thalweg": "Thalweg Elevation Function**", "sub_w_bf": "Bankfull Width Function**"
                }

    @staticmethod
    def get_parameters():
        return {"DOMAIN PARAMETERS (METERS)": ["datum", "length", "x_res", "chnl_xs_pts"],
                "DIMENSIONLESS PARAMETERS": ["s_valley", "taux"],
                "CHANNEL PARAMETERS (METERS)": ["w_bf", "w_bf_min", "h_bf", "d50"],
                "FLOODPLAIN PARAMETERS (METERS)****": ["w_floodplain", "floodplain_outer_height", "w_terrace",
                                                       "terrace_outer_height", "w_boundary"],
                "USER-DEFINED FUNCTIONS": ["user_functions"],
                "SUB-REACH VARIABILITY PARAMETERS (ADD FUNCTIONS)": ["sub_curvature", "sub_floodplain_l", "sub_floodplain_r",
                                                     "sub_meander", "sub_thalweg", "sub_w_bf"],
                "CROSS SECTIONAL SHAPE": ["xs_shape"]
                }

    def get_var_names(self):
        return {"datum": self.datum, "length": self.length, "x_res": self.x_res,
                "chnl_xs_pts": self.chnl_xs_pts, "s_valley": self.s_valley, "taux": self.taux,
                "w_bf": self.w_bf, "w_bf_min":  self.w_bf_min, "h_bf": self.h_bf, "d50": self.d50,
                "w_floodplain": self.w_floodplain, "floodplain_outer_height": self.floodplain_outer_height,
                "w_terrace": self.w_terrace, "terrace_outer_height": self.terrace_outer_height,
                "w_boundary": self.w_boundary, "xs_shape": self.xs_shape, "user_functions": self.user_functions,
                "sub_curvature": self.sub_curvature, "sub_floodplain_l": self.sub_floodplain_l,
                "sub_floodplain_r": self.sub_floodplain_r, "sub_meander": self.sub_meander,
                "sub_thalweg": self.sub_thalweg, "sub_w_bf": self.sub_w_bf
                }

    @staticmethod
    def make_par_tk_characteristics():
        return {"datum": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "length": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "x_res": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "chnl_xs_pts": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "s_valley": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "taux": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "w_bf": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "w_bf_min": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "h_bf": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "d50": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "w_floodplain": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "floodplain_outer_height": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "w_terrace": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "terrace_outer_height": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "w_boundary": lambda tko, width, entries, row, col: tk.Entry(tko, width=width),
                "xs_shape": lambda tko, width, entries, row, col:  ttk.Combobox(tko, width=width, values=("AU", "SU", "TZ")),
                "user_functions": lambda tko, width, entries, row, col: tk.Button(tko, width=width, text="Create"),
                "sub_curvature": lambda tko, width, entries, row, col: ttk.Combobox(tko, width=width, values=entries),
                "sub_floodplain_l": lambda tko, width, entries, row, col: ttk.Combobox(tko, width=width, values=entries),
                "sub_floodplain_r": lambda tko, width, entries, row, col: ttk.Combobox(tko, width=width, values=entries),
                "sub_meander": lambda tko, width, entries, row, col: ttk.Combobox(tko, width=width, values=entries),
                "sub_thalweg": lambda tko, width, entries, row, col: ttk.Combobox(tko, width=width, values=entries),
                "sub_w_bf": lambda tko, width, entries, row, col: ttk.Combobox(tko, width=width, values=entries),
                }
    

    @staticmethod
    def make_header(head_name=str()):
        write_str = ""
        frame_l = []
        frame_entry = "####"
        frame_len = frame_entry.__len__() * 2 + 2 + head_name.__len__()
        [frame_l.append("#") for x in range(0, frame_len)]
        frame_line = "".join(frame_l)
        write_str += "\n" + frame_line + "\n"
        write_str += "{0} {1} {0}\n".format(frame_entry, head_name.strip("**"))
        write_str += frame_line + "\n"
        return write_str

    def make_file(self, file_name, user_input):
        # file_name = STR of file_name (without ending!
        # user_input = DICT with keys corresponding to self.par_name_dict
        write_list = self.make_write_list(user_input)
        f = open(config.dir2rb + file_name.split(".")[0] + ".txt", 'a')
        for l in write_list:
            f.write(l)
        f.close()

    @staticmethod
    def make_trigonometric_string(fun, fun_id, a, f, ps):
        return "{0}{1}={0}({2}, {3}, {4})".format(fun, str(fun_id), "%3.4f" % a, "%3.4f" % f, "%3.4f" % ps)

    def make_write_list(self, write_dict):
        # write_dict = DICT with keys corresponding to self.par_name_dict
        write_list = []
        for par_class, par_list in self.par_dict.items():

            write_list.append(self.make_header(par_class))
            for par in par_list:
                try:
                    write_str = write_dict[par]
                    if write_str.__len__() < 1:
                        write_str = str(self.par_defaults[par])
                except:
                    write_str = str(self.par_defaults[par])
                if write_str.__len__() < 1:
                    # do not use empty strings
                    continue
                if not ("user_functions" in par.lower()) or ("sub_"in par.lower()):
                    write_list.append("{0}={1}\n".format(self.par_name_dict[par].strip("**"), write_str))
                else:
                    if "sub_"in par.lower():
                        write_list.append("{0}\n".format(write_dict[par].split("=")[0]))
                    else:
                        write_list.append("{0}\n".format(write_dict[par]))
        return write_list

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = InputFile (%s)" % os.path.dirname(__file__))
        print(dir(self))
