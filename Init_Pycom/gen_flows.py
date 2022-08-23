""" Functions to generate message flows"""
import numpy as np
import pandas as pd

def print_csv(lst_all_mf):
    """ Print the list of list containing MFName, Criticality level, Payload Size, Interval to CSV"""

    data_frame = pd.DataFrame(lst_all_mf, columns=['MFName', 'CriticalityLevel', 'PayloadSize', 'PayloadInterval'])
    data_frame.to_csv('MsgFlows.csv', index=False)


def gen_mf():
    """ Generate Message Flows randomly with for criticality level 1 PS between 10-1000, for criticality level 2, PS 0-100 and for criticality level 3 PS is 0-10 """
    lst_all_mf = []


    for i in range(50):
        criticality_level = np.random.randint(0, 3)
        if criticality_level == 0:
            payload_size = np.random.randint(10, 1001)
            payload_interval = np.random.randint(5, 31)
        elif criticality_level == 1:
            payload_size = np.random.randint(0, 101)
            payload_interval = np.random.randint(10, 121)
        elif criticality_level == 2:
            payload_size = np.random.randint(0, 10)
            payload_interval = np.random.randint(20, 61)

        # msg_flows is a list to store message flow number, criticality_level, payload_size, payload_interval
        msg_flows = ["mf" + str(i), criticality_level, payload_size, payload_interval]

        lst_all_mf.append(msg_flows)

    return lst_all_mf




def main():
    """ Main function to call generate message flows function and print it to CSV file"""
    # Generate flows for criticality level 1 between 10 and 1000
    # 0 criticality level with 1000 bit of payload and payload interval is 10.
    #falld = MessageFlow("Fall Detection", 0, 1000 * MUL_CRIT_0, 10)
    lst_all_mf = gen_mf()
    print_csv(lst_all_mf)


if __name__ == "__main__":
    main()
