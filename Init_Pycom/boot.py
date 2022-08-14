""" Function definition for connecting different networks"""
#import urandom
import os
import sys
import struct
import socket
import logging
import timeit
# import ubinascii
# from network import WLAN
# from network import Sigfox
# from network import LTE
# from network import LoRa
#from umqtt import MQTTClient
# import urequests as requests
import _thread
# import machine
# from machine import UART
from mnm.multi_network_management import multi_network_management
from mnm.msgflow import MessageFlow
from mnm.network_algo import Network
# rtc = machine.RTC()
# Testing logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("BOOT")
# Utime

utime = os.utime
# UART Definitions
# uart = UART(1, 115200)                         # init with given baudrate
# uart.init(115200, bits=8, parity=None, stop=1) # init with given parameters
mnm = multi_network_management()




# Wifi_Creds
WIFI_SSID = "BTHub6-WK6Q"
WIFI_PASS = "9XGDxfLnPvEq"
# Lora OTAA Key
# create an OTAA authentication parameters
# APP_EUI = ubinascii.unhexlify('70B3D57ED0030B7E')
# APP_KEY = ubinascii.unhexlify('43FB05A51AA73EC05511F936279DEB4E')
MAX_LORA_PAYLOAD = 0
MAX_LORA_BANDWIDTH = 0


#The code is taken from https://docs.pycom.io/chapter/tutorials/all/wlan.html.
# wlan = WLAN(mode=WLAN.STA)
# sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
# #lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868,tx_power=14, sf=12)
# lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
# lte = LTE()

def uart_write(msg):
    """ Function to add ML and Newline as header """
    
    if msg.startswith("MFEA:"):
        log.info("MFEA Message sent at %s", rtc.now())
    # 5 == 4 for :ML:
    print(type(msg))
    base64_enc_msg = ubinascii.b2a_base64(msg)
    base64_enc_msg = base64_enc_msg.decode('utf-8')
    msg_len = len(base64_enc_msg)
    len_of_header = 5 + len(str(msg_len))
    uart_msg = ":ML:" + str(msg_len + len_of_header) + "," + base64_enc_msg + "\n"
    uart_msg = uart_msg.encode('utf-8')
    uart.write(uart_msg)


# A function has been defined to be called in the main file to make it shorter
def connect_wifi(ssid, passwifi):
    """ Connect WiFi using provided ssid, password"""

    log.debug("Trying to connect to %s", ssid)
    # wlan.antenna(WLAN.EXT_ANT)
    nets = wlan.scan()
    for net in nets:
        log.debug(net.ssid)
        if net.ssid == ssid:
            log.debug("Wi-Fi network found")
            wlan.connect(net.ssid, auth=(net.sec, passwifi), timeout=10000)
            while not wlan.isconnected():
                print('W', end='')
                utime.sleep(1)
                machine.idle() # save power while waiting
            log.debug('WLAN connection succeeded!')
            return True
    log.debug("network not found")
    return False

def connect_sigfox():
    """ Connect to SigFox and return sigfox and socket"""

# Create a Sigfox socket
    sock_sigfox = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
# make the socket blocking
    sock_sigfox.setblocking(True)
# Configure it as uplink
    sock_sigfox.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)
# send some data
#    sock_sigfox.send("Hello SigFox")
#    print("Message sent on Sigfox")
    return sock_sigfox

def connect_lora_otaa():
    """ Connect to LoRa and return lora and socket via OTAA auth method"""
    global MAX_LORA_BANDWIDTH
    global MAX_LORA_PAYLOAD
    lora.join(activation=LoRa.OTAA, auth=(APP_EUI, APP_KEY), timeout=0)

    # wait until the module has joined the network
    i = 1
    while not lora.has_joined():
        i = i + 1
        utime.sleep(2.5)
        print('L', end='')
        if i == 20:
            log.debug("Gave up on Lora; Network signal not strong")
            return None

    log.debug("Finally Joined")

# Print Stats
    sf = lora.sf()
    lb = lora.bandwidth()
    log.debug("Lora.bandwidth is %s", str(lb))
    log.debug("Lora.sf is %s", str(sf))
    log.debug("lora.coding_rate is %s", str(lora.coding_rate()))
    if sf == 7 and lb == 0:
        lora_max_bitrate = 5470
        lora_max_payload = 222
    elif sf == 8 and lb == 0:
        lora_max_bitrate = 3125
        lora_max_payload = 222
    elif sf == 9 and lb == 0:
        lora_max_bitrate = 1760
        lora_max_payload = 115
    elif sf == 10 and lb == 0:
        lora_max_bitrate = 980
        lora_max_payload = 51
    elif sf == 11 and lb == 0:
        lora_max_bitrate = 440
        lora_max_payload = 51
    elif sf == 12 and lb == 0:
        lora_max_bitrate = 250
        lora_max_payload = 51
    MAX_LORA_PAYLOAD = lora_max_payload
    MAX_LORA_BANDWIDTH = lora_max_bitrate

# create a LoRa socket
    sock_lora = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
    sock_lora.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
    sock_lora.setblocking(True)
# send some data
    sock_lora.send(bytes([0x01, 0x02, 0x03]))
# make the socket non-blocking
# (because if there's no data received it will block forever...)
    sock_lora.setblocking(False)

# get any data received (if any...)
    data = sock_lora.recv(64)
    log.debug(data)
    return sock_lora


def connect_lora_abp():
    """ Connect to LoRa and return lora and socket via ABP auth method"""
# create an ABP authentication params
    dev_addr = struct.unpack(">l", ubinascii.unhexlify('26001910'))[0]
    nwk_swkey = ubinascii.unhexlify('6AB31CFB360ACF58F327FC1CAD62F00C')
    app_swkey = ubinascii.unhexlify('84F85AB9B80943F7CF491D55EDEE1D56')

# join a network using ABP (Activation By Personalization)
    lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

# create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
    s.setblocking(True)

# send some data
    s.send(bytes([0x01, 0x02, 0x03]))

# make the socket non-blocking
# (because if there's no data received it will block forever...)
    s.setblocking(False)

# get any data received (if any...)
    data = s.recv(64)
    log.debug(data)

def read_uart():
    """ Function to read UART until newline or the length of message is reached """

# While waiting for the message with newline to fully arrive
    while True:
        data = ""
        size = len(data)

        while True:
            try:
                # Read UART
                byte = uart.readline()
                new_line = ["\n", "\r"]
                if byte is not None:
                    if byte not in new_line:
                        if len(byte) == 1:
                            ":".join("{:02x}".format(ord(c)) for c in str(byte))
                        byte = byte.decode('UTF-8')
                        data += byte
                # Check message starting with :ML: (Message Length)
                if data.startswith(':ML:'):
                #Setting ML length to be in format of :ML:500
                # Extract the message length
                    temp = data.split(",")
                    temp2 = temp[0].split(":")
                    msglen = int(temp2[2])
                    size = msglen
            except:
                log.debug("Len of byte is %s", str(len(byte)))
                log.debug("Troubling byte is %s", str(byte))
                log.debug("Keyboard Interrupt")
                raise

            if not data:
                log.debug("ERROR")
            # Newline terminates the read request
            if data.endswith("\n"):
                break
            # Sometimes a newline is missing at the end
            # If this round has the same data length as previous, we're done
            if size == len(data):
                break
            size = len(data)
        # Remove trailing newlines


        if data.startswith(':ML:') and data.endswith("\n"):
        #Setting ML length to be in format of :ML:500
        # Remove the header :ML: and send the actual message back
            temp = data.split(",", 1)
            data = temp[1]
            data = data.rstrip("\r\n")
            data = data.rstrip("\n")
        else:
            print("Something is wrong")
            print(data)
#        print("Final Message from read_uart is " + data)
        return data.encode("UTF-8")


def connect_uart(sock_lora, sock_sigfox):
    """ Connect to UART Pins P3/P4 and send data to the cloud"""
    while True:
        try:
            # Read UART continously, if any possible message call read_uart function
            if uart.any() != 0:
                uart_msg = read_uart()
                if uart_msg is not None:
                    uart_msg = uart_msg.decode("utf-8")
#                    print("UART Message Type is " + str(type(uart_msg)) + "and Message is" + str(uart_msg) + "!")
                    # Send the UART message to check_connection function with the lora and sigfox socket
                    if uart_msg.startswith("INFO:RE-ALLOC:ACCEPTED"):
                        # Ack message received from RPI, we can now clear list_old_allocations.
                        # As the messages already before this message would have been served using old Allocations
                        log.info("Re-alloc Accept message received at %s", rtc.now())
                        log.debug("Re-alloc ACK message received deleting old allocations")
                        mnm.list_old_allocations.clear()
                    else:
                        # Must contain the Message payload
                        check_connection(uart_msg, sock_lora, sock_sigfox)
        except:
            log.debug("Keyboard Interrupt")
            raise

def connect_nbiot():
    """ Connect to NB-IoT network"""
    lte.init()
    lte.attach(band=20, apn="pycom.io")
    while not lte.isattached():
        print('A', end='')
        utime.sleep(0.25)
    log.debug("LTE: Attached")
    lte.connect()       # start a data session and obtain an IP address
    while not lte.isconnected():
        print('C', end='')
        utime.sleep(0.25)
    log.debug("LTE: Connected")

def check_connection(msg_array, sock_lora, sock_sigfox):
    """ Check which networks are connected and send data via that network """
    # Figure out which Network Bin is allocated to the Message Flow
    try:
    # Splitting the message to get the flow name, crit_level and msg.
        temp_msg = msg_array.split(",")
        msgflow_name = temp_msg[0]
        msgflow_crit_level = temp_msg[1]
        msg = temp_msg[2]
        log.debug("%s, %s", msgflow_name, msgflow_crit_level)
        bin_name = mnm.get_network_bin(msgflow_name, int(msgflow_crit_level))
        log.debug("Check Network Bin: %s", str(bin_name or 'Not Allocated'))
    except:
        log.info("Message received is %s", msg_array)
    # If Message Flow has not been allocated, send error message message to RPi
    if bin_name is None:
        uart_write("ERROR:" + msgflow_name + ":" + "NOT_ALLOCATED")

    # Again as wifi disconnects, recheck
    connected_wifi = wlan.isconnected()
    if connected_wifi is False:
        connect_wifi(WIFI_SSID, WIFI_PASS)
        connected_wifi = wlan.isconnected()

#    connected_lte = lte.isconnected()
    connected_lte = False
    connected_lora = lora.has_joined()
    log.debug("Lora is %s | Wi-Fi is %s | LTE NB-IoT is %s", str(connected_lora), str(connected_wifi), str(connected_lte))

    # Check the allocated bin name and if the network interface is connected, send the message
    if bin_name == "Wi-Fi" and connected_wifi:
        ## Send data using WiFi
        log.debug("Data on WiFi")
        post_var(msg, "wifi", msgflow_name)
    elif bin_name == "LTE-M" and connected_lte:
        ## Send data using lte
        log.debug("Data on LTE")
        post_var(msg, "lte", msgflow_name)
    # Checking if Lora is connected + We have the socket instance
    elif bin_name == "LoRaWAN" and connected_lora and sock_lora is not None:
        ## Send data using lora, Trimming the payload as of now
        log.debug("Trying sending on Lora %s", str(type(sock_lora)))
        if len(msg) > MAX_LORA_PAYLOAD:
            msg = msg[:MAX_LORA_PAYLOAD]
        sock_lora.send(msg)
        ack_msg = "ACK:" + msgflow_name
        uart_write(ack_msg)
        log.debug("Data on Lora")
    # If allocated bin is Sigfox and we have the socket instance of sigfox
    elif bin_name == "SigFox" and sock_sigfox is not None:
        log.debug("Trying sending on Lora %s", str(type(sock_sigfox)))
        # Send only important data on SigFox (12bytes)
        if len(msg) > 12:
            # If data is greater than 12 bytes, trim it as of now
            msg = msg[:12]
        sock_sigfox.send(msg)
        log.debug("Data sent on SigFox")
        ack_msg = "ACK:" + msgflow_name
        uart_write(ack_msg)
    # Some interface is not connected or socket instance not founc
    else:
        uart_write("ERROR:" + msgflow_name + ":" + "NOT_DELIVERED")

# Sends the request. Please reference the REST API reference https://ubidots.com/docs/api/
def post_var(msg, medium, msgflow_name):
    """ Post the message via HTTP Post to the InfluxDB Server """
    try:
        url = "http://8.209.93.91:8080/"
        url = url + medium
        headers = {"X-Auth-Token": "FiPy", "Content-Type": "application/json"}
        if msg is not None:
            req = requests.post(url=url, headers=headers, data=msg)
            print(req.status_code)
            if int(req.status_code) == 200 or int(req.status_code) == 500:
                ack_msg = "ACK:" + msgflow_name
                uart_write(ack_msg)
            status_code = req.status_code
            req.close()
            return status_code
        log.debug("WTF: Error Message not sent")
    except:
        log.debug("Yahoo")
        raise
    return False

def define_msgflows():
    """ A function to define the Message Flows with MessageFlow(name, crit_level, payload, period) arguments """

#    MUL_CRIT_0 = 100000
#    MUL_CRIT_1 = 5000
    MUL_CRIT_0 = 1
    MUL_CRIT_1 = 1

    # MSG_FLOW Fall Detection with 3 criticality level 0, 1, 2 with payload size 1000, 40, 10 and payload interval 10, 20, 60 respectively.
    falld = MessageFlow("Fall Detection", 0, 1000 * MUL_CRIT_0, 10)
    falld.set_crit_level(1, 40 * MUL_CRIT_1, 20)
    falld.set_crit_level(2, 10, 60)

    # MSG_FLOW Heart Monitoring with 3 criticality level 0, 1, 2 with payload size 1000, 80 , 10 and payload interval 5, 10, 20 respectively.
    healthm = MessageFlow("Heart Monitoring", 0, 1000 * MUL_CRIT_0, 5)
    healthm.set_crit_level(1, 80 * MUL_CRIT_1, 10)
    healthm.set_crit_level(2, 10, 20)

    # MSG_FLOW Body Temperature with 2 criticality level 0, 1 with payload size 30, 10 and payload interval 30, 120 respectively.
    bodyt = MessageFlow("Body Temperature", 0, 30 * MUL_CRIT_0, 30)
    bodyt.set_crit_level(1, 10 * MUL_CRIT_1, 120)

    # MSG_FLOW Bedroom Sensor with 2 criticality level 0, 1 with payload size 40000, 10 and payload interval 10, 30 respectively.
    bedsens = MessageFlow("Bedroom Sensor", 0, 40000 * MUL_CRIT_0, 10)
    bedsens.set_crit_level(1, 10 * MUL_CRIT_1, 30)

    # MSG_FLOW Bathroom Sensor with 2 criticality level 0, 1 with payload size 80, 10 and payload interval 10, 30 respectively.
    bathsens = MessageFlow("Bathroom Sensor", 0, 80 * MUL_CRIT_0, 10)
    bathsens.set_crit_level(1, 10 * MUL_CRIT_1, 30)

    # MSG_FLOW Kitchen Sensor with 2 criticality level 0, 1 with payload size 40000, 10 and payload interval 10, 30 respectively.
    kitsens = MessageFlow("Kitchen Sensor", 0, 40000 * MUL_CRIT_0, 10)
    kitsens.set_crit_level(1, 10 * MUL_CRIT_1, 30)

    # MSG_FLOW Front Door with 2 criticality level 0, 1 with payload size 40000, 10 and payload interval 10, 30 respectively.
    frontsens = MessageFlow("Front Door Sensor", 0, 40000 * MUL_CRIT_0, 10)
    frontsens.set_crit_level(1, 10 * MUL_CRIT_1, 30)

    # MSG_FLOW Energy Usage with 1 criticality level 0 with payload size 40 and payload interval 3600 respectively.
    enermon = MessageFlow("Energy Usage", 0, 40 * MUL_CRIT_0, 3600)

## Defining Network Interface mnm is multi network management object and defined globally as of now ##
# Add the Message Flows
    mnm.add_msgflow(falld)
    mnm.add_msgflow(healthm)
    mnm.add_msgflow(bodyt)
    mnm.add_msgflow(bedsens)
    mnm.add_msgflow(bathsens)
    mnm.add_msgflow(kitsens)
    mnm.add_msgflow(frontsens)
    mnm.add_msgflow(enermon)

def define_networks():
    """ Define the Networks """

    enable_wlan = False
    enable_lora = True
    enable_sigfox = False
    enable_nbiot = False
    lora_sf = 7
    lora_lb = 0

    # Let's say Wi-Fi network  has 8000 bps bandwidth
    # Just because Wi-Fi disconnects sometimes, even it is present and connected
    wlan_available = True

    if enable_wlan:
        log.debug("Adding Wi-Fi to Network")
        # Defining the network, Refer network_algo.py / Network Class
        # Network takes Network_Name, Availablity, Bandwidth, Max Payload, Max number of messages
#        net_wifi = Network("Wi-Fi", True, 8000, -1, -1)
        net_wifi = Network("Wi-Fi", True, 750000, -1, -1)
        # Adding the network to the Network Bins
        mnm.add_network(net_wifi)
#     else:
#         # Trying WiFi one more time
#         connect_wifi(WIFI_SSID, WIFI_PASS)
#         if wlan.isconnected():
#             log.debug("Adding Wi-Fi to Network")
# #            net_wifi = Network("Wi-Fi", True, 8000, -1, -1)
#             net_wifi = Network("Wi-Fi", True, 750000, -1, -1)
#             mnm.add_network(net_wifi)
#         else:
#             # If we are unable to connect to Wi-Fi, then we switch to LTE
#             # As when both Wi-Fi and LTE are connected, it is difficult to find choose which interface the packet will go.
#             log.debug("Giving up WiFi")
#             wlan_available = False

    # Adding Lora to the Network
    # The concept here is if Lora is available, use LoRa
    # If Lora is not avaiable and the radio is free, use sigfox
    if enable_lora:
        log.debug("Adding LoRaWAN to Network")
#        print(str(MAX_LORA_PAYLOAD), str(MAX_LORA_BANDWIDTH))
        sf = lora_sf
        lb = lora_lb
        if sf == 7 and lb == 0:
            lora_max_bitrate = 5470
            lora_max_payload = 222
        elif sf == 8 and lb == 0:
            lora_max_bitrate = 3125
            lora_max_payload = 222
        elif sf == 9 and lb == 0:
            lora_max_bitrate = 1760
            lora_max_payload = 115
        elif sf == 10 and lb == 0:
            lora_max_bitrate = 980
            lora_max_payload = 51
        elif sf == 11 and lb == 0:
            lora_max_bitrate = 440
            lora_max_payload = 51
        elif sf == 12 and lb == 0:
            lora_max_bitrate = 250
            lora_max_payload = 51
        MAX_LORA_PAYLOAD = lora_max_payload
        MAX_LORA_BANDWIDTH = lora_max_bitrate

        net_lora = Network("LoRaWAN", True, MAX_LORA_BANDWIDTH, MAX_LORA_PAYLOAD, 144)
        mnm.add_network(net_lora)
    else:
        # Adding Sigfox to the network
        net_sigfox = Network("SigFox", True, 100, 12, 144)
        mnm.add_network(net_sigfox)

    # Adding LTE to the network only if Wi-Fi is not available because of the network interface
    if not enable_wlan and enable_nbiot:
        net_lte = Network("LTE-M", True, 55000, -1, -1)
        mnm.add_network(net_lte)


def check_allocations():
    """ Setting up the message flows and the networks """

    # Define the msgflows
    define_msgflows()
    # Define the Networks
    define_networks()

# Setting the parameters for Bin Packing Algo
    mnm.set_decreasing(False)
    mnm.set_best_fit()

# Perform the CABFInv Allocation
    mnm.perform_inverted_allocation()
    # print_all_allocation prints and create a dictionary new_alloc to be written on UART
    new_alloc = mnm.print_all_allocation()
    msgflow_alloc = "MFEA:" + str(new_alloc)
    msgflow_alloc_enc = msgflow_alloc.encode('UTF-8')
    print(msgflow_alloc)
#    uart_write(msgflow_alloc)

# Print Unallocated Message Flow Elements
    mnm.print_unallocated_elements()
    mnm.print_all_networkbins()
    log.info("Allocated Percentage is %s", str(mnm.get_allocated_percentage()))
    log.debug("Average Criticality is %s", str(mnm.get_avg_criticality()))


def test_reallocation():
    """ Funtion to test the reallocation setting the WiFi to be disabled """
    # Send the message to FiPy that we are reallocating the message flows, notify the Applications (Threads to stop the messages)
    uart_write("INFO:RE-ALLOC:INIT")
    log.info("Re-alloc INIT message sent at %s", rtc.now())
    # Simulating that the Wi-Fi is disconnected
    log.debug("Setting the WiFi bandwidth to 0")
    log.debug(mnm.list_elements)
    mnm.list_bins[0].get_network().set_bandwidth(0)
    bin_name = mnm.list_bins[0].get_network().get_name()
    print(bin_name)
    old_alloc = []
    # Trying to copy the allocations without the WiFi, have to do it differently because micropython copy doesn't allow copying objects
    for item in mnm.list_allocations:
        temp_name = item.get_network().get_name()
        if temp_name is not bin_name:
            print("Adding msgflow from " + temp_name)
            old_alloc.append(item)
    print("Old Allocations should be None atm")
    print(mnm.list_old_allocations)
    mnm.list_old_allocations = old_alloc[:]
    # Remove all the allocations
    mnm.list_allocations.clear()
    print("Old Allocations????")
    print(mnm.list_old_allocations)
    # CLear the list of criticalities
    mnm.list_criticalities.clear()
    # Redefine the list of criticalities
    mnm.list_criticalities = [None] * mnm.num_crit_levels
    mnm.list_unallocated_elements.clear()
    # Redefine the list_criticalities as list
    for i in range(0, mnm.num_crit_levels):
        mnm.list_criticalities[i] = []
    # We further have to remove all the elements from the bins!
    for j in range(0, len(mnm.list_bins)):
        ele = mnm.list_bins[j].remove_all_elements()
        # print("Elements in Bin " + mnm.list_bins[j].get_id())
        # print(ele)
        # for item in ele:
        #     mnm.list_bins[j].remove_element(item)
    for j in range(0, len(mnm.list_bins)):
        ele = mnm.list_bins[j].get_elements()
#        print("After Removing Elements in Bin " + mnm.list_bins[j].get_id())
#        print(ele)
#    print(mnm.list_elements)
    mnm.perform_inverted_allocation()
    new_alloc = mnm.print_all_allocation()
    msgflow_alloc = "MFEA:" + str(new_alloc)
    mnm.print_unallocated_elements()
    log.info("Allocated Percentage is %s", str(mnm.get_allocated_percentage()))
    log.info("Average Criticality is %s", str(mnm.get_avg_criticality()))
    uart_write(msgflow_alloc)



def main():
    """ Main function currently make calls to connect all networks and UART """
    ## Flush the uart
    # while uart.any():
    #     uart.readline()
    # print("Cleared the UART")
    # Connect to the Wi-Fi
    # connect_wifi(WIFI_SSID, WIFI_PASS)
    # Try to sync the time with NTP
    # rtc.ntp_sync("pool.ntp.org")
    # utime.timezone(3600)
    # utime.sleep(5)
    # rtc.ntp_sync("pool.ntp.org")
    # rtc.ntp_sync("pool.ntp.org")
    # rtc.ntp_sync("pool.ntp.org")
    # Connect to the lora and save the socket as sock_lora
    # sock_lora = connect_lora_otaa()
    # if sock_lora is None:
    #     log.debug("ERROR: Lora socket not returned")
    # sock_sigfox = connect_sigfox()
    # if sock_sigfox is None:
    #     log.debug("ERROR: Sigfox socket not returned")

    # # Although we connect the Wi-Fi, for some reason it gets disconnected, so just checking
    # if not wlan.isconnected():
    #     connect_wifi(WIFI_SSID, WIFI_PASS)
    # if wlan.isconnected():
    #     log.debug("Wi-Fi is connected")

    # Allocate the Message Flows defined in the function to the Network Bin
    #start_time = utime.ticks_ms()
    start_time = timeit.default_timer()
    check_allocations()
    #stop_time = utime.ticks_ms()
    stop_time = timeit.default_timer()
    realloc_time = stop_time - start_time
    print("\nAllocation Time is " + str(realloc_time))

    # Create a tuple and pass it to connect_uart function which checks for messages on UART
    # args_tuple = [sock_lora, sock_sigfox]
    # _thread.start_new_thread(connect_uart, args_tuple)

    # Just for debugging purposes? Is Wi-Fi still connected
    # if wlan.isconnected():
    #     log.debug("Wi-Fi is connected")
    # else:
    #     log.debug("Wi-Fi got disconnected")
    # log.debug("Everything is a thread")
    # # Testing the reallocation by setting Wi-Fi to zero.
#    test_reallocation()


if __name__ == "__main__":
    main()
