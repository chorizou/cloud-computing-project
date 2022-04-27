import networkx
import matplotlib as mpl
import random
mpl.use('Agg')
import matplotlib.pyplot as plt
from itertools import islice

# ECMP: Equal-cost multipath (ECMP) is a network routing strategy that allows for traffic of the same session, 
# or flow—that is, traffic with the same source and destination—to be transmitted across multiple paths of equal cost. 
# It is a mechanism that allows you to load balance traffic and increase bandwidth by fully utilizing otherwise 
# unused bandwidth on links to the same destination.
# 
# The ECMP process identifies a set of routers, each of which is a legitimate equal cost next hop towards the destination. 
# The routes that are identified are referred to as an ECMP set. Because it addresses only the next hop destination, 
# ECMP can be used with most routing protocols.
# 
# all_shortest_paths: computes all shortest simple paths in the graph
# graph nodes are strings of integers

def compute_ecmp_paths(graph, n):
	ecmp_paths = {}
	for a in range(n):
		for b in range(a+1, n):
			shortest_paths = networkx.all_shortest_paths(graph, source=str(a), target=str(b))
			ecmp_paths[(str(a), str(b))] = [p for p in shortest_paths]
	return ecmp_paths


# shortest_simple_paths: Generate all simple paths in the graph G from source to target, starting from shortest ones.
# A simple path is a path with no repeated nodes.
# If a weighted shortest path search is to be used, no negative weights are allowed.

def compute_k_shortest_paths(graph, n, k=8):
	k_shortest_paths = {}
	for a in range(n):
		for b in range(a+1, n):
			# slicing before casting to list improves speed
			ksp = list(islice(networkx.shortest_simple_paths(graph, source=str(a), target=str(b)), k))
			k_shortest_paths[(str(a), str(b))] = ksp
	return k_shortest_paths

# ecmp_paths: all equal-cost shortest paths
# k_shortest_paths: the shortest k paths between two hosts
# traffic_matrix: randomly permuted array of all the hosts (integers) such that no element is in its original position 
# this way, when you do dest_host = traffic_matrix[start_host], you are guaranteed to not have the same start and dest host
# all_links: all the edges in the graph

def count_paths(ecmp_paths, k_shortest_paths, traffic_matrix, all_links):
	# initialize counts for all links: the number of times they appear on distinct paths in the diff routing protocols
	# dictionary of (src, dest) : {8-ksp: #, 8-ecmp: #, 64-ecmp: #}
	counts = {}
	
	for link in all_links:
		a, b = link
		counts[(str(a),str(b))] = {"8-ksp": 0, "8-ecmp": 0, "64-ecmp": 0} 
		counts[(str(b),str(a))] = {"8-ksp": 0, "8-ecmp": 0, "64-ecmp": 0} 
	
	# iterate through all the hosts, which is the length of the traffic matrix array
	# assume dest host is the host randomly permutated to the index of the current host 
	for start_host in range(len(traffic_matrix)):
		dest_host = traffic_matrix[start_host]
		start_node = int(start_host / 3)
		dest_node = int(dest_host / 3)
		
		if start_node == dest_node:
			continue
		
		# swap them so that start_node < dest_node
		if start_node > dest_node:
			start_node, dest_node = dest_node, start_node

		# get all paths from this start node to this dest node
		# only need the first 64 paths (for ecmp 64-way)
		paths = ecmp_paths[(str(start_node), str(dest_node))]
		if len(paths) > 64:
			paths = paths[:64]

		for i in range(len(paths)):
			path = paths[i]
			prev_node = None
			for node in path:
				if not prev_node:
					prev_node = node
					continue

				link = (str(prev_node), str(node))
				
				if i < 8:
					counts[link]["8-ecmp"] += 1

				counts[link]["64-ecmp"] += 1
				prev_node = node

		ksp = k_shortest_paths[(str(start_node), str(dest_node))]
		for path in ksp:
			prev_node = None
			for node in path:
				if not prev_node:
					prev_node = node
					continue
				link = (str(prev_node), str(node))
				counts[link]["8-ksp"] += 1
				prev_node = node
	
	return counts


def plot(path_counts, file_name):
	ksp_distinct_paths_counts = []
	ecmp_8_distinct_paths_counts = []
	ecmp_64_distinct_paths_counts = []
	
	for _, value in sorted(path_counts.items(), key=lambda x: (x[1]["8-ksp"], x[0])):
		ksp_distinct_paths_counts.append(value["8-ksp"])
	for _, value in sorted(path_counts.items(), key=lambda x: (x[1]["8-ecmp"], x[0])):
		ecmp_8_distinct_paths_counts.append(value["8-ecmp"])
	for _, value in sorted(path_counts.items(), key=lambda x: (x[1]["64-ecmp"], x[0])):
		ecmp_64_distinct_paths_counts.append(value["64-ecmp"])

	x = range(len(ksp_distinct_paths_counts))
	fig = plt.figure()
	ax1 = fig.add_subplot(111)

	ax1.plot(x, ksp_distinct_paths_counts, color='b', label="8 Shortest Paths")
	ax1.plot(x, ecmp_64_distinct_paths_counts, color='r', label="64-way ECMP")
	ax1.plot(x, ecmp_8_distinct_paths_counts, color='g', label="8-way ECMP")

	plt.legend(loc="upper left")
	plt.title("# Distinct Paths vs. Link Rank")
	ax1.set_xlabel("Rank of Link")
	ax1.set_ylabel("# Distinct Paths Link is on")
	plt.savefig("plots/figure_9%s.png" % file_name)


# https://stackoverflow.com/questions/25200220/generate-a-random-derangement-of-a-list
# 
# random permutation traffic matrix: each server sends at its full output link rate to a single other server, 
# and receives from a single other server, and this permutation is chosen uniform-randomly. This generates a 
# a random permutation of the hosts such that each host will be at a different index.

def random_derangement(n):
    while True:
        v = list(range(n))
        for j in range(n - 1, -1, -1):
            p = random.randint(0, j)
            if v[p] == j:
                break
            else:
                v[j], v[p] = v[p], v[j]
        else:
            if v[0] != 0:
                return tuple(v)

def main():
	n = 36
	numHosts = 3 * n
	d = 3

	ecmp_paths = {}
	k_shortest_paths = {}
	file_name = "d_%s_n_%s" % (d, n)

	# Returns a random d-regular graph on n nodes. The resulting graph has no self-loops or parallel edges.
	# d: degree of each node
	# n: number of nodes
	graph = networkx.random_regular_graph(d, n) 
	
	# Write graph G in single-line adjacency-list format to path.
	networkx.write_adjlist(graph, file_name)
	graph = networkx.read_adjlist(file_name)

	print("Computing ECMP paths...")
	ecmp_paths = compute_ecmp_paths(graph, n)
	print("Computing KSP paths...")
	k_shortest_paths = compute_k_shortest_paths(graph, n)

	traffic_matrix = random_derangement(numHosts)
	all_links = graph.edges()
	path_counts = count_paths(ecmp_paths, k_shortest_paths, traffic_matrix, all_links)
	
	print("Plotting...")
	plot(path_counts, file_name)
	
if __name__ == "__main__":
	main()

