from parse.trap_data import TrapData
from parse.trap_graph import TrapGraph

"""
Note:

For tree layout,
https://apps.cytoscape.org/apps/yfileslayoutalgorithms, Install & Restart
"""


def main():

    source_file = "FT_BC8_yolo_short.csv"
    trap_num = 1

    trap_data = TrapData(source_file)
    trap_df = trap_data.get_single_trap_df(trap_num)
    trap_graph = TrapGraph(trap_df, run_graph=True, file_name=source_file)
    trap_graph.write_cytoscape_network_csv()

    print("Wrote CytoScape")


if __name__ == "__main__":

    main()


