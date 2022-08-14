""" Class to store a list of networks, msgflows and allocations """
import copy
import logging
from mnm.msgflow import MessageFlow
from mnm.network_algo import Network
from mnm.allocation import Allocation
#from multi_network_management import multi_network_management
from binpacking.message_flow_element import MessageFlowElement
from binpacking.network_bin import NetworkBin
from binpacking.doublevaluesize import DoubleValueSize
from binpacking.exceptions.exceptions import BinFullException, DuplicateElementException
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("MNM")

class multi_network_management():
    """ Class to store a list of networks, msgflows and allocations """
    # Multi Network Management
    num_crit_levels = 6
    list_networks = []
    list_msgflows = []
    list_allocations = []
    # List to store old still valid allocations until new reallocations are setup
    # so that we can serve msgflows which are not affected.
    list_old_allocations = []
    # Utilisation based MultiNetwork Mangement
    list_elements = []
    list_elements_original = []
    list_unallocated_elements = []
    list_bins = []
    list_criticalities = [None] * num_crit_levels
    decreasing = False
    highest = False
    best = False
    worst = False
    first = False

    for i in range(0, num_crit_levels):
        list_criticalities[i] = []

    def __init__(self):
        """ Initialise the Multi Network Management class """
        self.set_best_fit()
        self.set_highest(True)
        self.set_decreasing(True)


    def mf_allocate(self, msgflow, network, critlevel):
        """ Allocate a msgflow of a certain criticality to a network """
        # Deallocate if existing
        self.mf_deallocate(msgflow)
        # Append to the list of allocation
        self.list_allocations.append(Allocation(msgflow, network, critlevel))


    def mf_deallocate(self, msgflow):
        """ De-allocate a msgflow if it is allocated """
        # Find the old allocation
        old_alloc = self.get_allocation_by_msgflow(msgflow)

        # If found, delete it from the list
        if old_alloc is not None:
   #         print("Old allocation found")
            self.list_allocations.remove(old_alloc)

    def allocate(self, mfe, network):
        """ Allocate the MFE to the network """
        network.add_element(mfe)
        self.mf_allocate(mfe.get_message_flow(), network.get_network(), mfe.get_allocated_crit_level())
#        print("Allocated " + mfe.get_id() + " of criticality level " + str(mfe.get_allocated_crit_level()) + " in to " + network.get_id())

    def deallocate(self, mfe):
        """ De-allocate the MFE if it's allocated """
        network = self.get_bin(mfe)
        if network is not None:
            network.remove_element(mfe)
            self.mf_deallocate(mfe.get_message_flow())

    def get_bin(self, mfe):
        """ Return the Network Bin """
        for iter1 in self.list_bins:
            if iter1.contains(mfe):
                return iter1
        return None


    def get_allocation_by_msgflow(self, msgflow):
        """ Find the msgflow allocation in the list list_allocation """
        for i in self.list_allocations:
            if i.get_flow() == msgflow:
                return i
        return None

    def print_all_allocation(self):
        """ Print all the allocated msgflows """
        list_alloc = []
        log.info("Allocated MFE:")
        for i in self.list_allocations:
            list_alloc.append(i.to_string())

        print("\n")            
        log.info("MFEA Message:")
#        log.info(list_alloc)

        for j in list_alloc:
            log.info(j)
        return list_alloc

    def add_msgflow(self, msgflow):
        """ Add msgflow in the list_msgflow and elements based on criticality"""
        self.list_msgflows.append(msgflow)

        if self.highest:
            #print(msgflow.get_name() + str(msgflow.get_highest_criticality()))
            mfe = MessageFlowElement(msgflow, msgflow.get_highest_criticality())
            self.list_elements.append(mfe)
            self.list_elements_original.append(mfe)
        else:
            mfe = MessageFlowElement(msgflow, msgflow.get_lowest_criticality())
            self.list_elements.append(mfe)
            self.list_elements_original.append(mfe)

    def add_network(self, network):
        """ Add the network to list_networks and list_bins """
        self.list_networks.append(network)
        # Create a instance of Network Bin and append to the list_bins
        self.list_bins.append(NetworkBin(network))

    def get_largest_bin(self):
        """ Find the network bin with the largest capacity (currently bandwidth) """
        largest = None
        iter_list_bins = iter(self.list_bins)
        for i in iter_list_bins:
            current_bin = i
            #print(current_bin.get_id())
            if largest is None:
                largest = current_bin
            elif largest.get_capacity().compare_to(current_bin.get_capacity()) < 0:
                largest = current_bin
#        print("Largest Bin is " + largest.get_id())
        return largest

    def perform_inverted_allocation(self):
        """ Criticality aware algo """
        all_success = True

        ## Populate all the criticalitiy list.
        ## Basically, if we have 5 critical level, we have a list of 5 elements
        # where wach element is another list of MFE of that critical level
        self.populate_criticality_lists()

        # Loop thru all the list of critical levels from High to Low 5 - > 0
        for i in range(len(self.list_criticalities) - 1, -1, -1):
            # Get all the allocated elements from all the network bins
            list_allocated = self.get_all_allocated_elements()
            log.debug("Allocated at criticality level %s", str(i +1))
            for item in list_allocated:
                log.debug("%s %s", str(i+1), item.get_id())

            # Sort the allocated list of MFE by bandwidth utilisation
            self.sort_mfe_by_bandwidth_utilisation(list_allocated, not self.decreasing)

            # Iterating the MFE list of a certain critical level
            iter1_loop = list(self.list_criticalities[i])
            iter1_result = list(self.list_criticalities[i])

            log.debug("Current MFE at criticality level %s", str(i))
            for k in iter1_loop:
                log.debug(k.get_message_flow().get_name())
            #for j in iter1:
            for j in iter1_loop:
                temp_msgflow = j.get_message_flow()
                temp_msgflow_name = temp_msgflow.get_name()
                # If the MFE is already allocated remove it from the list
                if self.is_allocated(temp_msgflow):
#                    print("Removing " + temp_msgflow_name + " of criticality level " + str(i+1))
                    iter1_result.remove(j)

            # Assigned the MFE elements of a certain critical level
            self.list_elements = iter1_result

            all_success = (self.perform_allocation() or all_success)

            # Message Flow Element
            for mfe in list_allocated:
#                print (mfe.get_id())
                if mfe.get_message_flow().has_criticality(i) and mfe.get_allocated_crit_level() > i:
                    old_crit_level = mfe.get_allocated_crit_level()
                    self.deallocate(mfe)

                    mfe.set_allocated_crit_level(i)
                    success = self.perform_allocation_step(mfe)
#                    print("upgrade attempt: " + mfe.get_id() + " " + str(old_crit_level) + " -> " + str(i))
                    if success:
                        log.debug("upgrade success: " + mfe.get_id() + " " + str(old_crit_level) + " -> " + str(i))
                    else:
#                        print("upgrade failed -- rollback: " + mfe.get_id() + " " + str(old_crit_level) + " <- " + str(i))
                        mfe.set_allocated_crit_level(old_crit_level)
                        success = self.perform_allocation_step(mfe)
                        if not success:
                            log.debug("Critical Error: unsuccessful rollback of criticality-aware allocation")

        return all_success

        #for i in range(0, len(self.list_criticalities)):
        #    print("New Criticality list " + str(i) + " has ")
        #    for j in range(0, len(self.list_criticalities[i])):
        #        print(self.list_criticalities[i][j].get_id())

    def populate_criticality_lists(self):
        """ Populate all the msgflow list - criticality wise """
        # Read all the elements in list_elements (contains msgflows

        for msgflow in self.list_elements_original:
            #print("MSGFLOW: " + msgflow.to_string())
            # Read all the msgflws, check all criticalties
            mfe = msgflow
            mf = mfe.get_message_flow()
            for i in range(0, len(self.list_criticalities)):
                #If criticality exists add it to the list.
                # Ideally, this would be sorting all the criticality of 0, 1, 2 of all flows
                if mf.has_criticality(i):
                    self.list_criticalities[i].append(mfe)

    #    for i in range(0, len(self.list_criticalities)):
    #        print("Criticality list " + str(i) + " has ")
    #        for j in range(0, len(self.list_criticalities[i])):
    #            print(self.list_criticalities[i][j].get_id())

    def get_all_allocated_elements(self):
        """ Get all allocated items for the network bins """
        allocated_elements = []
        for bins in self.list_bins:
            allocated_elements.extend(bins.get_elements())
        return allocated_elements

    def sort_mfe_by_bandwidth_utilisation(self, list_sort, asc_or_dsc):
        """ Sort the list of MFE by bandwidth utilisation """
        reverse_temp = not asc_or_dsc
        list_sort.sort(reverse=reverse_temp, key=self.myfunc)
#        print("Sorted List:")
#        for j in list_sort:
#            print(j.to_string())

    def myfunc(self, mfe):
        """ Comparator function for sorting """
        temp = mfe.get_size()
        temp2 = temp.get_value()
        return temp2

    def is_allocated(self, msgflow):
        """ Check if the msgflow is allocated or not
        Calls get_allocation function from Allocation Class """
        current = self.get_allocation(msgflow)
        if current is None:
            return False
        return True

    def get_allocation(self, msgflow):
        """ Return whether the msgflow is allocated or not """
        str_temp = "Checking if " + msgflow.get_name() + " is allocated"
        for i in range(0, len(self.list_allocations)):
            if self.list_allocations[i].get_flow() == msgflow:
#                print(str_temp + ": Yes")
                return self.list_allocations[i]
#        print(str_temp + ": No")
        return None

    def is_in_list_unallocated(self, mfe):
        """ Check if the mfe is present in the list_unalloacted_elements or not """
        for item in self.list_unallocated_elements:
            if mfe.allocated_crit_level == item.allocated_crit_level and mfe.get_message_flow().get_name() == item.get_message_flow().get_name():
                return True
        return False

    def perform_allocation(self):
        """ Perform the allocation of the elements """
        if self.decreasing:
            # Sort the allocated list of MFE by bandwidth utilisation
            self.sort_mfe_by_bandwidth_utilisation(self.list_elements, not self.decreasing)

        for element in self.list_elements:
            self.perform_allocation_step(element)

        # Check if the list of unallocated_elements empty.
        if self.list_unallocated_elements:
            return False
        return True

    def perform_allocation_step(self, element):
        """ Perform the allocation step """

        # Get the largest bin capacity
        bin_capacity = self.get_largest_bin().get_capacity()
        bin_payload_size = self.get_largest_bin().get_payload_size()
        
        # Check if the elements fits into the Network bin
        if not element.fits_into(bin_capacity, bin_payload_size):
            log.debug("Element %s doesn't fit in to Network Bin %s", element.get_id(), self.get_largest_bin().get_id())
            # Check if the element is present in list_unallocated_elements; If present don't add
            if not self.is_in_list_unallocated(element):
#                self.list_unallocated_elements.append(copy.copy(element))
                self.list_unallocated_elements.append(element)

        else:
            current_bin = None
            matching_bin = None
            largest_space = DoubleValueSize(0.0)
            # Start using the largest
            lowest_space = bin_capacity

            # For each existing bin
            for item_bin in self.list_bins:
                current_bin = item_bin
                current_free_space = DoubleValueSize(current_bin.get_free_space())

                # Worst Fit
                if self.worst:
                    # Current Free space is the largest and elements fits the bin
                    if element.fits_into(current_free_space, bin_payload_size) and current_free_space.compare_to(largest_space) > 0:
                        largest_space = current_free_space
                        matching_bin = current_bin
                # Best Fit
                elif self.best:
                    if element.fits_into(current_free_space, bin_payload_size) and current_free_space.compare_to(lowest_space) <= 0:
                        lowest_space = current_free_space
                        matching_bin = current_bin
                # First Fit
                elif self.first:
                    if matching_bin is None and element.fits_into(current_free_space, bin_payload_size):
                        matching_bin = current_bin
                else:
                    if element.fits_into(current_free_space, bin_payload_size):
                        matching_bin = current_bin

            # Element doesn't fit into any bin
            if ((matching_bin is None) or not element.fits_into( DoubleValueSize(matching_bin.get_free_space()), bin_payload_size)):
                if not self.is_in_list_unallocated(element):
#                    self.list_unallocated_elements.append(copy.copy(element))
                    self.list_unallocated_elements.append(element)
                    # temp_list = []
                    # temp_list.append(element)
                    # self.list_unallocated_elements.extend(temp_list)
            else:
                try:
                    mfe = element
                    nb = matching_bin
                    log.debug("Trying allocating " + mfe.get_id() + " of criticality level " + str(mfe.get_allocated_crit_level()) + " in to " + nb.get_id())
                    self.allocate(mfe, nb)
                    return True

                except BinFullException as Error:
                    log.debug("INFO: Network Bin is full")
                    return False
                except DuplicateElementException as Error:
                    log.debug("INFO: Duplicate Element")
                    log.error(Error)
                    return False

        return False

    def print_unallocated_elements(self):
        """ Print Unallocated MFE """

        print("\n")
        log.info("Un-allocated MFE:")
        for mfe in self.list_unallocated_elements:
            log.info(mfe.to_string())

    def set_first_fit(self):
        """ Set the First fit to True """
        self.first = True
        self.worst = False
        self.best = False

    def set_best_fit(self):
        """ Set the Best fit to True """
        self.first = False
        self.worst = False
        self.best = True

    def set_worst_fit(self):
        """ Set the Worst fit to True """
        self.first = False
        self.worst = True
        self.best = False


    def set_highest(self, value):
        """ Set the highest to the value """
        self.highest = value

    def set_decreasing(self, value):
        """ Set the decreasing to the value """
        self.decreasing = value

    def get_allocated_percentage(self):
        """ Return the allocated percentage """
        total = len(self.list_msgflows)
        allocated = len(self.list_allocations)
        res = (allocated/total) * 100
        return res

    def get_avg_criticality(self):
        """ Return the average criticality """
        total_crit = 0
        for alloc in self.list_allocations:
            total_crit = total_crit + alloc.get_crit_level()
        result = float(total_crit)/ float((len(self.list_allocations)))
        return result

    def get_network_bin(self, msgflow_name, msgflow_crit_level):
        # If the reallocation has happened, the list_old_allocations will be valid for short amount of time
        for item in self.list_old_allocations:
            log.info("Item found in Old Allocations")
            log.debug("Testing " + msgflow_name + " with " + str(msgflow_crit_level) + " against " + item.flow.get_name() + " " + str(item.get_crit_level()))
            if item.flow.get_name() == msgflow_name and item.get_crit_level() == msgflow_crit_level:
                return item.net.get_name()

        # Check in the new allocations table: This way we ensure that message flows which are already written in UART, get delivered.
        for item in self.list_allocations:
            log.debug("Item found in New Allocations")
            log.debug("Testing " + msgflow_name + " with " + str(msgflow_crit_level) + " against " + item.flow.get_name() + " " + str(item.get_crit_level()))
            if item.flow.get_name() == msgflow_name and item.get_crit_level() == msgflow_crit_level:
                return item.net.get_name()
        # If not found, probably the msg flow is not allocated.
        return None

    def print_all_networkbins(self):
        print("\n")
        log.info("Current Network Bins are")
        for item in self.list_bins:
            name = item.get_id()
            bandwidth = item.get_network().get_bandwidth()
            log.info("%s with a bandwidth of %s bps", name, str(bandwidth))
