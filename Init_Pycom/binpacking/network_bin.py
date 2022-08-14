""" Class for implementing Network Bin, Basically tells what elements (msgflows)
    are fulfilled by this Network Bin, capacity of it """
from binpacking.exceptions.exceptions import BinFullException, DuplicateElementException
from binpacking.doublevaluesize import DoubleValueSize
from binpacking.message_flow_element import MessageFlowElement
class NetworkBin:
    """ Network Bin Class with add_element, remove_element, other functions"""
    def __init__(self, network):
        self.network = network
        self.allocated = []

    def get_network(self):
        """ Return the network instance """
        return self.network

    def add_element(self, element):
        """ Add a element (msgflow) to the allocated list of network """
        if element in self.allocated:
            is_duplicate = True
        else:
            is_duplicate = False
        # Check if element is already allocated to the Network Bin
        if is_duplicate:
            error_msg = "Network Bin " + str(self.get_id()) + " already contains the element " + str(element.get_id())
            print(error_msg)
            raise DuplicateElementException(error_msg)
        current_bin_free_space = self.get_free_space()
        current_bin_payload_size = self.get_payload_size()

        # Check if the Network Bin has enough free space for the element
        if element.fits_into(DoubleValueSize(current_bin_free_space), current_bin_payload_size) is None:
            error_msg = "Network Bin " + str(self.get_id()) + " is full. Can't add the element " + str(element.get_id())
            raise BinFullException(error_msg)
        else:
            self.allocated.append(element)

    def remove_element(self, element):
        """ Remove a element (msgflow) from the allocated list of network """
        self.allocated.remove(element)

    def remove_all_elements(self):
        """ Remove all elements (msgflow) from the allocated list of network """
        self.allocated.clear()

    def contains(self, element):
        """ Check whether a element is already allocated """
        return element in self.allocated

    def get_capacity(self):
        """ Get the current capacity of the network bin """
        return DoubleValueSize(self.network.get_bandwidth())

    def get_payload_size(self):
        """Get the current payload size of the network bin"""
        return DoubleValueSize(self.network.get_payload_size())

    def get_element_count(self):
        """ Return the number of elements (msgflow) assigned to the network """
        return len(self.allocated)

    def get_elements(self):
        """ Return the allocated elements """
        return self.allocated

    def get_fill_level(self):
        """ Return the fill level? """
        return 1 - self.get_capacity().calculate_percentage(self.get_free_space())

    def get_free_space(self):
        """ Return the free space in the Network Bin """
        current_bin_capacity = self.get_capacity()
        current_bin_allocated_size = self.get_allocated_size()
        return current_bin_capacity.subtract(current_bin_allocated_size)

    def get_id(self):
        """ Return the network bin name """
        return self.network.get_name()

    def get_allocated_size(self):
        """ Return the current allocated size of the Network Bin """
        usage = DoubleValueSize(0.0)
        for element in self.allocated:
            usage = DoubleValueSize(usage.add(element.get_size()))
        return usage

    def print_allocated(self):
        """ Print all the elements (msgflow) with their size """
        for element in self.allocated:
            print(element.get_id() + " " + element.get_size())
