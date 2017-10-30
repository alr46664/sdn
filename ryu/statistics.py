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

 # funcao que converte das versoes OFP do RYU para as versoes reais
def _convert_ofp_versions(x):
    if   x == ofproto_v1_0.OFP_VERSION:
        return '1.0'
    elif x == ofproto_v1_2.OFP_VERSION:
        return '1.2'
    elif x == ofproto_v1_3.OFP_VERSION:
        return '1.3'
    elif x == ofproto_v1_4.OFP_VERSION:
        return '1.4'
    elif x == ofproto_v1_5.OFP_VERSION:
        return '1.5'
    return '???'

class Statistics(app_manager.RyuApp):

    # versoes do OpenFlow suportadas pelo Controller
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    # inicializicacao do controller
    def __init__(self, *args, **kwargs):
        super(RyuAbstractApp, self).__init__(*args, **kwargs)
        supported_versions = map(_convert_ofp_versions, self.OFP_VERSIONS)
        print('''

            Inicializando controller Ryu ...

            Versoes OFP Suportadas:
            %s

            ''' % ( supported_versions.__str__().center(22, ' ') ))

    # esta funcao gerencia a conexao / desconexao do switch OF
    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def _switch_conn_handler(self, event_dp):
        dp = event_dp.dp
        ofp_parser = dp.ofproto_parser
        if event_dp.enter:
            version = _convert_ofp_versions(dp.ofproto.OFP_VERSION)
            print('''
            -------------------------------------
            |                                   |
            |    Switch OpenFlow - Conectado    |
            |           ID: %16d|
            |                                   |
            |    Versao OFP (Negociada):        |
            |    %s         |
            |                                   |
            -------------------------------------
            ''' % ( dp.id, version.center(22, ' ') ))
            # envie solicitacao para obtencao de detalhes do switch
            req = ofp_parser.OFPDescStatsRequest(dp, 0)
            dp.send_msg(req)
        else:
            print('''
                ------------------------------------
                |                                  |
                |  Switch OpenFlow - DesConectado  |
                |                                  |
                ------------------------------------
                ''')
        # mostre as portas do switch detectadas pelo OpenFlow
        print('''
            Portas do Switch:
            ''')
        for port in event_dp.ports:
            print(port)

    # mostre os detalhes do switch conectado
    @set_ev_cls(ofp_event.EventOFPDescStatsReply, MAIN_DISPATCHER)
    def _desc_stats_reply_handler(self, ev):
        body = ev.msg.body
        print('''
            SN:            %s
            Manufacturer:  %s
            HW / SW:       %s %s
            ''' % ( body.serial_num, body.mfr_desc, body.hw_desc, body.sw_desc) )

    # handler da resposta da solicitacao de status agregado
    @set_ev_cls(ofp_event.EventOFPAggregateStatsReply, MAIN_DISPATCHER)
    def _aggregate_stats_reply_handler(self, ev):
        msg = ev.msg
        ofp = msg.datapath.ofproto
        # chame o handler
        for body in ev.msg.body:
            for stat in body:
                print('''
                    AggregateStats:
                    \tpacket_count: %d  byte_count: %d  flow_count: %d''' % (
                    stat.packet_count, stat.byte_count, stat.flow_count ))

    # handler da resposta da solicitacao de status agregado
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        msg = ev.msg
        ofp = msg.datapath.ofproto
        body = ev.msg.body
        # chame o handler
        flows = []
        for stat in body:
            flows.append('table_id=%s  match=%s  '
                         'duration_sec=%d  duration_nsec=%d  '
                         'priority=%d  '
                         'idle_timeout=%d  hard_timeout=%d  '
                         'cookie=%d  packet_count=%d  byte_count=%d  '
                         'actions=%s \n' %
                         (stat.table_id,
                          stat.duration_sec, stat.duration_nsec,
                          stat.priority,
                          stat.idle_timeout, stat.hard_timeout,
                          stat.cookie, stat.packet_count, stat.byte_count,
                          stat.match, stat.actions))
        print('''
            FlowStats:
            %s''' % flows)

    # handler do table stats
    @set_ev_cls(ofp_event.EventOFPTableStatsReply, MAIN_DISPATCHER)
    def _table_stats_reply_handler(self, ev):
        msg = ev.msg
        ofp = msg.datapath.ofproto
        body = ev.msg.body
        # chame o handler
        tables = []
        for stat in body:
            tables.append('table_id=%d  name=%s  wildcards=0x%02x  '
                          'max_entries=%d  active_count=%d  '
                          'lookup_count=%d  matched_count=%d \n' %
                          (stat.table_id, stat.name, stat.wildcards,
                           stat.max_entries, stat.active_count,
                           stat.lookup_count, stat.matched_count))
        print('''
            TableStats:
            %s''' % tables)

    # handler do port stats
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        msg = ev.msg
        ofp = msg.datapath.ofproto
        body = ev.msg.body
        # chame o handler
        ports = []
        for stat in body:
            ports.append('port_no=%d  '
                         'rx_packets=%d  tx_packets=%d '
                         'rx_bytes=%d  tx_bytes=%d '
                         'rx_dropped=%d  tx_dropped=%d '
                         'rx_errors=%d  tx_errors=%d '
                         'rx_frame_err=%d  rx_over_err=%d  rx_crc_err=%d '
                         'collisions=%d \n' %
                         (stat.port_no,
                          stat.rx_packets, stat.tx_packets,
                          stat.rx_bytes, stat.tx_bytes,
                          stat.rx_dropped, stat.tx_dropped,
                          stat.rx_errors, stat.tx_errors,
                          stat.rx_frame_err, stat.rx_over_err,
                          stat.rx_crc_err, stat.collisions))
        print('''
            PortStats:
            %s''' % ports)

    # handler do queue stats
    @set_ev_cls(ofp_event.EventOFPQueueStatsReply, MAIN_DISPATCHER)
    def _queue_stats_reply_handler(self, ev):
        msg = ev.msg
        ofp = msg.datapath.ofproto
        body = ev.msg.body
        # chame o handler
        queues = []
        for stat in body:
            queues.append('port_no=%d  queue_id=%d  '
                          'tx_bytes=%d  tx_packets=%d  tx_errors=%d  \n' %
                          (stat.port_no, stat.queue_id,
                           stat.tx_bytes, stat.tx_packets, stat.tx_errors))
        print('''
            QueueStats:
            %s''' % queues)

    # envie solicitacao de status agregado do switch
    def get_aggregate_stats(self, dp, match):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        req = ofp_parser.OFPAggregateStatsRequest(
            dp, 0, match, 0xff, ofp.OFPP_NONE)
        dp.send_msg(req)

    # pegue stats de um unico flow
    def get_flow_stats(self, dp, match):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        req = ofp_parser.OFPFlowStatsRequest(
            dp, 0, match, 0xff, ofp.OFPP_NONE)
        dp.send_msg(req)

    # pegue stats da table
    def get_table_stats(self, dp):
        ofp_parser = dp.ofproto_parser
        req = ofp_parser.OFPTableStatsRequest(dp, 0)
        dp.send_msg(req)

    # pegue stats da port
    def get_port_stats(self, dp, port):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        req = ofp_parser.OFPPortStatsRequest(dp, 0, port)
        dp.send_msg(req)

    # pegue stats da queue
    def get_queue_stats(self, dp, port):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        req = ofp_parser.OFPQueueStatsRequest(dp, 0, port, ofp.OFPQ_ALL)
        dp.send_msg(req)
