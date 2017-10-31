#!/usr/bin/ryu-manager

# pacote do APP principal Ryu
from ryu.base import app_manager
# pacotes que gerenciam os eventos
from ryu.controller import dpset, ofp_event
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
# pacotes que gerenciam os protocolos OpenFlow (1.0 - 1.5)
from ryu.ofproto import ofproto_v1_0, ofproto_v1_2, ofproto_v1_3, ofproto_v1_4, ofproto_v1_5
# gerencimento de pacotes
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import icmp
from ryu.lib.packet import ether_types

# imports do usuario
from classes import Flow
from classes import Packet

class L2Switch(app_manager.RyuApp):

    # versoes do OpenFlow suportadas pelo Controller
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    # inicializicacao do controller
    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def close(self):
        print("\n\tL2Switch - STOPPED\n")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # leia a mensagem do packet_in
        buffer_id = msg.buffer_id
        total_len = msg.total_len
        in_port = msg.in_port
        reason = msg.reason
        data = msg.data

        if reason == ofp.OFPR_NO_MATCH:
            reason_txt = 'NO MATCH'
        elif reason == ofp.OFPR_ACTION:
            reason_txt = 'ACTION'
        elif reason == ofp.OFPR_INVALID_TTL:
            reason_txt = 'INVALID TTL'
        else:
            reason_txt = 'unknown'

        out_port = ofp.OFPP_FLOOD

        # BEGIN - modificacoes do switch em relacao ao hub

        pkt = packet.Packet(data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        print("   PKT IN (EVENT)\n\tID:  %s - Reason:  %s\n\tPkt:  %s\n" % (buffer_id, reason_txt, pkt) )

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[eth.src] = in_port

        if eth.dst in self.mac_to_port:
            # set the proper out port to avoid flooding
            out_port = self.mac_to_port[eth.dst]

        # define the aciton the switch will take
        actions = [ofp_parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD:
            # install a flow to avoid packet_in next time
            print("   add flow  -  dst:  %s  - out:  %s\n" % (eth.dst, out_port) )
            match = ofp_parser.OFPMatch(dl_dst=haddr_to_bin(eth.dst))
            flow = Flow(dp, match, actions )
            flow.add()

        # END - modificacoes do switch em relacao ao hub

        Packet.send(dp=dp, in_port=in_port, actions=actions, data=data)
