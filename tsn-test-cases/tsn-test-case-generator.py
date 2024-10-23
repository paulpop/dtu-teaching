import os
import sys
import random
import configparser
import csv
import networkx as nx
import pygraphviz as pgv
import matplotlib.pyplot as plt
from collections import defaultdict

# Load configuration
config = configparser.ConfigParser()
ini_path = os.path.join(os.getcwd(),'config.ini')
config.read(ini_path)

# General settings
SHOW_TOPOLOGY = config.getboolean('General', 'SHOW_TOPOLOGY', fallback=False)
GENERATE_OMNET_FILES = config.getboolean('General', 'GENERATE_OMNET_FILES', fallback=True)
NETWORK_TYPE = config.get('General', 'NETWORK_TYPE', fallback='ring_topology')
NUM_SWITCHES = config.getint('General', 'NUM_SWITCHES', fallback=32)
NODES_PER_SWITCH = config.getint('General', 'NODES_PER_SWITCH', fallback=3)
OUTPUT_DIR = config.get('Output', 'OUTPUT_DIR', fallback='simulation_output')

# Units configuration
PeriodUnit = config.get('Units', 'PeriodUnit', fallback='MICROSECOND')
DeadlineUnit = config.get('Units', 'DeadlineUnit', fallback='MICROSECOND')
SizeUnit = config.get('Units', 'SizeUnit', fallback='BYTES')

traffic_types = {}
for tt in config.items('TrafficTypes'):
    tt_name = tt[0]
    flows_per_node = int(tt[1])
    traffic_types[tt_name] = {
        'FlowsPerNode': flows_per_node,
        'Parameters': {}
    }
    print(tt_name)
    # Load traffic type parameters
    if config.has_section(tt_name):
        params = config.items(tt_name)
        for param in params:
            key = param[0]
            value = param[1]
            if key == 'period' or key == 'deadline':
                # Parse list of integers
                value = [int(x.strip()) for x in value.strip('[]').split(',')]
            elif key == 'size' or key == 'traffic_class':
                value = [int(x.strip()) for x in value.strip('[]').split(',')]
            traffic_types[tt_name]['Parameters'][key] = value

def create_network():
    if NETWORK_TYPE == 'ring_topology':
        G = nx.cycle_graph(NUM_SWITCHES)
        mapping = {i: f'Switch_{i+1}' for i in range(NUM_SWITCHES)}
        G = nx.relabel_nodes(G, mapping)
    elif NETWORK_TYPE == 'path_graph':
        G = nx.path_graph(NUM_SWITCHES)
        mapping = {i: f'Switch_{i+1}' for i in range(NUM_SWITCHES)}
        G = nx.relabel_nodes(G, mapping)
    else:
        raise ValueError('Invalid NETWORK_TYPE specified in config.ini')
    return G

def generate_topology(G):
    devices = []
    links = []

    # Add switches
    for node in G.nodes():
        devices.append(['SW', node, NODES_PER_SWITCH + G.degree[node]])

    # Add end systems to each switch
    es_counter = 1
    for node in G.nodes():
        for i in range(NODES_PER_SWITCH):
            es_name = f'Node_{es_counter}'
            devices.append(['ES', es_name, 1])
            link_id = f'Link_{len(links)+1}'
            links.append(['LINK', link_id, es_name, 1, node, i+1])
            es_counter += 1

    # Add links between switches
    port_mapping = defaultdict(int)
    for edge in G.edges():
        src_port = port_mapping[edge[0]] + NODES_PER_SWITCH + 1
        dst_port = port_mapping[edge[1]] + NODES_PER_SWITCH + 1
        port_mapping[edge[0]] += 1
        port_mapping[edge[1]] += 1
        link_id = f'Link_{len(links)+1}'
        links.append(['LINK', link_id, edge[0], src_port, edge[1], dst_port])

    # Write to topology.csv
    with open(os.path.join(OUTPUT_DIR, 'topology.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for device in devices:
            writer.writerow(device)
        for link in links:
            writer.writerow(link)
    return devices, links

def generate_streams(devices):
    streams = []
    stream_id = 1
    es_nodes = [device[1] for device in devices if device[0] == 'ES']
    for tt_name, tt_info in traffic_types.items():
        flows_per_node = tt_info['FlowsPerNode']
        params = tt_info['Parameters']
        for es in es_nodes:
            for _ in range(flows_per_node):
                dest = random.choice([n for n in es_nodes if n != es])
                stream_name = f'Stream_{stream_id}'
                traffic_class = random.randint(0,7)
                size = random.randint(params.get('size', 100)[0], params.get('size', 100)[1])
                period = random.choice(params.get('period', [1000]))
                deadline = random.randint(params.get('deadline', 2*period)[0], params.get('deadline', 2*period)[1])
                stream = [
                    traffic_class,
                    stream_name,
                    tt_name,
                    es,
                    dest,
                    size,
                    period,
                    deadline
                ]
                streams.append(stream)
                stream_id += 1

    # Write to streams.csv
    with open(os.path.join(OUTPUT_DIR, 'streams.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for stream in streams:
            writer.writerow(stream)
    return streams

def visualize_topology(G):
    A = nx.nx_agraph.to_agraph(G)
    A.layout('circo')
    A.draw('topology.png')
    plt.imshow(plt.imread('topology.png'))
    plt.axis('off')
    plt.show()

def generate_ned_file(G):
    # Create NED file content
    ned_lines = []
    ned_lines.append(f'network TSN_Network {{')
    ned_lines.append(f'    submodules:')
    for node in G.nodes():
        if node.startswith('Switch'):
            ned_lines.append(f'        {node}: EtherSwitch {{}}')
        else:
            ned_lines.append(f'        {node}: StandardHost {{}}')
    ned_lines.append(f'    connections:')
    for edge in G.edges():
        ned_lines.append(f'        {edge[0]}.pppg++ <--> Eth100M <--> {edge[1]}.pppg++;')
    ned_lines.append('}')

    # Write to .ned file
    with open(os.path.join(OUTPUT_DIR, 'network.ned'), 'w') as ned_file:
        ned_file.write('\n'.join(ned_lines))

def generate_ini_file(streams):
    ini_lines = []
    ini_lines.append('[General]')
    ini_lines.append('network = TSN_Network')
    ini_lines.append('sim-time-limit = 10.0s')
    ini_lines.append('**.connFIXdelay = 0ns')
    ini_lines.append('**.connFIXdataRate = 100Mbps')
    ini_lines.append('**.connFIXber = 0')

    # Configure applications
    app_index = 0
    for stream in streams:
        traffic_class, stream_name, tt_name, src, dest, size, period, deadline = stream
        ini_lines.append(f'**.{src}.numApps = {app_index + 1}')
        ini_lines.append(f'**.{src}.app[{app_index}].typename = "UdpBasicApp"')
        ini_lines.append(f'**.{src}.app[{app_index}].destAddresses = "{dest}"')
        ini_lines.append(f'**.{src}.app[{app_index}].messageLength = {size}B')
        ini_lines.append(f'**.{src}.app[{app_index}].sendInterval = {period}us')
        app_index += 1

    # Write to .ini file
    with open(os.path.join(OUTPUT_DIR, 'omnetpp.ini'), 'w') as ini_file:
        ini_file.write('\n'.join(ini_lines))

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    G = create_network()
    devices, links = generate_topology(G)
    streams = generate_streams(devices)
    print(f"Generated streams.csv and topology.csv in {OUTPUT_DIR}")
    if SHOW_TOPOLOGY:
        visualize_topology(G)
    if GENERATE_OMNET_FILES:
        generate_ned_file(G)
        generate_ini_file(streams)
        print(f"Generated OMNeT++ .ned and .ini files in {OUTPUT_DIR}")

if __name__ == '__main__':
    main()