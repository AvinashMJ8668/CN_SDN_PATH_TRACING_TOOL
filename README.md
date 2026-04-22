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
