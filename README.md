# smartcity_multimode_networks

## Different message formats details

The FiPY generates the MFEA (Message Flow Element Allocation) message (a list of dict)

```json
"[{'PS': 40, 'N': 'LoRaWAN', 'PE': 3600, 'MF': 'Energy Usage', 'CL': 0}, {'PS': 30, 'N': 'LoRaWAN', 'PE': 30, 'MF': 'Body Temperature', 'CL': 0}, {'PS': 40000, 'N': 'LoRaWAN', 'PE': 10, 'MF': 'Front Door Sensor', 'CL': 0}, {'PS': 40000, 'N': 'Wi-Fi', 'PE': 10, 'MF': 'Kitchen Sensor', 'CL': 0}, {'PS': 80, 'N': 'LoRaWAN', 'PE': 10, 'MF': 'Bathroom Sensor', 'CL': 0}, {'PS': 40000, 'N': 'Wi-Fi', 'PE': 10, 'MF': 'Bedroom Sensor', 'CL': 0}, {'PS': 1000, 'N': 'LoRaWAN', 'PE': 10, 'MF': 'Fall Detection', 'CL': 0}, {'PS': 1000, 'N': 'LoRaWAN', 'PE': 5, 'MF': 'Heart Monitoring', 'CL': 0}]"
```

A sample dict is

```
{'PS': 40, 'N': 'LoRaWAN', 'PE': 3600, 'MF': 'Energy Usage', 'CL': 0}
```
where

- PS is Payload Size, 
- N is the Network, 
- PE is Period, 
- MF is Message Flow and 
- CL is Criticality Level.

We add a header `MFEA:` to the message and send it to UART for RPI to read

```
"MFEA:[{'PS': 40, 'N': 'LoRaWAN', 'PE': 3600, 'MF': 'Energy Usage', 'CL': 0}, {'PS': 30, 'N': 'LoRaWAN', 'PE': 30, 'MF': 'Body Temperature', 'CL': 0}, {'PS': 40000, 'N': 'LoRaWAN', 'PE': 10, 'MF': 'Front Door Sensor', 'CL': 0}, {'PS': 40000, 'N': 'Wi-Fi', 'PE': 10, 'MF': 'Kitchen Sensor', 'CL': 0}, {'PS': 80, 'N': 'LoRaWAN', 'PE': 10, 'MF': 'Bathroom Sensor', 'CL': 0}, {'PS': 40000, 'N': 'Wi-Fi', 'PE': 10, 'MF': 'Bedroom Sensor', 'CL': 0}, {'PS': 1000, 'N': 'LoRaWAN', 'PE': 10, 'MF': 'Fall Detection', 'CL': 0}, {'PS': 1000, 'N': 'LoRaWAN', 'PE': 5, 'MF': 'Heart Monitoring', 'CL': 0}]"
```

The [RPI Script](https://github.com/bitvijays/smartcity_multimode_networks/blob/algo-implementation-FiPy/RPI_Edge/cpu_temp_uart.py) reads the above message, take out each dict

```
{'PS': 40, 'N': 'LoRaWAN', 'PE': 3600, 'MF': 'Energy Usage', 'CL': 0}
```

and creates a thread to send the a message of size PS on the UART, sleeps for PE time.

Sample message on UART by a thread is in the format
```
"Message Flow Name, Criticality Level, Payload"
```
A example 
```
{"Energy Usage", 0, EnergyUsageEnergyUsage
```

FiPy on receiving the message, checks whether the Message Flow with the Criticality level has been allocated.

If not, it will send a error message to the RPI
```
"ERROR:Bedroom Sensor:NOT_ALLOCATED"
```

If it has been allocated, it will check whether the allocated network interface is connected and then send the message via that interface.

If any error is received, it will send 
```
"ERROR:Bedroom Sensor:NOT_DELIVERED"
```
If no error has been received, it will send
```
ACK:Energy Usage
```

The RPI creates a stats dictionary to store how many messages has been sent, ack received etc.
```
{'Energy Usage': {'sent': 1, 'recv': 1, 'error_na': 0}, 'Body Temperature': {'sent': 2, 'recv': 2, 'error_na': 0}, 'Front Door Sensor': {'sent': 2, 'recv': 2, 'error_na': 0}, 'Kitchen Sensor': {'sent': 2, 'recv': 2, 'error_na': 0}, 'Bathroom Sensor': {'sent': 2, 'recv': 2, 'error_na': 0}, 'Bedroom Sensor': {'sent': 2, 'recv': 2, 'error_na': 0}, 'Fall Detection': {'sent': 2, 'recv': 2, 'error_na': 0}, 'Heart Monitoring': {'sent': 2, 'recv': 2, 'error_na': 0}}
```

On the cloud, the cloud gets the data via HTTP POST, Lora/ Sigfox callbacks and store it into a file.


## How to run

`boot.py` in `Init_Pycom` is the main file that executes the multi-network ILP algorithim. The main function calls the `check_allocation` functions. `Check_allocations` function calls the `define_msgflows` function. `define_msgflows` function defines the message flow as defined in the paper. The function `define_msgflows_csv` read the message flows from the CSV file.

The `check_allocation` function then calls the `define_networks` function. As we are simulating the networks, the bandwidth of the different networks can be defined.