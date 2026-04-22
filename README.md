Usage
Start the Ryu controller in one terminal:

Start the custom Mininet topology in a second terminal:

Validation Scenarios
Scenario 1: Route Discovery and Flow Installation
In the Mininet CLI, initiate a ping between two allowed hosts:

Verify the controller terminal logs the discovered path [ROUTE] and installed flow rules [FLOW INSTALLED].

Scenario 2: Dynamic Path Recovery (Failure Simulation)
In the Mininet CLI, take down an active link (e.g., between s1 and s2):

Initiate another ping (e.g. h1 ping h3). The controller will detect the topology change, recalculate the graph, and output the new backup path routing through s3.

Scenario 3: Congestion Monitoring
In the Mininet CLI, initiate an iperf test between two hosts to generate heavy traffic:

Verify the controller terminal outputs [MONITOR] logs indicating the traffic load in bytes.

Scenario 4: Access Control (Allowed vs. Blocked)
In the Mininet CLI, verify that h1 can communicate with h2 (Allowed):

Attempt to ping h4 from h1 (Blocked by Firewall):

The ping will fail (100% packet loss). Verify that the controller logs [FIREWALL BLOCKED] Dropping packet... and installs a drop flow rule with an empty action list to block future packets in hardware.

Expected Output / Proof of Execution
To complete the final deliverables for the assignment, execute the validation scenarios above and capture screenshots of:

The controller terminal showing topology maps, routes, installed flows, congestion logs, and firewall blocks.

The Mininet terminal showing successful pings, failed (blocked) pings, and iperf results.

Open vSwitch flow tables (sudo ovs-ofctl -O OpenFlow13 dump-flows s1).
