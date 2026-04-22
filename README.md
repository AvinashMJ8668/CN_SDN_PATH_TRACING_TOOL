# SDN Path Tracing Tool

## Problem Statement & Objective
The goal of this assignment is to implement an SDN-based solution using Mininet and an OpenFlow controller (Ryu) that demonstrates controller-switch interaction, flow rule design, and network behavior observation. This project functions as a Path Tracing Tool that dynamically discovers network topologies, calculates shortest paths, tracks flow rules, implements access control (firewall filtering), and monitors link congestion.

## Topology Design & Justification
Instead of a standard tree topology, this project utilizes a custom triangle topology (`topologies/custom_topo.py`) consisting of three interconnected switches (`s1`, `s2`, `s3`). 
**Justification**: This topology introduces multiple redundant paths between hosts, making it ideal for demonstrating dynamic shortest-path routing (using Breadth-First Search) and testing automatic path recovery when a link fails.

## Core Features
- **Topology Discovery:** Dynamically detects switches and links in the network.
- **Path Calculation & Routing:** Computes the shortest path for packets using Breadth-First Search (BFS).
- **Flow Rule Tracking:** Installs and tracks OpenFlow match-action rules dynamically.
- **Blocking/Filtering (Firewall):** Implements an access control policy driven by a `policies.json` configuration file to drop packets between specific hosts (e.g., `h1` and `h4`), demonstrating hardware-level blocking via flow rules.
- **Congestion Monitoring:** Actively polls switch port statistics to monitor traffic load across links.
- **Fault Tolerance:** Automatically detects link failures and recalculates routing paths.

## Prerequisites
- Python 3.9
- Mininet
- Open vSwitch (OVS)
- uv (Python package manager)

## Installation
Due to legacy build dependencies in Ryu, the environment must be configured precisely using `uv`:

```bash
# 1. Install base dependencies
uv sync

# 2. Install Ryu and specific Eventlet version bypassing build isolation
uv pip install ryu --no-build-isolation
uv pip install eventlet==0.30.2
```

## Usage
Start the Ryu controller in one terminal:
```bash
uv run ryu-manager --observe-links main.py
```

Start the custom Mininet topology in a second terminal:
```bash
sudo mn --custom topologies/custom_topo.py --topo custom --controller=remote --switch=ovsk,protocols=OpenFlow13
```

## Validation Scenarios

### Scenario 1: Route Discovery and Flow Installation
1. In the Mininet CLI, initiate a ping between two allowed hosts:
   ```bash
   mininet> h1 ping h2 -c 4
   ```
2. Verify the controller terminal logs the discovered path `[ROUTE]` and installed flow rules `[FLOW INSTALLED]`.

### Scenario 2: Dynamic Path Recovery (Failure Simulation)
1. In the Mininet CLI, take down an active link (e.g., between `s1` and `s2`):
   ```bash
   mininet> link s1 s2 down
   ```
2. Initiate another ping (e.g. `h1 ping h3`). The controller will detect the topology change, recalculate the graph, and output the new backup path routing through `s3`.

### Scenario 3: Congestion Monitoring
1. In the Mininet CLI, initiate an iperf test between two hosts to generate heavy traffic:
   ```bash
   mininet> iperf h1 h3
   ```
2. Verify the controller terminal outputs `[MONITOR]` logs indicating the traffic load in bytes.

### Scenario 4: Access Control (Allowed vs. Blocked)
1. In the Mininet CLI, verify that `h1` can communicate with `h2` (Allowed):
   ```bash
   mininet> h1 ping h2 -c 1
   ```
2. Attempt to ping `h4` from `h1` (Blocked by Firewall):
   ```bash
   mininet> h1 ping h4 -c 1
   ```
3. The ping will fail (100% packet loss). Verify that the controller logs `[FIREWALL BLOCKED] Dropping packet...` and installs a drop flow rule with an empty action list to block future packets in hardware.

## Expected Output / Proof of Execution
To complete the final deliverables for the assignment, execute the validation scenarios above and capture screenshots of:
- The controller terminal showing topology maps, routes, installed flows, congestion logs, and firewall blocks.
- The Mininet terminal showing successful pings, failed (blocked) pings, and iperf results.
- Open vSwitch flow tables (`sudo ovs-ofctl -O OpenFlow13 dump-flows s1`).