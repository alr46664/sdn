#!/usr/bin/ryu-manager

# pacote do APP principal Ryu
from ryu.base import app_manager
# pacotes que gerenciam os eventos
from ryu.controller import dpset, ofp_event
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
# pacotes que gerenciam os protocolos OpenFlow (1.0 - 1.5)
from ryu.ofproto import ofproto_v1_0, ofproto_v1_2, ofproto_v1_3, ofproto_v1_4, ofproto_v1_5
# gerencimento de pacotes
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import icmp
from ryu.lib.packet import ether_types

# imports do usuario
from classes import Flow
from classes import PacketManager

class L2Switch(app_manager.RyuApp):

    # versoes do OpenFlow suportadas pelo Controller
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    # inicializicacao do controller
    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        # definicao das prioridades dos flows
        self.flow_priorities = {
            'default': 0 ,
            'flood':   1 ,
            'arp':     2
        }

    # rotina executado quando o controller para
    def close(self):
        print("\n\tL2Switch - STOPPED\n")

    # adiciona um flow ao roteador
    def _add_flow(self, dp, dst, port, priority=None):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        # install a flow to avoid packet_in next time
        print("\n   add flow  -  dst:  %s  - out:  %s" % (dst, port) )
        match = ofp_parser.OFPMatch(dl_dst=dst)
        actions = [ofp_parser.OFPActionOutput(port)]
        Flow(dp, match, actions, priority=priority).add()

    # rotina que adiciona os flows default aos roteadores
    def _add_default_flows(self, dp):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        # permita que o controller sempre receba pacotes ARP (e aprenda
        # o eth.src deles)
        priority = ofp.OFP_DEFAULT_PRIORITY + self.flow_priorities['arp']
        action = [ ofp_parser.OFPActionOutput( ofp.OFPP_CONTROLLER ) ]
        match = ofp_parser.OFPMatch(dl_type=ether_types.ETH_TYPE_ARP)
        Flow(dp, match, action, priority=priority).add()
        # permita que os pedidos de flood sejam direcionados automaticamente
        priority = ofp.OFP_DEFAULT_PRIORITY + self.flow_priorities['flood']
        action = [ ofp_parser.OFPActionOutput( ofp.OFPP_FLOOD ) ]
        match = ofp_parser.OFPMatch(dl_dst='ff:ff:ff:ff:ff:ff')
        Flow(dp, match, action, priority=priority).add()
        # leia o mapa de macs e faca o add flow do mapa
        priority = ofp.OFP_DEFAULT_PRIORITY + self.flow_priorities['default']
        mac_to_port = self.mac_to_port[dp.id]
        for hw in mac_to_port:
            port = mac_to_port[hw]
            self._add_flow(dp, hw, port, priority=priority)

    # esta funcao gerencia a conexao / desconexao do switch OF
    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def _switch_conn_handler(self, ev):
        dp = ev.dp
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        if ev.enter:
            # crie uma tabela de macs
            print('''\nSwitch \"%d\"  -  Criando tabela de macs ...\n''' % (dp.id))
            self.mac_to_port[dp.id] = {}
            mac_to_port = self.mac_to_port[dp.id]
            # sempre que receber um pacote direcionado pra uma das portas
            # do switch, redirecione para Network Stack interno (OVS Bridge)
            # do roteador
            for port in ev.ports:
                if port.port_no != ofp.OFPP_LOCAL:
                    mac_to_port[port.hw_addr] = ofp.OFPP_LOCAL
            # adicione as flows default do switch
            self._add_default_flows(dp)
        else:
            # delete tabela de macs da memoria
            print('''\nSwitch \"%d\"  -  Destruindo tabela de macs ...\n''' % (dp.id))
            del self.mac_to_port[dp.id]


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # leia a mensagem do packet_in
        buffer_id = msg.buffer_id
        total_len = msg.total_len
        in_port   = msg.in_port
        reason    = msg.reason
        data      = msg.data

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

        # BEGIN - modificacoes do switch em relacao ao hub

        pkt = PacketManager(data)
        eth = pkt.get_protocol(ethernet.ethernet)
        arp_pkt = pkt.get_protocol(arp.arp)

        # learn mac address to avoid FLOOD
        if eth.src not in mac_to_port:
            mac_to_port[eth.src] = in_port
            print("\n\tPACKET Received  -  Learning MAC ...")
            self._add_flow(dp, eth.src, in_port, priority=self.flow_priorities['default'])

        # find out the output port
        out_port = ofp.OFPP_FLOOD
        if eth.dst in mac_to_port:
            # set the proper out port to avoid flooding
            out_port = mac_to_port[eth.dst]
        elif eth.dst != 'ff:ff:ff:ff:ff:ff':
            # nothing to do, we dont have a instruction to proceed
            return

        # debugging
        print('''\n\n\t------------ PKT IN ( datapath: %d) ------------''' % (dp.id))
        print('''\t       Buffer_ID:  %s      Reason:  %s''' % (buffer_id, reason_txt ))
        print('''\t       In_Port:  %s''' % (in_port ))
        print('''\t       %s''' % (str(pkt).replace('\n', '\n\t       ') ))

        # define the aciton the switch will take
        actions = [ofp_parser.OFPActionOutput(out_port)]

        # END - modificacoes do switch em relacao ao hub

        print("\n\tPacket OUT  -  SEND")
        PacketManager.send(dp=dp, in_port=in_port, actions=actions, data=data)
