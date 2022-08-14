""" MessageFlow Element is just an element which can be assigned to Network Bin"""
#from binpacking.doublevaluesize import DoubleValueSize
from mnm.msgflow import MessageFlow
from .doublevaluesize import DoubleValueSize


class MessageFlowElement:
    """ Class MessageFlowElement to store msgflow as an Element """

    def __init__(self, msgflow, crit_level):
        """ Defined a msgflow with assigned crit_level """
        self.msgflow = msgflow
        self.allocated_crit_level = crit_level

    def get_message_flow(self):
        """ Return the msgflow """
        return self.msgflow

    def fits_into(self, network_bandwidth_size, network_payload_size):
        """ Return True if the Msgflow element fits into the Bin?? """
        if (self.get_size().compare_to(network_bandwidth_size) <= 0) and (self.get_payload_size().compare_to(network_payload_size) <= 0):
            return True
        return False

    def get_id(self):
        """ Return the msgflow name """
        return self.msgflow.get_name()

    def get_size(self):
        """ Return the size of the MsgFlow """
        mfe_bandwidth_utilisation = self.msgflow.get_bandwidth_utilisation(self.allocated_crit_level)
        return DoubleValueSize(mfe_bandwidth_utilisation)

    def get_payload_size(self):
        """ Return the payload size of the MsgFlow """
        mfe_payload_size = self.msgflow.get_payload(self.allocated_crit_level)
        return DoubleValueSize(mfe_payload_size)

    def get_allocated_crit_level(self):
        """ Return the allocated criticality level """
        return self.allocated_crit_level

    def set_allocated_crit_level(self, allocated_crit_level):
        """ Set the allocated criticality level """
        self.allocated_crit_level = allocated_crit_level

    def to_string(self):
        """ ???? """
        return self.msgflow.get_name() + " with criticality level " + str(self.allocated_crit_level) + " with Bandwidth Utilisation of " + str(self.get_size().get_value()) + " and PS: " + str(self.get_payload_size().get_value())
