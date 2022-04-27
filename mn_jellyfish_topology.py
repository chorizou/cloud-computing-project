from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import RemoteController
import networkx as nx

def construct_mininet_from_networkx(graph, host_range):
    """ Builds the mininet from a networkx graph.

    :param graph: The networkx graph describing the network
    :param host_range: All switch indices on which to attach a single host as integers
    :return: net: the constructed 'Mininet' object
    """

    net = Mininet()

    # Construct mininet
    for n in graph.nodes:
        net.addSwitch("s_%s" % n)
        
        # Add single host on designated switches
        if int(n) in list(range(host_range)):
            net.addHost("h%s" % n)
            # directly add the link between hosts and their gateways
            net.addLink("s_%s" % n, "h%s" % n)

    # Connect switches to each other as defined in networkx graph
    for (n1, n2) in graph.edges:
        net.addLink('s_%s' % n1,'s_%s' % n2)

    return net

n = 2
d = 1
host_range = 3 * n
graph = nx.random_regular_graph(d, n)
net = construct_mininet_from_networkx(graph, host_range)

# ADDING COTROLLER
# This is the pox controller ip and port
# Start the controller in a separate window first: ~./pox/pox.py forwarding.l2_learning
net.addController("c0",controller=RemoteController,ip="127.0.0.1",port=6633)

# START Mininet
net.start()
CLI(net)
net.stop()
# EXIT Mininet