"""
Generate a knowledge graph from a list of torrent filenames + PTN inference.
"""
import os

import PTN

import networkx as nx

filenames_to_index = {}
metadata = {}

with open("data/torrents_1000.txt") as in_file:
    index = 0
    for line in in_file.readlines():
        stripped_line = line.strip()
        filenames_to_index[stripped_line] = index
        metadata[index] = PTN.parse(stripped_line)
        index += 1


# Create a graph
G = nx.DiGraph()

for index, metadata_dict in metadata.items():
    G.add_node(index)
    for key, value in metadata_dict.items():
        if key == "excess":
            continue
        node_name = "%s_%s" % (key, value)
        G.add_edge(index, node_name, attr={"type": key})


nx.nx_pydot.write_dot(G, os.path.join("data", "torrents_1000_graph.dot"))
