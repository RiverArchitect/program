#!/usr/bin/python
# Filename: cPoolRiffle.py
from __future__ import division  # required to enforce correct division
import cHydraulic as chy
from math import *
import numpy as np


class PoolRiffle:
    def __init__(self, *args, **kwargs):
        # args
        # kwargs: forced(bool), wood(bool)
        if not('forced' in kwargs):
            self.forced = False  # default: forced pool = false
        else:
            self.forced = kwargs['forced']

        if not('wood' in kwargs):
            self.wood = False  # default: wood presence = false
        else:
            self.wood = kwargs['wood']

        # Global constants
        self.g = 9.81   # (m/s2)

        # Void global variable instantiation
        self.D50 = float()
        self.L = float()
        self.m = float()
        self.n = float()
        self.S0 = float()
        self.w_base = float()

    def pool_riffle_designer(self, target_D_z):
        # returns required pool/riffle width ratio
        # requires that self.set_normal_channel(...) is first executed
        if not(self.n > 0):
            print("ERROR: Use PoolRiffle.set_normal_channel(...) first.")
            return -1

        # get reversal discharge and flow depth
        Q_rev, h_rev = self.hy.get_Q_for_bedload(self.m, self.n, self.w_base)

        # get pool to pool and pool to riffle spacing values
        l_pool2pool, l_pool2riffle = self.get_spacing(self.w_base + 2 * self.m * h_rev)

        # set initial conditions
        # h_p = h_rev
        # h_r = h_rev
        # z_r = 0
        # z_p = z_r + self.S0 * l_pool2riffle
        B_p = self.w_base
        B_r = self.w_base
        # u = Q_rev / (h_rev * (self.w_base + self.m * h_rev))
        beta_increment = 0.001  # dimensionless factor

        m_riffle = self.m
        m_pool = self.m

        # set iteration criteria
        iter_max = 10 ** 4  # emergency iteration break criterion
        iter_count = 0
        D_z_ratio = 1.0
        convergence_crit = 10 ** -3

        while D_z_ratio > convergence_crit:
            B_p -= beta_increment
            if B_p <= 0:
                print("EMERGENCY BREAK: The target D_z value is not suitable.")
                return -1

            h_p = self.hy.get_h(m_pool, self.n, Q_rev, B_p)
            A_p = (B_p + m_pool * h_p) * h_p
            u = Q_rev / A_p

            B_r += beta_increment
            h_r = (-B_r + sqrt(B_r ** 2 + 4 * m_riffle * A_p)) / (2 * m_riffle)
            # A_r = (B_r + m_riffle * h_r) * h_r

            # compute expansion loss coefficient (Hager 2010, p.36)
            ex_angle = atan(radians((B_r - B_p) / l_pool2riffle))
            zeta_ex = (ex_angle / 90 + sin(radians(2 * ex_angle))) * (1 - (B_p / B_r)) ** 2
            D_z = h_p - h_r - u ** 2 / (2 * self.g) * zeta_ex

            # verify caamano criterion
            try:
                caamano_left = B_r / B_p - 1
            except:
                print("WARNING: B_p is zero or NaN.")
                caamano_left = 0.0
            try:
                caamano_right = D_z / h_r
            except:
                print("WARNING: h_r is zero or NaN.")
                caamano_right = float("inf")

            try:
                caamano_ratio = caamano_left / caamano_right
            except:
                print("WARNING: D_z / h_r is zero or NaN.")
                caamano_ratio = 1.0
            if caamano_ratio > 1:
                D_z_ratio = abs((target_D_z - D_z) / target_D_z)
                if iter_count < 10:
                    print("Caamano criterion NOT fulfilled ...")
                    if m_pool > 1.0:
                        print("Fitting shape with steeper pool bank slope.")
                        m_pool -= 0.1
                # if m_riffle > 1.0:
                #     print("Fitting shape with smoother riffle bank slope.")
                #     m_riffle -= 0.1

            iter_count += 1
            if not (iter_count < iter_max):
                print("Emergency break: No convergence reached (Caamano).")
                break

        print("Pool riffle design completed after " + str(iter_count - 1) + " iterations.")
        if caamano_ratio > 1:
            print("Caamano criterion OK.")
            # z_p = z_r + self.S0 * l_pool2riffle - D_z
        else:
            print("Caamano criterion NOT fulfilled.")
        results = [B_p, B_r, D_z, h_p, h_r, h_rev, l_pool2pool, l_pool2riffle, m_pool, m_riffle, Q_rev]
        return results

    def get_spacing(self, w_bf):
        # creates a log-normally distributed value for pool to pool spacing based on Thompson (2013)
        # w_bf =  bankfull discharge width (m)

        factors = [(2.50 + 3.76) / 2, 3.25, 5.4, 6.51, 6.7]  # possible multipliers from Thompson (2013)
        lognormal_mean = np.mean(factors)
        lognormal_std = (max(factors) - min(factors)) / 2
        normal_std = np.sqrt(np.log(1 + (lognormal_std / lognormal_mean) ** 2))
        normal_mean = np.log(lognormal_mean) - normal_std ** 2 / 2
        random_width_set = w_bf * np.random.lognormal(normal_mean, normal_std, size=10000000)

        l_pool2pool = sum(random_width_set) / random_width_set.__len__()
        l_pool2riffle = l_pool2pool / 2
        return(l_pool2pool, l_pool2riffle)



    def set_normal_channel(self, D50, m, n, reach_length, S0, w_base):
        try:
            self.D50 = float(D50)
            self.L = float(reach_length)
            self.m = float(m)
            self.n = float(n)
            self.S0 = float(S0)
            self.w_base = float(w_base)
            if self.S0 > 0.02:
                print("WARNING: Unvalid Riffle-Pool domain (channel slope must be smaller than 0.02).")

            try:
                self.hy = chy.Hydraulic(self.S0, self.D50)
            except:
                print("ERROR: Failed to instantiated Hydraulic class object.")
        except:
            print("ERROR: Invalid input parameter type (not-a-number).")

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = RifflePool")