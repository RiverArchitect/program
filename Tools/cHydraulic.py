#!/usr/bin/python
# Filename: cHydraulic.py

class Hydraulic:
    def __init__(self, channel_slope, D50, *args, **kwargs):
        # kwargs may be: taux_cr
        self.g = 9.81   # (m/s2)
        self.s = 2.68   # (--) relative grain density
        self.S0 = channel_slope
        self.D50 = D50

        if not('taux_cr' in kwargs):
            self.taux_cr = 0.047
        else:
            self.taux_cr = kwargs['taux_cr']

    def calc_h_for_bedload(self):
        # returns critical flow depth for incipient sediment motion
        h_cr = self.D50 / self.S0 * self.taux_cr * (self.s - 1)
        return h_cr

    def calc_Q(self, h, m, n, w_base):
        A = h * (w_base + m * h)  # wet cross section area
        P = w_base + (2 * h * ((1 + m**2)**0.5))  # wet cross section length
        Q = (1 / n) * ((A / P)**(2 / 3)) * A * (self.S0**0.5)
        return float(Q)

    def get_h(self, m, n, Q, w_base, *args):
        # iteratively solves Manning-Strickler equation to derive flow depth
        # numerical scheme: Newton-Raphson (refer to Shayya 1996)
        try:
            messaging = args[0]  # Enable function messages if wanted
        except:
            messaging = False  # Deactivate by default

        # m = dimensionless bank slope as 1:m = y:x = TAN(bank slope[DEG])
        # n = Manning's n [s/m^(1/3)]
        # Q = discharge [m^3/s]
        # S0= channel slope [dimensionless]
        # w_base = channel base width [m]

        # PREAMBLE
        convergence_crit = 10**(-3)
        convergence_ratio = 1  # initial value
        iter_max = 10**3  # emergency iteration break criterion
        iter_count = 0
        h_init = 1/w_base  # initial value for flow depth solution

        # SOLVER
        while convergence_ratio > convergence_crit:
            A = w_base * h_init + m * h_init**2  # wet cross section area
            P = w_base + 2 * h_init / (1 / (m**2 + 1)**0.5)  # whetted cross section length
            Qk = A ** (5 / 3) * self.S0 ** 0.5 / (n * P ** (2 / 3))  # solved discharge with former h_init

            convergence_ratio = (((Q - Qk)/Q) ** 2) ** 0.5

            # continue iteration if convergence criterion was not reached:
            dA_dh = w_base + 2 * m * h_init
            dP_dh = 2 * (m**2 + 1)**0.5
            F = n * Q * P**(2 / 3) - A**(5 / 3) * self.S0**0.5
            dF_dh = 2 / 3 * n * Q * P**(-1 / 3) * dP_dh - 5 / 3 * A**(2 / 3) * self.S0**0.5 * dA_dh

            h_init = abs(h_init - F/dF_dh)  # compute new flow

            iter_count += 1
            if not(iter_count < iter_max):
                print("Emergency break: No convergence reached (flow depth iteration).")
                h_init = 0
                break
        if messaging:
            print("Flow depth convergence (prec. " + str(convergence_ratio) + ") reached after " + str(
                iter_count - 1) + " iterations.")
        return h_init

    def get_Q_for_bedload(self, m, n, w_base):
        # returns discharge for incipient grain motion based on cross section geometry

        h_cr = float(self.calc_h_for_bedload())
        Q_cr = self.calc_Q(float(h_cr), m, n, w_base)
        print("Critical depth for bed mobilization: %02.4f m." % (float(h_cr),))
        print("Critical discharge for bed mobilization: %02.4f m^3/s." % (float(Q_cr),))
        return(float(Q_cr), float(h_cr))

    def get_w_base(self, h, m, n, Q, *args):
        # iteratively solves Manning-Strickler equation to derive channel base width based on normal flow depth
        # numerical scheme: Newton-Raphson
        try:
            messaging = args[0]  # Enable function messages if wanted
        except:
            messaging = False  # Deactivate by default
        # h = normal target flow depth [m]
        # m = dimensionless bank slope as 1:m = y:x = TAN(bank slope[DEG])
        # n = Manning's n [s/m^(1/3)]
        # Q = discharge [m^3/s]
        # S0= channel slope [dimensionless]

        # PREAMBLE
        convergence_crit = 10**(-3)
        convergence_ratio = 1  # initial value
        iter_max = 10**3  # emergency iteration break criterion
        iter_count = 0
        w_base = 10*h  # initial value for channel base width solution

        # SOLVER
        while convergence_ratio > convergence_crit:
            A = w_base * h + m * h**2  # wet cross section area
            P = w_base + 2 * h / (1 / (m**2 + 1)**0.5)  # whetted cross section length
            Qk = A ** (5 / 3) * self.S0 ** 0.5 / (n * P ** (2 / 3))  # solved discharge with former h_init

            convergence_ratio = abs((Q - Qk)/Q)

            # continue iteration if convergence criterion was not reached:
            dA_dw = h
            dP_dw = 1
            F = n * Q * P**(2 / 3) - A**(5 / 3) * self.S0**0.5
            dF_dh = 2 / 3 * n * Q * P**(-1 / 3) * dP_dw - 5 / 3 * A**(2 / 3) * self.S0**0.5 * dA_dw

            w_base = abs(w_base - F/dF_dh)  # compute new flow

            iter_count += 1
            if not(iter_count < iter_max):
                print("Emergency break: No convergence reached (flow depth iteration).")
                w_base = 0
                break
        if messaging:
            print("Channel base width convergence (prec. " + str(convergence_ratio) + ") reached after " + str(
                iter_count - 1) + " iterations.")
        return w_base

    def roughness_mpm(self, D90):
        # returns Manning's n according to Meyer-Peter and Mueller (1948)
        # only valid in fully turbulent flow
        n = D90 ** (1/6) / 26.0
        print("Manning\'s n (Meyer-Peter and Mueller (1948): %02.4f s / m^(1/3)." % (float(n),))
        return n

    def roughness_strickler(self, D50):
        # returns Manning's n according to Strickler (1923)
        n = D50 ** (1/6) / 21.1
        print("Manning\'s n (Strickler (1923): %02.4f s / m^(1/3)." % (float(n),))
        return n

    def roughness_vpe_rr(self, h, D84):
        # returns Manning's n according to variable power law for roughness (Rickenmann and Recking 2011)
        # recommendation D84 = 2.2 * D50
        sqrt_8f = 4.416 * (h / D84) ** 1.904 * (1 + (h / (1.283 * D84)) ** 1.618) ** -1.083
        n = h ** (1/6) / sqrt_8f
        print("Manning\'s n (Rickenmann and Recking (2011): %02.4f s / m^(1/3)." % (float(n),))
        return n

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = Hydraulic")

