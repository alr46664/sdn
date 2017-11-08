#!/usr/bin/ryu-manager

from datetime import datetime

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

from classes import RepeatedTimer

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

    # intervalo entre solicitacoes de estatisticas (em sec)
    STAT_INTERVAL = 15*60

    # versoes do OpenFlow suportadas pelo Controller
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    # inicializicacao do controller
    def __init__(self, *args, **kwargs):
        super(Statistics, self).__init__(*args, **kwargs)
        # hash table dos switches conectados

        self.dps = {}
        supported_versions = map(_convert_ofp_versions, self.OFP_VERSIONS)
        print('''

            Inicializando controller Ryu ...

            Versoes OFP Suportadas:
            %s

            ''' % ( supported_versions.__str__().center(22, ' ') ))

    # este metodo sera chamado periodicamente (a cada STAT_INTERVAL secs)
    # de modo assincrono e em um thread a parte desse
    # para coletar as estatisticas do OpenFlow
    def get_stats(self, dp):
        curr_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        print("\n\n\t---------- Request Statistics ----------- \n")
        print("\t            %s" %( curr_time ))
        self.get_aggregate_stats(dp)
        self.get_flow_stats(dp)
        # self.get_table_stats(dp)
        self.get_port_stats(dp)
        # self.get_queue_stats(dp)

    # este metodo e chamado quando a classe e destruida
    def close(self):
        # pare todos os timers!
        for _, timer in self.dps.values():
            timer.stop()
        print("\n\tStatistics - STOPPED\n")

    # esta funcao gerencia a conexao / desconexao do switch OF
    @set_ev_cls(dpset.EventDP, MAIN_DISPATCHER)
    def _switch_conn_handler(self, event_dp):
        dp = event_dp.dp
        ofp_parser = dp.ofproto_parser
        dp_id = dp.id
        if event_dp.enter:
            self.dps[dp_id] = (dp, RepeatedTimer(Statistics.STAT_INTERVAL, self.get_stats, dp) )
            version = _convert_ofp_versions(dp.ofproto.OFP_VERSION)
            switch_id = "ID: " + str(dp_id)
            print('''
            -------------------------------------
            |                                   |
            |    Switch OpenFlow - Conectado    |
            |    %s         |
            |                                   |
            |    Versao OFP (Negociada):        |
            |    %s         |
            |                                   |
            -------------------------------------
            ''' % ( switch_id.center(22, ' '), version.center(22, ' ') ))
            # envie solicitacao para obtencao de detalhes do switch
            req = ofp_parser.OFPDescStatsRequest(dp, 0)
            dp.send_msg(req)
        else:
            # pare os timers quando o switch for desconectado
            if dp_id in self.dps:
                _, timer = self.dps.pop(dp_id)
                timer.stop()
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
            ''' % (
                body.serial_num, body.mfr_desc,
                body.hw_desc, body.sw_desc ))

    # handler da resposta da solicitacao de status agregado
    @set_ev_cls(ofp_event.EventOFPAggregateStatsReply, MAIN_DISPATCHER)
    def _aggregate_stats_reply_handler(self, ev):
        msg = ev.msg
        dp  = msg.datapath
        ofp = dp.ofproto
        # chame o handler
        # for body in ev.msg.body:
        for stat in ev.msg.body:
            print('''
            Aggregate Stats ( Datapath: %d ):
            \tpacket_count: %d
            \tbyte_count:   %d
            \tflow_count:   %d \n''' % (
                dp.id, stat.packet_count, stat.byte_count, stat.flow_count ))

    # handler da resposta da solicitacao de status agregado
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        msg = ev.msg
        dp  = msg.datapath
        ofp = dp.ofproto
        # chame o handler
        print('''
            Flow Stats ( Datapath: %d ):''' %(dp.id) )
        for stat in msg.body:
            print('''
            \ttable_id:      %s
            \tmatch:         %s
            \tduration_sec:  %d
            \tduration_nsec: %d
            \tcookie:        %d
            \tpriority:      %d
            \tidle_timeout:  %d
            \thard_timeout:  %d
            \tpacket_count:  %d
            \tbyte_count:    %d
            \tactions:       %s \n ''' % (
                  stat.table_id, stat.match,
                  stat.duration_sec, stat.duration_nsec,
                  stat.cookie, stat.priority,
                  stat.idle_timeout, stat.hard_timeout,
                  stat.packet_count, stat.byte_count,
                  stat.actions ))

    # handler do table stats
    @set_ev_cls(ofp_event.EventOFPTableStatsReply, MAIN_DISPATCHER)
    def _table_stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        # chame o handler
        print('''
            Table Stats ( Datapath: %d ):''' %(dp.id) )
        for stat in msg.body:
            print('''
            \ttable_id:      %d      name:          %s
            \twildcards:     0x%02x     max_entries:   %d
            \tactive_count:  %d      lookup_count:  %d
            \tmatched_count: %d \n ''' % (
               stat.table_id, stat.name, stat.wildcards,
               stat.max_entries, stat.active_count,
               stat.lookup_count, stat.matched_count ))


    # handler do port stats
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        # chame o handler
        print('''
            Port Stats ( Datapath: %d ):''' %(dp.id) )
        for stat in msg.body:
            print('''
            \t   port_no:   %d  collisions: %d
            \t--------------------------------
            \t     RX:                TX:
            \trx_packets:   %d   tx_packets: %d
            \trx_bytes:     %d   tx_bytes:   %d
            \trx_dropped:   %d   tx_dropped: %d
            \trx_errors:    %d   tx_errors:  %d
            \t    ______
            \t     ERR:
            \trx_frame_err: %d
            \trx_over_err:  %d
            \trx_crc_err:   %d \n''' % (
                stat.port_no, stat.collisions,
                stat.rx_packets, stat.tx_packets,
                stat.rx_bytes, stat.tx_bytes,
                stat.rx_dropped, stat.tx_dropped,
                stat.rx_errors, stat.tx_errors,
                stat.rx_frame_err, stat.rx_over_err,
                stat.rx_crc_err ) )


    # handler do queue stats
    @set_ev_cls(ofp_event.EventOFPQueueStatsReply, MAIN_DISPATCHER)
    def _queue_stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        # chame o handler
        print('''
            Queue Stats ( Datapath: %d ):''' %(dp.id) )
        for stat in msg.body:
            print('''
            \tport_no:    %d
            \tqueue_id:   %d
            \ttx_bytes:   %d
            \ttx_packets: %d
            \ttx_errors:  %d  \n''' % (
                stat.port_no, stat.queue_id,
                stat.tx_bytes, stat.tx_packets, stat.tx_errors ))

    # envie solicitacao de status agregado do switch
    def get_aggregate_stats(self, dp, match=None):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        # in_port=ofp.OFPP_ALL
        if match == None:
            match = ofp_parser.OFPMatch()

        req = ofp_parser.OFPAggregateStatsRequest(
            dp, 0, match, 0xff, ofp.OFPP_NONE)
        dp.send_msg(req)

    # pegue stats de um unico flow
    def get_flow_stats(self, dp, match=None):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        if match == None:
            match = ofp_parser.OFPMatch()

        req = ofp_parser.OFPFlowStatsRequest(
            dp, 0, match, 0xff, ofp.OFPP_NONE)
        dp.send_msg(req)

    # pegue stats da table
    def get_table_stats(self, dp):
        ofp_parser = dp.ofproto_parser
        req = ofp_parser.OFPTableStatsRequest(dp, 0)
        dp.send_msg(req)

    # pegue stats da port
    def get_port_stats(self, dp, port=None):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        if port == None:
            port = ofp.OFPP_LOCAL

        req = ofp_parser.OFPPortStatsRequest(dp, 0, port)
        dp.send_msg(req)

    # pegue stats da queue
    def get_queue_stats(self, dp, port=None):
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        if port == None:
            port = ofp.OFPP_LOCAL

        req = ofp_parser.OFPQueueStatsRequest(dp, 0, port, ofp.OFPQ_ALL)
        dp.send_msg(req)
