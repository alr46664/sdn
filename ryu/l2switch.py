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

    # esta funcao gerencia a conexao / desconexao do switch OF
    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def _switch_conn_handler(self, ev):
        dp = ev.dp
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        dp_id = dp.id
        if ev.enter:
            # crie uma tabela de macs
            print('''Conexao com Switch \"%d\", criando tabela de macs ...''' % (dp_id))
            self.mac_to_port[dp_id] = {}
            mac_to_port = self.mac_to_port[dp_id]
            # sempre que receber um pacote direcionado pra uma das portas
            # do switch, redirecione para Network Stack interno (Linux Bridge)
            # do roteador
            for port in ev.ports:
                mac_to_port[port.hw_addr] = ofp.OFPP_LOCAL
                # se recebermos um pacote com endereco para placa de rede, reenvie ele
                # pela mesma placa
                #if (port.name[0:4] == 'wlan'):
                #    mac_to_port[port.hw_addr] = port.port_no
                #    print('wlan recv')
                #print(port.hw_addr)
                #print(port.port_no)
        else:
            # delete tabela de macs da memoria
            print('''Switch \"%d\" Desconectado, destruindo tabela de macs ...''' % (dp_id))
            del self.mac_to_port[dp_id]


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

        # pegue a tabela mac deste switch (datapath)
        mac_to_port = self.mac_to_port[dp.id]

        out_port = ofp.OFPP_FLOOD

        # BEGIN - modificacoes do switch em relacao ao hub

        pkt = packet.Packet(data)
        eth = pkt.get_protocol(ethernet.ethernet)
        arp_pkt = pkt.get_protocol(arp.arp)

        # learn a mac address to avoid FLOOD next time.
        mac_to_port[eth.src] = in_port

        # ignore non arp packets, that we dont know the MAC address
        if (eth.dst != 'ff:ff:ff:ff:ff:ff') and (eth.dst not in mac_to_port) and (not arp_pkt):
            return

        # debugging
        print('''\n\n\t------------ PKT IN ( datapath: %d) ------------''' % (dp.id))
        print('''\t       Buffer_ID:  %s      Reason:  %s''' % (buffer_id, reason_txt ))
        print('''\t       In_Port:  %s''' % (in_port ))
        print('''\t       Pkt:  ''' )
        for p in pkt:
            print('''\t             %s'''  %( repr(p) ))

        if eth.dst in mac_to_port:
            # set the proper out port to avoid flooding
            out_port = mac_to_port[eth.dst]

        # define the aciton the switch will take
        actions = [ofp_parser.OFPActionOutput(out_port)]

        if out_port != ofp.OFPP_FLOOD:
            # install a flow to avoid packet_in next time
            print("\n   add flow  -  dst:  %s  - out:  %s\n" % (eth.dst, out_port) )
            match = ofp_parser.OFPMatch(dl_dst=haddr_to_bin(eth.dst))
            flow = Flow(dp, match, actions )
            flow.add()

        # END - modificacoes do switch em relacao ao hub

        Packet.send(dp=dp, in_port=in_port, actions=actions, data=data)
