#!/usr/bin/python

class Flow(object):
    """ gerencia eventos dos Flows """

    def __init__(self, dp, match, actions, flags=None, cookie=0, priority=None, idle_timeout=0, hard_timeout=0):
        self.dp = dp
        self.ofp = dp.ofproto
        self.ofp_parser = dp.ofproto_parser

        if priority == None:
            priority = self.ofp.OFP_DEFAULT_PRIORITY

        if flags == None:
            flags = self.ofp.OFPFF_SEND_FLOW_REM

        self.match = match
        self.actions = actions
        self.flags = flags
        self.cookie = cookie
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout


    def _send(self, command):
        ''' envia Flow Mod pro roteador '''
        mod = self.ofp_parser.OFPFlowMod(
            datapath=self.dp, command=command, match=self.match,  priority=self.priority,
            actions=self.actions, idle_timeout=self.idle_timeout, hard_timeout=self.hard_timeout,
            flags=self.flags, cookie=self.cookie)
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


    def delete(self, strict=False):
        ''' permite que adicionemos um flow ao OFP switch '''
        command = self.ofp.OFPFC_DELETE
        if strict:
            command = self.ofp.OFPFC_DELETE_STRICT
        self._send(command)
