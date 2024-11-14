# TSN Test Case Generator

## Contacts: 

- Andrei-Robert Cuzenco s242817@student.dtu.dk
- Paul Pop paupo@dtu.dk

A tool for generating Time-Sensitive Networking (TSN) test cases with configurable network topologies and stream configurations.

## Documentation

- [File Format Specifications](file_format_specs.md): Details about the input and output file formats used by the tool.

## Usage Guide

### Basic Usage

Run the generator with default configuration:
```bash
python3 tsn-test-case-generator.py
```

## Disclaimer

Don't forget to change the project names from the generated OMNeT++ files otherwise you will get an error when importing.

Increasing the size for the ats category above 1000 in the config might produce unexpected results.

### Configuration

The tool uses a `config.ini` file for all settings. Key configuration options include:

1. Network Topology Settings:
```ini
[General]
NETWORK_TYPE = mesh_graph    # Type of network topology
NUM_SWITCHES = 32           # Number of switches in the network
NODES_PER_SWITCH = 3       # End systems per switch
```

Supported network types:
- `cycle_graph` or `ring_topology`: Ring network
- `path_graph`: Linear network
- `mesh_graph`: 2D mesh network
- `random_geometric_graph`: Random network with geometric constraints
- `binomial_graph`: Random network with binomial degree distribution
- `expected_nd_graph`: Random network with expected node degree

2. Stream Configuration:
```ini
[TrafficTypes]
ATS = 2    # Number of streams per end system

[ats]
period = [500,1000,2000]    # Possible periods in microseconds
size = [500,1000]           # Size range in bytes
deadline = [1000,20000]     # Deadline range in microseconds
```

### Output Files

The tool generates several files in the specified output directory:

1. `topology.csv`: Network topology definition including:
   - Switches and their ports
   - End systems
   - Network links

2. `streams.csv`: Stream configurations including:
   - Priority Code Point (PCP)
   - Stream names
   - Source and destination nodes
   - Size, period, and deadline

3. `topology.png`: Visual representation of the network

4. OMNeT++ files (if enabled):
   - `Network.ned`: Network description
   - `omnetpp.ini`: Network description

### Example Usage

1. Create a mesh network with 16 switches:
```ini
[General]
NETWORK_TYPE = mesh_graph
NUM_SWITCHES = 16
NODES_PER_SWITCH = 4
```

2. Configure high-priority streams:
```ini
[TrafficTypes]
ATS = 3    # 3 streams per end system

[ats]
period = [500,1000]     # More frequent periods
size = [64,128]         # Smaller packets
deadline = [1000,5000]  # Stricter deadlines
```

Total streams generated = NUM_SWITCHES × NODES_PER_SWITCH × streams_per_es
In this example: 16 × 4 × 3 = 192 streams

### Visualization

Enable topology visualization:
```ini
[General]
SHOW_TOPOLOGY = True
```

This will display and save a visual representation of the network topology.

## Installation Guide

### Windows Installation

1. Install Python dependencies using pip:
```bash
python3 -m pip install networkx matplotlib
```

2. Install Graphviz:
   - Download from: https://gitlab.com/graphviz/graphviz/-/package_files/6164164/download
   - Note: Other versions may not be compatible

3. Install Microsoft Build Tools:
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

4. Install pygraphviz with specific configurations:
```bash
python3 -m pip install --config-settings="--global-option=build_ext" `
              --config-settings="--global-option=-IC:\Program Files\Graphviz\include" `
              --config-settings="--global-option=-LC:\Program Files\Graphviz\lib" `
              pygraphviz
```

### macOS Installation

1. Install Graphviz using Homebrew:
```bash
brew install graphviz
```

2. Install Python dependencies:
```bash
python3 -m pip install networkx matplotlib pygraphviz
```

### Linux/Ubuntu Installation

1. Install Graphviz packages:
```bash
sudo apt-get install graphviz graphviz-dev
```

2. Install Python dependencies:
```bash
python3 -m pip install networkx matplotlib pygraphviz
```

## Contributing

Feel free to submit issues and enhancement requests.

## License

MIT License

