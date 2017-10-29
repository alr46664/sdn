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
from ryu.lib.packet import ether_types

# faca o import de nossa classe abstrata do Ryu
from ryu_abstract import RyuAbstractApp

class L2Switch(RyuAbstractApp):
    # versoes do OpenFlow suportadas pelo Controller
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    # inicializicacao do controller
    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        # faca o ctrl funcionar como learning switch
        self.switch(ev)
        # por enquanto, faca o ctrl funcionar como hub
        # self.hub(ev)

    # esta funcao serve de handler para o packet in caso desejemos que nosso
    # controller funcione como um learning switch
    def switch(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # aparentemente este campo foi desativado e causa problemas no OpenFlow
        # desativando com FFFFF
        # buffer_id = msg.buffer_id if msg.buffer_id != 0xffffffff else None
        buffer_id = 0xffffffff

        data = msg.data

        in_port = msg.in_port
        out_port = ofp.OFPP_FLOOD

        # BEGIN - modificacoes do switch em relacao ao hub

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        print("packet in:  src: %s  dst: %s" % (eth.src,eth.dst) )

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[eth.src] = msg.in_port

        if eth.dst in self.mac_to_port:
            # set the proper out port to avoid flooding
            out_port = self.mac_to_port[eth.dst]

        # define the aciton the switch will take
        actions = [ofp_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofp.OFPP_FLOOD:
            match = ofp_parser.OFPMatch(dl_dst=haddr_to_bin(eth.dst))
            self.add_flow(dp, match, actions)

        # END - modificacoes do switch em relacao ao hub

        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=buffer_id, in_port=in_port,
            actions=actions, data=data)
        dp.send_msg(out)

    # esta funcao serve de handler para o packet in caso desejemos que nosso
    # controller funcione como um hub
    def hub(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # buffer_id = msg.buffer_id
        buffer_id = 0xffffffff
        data = msg.data

        in_port = msg.in_port
        out_port = ofp.OFPP_FLOOD

        actions = [ofp_parser.OFPActionOutput(out_port)]
        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=buffer_id, in_port=in_port,
            actions=actions, data=data)
        dp.send_msg(out)
