import json
import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.lib import hub
from ryu.lib.packet import ethernet, ipv4, packet
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology.api import get_link, get_switch


class PathTracer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PathTracer, self).__init__(*args, **kwargs)
        self.graph = {}
        self.host_tracker = {}
        self.datapaths = {}
        self.port_stats = {}
        self.recent_flows = {}
        self.seen_broadcasts = {}  # Cache to prevent ARP storms

        self.switch_policies = {}
        self._load_policies()
        self.monitor_thread = hub.spawn(self._monitor)

    def _load_policies(self):
        try:
            with open("policies.json", "r") as f:
                data = json.load(f)
                fw = data.get("firewall", {})
                self.switch_policies = fw.get("switch_policies", {})
                print(
                    f"[POLICY LOADED] Loaded switch-specific policies for {len(self.switch_policies)} switches."
                )
        except FileNotFoundError:
            print("[POLICY WARN] policies.json not found, firewall disabled.")
        except json.JSONDecodeError:
            print("[POLICY ERROR] policies.json contains invalid JSON.")

    def _monitor(self):
        while True:
            hub.sleep(5)
            for dp in self.datapaths.values():
                ofp = dp.ofproto
                ofp_parser = dp.ofproto_parser
                req = ofp_parser.OFPPortStatsRequest(dp, 0, ofp.OFPP_ANY)
                dp.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        ofp = ev.msg.datapath.ofproto

        self.port_stats.setdefault(dpid, {})
        active_ports = []

        for stat in body:
            port_no = stat.port_no
            if port_no == ofp.OFPP_LOCAL:
                continue

            prev = self.port_stats[dpid].get(port_no)
            self.port_stats[dpid][port_no] = (stat.tx_bytes, stat.rx_bytes)

            if prev is None:
                continue

            prev_tx, prev_rx = prev
            tx_kbps = (stat.tx_bytes - prev_tx) / 1024 / 5
            rx_kbps = (stat.rx_bytes - prev_rx) / 1024 / 5

            if tx_kbps > 100 or rx_kbps > 100:
                active_ports.append(
                    f"Port {port_no}: TX={tx_kbps:.1f} KB/s  RX={rx_kbps:.1f} KB/s"
                )

        if active_ports:
            print(f"[MONITOR] Switch {dpid} | " + " | ".join(active_ports))

    def add_flow(
        self,
        datapath,
        priority,
        match,
        actions,
        idle_timeout=0,
        hard_timeout=0,
        silent=False,
    ):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]

        mod = ofp_parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout,
        )

        if not silent:
            print(
                f"[FLOW INSTALLED] Switch: {datapath.id} | Priority: {priority} | Match: {match}"
            )
        datapath.send_msg(mod)

    def flush_flows(self, datapath):
        """Wipes flow table to force immediate path recalculation on link failure"""
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        empty_match = ofp_parser.OFPMatch()

        mod = ofp_parser.OFPFlowMod(
            datapath=datapath,
            table_id=ofp.OFPTT_ALL,
            command=ofp.OFPFC_DELETE,
            out_port=ofp.OFPP_ANY,
            out_group=ofp.OFPG_ANY,
            match=empty_match,
        )
        datapath.send_msg(mod)

        # Re-add the base controller flow
        actions = [
            ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, empty_match, actions, silent=True)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        self.datapaths[dp.id] = dp
        self.flush_flows(dp)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        dpid = dp.id

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == 35020:  # Ignore LLDP
            return

        dst = eth.dst
        src = eth.src
        in_port = msg.match["in_port"]
        now = time.time()

        # Prevent ARP / Broadcast Storms in the triangle topology securely
        if dst == "ff:ff:ff:ff:ff:ff":
            cache_key = (dpid, src)
            if (
                cache_key in self.seen_broadcasts
                and (now - self.seen_broadcasts[cache_key]) < 2
            ):
                return  # Drop loop
            self.seen_broadcasts[cache_key] = now

        # HOST TRACKING (Ignore multicast source MACs)
        if not (int(src.split(":")[0], 16) & 1):
            inter_switch_ports = list(self.graph.get(dpid, {}).values())
            if in_port not in inter_switch_ports:
                self.host_tracker[src] = (dpid, in_port)

        # FIREWALL LOGIC
        switch_policy = self.switch_policies.get(
            str(dpid), {"policy_type": "allow_all"}
        )
        policy_type = switch_policy.get("policy_type", "allow_all")

        if policy_type != "allow_all":
            for pair in switch_policy.get("blocked_mac_pairs", []):
                if (src == pair[0] and dst == pair[1]) or (
                    src == pair[1] and dst == pair[0]
                ):
                    print(f"[FIREWALL] Switch {dpid} BLOCKED MAC {src} <-> {dst}")
                    match = ofp_parser.OFPMatch(eth_src=src, eth_dst=dst)
                    self.add_flow(dp, 100, match, [], hard_timeout=30)
                    return

            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            if ipv4_pkt:
                ip_src, ip_dst, proto = ipv4_pkt.src, ipv4_pkt.dst, ipv4_pkt.proto

                if policy_type == "whitelist" and proto not in switch_policy.get(
                    "allowed_protocols", []
                ):
                    print(
                        f"[FIREWALL] Switch {dpid} BLOCKED protocol {proto} (Not Whitelisted)"
                    )
                    match = ofp_parser.OFPMatch(eth_type=0x0800, ip_proto=proto)
                    self.add_flow(dp, 100, match, [], hard_timeout=30)
                    return

                elif policy_type == "blacklist":
                    if proto in switch_policy.get("blocked_protocols", []):
                        print(f"[FIREWALL] Switch {dpid} BLOCKED protocol {proto}")
                        match = ofp_parser.OFPMatch(eth_type=0x0800, ip_proto=proto)
                        self.add_flow(dp, 100, match, [], hard_timeout=30)
                        return

                    for pair in switch_policy.get("blocked_ipv4_pairs", []):
                        if (ip_src == pair[0] and ip_dst == pair[1]) or (
                            ip_src == pair[1] and ip_dst == pair[0]
                        ):
                            print(
                                f"[FIREWALL] Switch {dpid} BLOCKED IP {ip_src} <-> {ip_dst}"
                            )
                            match = ofp_parser.OFPMatch(
                                eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst
                            )
                            self.add_flow(dp, 100, match, [], hard_timeout=30)
                            return

        # ROUTING LOGIC
        if dst in self.host_tracker:
            dst_dpid, dst_port = self.host_tracker[dst]
            if dpid == dst_dpid:
                out_port = dst_port
            else:
                path = self.get_shortest_path(dpid, dst_dpid)
                if path and len(path) > 1:
                    next_hop = path[1]
                    out_port = self.graph[dpid][next_hop]
                else:
                    out_port = ofp.OFPP_FLOOD
        else:
            out_port = ofp.OFPP_FLOOD

        actions = [ofp_parser.OFPActionOutput(out_port)]

        # LOG DEDUPLICATION
        log_key = (src, dst, dpid)
        is_duplicate = (
            log_key in self.recent_flows and (now - self.recent_flows[log_key]) < 5
        )

        if not is_duplicate:
            self.recent_flows[log_key] = now
            if (
                out_port != ofp.OFPP_FLOOD
                and dst in self.host_tracker
                and dpid != dst_dpid
            ):
                path = self.get_shortest_path(dpid, dst_dpid)
                if path:
                    print(f"[ROUTE] {src} -> {dst} via path {path}")

        # Install routing flow
        if out_port != ofp.OFPP_FLOOD:
            match = ofp_parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(
                dp,
                10,
                match,
                actions,
                idle_timeout=15,
                hard_timeout=30,
                silent=is_duplicate,
            )

        # Forward current packet
        data = None
        if msg.buffer_id == ofp.OFP_NO_BUFFER:
            data = msg.data

        out = ofp_parser.OFPPacketOut(
            datapath=dp,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        dp.send_msg(out)

    @set_ev_cls(
        [event.EventLinkAdd, event.EventLinkDelete, event.EventSwitchEnter],
        MAIN_DISPATCHER,
    )
    def update_topology(self, ev):
        switch_list = get_switch(self, None)
        switches = [switch.dp.id for switch in switch_list]
        link_list = get_link(self, None)

        self.graph = {s: {} for s in switches}

        for link in link_list:
            src_dpid = link.src.dpid
            dst_dpid = link.dst.dpid
            src_port = link.src.port_no
            self.graph[src_dpid][dst_dpid] = src_port

        print(f"[TOPOLOGY] Updated Map: {self.graph}")

        # Flush flows on all active switches so traffic immediately uses the new topology
        for dp in self.datapaths.values():
            self.flush_flows(dp)

    def get_shortest_path(self, src_dpid, dst_dpid):
        if src_dpid not in self.graph or dst_dpid not in self.graph:
            return []

        queue = [[src_dpid]]
        visited = set()

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if node == dst_dpid:
                return path

            if node not in visited:
                for neighbor in self.graph.get(node, {}):
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
                visited.add(node)
        return []

