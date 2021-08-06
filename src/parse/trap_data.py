import os
import sys
import pandas as pd
import numpy as np


from .rls_peak import RLSPeak
from .rls_params import RLSParams

"""
Doc Doc Doc
"""


class TrapData:

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.experimental_results = self._load_experimental_results()
        self.df = pd.read_csv("data/{}".format(self.file_name))
        self.traps = list(self.df["trap_num"].unique())

    @staticmethod
    def _load_experimental_results():
        """
        Parses experimental results for easier access.

        :return: dict where k == trap_num, v == exp RLS count
        """

        exp_df = pd.read_csv("experimental_results/BC8_rls_exp.csv")
        exp_dict = dict()
        for i, v in exp_df.iterrows():
            trap_num = v["trap"]
            res = v["exp"]
            try:
                res = int(res)
            except ValueError:
                continue
            exp_dict[trap_num] = res

        return exp_dict

    def _get_trap_df(self, trap_num: int):
        """
        Helper method. Filter's combined dataframe by trap_num, remove's some unneeded columns if present. Writes
        df to recent/recent_query.csv (for quick comparison with raw data).

        :param trap_num: see data.csv/trap_num
        :return: dataframe
        """

        df = self.df.loc[self.df['trap_num'] == trap_num]

        for k in ["image_num", "image_path"]:
            try:
                del df[k]
            except KeyError:
                pass

        if not os.path.exists("recent"):
            os.mkdir("recent")

        df.to_csv("recent/recent_query.csv", index=False)

        return df

    def get_rls_peak(self, trap_num: int, params: RLSParams, get_rls_obj: bool = False):
        """
        Run's RLS calculations using sum_area and obj_count.

        :param trap_num: see data.csv/trap_num
        :param get_rls_obj: for use in plotting/full results
        :param params:
        :return: dict containing RLS information for specified trap_num along with experimental count
        """

        assert trap_num in self.traps, "invalid trap_num:{}".format(trap_num)

        trap_df = self._get_trap_df(trap_num)

        rls = RLSPeak(trap_df, params=params)
        if get_rls_obj:
            return rls

        rls = rls.results()
        try:
            rls.update({"exp_div": self.experimental_results[trap_num]})
        except KeyError:
            return None

        return rls

    def get_rls_peak_all(self, params: RLSParams, as_sum_res=False):
        """
        Doc Doc Doc

        :return:
        """

        res = []
        sum_res = []

        for v in self.traps:
            try:
                rls = self.get_rls_peak(v, params, get_rls_obj=False)
            except ValueError:
                continue
            # if rls is None, experimental results were not found. Will ignore it.
            if rls:
                res.append(rls)
                residuals = abs(rls["exp_div"] - rls["pred_div"])
                sum_res.append(residuals)

        if as_sum_res:
            return [[sum(sum_res)] + params.to_param_list()]

        return res






