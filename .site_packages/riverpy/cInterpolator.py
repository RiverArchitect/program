try:
    import sys, os, logging
    import numpy as np
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, datetime, logging, numpy).")

try:
    import fGlobal as fG
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: fGlobal).")


class Interpolator:
    def __init__(self):
        self.max_x = float()
        self.max_y = float()
        self.x_input = []
        self.y_target = []
        self.logger = logging.getLogger("logfile")

    def assign_targets(self, x_data_list, y_data_list):
        # x_data_list = LIST with input x data for interpolation
        # y_data_list = LIST with target y data
        # x_input and y_input should be ordered lists (from smallest to largest)
        self.x_input = x_data_list
        self.y_target = y_data_list
        [self.x_input, self.y_target] = fG.eliminate_nan_from_list(self.x_input, self.y_target)
        if self.x_input[0] > self.x_input[-1]:
            self.logger.info("     - reordering interpolation target lists (smallest to largest)")
            self.x_input.reverse()
            self.y_target.reverse()

        self.max_x = max(self.x_input)
        self.max_y = max(self.y_target)

    def get_closest_values(self, value):
        # value = FLOAT
        # returns closest values x_lower, x_upper, y_lower, y_upper
        if value < self.x_input[0]:
            return 0.0, self.x_input[0], 0.0, self.y_target[0]
        if value > self.x_input[-1]:
            return self.x_input[-1], float("inf"), self.y_target[-1], float("nan")
        cc = -1
        for x_i in self.x_input:
            if value >= float(x_i):
                return float(self.x_input[cc]), float(x_i), float(self.y_target[cc]), float(self.y_target[cc+1])
            cc += 1

    def linear_central(self, x_data):
        # x_data_list = LIST with x data that will get interpolated y values
        interpolated_y = []
        for x in x_data:
            x_lower, x_upper, y_lower, y_upper = self.get_closest_values(x)
            try:
                interpolated_y.append(fG.interpolate_linear(x_lower, x_upper, y_lower, y_upper, x))
            except:
                interpolated_y.append("NaN")
                self.logger.info("WARNING: Non-numeric values in data.")
        return interpolated_y

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = Interpolator (%s)" % os.path.dirname(__file__))
        print(dir(self))
