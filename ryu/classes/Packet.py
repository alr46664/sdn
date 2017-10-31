#!/usr/bin/python

# gerencimento de pacotes
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class Packet(object):
    """ gerencia eventos dos Flows """

    @staticmethod
    def send(dp, actions, data, buffer_id=None, in_port=None):
        ''' permite que enviemos um pacote para o switch dp '''
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        if buffer_id == None:
            buffer_id = ofp.OFP_NO_BUFFER

        if in_port == None:
            in_port = ofp.OFPP_NONE

        if actions == None:
            actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]

        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=buffer_id, in_port=in_port,
            actions=actions, data=data)
        dp.send_msg(out)

    @staticmethod
    def build(layers):
        ''' retorna pacote montado e serializado '''
        pkt = packet.Packet()
        for p in layers:
            pkt.add_protocol(p)
        pkt.serialize()
        return pkt

