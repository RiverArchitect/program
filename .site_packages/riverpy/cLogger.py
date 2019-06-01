#!/usr/bin/python
try:
    import os, sys, logging
except:
    print("ExceptionERROR: Missing fundamental packages (required: os, sys, logging).")


class Logger:
    def __init__(self, logfile_name, *args):
        # args[0] = BOOL that states if an existing logfile should be deleted or not. Default is TRUE
        try:
            self.logger = self.logging_start(logfile_name, args[0])
        except:
            self.logger = self.logging_start(logfile_name)

    def logging_start(self, logfile_name, *args):
        # args[0] = BOOL that states if an existing logfile should be deleted or not. Default is TRUE
        try:
            delete_old_logfile = args[0]
        except:
            delete_old_logfile = True
        logfilenames = ["error.log", logfile_name + ".log", "logfile.log"]
        for fn in logfilenames:
            fn_full = os.path.join(os.getcwd(), fn)
            if os.path.isfile(fn_full):
                try:
                    os.remove(fn_full)
                except:
                    pass
        # start logging
        logger = logging.getLogger(logfile_name)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s")

        # create console handler and set level to info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        # create error file handler and set level to error
        err_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[0]), "w", encoding=None, delay="true")
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(formatter)
        logger.addHandler(err_handler)
        # create debug file handler and set level to debug
        debug_handler = logging.FileHandler(os.path.join(os.getcwd(), logfilenames[1]), "w")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        logger.addHandler(debug_handler)

        return logger

    def logging_stop(self):
        # stop logging and release logfile
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = Logger (%s)" % os.path.dirname(__file__))
        print(dir(self))
