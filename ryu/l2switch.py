#!/usr/bin/ryu-manager

# pacote do APP principal Ryu
from ryu.base import app_manager
# pacotes que gerenciam os eventos
from ryu.controller import dpset, ofp_event
from ryu.controller.handler import set_ev_cls, HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER
# pacotes que gerenciam os protocolos OpenFlow (1.0 - 1.5)
from ryu.ofproto import ofproto_v1_0, ofproto_v1_2, ofproto_v1_3, ofproto_v1_4, ofproto_v1_5
# gerencimento de pacotes
from ryu.lib import mac
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
        # definicao do timeout para esquecer os macs
        self.mac_timeout = 10

    # rotina executado quando o controller para
    def close(self):
        print("\n\tL2Switch - STOPPED\n")


    def _add_mac(self, dp, hw, port, idle_timeout=None):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        mac_to_port = self.mac_to_port[dp.id]

        if (idle_timeout == None):
            idle_timeout = self.mac_timeout

        # se nao houver alteracoes na porta do mac, nao faca nada!
        if hw in mac_to_port and mac_to_port[hw] == port:
            return

        # aprenda a porta
        mac_to_port[hw] = port

        # mande o flow
        match = ofp_parser.OFPMatch(dl_dst=hw)
        actions = [ofp_parser.OFPActionOutput(port)]
        flow = Flow(dp, match, actions, idle_timeout=idle_timeout)
        flow.add()
        print("\n   add flow ( dp: %d )  -  dst:  %s  - out:  %s" % (dp.id, hw, port) )


    # rotina que adiciona os flows default aos roteadores
    def _add_default_flows(self, dp, ports):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # permita que o controller sempre receba pacotes ARP (e aprenda
        # o eth.src deles)
        priority = ofp.OFP_DEFAULT_PRIORITY + self.flow_priorities['arp']
        action = [ ofp_parser.OFPActionOutput( ofp.OFPP_CONTROLLER ) ]
        match = ofp_parser.OFPMatch(dl_type=ether_types.ETH_TYPE_ARP)
        Flow(dp, match, action, priority=priority).add()
        print("\n   add flow  -  ARPs => Controller ... " )

        # permita que os pedidos de flood sejam direcionados automaticamente
        priority = ofp.OFP_DEFAULT_PRIORITY + self.flow_priorities['flood']
        action = [ ofp_parser.OFPActionOutput( ofp.OFPP_FLOOD ) ]
        match = ofp_parser.OFPMatch(dl_dst='ff:ff:ff:ff:ff:ff')
        Flow(dp, match, action, priority=priority).add()
        print("\n   add flow  -  MAC FLOOD => Controller ... " )

        # sempre que receber um pacote direcionado pra uma das portas
        # do switch, redirecione para Network Stack interno (OVS Bridge)
        # do roteador
        priority = ofp.OFP_DEFAULT_PRIORITY + self.flow_priorities['default']
        for port in ports:
            if port.port_no != ofp.OFPP_LOCAL:
                self._add_mac(dp=dp, hw=port.hw_addr, port=ofp.OFPP_LOCAL, idle_timeout=0)


    # esta funcao gerencia a conexao / desconexao do switch OF
    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def _switch_conn_handler(self, ev):
        dp = ev.dp
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        if ev.enter:
            # crie uma tabela de macs
            print('''\nSwitch \"%d\"  -  Criando tabela de macs ...''' % (dp.id))
            self.mac_to_port[dp.id] = {}
            # adicione as flows default do switch
            self._add_default_flows(dp, ev.ports)
        else:
            # delete tabela de macs da memoria
            print('''\nSwitch \"%d\"  -  Destruindo tabela de macs ...''' % (dp.id))
            del self.mac_to_port[dp.id]


    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        if msg.reason == ofp.OFPRR_IDLE_TIMEOUT:
            reason = 'IDLE TIMEOUT'
        elif msg.reason == ofp.OFPRR_HARD_TIMEOUT:
            reason = 'HARD TIMEOUT'
        elif msg.reason == ofp.OFPRR_DELETE:
            reason = 'DELETE'
        elif msg.reason == ofp.OFPRR_GROUP_DELETE:
            reason = 'GROUP DELETE'
        else:
            reason = 'Unknown'

        mac_to_port = self.mac_to_port[dp.id]
        eth_dst = mac.haddr_to_str(msg.match.dl_dst)

        print("\n\t------------ FLOW REMOVED ( datapath: %d ) ------------" % (dp.id))
        if eth_dst in mac_to_port and msg.reason == ofp.OFPRR_IDLE_TIMEOUT:
            del mac_to_port[eth_dst]
            print("\t       MAC:  %s  -  Expirado" % ( eth_dst ))
        else:
            print("\t       Reason:  \"%s\"" % ( reason ))
            print("\t       Match:  \"%s\"" % ( msg.match ))
            print("\t       Cookie:  %d    Priority:  %d " % ( msg.cookie, msg.priority ))
            print("\t       Duration:  %d s    Idle Timeout:  %d" % ( msg.duration_sec,  msg.idle_timeout ))
            print("\t       Pkt Count:  %d    Byte Count:  %d" % ( msg.packet_count,  msg.byte_count ))


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
        self._add_mac(dp, hw=eth.src, port=in_port)

        # find out the output port
        out_port = ofp.OFPP_FLOOD
        if eth.dst in mac_to_port:
            # set the proper out port to avoid flooding
            out_port = mac_to_port[eth.dst]
        elif eth.dst != 'ff:ff:ff:ff:ff:ff':
            # nothing to do, we dont have a instruction to proceed with
            return

        # debugging
        print('''\n\n\t------------ PKT IN ( datapath: %d ) ------------''' % (dp.id))
        print('''\t       Buffer_ID:  %s      Reason:  %s''' % (buffer_id, reason_txt ))
        print('''\t       In_Port:  %s''' % (in_port ))
        print('''\t       %s''' % (str(pkt).replace('\n', '\n\t       ') ))

        # define the aciton the switch will take
        actions = [ofp_parser.OFPActionOutput(out_port)]

        # END - modificacoes do switch em relacao ao hub

        PacketManager.send(dp=dp, in_port=in_port, actions=actions, data=data)
        print("\n\t       PKT  -  SEND")


        @set_ev_cls(ofp_event.EventOFPErrorMsg, [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
        def _error_handler(self, ev):
            msg = ev.msg
            dp = msg.datapath
            ofp = dp.ofproto
            ofp_parser = dp.ofproto_parser

            if msg.type == ofp.OFPET_HELLO_FAILED:
                reason = "Hello protocol failed"
            elif msg.type == ofp.OFPET_BAD_REQUEST:
                reason = "Request was not understood"
            elif msg.type == ofp.OFPET_BAD_ACTION:
                reason = "Error in action description"
            elif msg.type == ofp.OFPET_FLOW_MOD_FAILED:
                reason = "Problem modifying flow entry"
            elif msg.type == ofp.OFPET_PORT_MOD_FAILED:
                reason = "OFPT_PORT_MOD failed"
            elif msg.type == ofp.OFPET_QUEUE_OP_FAILED:
                reason =  "Queue operation failed"
            else:
                reason = ("Undefined \"%d\"" % (msg.type))

            print("\n\t------------ ERROR ( datapath: %d ) ------------" % (dp.id))
            print("\t       Reason:  \"%s\"    Code=0x%02x " % ( reason, msg.code ))
            print("\t       Msg:  %s" % ( utils.hex_array(msg.data) ))
