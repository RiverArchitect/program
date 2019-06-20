try:
    import os, logging, sys, glob
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, glob, logging.")

# recurring variables:
# _f = TXT FILE  - input file (opened)
# par_name = STR - RiverBuilder Parameter Name
# write_list = list of lines that will eventually be written
class InputFile:
    def __init__(self, file_name):
        # processing variables
        self.file_name = file_name
        self.par_names = self.get_par_names()
        self.write_list = []

        # RiverBuilder variables
        self.chnl_xs_pts = 2
        self.d50 = 0.0
        self.datum = 1
        self.dx = 1.0  # FLOAT of x-intercept
        self.dy = 1.0  # FLOAT of y-intercept
        self.floodplain_outer_height = 0.0
        self.h_bf = 0.0
        self.length = 1.0
        self.s_valley = 0.0
        self.taux = 0.0
        self.terrace_outer_height = 0.0
        self.user_functions = []#"SIN1=SIN(0, 1, 0)"
        self.user_function_count = 0
        self.user_function_dict = {"SIN": lambda a, f, ps: self.add_user_function(fun="SIN", a=a, f=f, ps=ps),
                                   "COS": lambda a, f, ps: self.add_user_function(fun="COS", a=a, f=f, ps=ps),
                                   "SIN_SQ": lambda a, f, ps: self.add_user_function(fun="SIN_SQ", a=a, f=f, ps=ps),
                                   "LINE": lambda: self.add_user_function(fun="LINE"),
                                   "PERL": lambda a, lam: self.add_user_function(fun="PERL", a=a, lam=lam)}
        self.w_bf = 0.0
        self.w_bf_min = 0.0
        self.w_boundary = 0.0
        self.w_floodplain = 0.0
        self.w_terrace = 0.0
        self.x_res = 1
        self.xs_shape = "AU"

    def add_user_function(self, fun=str(), a=float(), f=float(), ps=float, lam=float()):
        # fun = STR  of SIN#, COS#, SIN_SQ# (sin-square), LINE#, PERL# (Perlin)
        # a = FLOAT - amplitude
        # f = FLOAT - frequency
        # ps = FLOAT - phase shift (multiple or fraction of PI)
        # lam = FLOAT - wavelength (originally in RiverBuilder denoted as "w"
        if "sin" or "cos" or "line" or "perl" in fun.lower():
            self.user_function_count += 1
        if "sin" or "cos" in fun.lower():
            self.user_functions.append(self.make_trignonometric_string(fun, a, f, ps))
        if "line" in fun.lower():
            self.user_functions.append("{0}{1}={0}({2}, {3})".format(fun, str(self.user_function_count), str(self.s_valley), str(self.dy)))
        if "perl" in fun.lower():
            self.user_functions.append("{0}{1}={0}({2}, {3})".format(fun, str(self.user_function_count), "%3.4f" % a, "%3.4f" % lam))


    def get_par_dict(self):
        return {"NOTES": "# - All dimensional numbers are in units of meters.\n"}


    def get_par_names(self):
        return ["DOMAIN PARAMETERS (METERS)", "DIMENSIONLESS PARAMETERS",
                "CHANNEL PARAMETERS (METERS)", "FLOODPLAIN PARAMETERS (METERS)", "CROSS SECTIONAL SHAPE",
                "USER-DEFINED FUNCTIONS", "SUB-REACH VARIABILITY PARAMETERS"]

    def make_header(self, write_list, par_name=str()):
        frame_l = []
        frame_entry = "####"
        frame_len = frame_entry.__len__() * 2 + 2 + par_name.__len__()
        [frame_l.append("#") for x in range(0, frame_len)]
        frame_line = "".join(frame_l)
        write_list.append("\n" + frame_line + "\n")
        write_list.append("{0} {1} {0}\n".format(frame_entry, par_name))
        write_list.append(frame_line + "\n")
        return write_list

    def make_file(self):
        f = open(self.dir + self.file_name.split(".")[0] + ".txt", 'a')
        for l in self.write_list:
            f.write(l)
        f.close()

    def make_trignonometric_string(self, fun, a, f, ps):
        return "{0}{1}={0}({2}, {3}, {4})".format(fun, str(self.user_function_count), "%3.4f" % a, "%3.4f" % f, "%3.4f" % ps)

    def make_write_list(self):
        for par in self.par_names:
            pass


class Messenger:
    def __init__(self):
        self.message_dict = {}

    def get_msg(self, par):
        self.message_dict[par]
