import os
import sys
import random
import configparser
import csv
import networkx as nx
import math
import matplotlib.pyplot as plt
from collections import defaultdict

def create_network():
    """Creates network topology based on configuration"""
    if NETWORK_TYPE == 'cycle_graph' or NETWORK_TYPE == 'ring_topology':
        G = nx.cycle_graph(NUM_SWITCHES)
    elif NETWORK_TYPE == 'path_graph':
        G = nx.path_graph(NUM_SWITCHES)
    elif NETWORK_TYPE == 'mesh_graph':
        width = math.ceil(math.sqrt(NUM_SWITCHES))
        height = math.ceil(NUM_SWITCHES / width)
        G = nx.grid_2d_graph(height, width)
        # Remove extra nodes if any
        while G.number_of_nodes() > NUM_SWITCHES:
            G.remove_node(list(G.nodes())[-1])
        # Relabel nodes to match expected format
        mapping = {node: i for i, node in enumerate(G.nodes())}
        G = nx.relabel_nodes(G, mapping)
    elif NETWORK_TYPE == 'random_geometric_graph':
        # Use reasonable radius for connectivity
        radius = math.sqrt(2.0 * math.log(NUM_SWITCHES) / NUM_SWITCHES)
        while True:
            G = nx.random_geometric_graph(NUM_SWITCHES, radius)
            if nx.is_connected(G):
                break
            radius += 0.1
    elif NETWORK_TYPE == 'binomial_graph':
        # Use reasonable probability for connectivity
        p = 2 * math.log(NUM_SWITCHES) / NUM_SWITCHES
        while True:
            G = nx.binomial_graph(NUM_SWITCHES, p)
            if nx.is_connected(G):
                break
            p += 0.1
    elif NETWORK_TYPE == 'expected_nd_graph':
        # Use reasonable expected degree
        exp_degree = math.ceil(math.log2(NUM_SWITCHES))
        node_weights = [exp_degree for _ in range(NUM_SWITCHES)]
        while True:
            G = nx.expected_degree_graph(node_weights)
            G = nx.Graph(G)  # Remove parallel edges
            G.remove_edges_from(nx.selfloop_edges(G))  # Remove self-loops
            if nx.is_connected(G):
                break
            exp_degree += 1
            node_weights = [exp_degree for _ in range(NUM_SWITCHES)]
    else:
        raise ValueError(f'Invalid NETWORK_TYPE specified in config.ini: {NETWORK_TYPE}')

    # Relabel nodes to match Switch_X format
    mapping = {i: f'Switch_{i+1}' for i in range(NUM_SWITCHES)}
    G = nx.relabel_nodes(G, mapping)
    return G

def generate_topology(G):
    """Generates topology description including switches and end systems"""
    devices = []
    links = []

    # Add switches
    for node in G.nodes():
        devices.append(['SW', node, NODES_PER_SWITCH + G.degree[node]])

    # Add end systems to each switch
    es_counter = 1
    for node in G.nodes():
        for i in range(NODES_PER_SWITCH):
            es_name = f'ES_{es_counter}'
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
    """Generates stream configurations based on traffic types"""
    streams = []
    stream_id = 1
    es_nodes = [device[1] for device in devices if device[0] == 'ES']
    
    for tt_name, tt_info in traffic_types.items():
        streams_per_es = tt_info['StreamsPerES']  # Updated from FlowsPerNode
        params = tt_info['Parameters']
        
        for es in es_nodes:
            for _ in range(streams_per_es):
                dest = random.choice([n for n in es_nodes if n != es])
                stream_name = f'Stream_{stream_id}'
                # PCP (Priority Code Point) instead of traffic class
                pcp = random.randint(0, 7)
                size = random.randint(params.get('size', [100])[0], params.get('size', [100])[1])
                period = random.choice(params.get('period', [1000]))
                deadline = random.randint(params.get('deadline', [period, 2*period])[0], 
                                       params.get('deadline', [period, 2*period])[1])
                
                stream = [
                    pcp,
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
        writer.writerow(['PCP', 'StreamName', 'StreamType', 'SourceNode', 'DestinationNode', 
                        'Size', 'Period', 'Deadline'])  # Header
        for stream in streams:
            writer.writerow(stream)
    return streams

def visualize_topology(devices, links):
    """Creates a visualization of the network topology including switches and end systems"""
    H = nx.Graph()
    # Add devices as nodes with type attribute
    for device in devices:
        device_type, device_name, _ = device
        H.add_node(device_name, type=device_type)
    # Add links as edges
    for link in links:
        # LINK, link_id, node1, port1, node2, port2
        _, _, node1, _, node2, _ = link
        H.add_edge(node1, node2)
    # Now draw the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(H)
    node_types = nx.get_node_attributes(H, 'type')
    node_colors = []
    for node in H.nodes():
        if node_types[node] == 'SW':
            node_colors.append('lightblue')
        elif node_types[node] == 'ES':
            node_colors.append('lightgreen')
        else:
            node_colors.append('grey')
    nx.draw(H, pos, with_labels=True, node_color=node_colors,
            node_size=600, font_size=8, font_weight='bold')
    plt.title(f'Network Topology: {NETWORK_TYPE} ({NUM_SWITCHES} switches)')
    plt.savefig(os.path.join(OUTPUT_DIR, 'topology.png'))
    if SHOW_TOPOLOGY:
        plt.show()
    plt.close()


def generate_ned_file(devices, links):
    """Generates OMNeT++ network description file"""
    ned_lines = []
    ned_lines.append('package tsn;')
    ned_lines.append('')
    ned_lines.append('import inet.networks.base.TsnNetworkBase;')
    ned_lines.append('import inet.node.ethernet.Eth1G;')
    ned_lines.append('import inet.node.tsn.TsnDevice;')
    ned_lines.append('import inet.node.tsn.TsnSwitch;')
    ned_lines.append('')
    ned_lines.append(f'network TSN_Network {{')
    ned_lines.append('    @display("bgb=1000,1000");')
    ned_lines.append('    submodules:')
    for device in devices:
        node_type, node, _ = device
        if node_type == 'ES':
            ned_lines.append(f'        {node}: TsnDevice {{}}')
        elif node_type == 'SW':
            ned_lines.append(f'        {node}: TsnSwitch {{}}')
    ned_lines.append('    connections:')
    for link in links:
        _, _, node1, _, node2, _ = link
        ned_lines.append(f'        {node1}.ethg++ <--> Eth1G <--> {node2}.ethg++;')
    ned_lines.append('}')

    with open(os.path.join(OUTPUT_DIR, 'Network.ned'), 'w') as ned_file:
        ned_file.write('\n'.join(ned_lines))

def generate_ini_file(devices, streams):
    """Generates OMNeT++ initialization file resembling the provided sample"""
    # TODO: Implement this function
    ini_lines = []

def main():
    """Main execution function"""
    try:
        # Load configuration
        config = configparser.ConfigParser()
        config.read('config.ini')

        # Set global variables
        global SHOW_TOPOLOGY, GENERATE_OMNET_FILES, NETWORK_TYPE, NUM_SWITCHES
        global NODES_PER_SWITCH, OUTPUT_DIR, traffic_types

        SHOW_TOPOLOGY = config.getboolean('General', 'SHOW_TOPOLOGY', fallback=False)
        GENERATE_OMNET_FILES = config.getboolean('General', 'GENERATE_OMNET_FILES', fallback=True)
        NETWORK_TYPE = config.get('General', 'NETWORK_TYPE', fallback='cycle_graph')
        NUM_SWITCHES = config.getint('General', 'NUM_SWITCHES', fallback=32)
        NODES_PER_SWITCH = config.getint('General', 'NODES_PER_SWITCH', fallback=3)
        OUTPUT_DIR = config.get('Output', 'OUTPUT_DIR', fallback='simulation_output')

        # Load traffic types
        traffic_types = {}
        for tt in config.items('TrafficTypes'):
            tt_name = tt[0]
            streams_per_es = int(tt[1])
            traffic_types[tt_name] = {
                'StreamsPerES': streams_per_es,
                'Parameters': {}
            }
            
            if config.has_section(tt_name):
                for param, value in config.items(tt_name):
                    if param in ['period', 'size', 'deadline']:
                        value = [int(x.strip()) for x in value.strip('[]').split(',')]
                    traffic_types[tt_name]['Parameters'][param] = value

        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Generate network and configurations
        G = create_network()
        devices, links = generate_topology(G)
        streams = generate_streams(devices)
        visualize_topology(devices, links)

        if GENERATE_OMNET_FILES:
            generate_ned_file(devices, links)
            # generate_ini_file(devices, streams)

        print(f"Generated files in {OUTPUT_DIR}:")
        print(f"- topology.csv: Network topology definition")
        print(f"- streams.csv: Stream configurations")
        print(f"- topology.png: Network visualization")
        if GENERATE_OMNET_FILES:
            print(f"- Network.ned: OMNeT++ network description")
            # print(f"- omnetpp.ini: OMNeT++ initialization file")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
    