from operator import attrgetter
from typing import DefaultDict
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.lib.packet import *
from ryu.app import simple_switch_13
from ryu.lib import hub
from collections import defaultdict

class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        ##### monitor
        self.dataptaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    ### monitor 
    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
    

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)


    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)
    
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        sum = defaultdict(int)
        
        body = ev.msg.body
        self.logger.info('Flow Statistical Information')
        self.logger.info('datapath         '
                         'in-port  src_ip            '
                         'src_port dst_ip            '
                         'dst_port protocol  '
                         'action   packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- ----------------- '
                         '-------- --------- '
                         '-------- -------- ----------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match.get('in_port', 0), 
                                             flow.match.get('eth_dst', 0))):
            if stat.instructions[0].type != 5:
                port = stat.instructions[0].actions[0].port
                if stat.match['ip_proto'] == 0x06:
                    sum[port] += stat.byte_count - self.flow[(ev.msg.datapath.id, stat.instructions[0].actions[0].port)][(stat.match['ipv4_src'], stat.match['tcp_src'], 
                                                        stat.match['ipv4_dst'],stat.match['tcp_dst'], 'TCP')]
                    self.flow[(ev.msg.datapath.id, stat.instructions[0].actions[0].port)][(stat.match['ipv4_src'], stat.match['tcp_src'], stat.match['ipv4_dst'],stat.match['tcp_dst'], 'TCP')] = stat.byte_count
                elif stat.match['ip_proto'] == 0x11:
                    sum[port] += stat.byte_count - self.flow[(ev.msg.datapath.id, stat.instructions[0].actions[0].port)][(stat.match['ipv4_src'], stat.match['udp_src'], 
                                                        stat.match['ipv4_dst'],stat.match['udp_dst'], 'UDP')]
                    self.flow[(ev.msg.datapath.id, stat.instructions[0].actions[0].port)][(stat.match['ipv4_src'], stat.match['udp_src'], stat.match['ipv4_dst'],stat.match['udp_dst'], 'UDP')] = stat.byte_count

            # datapath_id in-port src_ip src_port dst_ip dst_port protocol  action packets  bytes
            if stat.match['ip_proto'] == 0x06 :
                self.logger.info('%016x %8x %17s %8d %17s %8d %9s %8s %8d %10d',
                                 ev.msg.datapath.id,
                                 stat.match['in_port'], stat.match['ipv4_src'],
                                 stat.match['tcp_src'], stat.match['ipv4_dst'],
                                 stat.match['tcp_dst'], 'TCP',
                                 stat.instructions[0].actions[0].port,
                                 stat.packet_count, stat.byte_count)
            elif stat.match['ip_proto'] == 0x11 :
                # datapath_id in-port src_ip src_port dst_ip dst_port protocol  action packets  bytes
                    self.logger.info('%016x %8x %17s %8d %17s %8d %9s %8s %8d %10d',
                                 ev.msg.datapath.id,
                                 stat.match['in_port'], stat.match['ipv4_src'],
                                 stat.match['udp_src'], stat.match['ipv4_dst'],
                                 stat.match['udp_dst'], 'UDP',
                                 stat.instructions[0].actions[0].port,#action
                                 stat.packet_count, stat.byte_count)
            elif stat.match['ip_proto'] == 0x01 :
                # datapath_id in-port src_ip src_port dst_ip dst_port protocol  action packets  bytes
                    self.logger.info('%016x %8x %17s %8s %17s %8s %9s %8s %8d %10d',
                                 ev.msg.datapath.id,
                                 stat.match['in_port'], stat.match['ipv4_src'],
                                 ' ', stat.match['ipv4_dst'],
                                 ' ', 'ICMP',
                                 stat.instructions[0].actions[0].port,#action
                                 stat.packet_count, stat.byte_count)
        for port in sum.keys():
            if sum[port] >= 1000000 :
                print("Congestion Alert! dpid : {} port : {} sum of flows : {}".format(ev.msg.datapath.id, port, sum[port]))
        
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        self.logger.info('Port Statistical Information')
        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                                ev.msg.datapath.id, stat.port_no,
                                stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                                stat.tx_packets, stat.tx_bytes, stat.tx_errors)