#!/usr/bin/python

class Flow(object):
    """ gerencia eventos dos Flows """

    def __init__(self, dp, match, actions, buffer_id=None, priority=None, idle_timeout=0, hard_timeout=0):
        self.dp = dp
        self.ofp = dp.ofproto
        self.ofp_parser = dp.ofproto_parser

        if buffer_id == None:
            buffer_id = self.ofp.OFP_NO_BUFFER

        if priority == None:
            priority = self.ofp.OFP_DEFAULT_PRIORITY

        self.match = match
        self.actions = actions
        self.buffer_id = buffer_id
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout


    def _send(self, command):
        ''' envia Flow Mod pro roteador '''
        mod = self.ofp_parser.OFPFlowMod(
            datapath=self.dp, match=self.match, command=command,
            idle_timeout=self.idle_timeout, hard_timeout=self.hard_timeout,
            buffer_id=self.buffer_id, priority=self.priority, actions=self.actions)
        self.dp.send_msg(mod)


    def add(self):
        ''' permite que adicionemos um flow ao OFP switch '''
        self._send(self.ofp.OFPFC_ADD)


    def modify(self, strict=False):
        ''' permite que adicionemos um flow ao OFP switch '''
        command = self.ofp.OFPFC_MODIFY
        if strict:
            command = self.ofp.OFPFC_MODIFY_STRICT
        self._send(command)


    def delete(self):
        ''' permite que adicionemos um flow ao OFP switch '''
        command = self.ofp.OFPFC_DELETE
        if strict:
            command = self.ofp.OFPFC_DELETE_STRICT
        self._send(command)
