from parse.trap_data import TrapData
from parse.trap_graph import TrapGraph

"""
Doc Doc Doc
"""


def trap_data_tests():

    a = TrapData("FT_BC8_yolo_short.csv")

    # a.set_data_info(do_write=False)

    b = a.get_single_trap_df(trap_num=65)

    # print(b)
    # print(a.data_info[9])


def trap_graph_tests():

    # trap_data = TrapData("FT_BC8_yolo_short_v2.csv")
    trap_data = TrapData("FT_BC8_yolo_short.csv")

    for t in trap_data.traps:

        trap_df = trap_data.get_single_trap_df(trap_num=t)

        # trap_graph = TrapGraph(df=trap_df, run_graph=False)

        # print(trap_graph.graph)

        trap_graph = TrapGraph(df=trap_df, run_graph=False)
        print(t, trap_graph.root_endpoints)


if __name__ == "__main__":

    trap_data_tests()

