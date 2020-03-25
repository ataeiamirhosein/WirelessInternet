import pyshark, numpy
import matplotlib.pyplot as plt, itertools

#load OUT list: this is useful for understanging the vendor. the first 3 bytes of each MAC address are assigned to the manufacturer.
f = open('D:/amir-polimi-class/WIFI/analyze_probe_requests/oui.txt','r')
vendor_mac = []
vendor_name = []
for line in f:
    if "(base 16)" in line:
        fields = line.split("\t")
        vendor_mac.append(fields[0][0:6])
        vendor_name.append(fields[2])
UNIQUE_VENDOR = numpy.unique(vendor_name)
UNIQUE_VENDOR = numpy.append(UNIQUE_VENDOR,"UNKOWN")
VENDOR_HIST = [0]*len(UNIQUE_VENDOR)

#load file
cap = pyshark.FileCapture('D:/amir-polimi-class/WIFI/office_capture/home_capture.pcapng')

#define lists
ssid_list = [] #this one will store the SSID searched in each probe request
mac_list = [] #this list will store who transmitted the probe request
rssi_list = [] #this list will store the RSSI of the probe request

#loop on all packets captured
probe_counter = 0
for packet in cap:
    try:            #used to deal with malformed packets
        if(packet.wlan.fc_type_subtype == '4'):     #access only if the packet is a probe request.
            ssid = packet.wlan_mgt.ssid             #get the SSID of this probe request
            mac = packet.wlan.sa                    #get the source address of this probe request
            rssi = packet.wlan_radio.signal_dbm     #get the rssis of this probe request
            if(ssid != 'SSID: ' and len(ssid)<=32): #check that the SSID is ok
                if(ssid.isascii()):
                    try:
                        #ssid.decode('ascii')
                        ssid_list.append(ssid)          #append the ssid, mac and rssi to the lists
                        mac_list.append(mac)
                        rssi_list.append(rssi)
                    except UnicodeDecodeError:
                        pass                            #skip if problems
                probe_counter = probe_counter+1     #increment the probe counter
    except:
        pass    #skip if problems

print("Captured " + str(probe_counter) + " probes")

#now let's see how many unique MAC addresses were found
unique_mac = numpy.unique(mac_list)
unique_mac_avg_power = []
ssid_list_per_mac = []
print("There were " + str(len(unique_mac)) + " unique MAC addresses")

#let's see which were the ssid queried by each mac
MIN_RSSI = -100
for mac in unique_mac:
    mac_ssid_list = [];
    rssi_ssid_list = [];
    idx = [i for i, x in enumerate(mac_list) if x == mac] #gets the indexes of the entries corresponding to the current mac
    for i in idx:
         mac_ssid_list.append(ssid_list[i])
         rssi_ssid_list.append(float(rssi_list[i]))

    avg_power = sum(rssi_ssid_list)/len(rssi_ssid_list) #compute the average power of the probes received by the current mac
    unique_mac_avg_power.append(avg_power)
    unique_mac_ssid_list = numpy.unique(mac_ssid_list)
    ssid_list_per_mac.append(unique_mac_ssid_list)
    print(mac, unique_mac_ssid_list, avg_power)

    if avg_power > MIN_RSSI:
        #search first 3 bytes of mac in vendor_mac
        red_mac = mac[0:8].upper()
        red_mac = red_mac.replace(':','')
        #get the corresponding vendor or unkown
        try:
            index = vendor_mac.index(red_mac)
        except ValueError:
            index = -1
        #increment the corresponding bin
        if index!=-1:
            v_name = vendor_name[index]
            vendor_idx = numpy.where(UNIQUE_VENDOR==v_name)
            vendor_idx = vendor_idx[0]
            VENDOR_HIST[vendor_idx[0]]  = VENDOR_HIST[vendor_idx[0]] + 1
        else:
            VENDOR_HIST[len(VENDOR_HIST)-1] = 0
            #remove comment to see also UNKOWN MAC
            VENDOR_HIST[len(VENDOR_HIST)-1] = VENDOR_HIST[len(VENDOR_HIST)-1] + 1

selectors = [x>0 for x in VENDOR_HIST]
red_vendor_hist = list(itertools.compress(VENDOR_HIST,selectors)) #compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F
vendor_labels = list(itertools.compress(UNIQUE_VENDOR,selectors))

#PLOT HISTOGRAM OF RSSI FOR ALL DEVICES
pasd = plt.figure()
n, bins, patches = plt.hist(unique_mac_avg_power, 10)
plt.xlabel('RSSI [dBm]')
plt.ylabel('Number of devices')
plt.show

#PLOT PIE OF VENDORS (ONLY FOR THOSE MAC WHOSE AVG RSSI IS GREATER THAN MIN_RSSI)
pasd = plt.figure()
ax = plt.axes([0.1, 0.1, 0.8, 0.8])
plt.pie(red_vendor_hist,labels = vendor_labels, autopct='%1.1f%%', shadow=True, startangle=90)
plt.show()