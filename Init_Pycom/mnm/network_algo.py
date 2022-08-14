""" Class to define a network interface """
class Network:
    """ Class to define a network interface """
    max_payload = 0
    max_num_msg = 0
    privacy = 0
    name = ""
    bandwidth = 0
    bandwidth_ul = 0
    bandwidth_dl = 0
    available = False

    def __init__(self, name, available, bandwidth, max_payload, max_num_msg):
        """ Init with the name of the network, availability, bandwidth,
        max payload and num of msg """
        self.name = name
        self.available = available
        self.bandwidth = bandwidth
        self.max_payload = max_payload
        self.max_num_msg = max_num_msg

    def get_bandwidth(self):
        """ Return the bandwidth of the network interface """
        return self.bandwidth

    def get_payload_size(self):
        """ Return the max payload size of the network"""
        return self.max_payload

    def get_name(self):
        """ Return the name of the network interface """
        return self.name

    def set_bandwidth(self, bandwidth):
        """ Set the bandwidth of the network interface """
        self.bandwidth = bandwidth

    def get_available(self):
        """ Return the availability of the network interface
        Useful when Wi-Fi, LTE is disconnected """
        return self.available

    def set_available(self, available):
        """ Set the availability of the network interface
        Useful when Wi-Fi, LTE is connected """
        self.available = available
