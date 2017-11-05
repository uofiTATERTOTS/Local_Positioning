'''
```
'''
import socket
import time
import numpy as np
import netifaces
from scipy.stats.kde import gaussian_kde
import matplotlib.pyplot as plt

def positioning_sequence_base(address, port, mode = 'c'):
    timeout = 10

    program_start = time.time()

    print 'Base: \t', address
            
    base = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    base.bind((address, port))
    base.settimeout(1)

    responses = list()
    nodes = list()
    node_index = 0

    start = time.time()
    end = start + timeout
    while time.time() < end:
        try:
            new_response, new_address = base.recvfrom(1024)
        except:
            pass
        else:
            responses.append(new_response)
            nodes.append(new_address)
            print "Received", new_response, "from", new_address
            print "Sending ", node_index, "to  ", new_address
            base.sendto(str(node_index), new_address)
            node_index = node_index + 1

    print "Initialization complete, ready to begin."
    print "Number of nodes: ", len(nodes), '\n'

    for ii in range(len(nodes)):
        base.sendto('ready', nodes[ii])

    for ii in range(len(nodes)):
        for kk in range(len(nodes)):
            print "Sending "+str(kk)+","+str(nodes[kk][0])+","+str(nodes[kk][1])
            base.sendto(str(kk)+","+str(nodes[kk][0])+","+str(nodes[kk][1]), nodes[ii])
        base.sendto('done', nodes[ii])
        try:
            new_response, new_address = base.recvfrom(1)
        except:
            pass
        else: 
            if new_response == "0":
                pass
            else:
                print "Initialization error."
                break

    peak_1 = 0
    peak_2 = 1        
    flag = 1
    time_end = time.time() + 180
    threshold = 0.1
    n = 1000
    flight_times_1 = np.zeros((n,len(nodes)))
    flight_times_2 = np.zeros((n,len(nodes)))
    
    if len(nodes) != 0:
        for ii in range(len(nodes)):
            peak_1 = 0
            peak_2 = 1
            iterations = 0
            flight_times_1_filt = list()
            flight_times_2_filt = list()
            start = time.time()
            end = start + 10
            print "\nNode ", ii
            if mode == 'converging' or mode == 'c':
                while abs(peak_1 - peak_2) > threshold:
                    for kk in range(n):
                        if abs(peak_1 - peak_2) < threshold and iterations > n:
                            print "Converged"
                            break
                        if time.time() > time_end:
                            print "Timed out in second loop"
                            break
                        start = time.time()
                        base.sendto(str(ii), nodes[ii])
                        while time.time() < end:
                            try:
                                new_response, new_address = base.recvfrom(1)
                            except:
                                pass
                            else:
                                iterations = iterations + 1
                                if iterations % 100 == 0:
                                    print iterations, '\r',
                                if flag == 1:
                                    flight_times_1[kk][ii] = time.time()-start
                                    flag = 2
                                elif flag == 2:
                                    flight_times_2[kk][ii] = time.time()-start
                                    flag = 1
                                break
                        if kk % (n/10) == 0:
                            flight_times_1_filt = list()
                            flight_times_2_filt = list()
                            if len(flight_times_1) > 0 and len(flight_times_1[0][:]) > 0:
                                for mm in range(len(flight_times_1)):
                                    if flight_times_1[mm][ii] != 0.0:
                                        flight_times_1_filt.append(flight_times_1[mm][ii])
                                if len(flight_times_1_filt) > 1:
                                    kde_1 = gaussian_kde(flight_times_1_filt, 0.05)
                                    dist_space_1 = np.linspace(0, max(flight_times_1_filt), n)
                                    values_1 = np.zeros(len(dist_space_1))
                                    maximum_1 = 0
                                    index_1 = 0
                                if 'dist_space_1' in locals():
                                    for mm in range(len(dist_space_1)):
                                        values_1[mm] = kde_1(dist_space_1[mm])
                                        if values_1[mm] > maximum_1:
                                            maximum_1 = values_1[mm]
                                            index_1 = mm
                                    peak_1 = dist_space_1[index_1]
                            if len(flight_times_2) > 0 and len(flight_times_2[0][:]) > 0:
                                for mm in range(len(flight_times_2)):
                                    if flight_times_2[mm][ii] != 0.0:
                                        flight_times_2_filt.append(flight_times_2[mm][ii])
                                if len(flight_times_2_filt) > 1:
                                    kde_2 = gaussian_kde(flight_times_2_filt, 0.05)
                                    dist_space_2 = np.linspace(0, max(flight_times_2_filt), n)
                                    values_2 = np.zeros(len(dist_space_2))
                                    maximum_2 = 0
                                    index_2 = 0
                                if 'dist_space_1' in locals():
                                    for mm in range(len(dist_space_2)):
                                        values_2[mm] = kde_2(dist_space_2[mm])
                                        if values_2[mm] > maximum_2:
                                            maximum_2 = values_2[mm]
                                            index_2 = mm
                                    peak_2 = dist_space_2[index_2]

                if 'dist_space_1' in locals() and abs(peak_1 - peak_2) < threshold:
                    print iterations, "iterations"
                    print "Converged"
                    print "Peak 1: ", peak_1, "\nPeak 2: ", peak_2
                    plt.plot(dist_space_1, kde_1(dist_space_1), lw = 1.0, ls = '-', c= 'k')
                    plt.plot(dist_space_2, kde_2(dist_space_2), lw = 1.0, ls = '-', c= 'b')
                    plt.show()
                if abs(peak_1 - peak_2) > threshold: 
                    print "Failed to converge"
                        
            elif mode == 'fixed' or mode == 'f':
                for kk in range(n):
                    if time.time() > time_end:
                        print "Timed out in second loop"
                        break
                    start = time.time()
                    base.sendto(str(ii), nodes[ii])
                    while time.time() < end:
                        try:
                            new_response, new_address = base.recvfrom(1)
                        except:
                            pass
                        else:
                            iterations = iterations + 1
                            if iterations % 100 == 0:
                                print iterations, '\r',
                            flight_times_1[kk][ii] = time.time()-start
                            break
                if len(flight_times_1) > 0 and len(flight_times_1[0][:]) > 0:
                    for mm in range(len(flight_times_1)):
                        if flight_times_1[mm][ii] != 0.0:
                            flight_times_1_filt.append(flight_times_1[mm][ii])
                    if len(flight_times_1_filt) > 1:
                        kde_1 = gaussian_kde(flight_times_1_filt, 0.05)
                        dist_space_1 = np.linspace(0, max(flight_times_1_filt), n)
                        values_1 = np.zeros(len(dist_space_1))
                        maximum_1 = 0
                        index_1 = 0
                    if 'dist_space_1' in locals():
                        for mm in range(len(dist_space_1)):
                            values_1[mm] = kde_1(dist_space_1[mm])
                            if values_1[mm] > maximum_1:
                                maximum_1 = values_1[mm]
                                index_1 = mm
                        peak_1 = dist_space_1[index_1]
                if 'dist_space_1' in locals():
                        print iterations, "iterations"
                        print "Peak 1: ", peak_1
                        plt.plot(dist_space_1, kde_1(dist_space_1), lw = 1.0, ls = '-', c= 'k')
                        plt.show()
                    
        with open("flight_times_1.txt", 'w') as fp:
            for ii in range(len(flight_times_1)):
                for kk in range(len(flight_times_1[0][:])):
                    fp.write('{0:1.12f}'.format(flight_times_1[ii][kk])+'\t')
                fp.write('\n')
        with open("flight_times_2.txt", 'w') as fp:
            for ii in range(len(flight_times_2)):
                for kk in range(len(flight_times_2[0][:])):
                    fp.write('{0:1.12f}'.format(flight_times_2[ii][kk])+'\t')
                fp.write('\n')

    if len(nodes) > 0:
        base.sendto('begin', nodes[0])
        print "Sending Begin"
    else:
        print "Failed to begin. Zero nodes connected"

    if len(nodes) > 0:
        start = time.time()
        end = start + 5
        while time.time() < end:
            try:
                new_response, new_address = base.recvfrom(1024)
            except:
                pass
            else:
                if new_response == "complete":
                    print "Received Complete"
                    node_1_complete = False
                    node_2_complete = False
                    node_3_complete = False
                    edge_1 = list()
                    edge_2 = list()
                    edge_3 = list()
                    start = time.time()
                    end = start + 5
                    while time.time() < end:
                        try:
                            data, address = base.recvfrom(1024)
                        except:
                            pass
                        else:
                            print "Received", '{0: <20}'.format(data), "from", address[0], address[1]
                            data = data.split(',')
                            if len(data) > 1:
                                if data[0] == '0':
                                    if data[1] == 'complete':
                                        node_1_complete = True
                                    else:
                                        edge_1.append(float(data[1]))
                                elif data[0] == '1':
                                    if data[1] == 'complete':
                                        node_2_complete = True
                                    else:
                                        edge_2.append(float(data[1]))
                                elif data[0] == '2':
                                    if data[1] == 'complete':
                                        node_3_complete = True
                                    else:
                                        edge_3.append(float(data[1]))
                                if node_1_complete == True and node_2_complete == True:
                                    if len(nodes) > 2:
                                        if node_3_complete == True:
                                            print "Received all times for the secondary sequence"
                                            break
                                    else:
                                        print "Received all times for the secondary sequence"
                                        break
                            else:
                                break
                    break
                    

    print "Complete"
    print '{0:1.12f}'.format(time.time() - program_start), "seconds elapsed"
    base.close()
    
positioning_sequence_base('192.168.137.1', 3010, mode = 'c')

'''
```
''' ;