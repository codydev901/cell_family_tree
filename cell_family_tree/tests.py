from parse.trap_data import TrapData
from parse.trap_graph import TrapGraph
from parse.trap_data_raw import TrapDataRaw
from parse.trap_graph_raw import TrapGraphRaw
from parse.trap_graph_peak import TrapGraphPeak
from parse.helpers import parse_experimental_results

"""
Doc Doc Doc
"""


def trap_data_tests():

    a = TrapData("FT_BC8_yolo_short.csv")

    # a.set_data_info(do_write=False)

    b = a.get_single_trap_df(trap_num=1)

    # print(b)
    # print(a.data_info[9])


def trap_graph_tests():

    trap_data = TrapData("FT_BC8_mrcnn_short_v2.csv")
    # trap_data = TrapData("FT_BC8_yolo_short_v2.csv")
    # trap_data = TrapData("FT_BC8_yolo_short.csv")

    # for t in trap_data.traps:
    #
    #     trap_df = trap_data.get_single_trap_df(trap_num=t)
    #
    #     # trap_graph = TrapGraph(df=trap_df, run_graph=False)
    #
    #     # print(trap_graph.graph)
    #
    #     trap_graph = TrapGraph(df=trap_df, run_graph=False)
    #     print(t, trap_graph.root_endpoints)

    b = trap_data.get_single_trap_df(trap_num=10)
    c = TrapGraph(b, run_graph=True)

    print(len(c.branch_nodes), c.branch_nodes)
    print(len(c.root_branch_nodes), c.root_branch_nodes)
    print(c.t_stop)

    # obj_count = c.get_divisions_from_obj_count()

    # print(obj_count)

    # for v in c.branch_nodes:
    #     print(v)
    #
    # print(len(c.branch_nodes))


def trap_data_raw_tests():

    # BC8_yolo_v1.csv
    # BC8_mrcnn_v1.csv

    a = TrapDataRaw("BC8_yolo_v1.csv")
    a.plot_single_trap_df_peak(trap_num=97, t_stop=None)


def trap_data_raw_graph_tests():

    file_name = "BC8_yolo_v1.csv"

    a = TrapDataRaw(file_name)
    b = a.get_single_trap_df(trap_num=59, t_stop=None)
    # c = TrapGraphRaw(df=b, file_name=file_name)
    c = TrapGraphPeak(df=b, file_name=file_name)

    # c.plot_rls_results()
    c.plot_peaks()


if __name__ == "__main__":

    # trap_data_raw_tests()

    trap_data_raw_graph_tests()
