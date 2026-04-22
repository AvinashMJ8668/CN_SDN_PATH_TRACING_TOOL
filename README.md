# SDN Path Tracing & Network Management Tool

[![Python](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Mininet](https://img.shields.io/badge/Mininet-2.3.0-green.svg)](http://mininet.org/)
[![Ryu](https://img.shields.io/badge/Ryu-Controller-orange.svg)](https://ryu.readthedocs.io/en/latest/)

## Overview
The **SDN Path Tracing Tool** is a robust Software-Defined Networking (SDN) solution built using Mininet and the Ryu OpenFlow controller. This project demonstrates advanced controller-switch interactions, dynamic flow rule provisioning, and real-time network telemetry. 

It functions as an intelligent network manager capable of dynamically discovering topologies, calculating optimal routing paths, enforcing L2/L3/L4 firewall policies, and monitoring link congestion in real-time.

## Table of Contents
- [Core Architecture & Features](#core-architecture--features)
- [Topology Design](#topology-design)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Validation & Testing Scenarios](#validation--testing-scenarios)
- [System Artifacts & Logging](#system-artifacts--logging)

## Core Architecture & Features
* **Dynamic Topology Discovery:** Automatically maps out switches, links, and hosts within the network using OpenFlow protocols.
* **Intelligent Path Calculation:** Utilizes Breadth-First Search (BFS) to compute and deploy the shortest path for packets, ensuring optimal routing.
* **Fault Tolerance & Self-Healing:** Actively detects link failures and instantly recalculates and installs backup routing paths to maintain network integrity.
* **Stateful Access Control (Firewall):** Enforces a dynamic security policy (configured via `policies.json`) to filter traffic at the hardware level. Capable of blocking specific MAC pairs, IP endpoints, or Layer 4 protocols (e.g., UDP).
* **Congestion Monitoring:** Continuously polls OpenFlow port statistics to monitor Tx/Rx byte rates and identify traffic bottlenecks across links.

## Topology Design
This system utilizes a custom, redundant triangle topology rather than a standard tree. This architecture provides multiple redundant pathways, allowing the system to demonstrate dynamic shortest-path routing and automatic link-failure recovery.

**Network Architecture:**
```text
  h1 (10.0.0.1)                    h3 (10.0.0.3)
  h2 (10.0.0.2)                    |
       |                           |
       |                     [s2: ALLOW ALL]
       |                    /              \
  [s1: BLACKLIST] ----------                [s3: WHITELIST]
   - blocks h1<->h4 (IP)                     - ICMP only
   - blocks h2<->h3 (MAC)                         |
   - blocks UDP                             h4 (10.0.0.4)
Prerequisites
Python: ==3.9.*

Network Emulator: Mininet & Open vSwitch (OVS)

Package Manager: uv (recommended for strict dependency resolution)

Installation
Due to specific build dependencies in the Ryu controller, the environment must be configured exactly as follows using uv:

Bash
# 1. Install base dependencies from the lockfile
uv sync

# 2. Install Ryu and the required Eventlet version (bypassing build isolation)
uv pip install ryu --no-build-isolation
uv pip install eventlet==0.30.2
Usage
The environment requires two terminal sessions—one for the SDN controller and one for the simulated data plane.

Terminal 1: Initialize the Ryu Controller

Bash
uv run ryu-manager --observe-links main.py
Terminal 2: Launch the Mininet Topology

Bash
sudo mn --custom topologies/custom_topo.py --topo custom --controller=remote --switch=ovsk,protocols=OpenFlow13
Validation & Testing Scenarios
Run the following commands in the Mininet CLI (mininet>) to validate system capabilities:

1. Route Discovery & Flow Provisioning
Action: h1 ping h2 -c 4
Expected Behavior: The controller dynamically maps the route and outputs [ROUTE] and [FLOW INSTALLED] logs. OpenFlow rules are pushed to the switches.

2. Dynamic Path Recovery (Failover)
Action: 1. Take down an active link: link s1 s2 down
2. Ping across the network: h1 ping h3
Expected Behavior: The controller detects the topology change, flushes outdated flows, recalculates the graph, and establishes a new backup path via s3.

3. Congestion Monitoring
Action: Generate heavy traffic using iperf: iperf h1 h3
Expected Behavior: The controller terminal will actively poll and display [MONITOR] logs detailing the traffic load (Tx/Rx) in KB/s for the utilized switch ports.

4. Firewall & Access Control
Action: Attempt an unauthorized connection: h1 ping h4 -c 1
Expected Behavior: The ping fails with 100% packet loss. The controller logs [FIREWALL] Switch X BLOCKED... and instantly installs a hardware-level drop rule (empty action list) to block subsequent unauthorized packets at line rate.

System Artifacts & Logging
When monitoring the controller output or inspecting the switches directly (e.g., sudo ovs-ofctl -O OpenFlow13 dump-flows s1), the system provides comprehensive telemetry:

[TOPOLOGY]: Real-time mapping of switch datapath IDs and ports.

[ROUTE]: Step-by-step pathing logic.

[FLOW INSTALLED]: Confirmation of match-action rules pushed to OVS.

[MONITOR]: Port statistics and bandwidth utilization.

[FIREWALL]: Security alerts for dropped packets based on the JSON configuration.
