from parse.trap_data import TrapData

"""
Doc Doc Doc
"""


def main():

    a = TrapData("FT_BC8_yolo_short_v2.csv")

    a.set_data_info(do_write=True)

    b = a.get_single_trap_df(trap_num=9)

    print(b)
    print(a.data_info[9])


if __name__ == "__main__":

    main()
