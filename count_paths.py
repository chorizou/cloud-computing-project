from math import ceil
import networkx
import matplotlib as mpl
import random

import numpy as np
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
		for b in range(a + 1, n):
			try:
				shortest_paths = networkx.all_shortest_paths(graph, source=str(a), target=str(b))
				ecmp_paths[(str(a), str(b))] = [p for p in shortest_paths]
			except:
				continue
	return ecmp_paths


# shortest_simple_paths: Generate all simple paths in the graph G from source to target, starting from shortest ones.
# A simple path is a path with no repeated nodes.
# If a weighted shortest path search is to be used, no negative weights are allowed.

def compute_k_shortest_paths(graph, n, k=8):
	k_shortest_paths = {}
	for a in range(n):
		for b in range(a + 1, n):
			# slicing before casting to list improves speed
			try:
				ksp = list(islice(networkx.shortest_simple_paths(graph, source=str(a), target=str(b)), k))
				k_shortest_paths[(str(a), str(b))] = ksp
			except:
				continue
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

	avg_path_len = {}
	total_path_len_8ecmp = 0
	total_path_len_64ecmp = 0
	total_path_len_ksp = 0
	total_paths_8ecmp = 0
	total_paths_64ecmp = 0
	total_paths_ksp = 0
	
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
		try:
			paths = ecmp_paths[(str(start_node), str(dest_node))]

			if len(paths) > 64:
				paths = paths[:64]

			for i in range(len(paths)):
				path = paths[i]

				if i < 8:
					total_path_len_8ecmp += len(path)
					total_paths_8ecmp += 1

				total_path_len_64ecmp += len(path) # always add to 64-ecmp bc we truncate paths to 64 entries 
				total_paths_64ecmp += 1

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
		except:
			pass

		try:
			ksp = k_shortest_paths[(str(start_node), str(dest_node))]
			for path in ksp:
				total_path_len_ksp += len(path)
				total_paths_ksp += 1

				prev_node = None

				for node in path:
					if not prev_node:
						prev_node = node
						continue
					link = (str(prev_node), str(node))
					counts[link]["8-ksp"] += 1
					prev_node = node
		except:
			pass
	
	avg_path_len["8-ecmp"] = total_path_len_8ecmp / total_paths_8ecmp
	avg_path_len["64-ecmp"] = total_path_len_64ecmp / total_paths_64ecmp
	avg_path_len["8-ksp"] = total_path_len_ksp / total_paths_ksp

	return counts, avg_path_len

# n: number of hosts
def connectivity(n, paths):
	# matrix of connectivity
	# m[0][3] denotes whether there is a path from h0 to h3
	# m[i][i] will always be 1 bc a host can always access itself 
	m = [[0] * n for i in range(n)]
	for i in range(n):
		m[i][i] = 1
	
	for i in range(n):
		for j in range(i + 1, n):
			if (str(i), str(j)) in paths.keys():
				m[i][j] = 1

	connected = 0
	for i in range(n):
		for j in range(i + 1, n):
			connected += m[i][j]
	
	return connected / (n * (n - 1) / 2)


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

	X = range(len(ksp_distinct_paths_counts))
	fig = plt.figure()
	ax = fig.add_subplot(111)

	ax.plot(X, ksp_distinct_paths_counts, color='b', label="8 Shortest Paths")
	ax.plot(X, ecmp_64_distinct_paths_counts, color='r', label="64-way ECMP")
	ax.plot(X, ecmp_8_distinct_paths_counts, color='g', label="8-way ECMP")

	plt.legend(loc="upper left")
	plt.title("# Distinct Paths vs. Link Rank")
	ax.set_xlabel("Rank of Link")
	ax.set_ylabel("# Distinct Paths Link is on")
	plt.savefig("plots/figure_9_%s.png" % file_name)


def plot_histogram(avg_path_len1, avg_path_len2, failProb, file_name):
	protocols = ['8-way ECMP', '64-way ECMP', '8 Shortest Paths']
	path_len = []
	path_len.append([avg_path_len1['8-ecmp'], avg_path_len1['64-ecmp'], avg_path_len1['8-ksp']])
	path_len.append([avg_path_len2['8-ecmp'], avg_path_len2['64-ecmp'], avg_path_len2['8-ksp']])

	fig = plt.figure()
	ax = fig.add_subplot(111)
	X = np.arange(len(protocols))

	label = str(failProb * 100) + "% Chance of Link Failure"
	ax.bar(X - 0.165, path_len[0], width = 0.33, label="Before failing links")
	ax.bar(X + 0.165, path_len[1], width = 0.33, label=label)

	plt.legend(loc="upper left")
	plt.title("Average Path Length of Protocols")
	plt.xticks(X, protocols)
	ax.set_xlabel("Protocols")
	ax.set_ylabel("Avg. Path Length")
	plt.savefig("plots/path lengths/avgPathLen_%s.png" % (file_name))


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


def aggregate(graph, n, failProb):
	edges = list(graph.edges)
	for e in edges:
		rand = random.uniform(0, 1)
		if (rand <= failProb):
			graph.remove_edge(e[0], e[1])

	ecmp_paths = compute_ecmp_paths(graph, n)
	k_shortest_paths = compute_k_shortest_paths(graph, n)

	percent_connected = connectivity(n, ecmp_paths)
	return percent_connected



def main():
	n = 10
	num_hosts = 3 * n
	d = 3

	ecmp_paths = {}
	k_shortest_paths = {}
	file_name = "d_%s_n_%s" % (d, n)

	# Returns a random d-regular graph on n nodes. The resulting graph has no self-loops or parallel edges.
	# d: degree of each node
	# n: number of nodes
	graph = networkx.random_regular_graph(d, n) 
	
	# Write graph G in single-line adjacency-list format to path.
	# Ex. The graph with edges a-b, a-c, d-e is represented as following:
	# 		a b c # source target target
	# 		d e
	networkx.write_adjlist(graph, file_name)
	graph = networkx.read_adjlist(file_name)

	print("Computing ECMP paths...")
	ecmp_paths = compute_ecmp_paths(graph, n)
	print("Computing KSP paths...")
	k_shortest_paths = compute_k_shortest_paths(graph, n)

	traffic_matrix = random_derangement(num_hosts)
	all_links = graph.edges()
	path_counts, avg_path_len1 = count_paths(ecmp_paths, k_shortest_paths, traffic_matrix, all_links)
	
	print("Plotting path counts...")
	plot(path_counts, file_name)

	percent_connected = connectivity(n, ecmp_paths) * 100
	print("Connectivity: {:0.2f}%".format(percent_connected))


	# Now we want to probablistically fail links
	# Each link has a 0.01 percent chance of failing
	failProb = 0.1

	# For connectivity, run 10 trials and take the average
	total_connectivity = 0
	for i in range(10):
		graph = networkx.read_adjlist(file_name)
		total_connectivity += aggregate(graph, n, failProb)
	avg = total_connectivity / 10

	file_name = "failProb_%s_d_%s_n_%s" % (failProb, d, n)
	txt_file = file_name + ".txt"
	with open("./connectivity/" + txt_file, "w") as f:
		f.write(str(avg))


	'''
	while (linksToFail > 0):
		e = random.choice(list(graph.edges))
		graph.remove_edge(e[0], e[1])
		linksToFail -= 1
	'''

	# Recalculate link rank and avg. path length based on latest failed link
	print("Computing ECMP paths...")
	ecmp_paths = compute_ecmp_paths(graph, n)
	print("Computing KSP paths...")
	k_shortest_paths = compute_k_shortest_paths(graph, n)

	traffic_matrix = random_derangement(num_hosts)
	all_links = graph.edges()
	path_counts, avg_path_len2 = count_paths(ecmp_paths, k_shortest_paths, traffic_matrix, all_links)
	
	print("Plotting path counts...")
	plot(path_counts, file_name)

	percent_connected = connectivity(n, ecmp_paths) * 100
	print("Connectivity: {:0.2f}%".format(percent_connected))


	# Compute average path lengths before and after failing link
	print("Plotting average path len...")
	plot_histogram(avg_path_len1, avg_path_len2, failProb, file_name)

	
if __name__ == "__main__":
	main()

