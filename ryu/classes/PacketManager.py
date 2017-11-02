#!/usr/bin/python

# gerencimento de pacotes
from ryu.lib.packet import packet

class PacketManager(packet.Packet):
    ''' gerencia Packets '''

    def __init__(self, *args, **kwargs):
        super(PacketManager, self).__init__(*args, **kwargs)

    def __str__(self):
        ''' representacao melhor do pacote '''
        s = '''Packet: \n'''
        tabs = ' ' * (len(s)/2)
        return s + '\n'.join(tabs + repr(p) for p in self.protocols)

    def add_protocols(self, protos):
        ''' add multiple protocols '''
        for p in protos:
            self.add_protocol(p)

    def send(self, dp, actions, buffer_id=None, in_port=None):
        ''' send the actual packet over the wire '''
        if not self.data:
            self.serialize()
        PacketManager.send(dp=dp, actions=actions, data=self.data, buffer_id=buffer_id, in_port=in_port)

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


