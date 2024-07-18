#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ===========================================================================================>
# COMP3331 - ASSIGNMENT 1
#
# Simple Transport Protocol (STP) - Reciever 
#
# Written by: Aryaman Sakthivel (z5455785)
# Date: 11-04-2024
#
# ===========================================================================================>

import sys,os
from socket import *
import time, pickle 
import threading

Num_Argumetns = 4

#This class is the blueprint for the packet object
class STPPacket:
    def __init__(self, data, seq_num, ACK=False, SYN=False, FIN=False):
        self.data = data
        self.seq_num = seq_num
        self.ACK = ACK
        self.SYN = SYN
        self.FIN = FIN 

#Creating the Reciever Class
class Receiver:

    #initialize the receiver
    def __init__(self, recv_port, sendr_port, filename, max_win,state):
        self.recv_port = recv_port
        self.sendr_port = sendr_port
        self.filename = filename
        self.max_win = max_win
        self.state = state

    #Create a socket
    Socket = socket(AF_INET,SOCK_DGRAM)

    #Recieve packet from sender
    def recieve_stp(self):
        print("Waiting for Sender......")
        data, sender_adr = self.Socket.recvfrom(2048) #max_win: maximum window size in bytes
        packet = pickle.loads(data)
        return packet, sender_adr

    #add payload to file 
    def add_payload(self, data):
        f = open(filename,'a+')
        f.write(data)
        f.close()

    #Send segments over UDP
    def udp_send(self,packet):
        self.Socket.sendto(pickle.dumps(packet),('',self.sendr_port))

    #Create ACK
    def create_ACK(self, seq_num):
        print("Creating ACK...")
        ACK = STPPacket('', seq_num, ACK=True, SYN=False, FIN=False)
        return ACK
    
    #Create FIN
    def create_FIN(self, seq_num):
        print("Creating FIN...")
        FIN = STPPacket('', seq_num, ACK=False, SYN=False, FIN=True)
        return FIN

    #Close Connection
    def close_stp(self):
        print("Connection Closed......")
        self.Socket.close()

    #Update Receiver Log
    def Update_log(self, action, pkt_type, packet):

        #Clocking the time 
        
        udp_time = (time.time() - start_time) * 1000
        udp_time = f"{udp_time:.2f}"

        #Getting header feilds
        seq = packet.seq_num
        size = len(packet.data)
          
        #Type casting variables to string type to write into the log file
        udp_time ,seq, size = str(udp_time), str(seq), str(size)

		#List of column lenghts and argumetns
        c_len = [5,8,6,8,5]
        args = [action, udp_time, pkt_type, seq, size]

        log_line = ''
        count=0

        for c in c_len:
            arg_len = len(args[count])
            space = ""
            #add whitespaces for each clm
            while arg_len < c:
                space += " "
                arg_len += 1
            log_line += str(args[count]) + space
            count += 1
        log_line += '\n'

        #Add the complete line to the log
        log_file = open("Receiver_log.txt","a+")
        log_file.write(log_line)
        log_file.close()


#This function checks if the port argument is a valid integer within the acceptable port number range (referenced from sample receiver.py)
def check_port(port_str,min_port=49152,max_port=65535):
    try: 
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid Port argument must be a numerical: {port_str}")

    if not (min_port <= port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")
    
    return port

#Thread Function Time Wait 
def time_wait():
    packet, _ =receiver.recieve_stp()
    if packet.FIN == True:
        print("DUPLICATE FIN RECIEVED")
        ack_pkt = receiver.create_ACK(seq_num)
        receiver.udp_send(ack_pkt)
        #receiver.Update_log('rcv','FIN',packet)
    


#===============================>
#       Main Function
#===============================>
if __name__ == "__main__":

    #Check if number of arguments are valid 
    if len(sys.argv) != Num_Argumetns + 1:
        sys.exit(f"Usage: {sys.argv[0]} reciever_port sender_port txt_file_recieved max_win")

    #Store arguments into variables for easier access
    recv_port = check_port(sys.argv[1])
    sendr_port = check_port(sys.argv[2])
    filename = sys.argv[3]
    max_win = int(sys.argv[4])

    #Initialize Seq and Ack variables
    seq_num = 0
    next_seq_num = 0


    #Bind Socket
    receiver = Receiver(recv_port, sendr_port, filename, max_win,'CLOSED')
    receiver.Socket.bind(('',recv_port))

    #Receiver States: CLOSED, LISTEN, ESTABLISHED, TIME_WAIT
    #Set Receiver State to LISTEN
    receiver.state = 'LISTEN'

    #Track progress of the file sent and conters
    progress = 0
    data_recv = 0
    original_segs = 0
    duplicate_segs = 0
    duplicate_acks = 0

    #Create buffer 
    buffer = []
    sequence_buffer = []

    #Create the file to store the contents of recieved file
    file = open(filename,'w')
    file.close()
    #Create the Reciever_log
    recv_log = open("Receiver_log.txt",'w')
    recv_log.close()

    #===================================>
    #           Main Loop
    #===================================>
    while True:
        #__________Listening State__________
        if receiver.state == 'LISTEN':
            print("\n__________STATE: LISTEN__________")
            syn_pkt, _ = receiver.recieve_stp()
            #Start the timer
            start_time = time.time()
            #Update log
            receiver.Update_log("rcv","SYN",syn_pkt)
            #Check if SYN
            if syn_pkt.SYN == True:
                #Acknowledge sender SYN
                seq_num = (syn_pkt.seq_num + 1)%(2**16)
                #Creating ACK packet
                ack_pkt = receiver.create_ACK(seq_num)
                receiver.udp_send(ack_pkt)
                #Update log
                receiver.Update_log("snd","ACK",ack_pkt)
                
                #2-way-handshake established
                receiver.state = 'ESTABLISHED'

            #Exit if Unexpected Behaviour by sender
            else:
                sys.exit(f"received unexpected data: Reset Connection")       

        #__________Established State__________
        if receiver.state == 'ESTABLISHED': 
            print("\n__________STATE: ESTABLISHED__________")
            
            #Get packets until FIN close request by sender
            while True:
                packet, _ = receiver.recieve_stp()
                data = packet.data

                print("SEQUENCE NUMBER =",seq_num)

                #If FIN is received then set state to TIME_WAIT
                if packet.FIN == True:
                    print("FIN Initiated (by sender).......")
                    receiver.Update_log("rcv",'FIN',packet)
                    #acknowledge FIN
                    seq_num = (packet.seq_num +1)%(2**16)
                    #Send ACK
                    ack_pkt = receiver.create_ACK(seq_num)
                    print("SEQUENCE NUMBER (FIN)=",ack_pkt.seq_num)
                    receiver.udp_send(ack_pkt)
                    #Update log 
                    receiver.Update_log('snd','ACK',ack_pkt)
                    receiver.state = 'TIME_WAIT'
                    break
                
                #Duplicate SYN arrives
                elif packet.SYN == True:
                    print("Duplicate SYN Recieved")
                    #Creating ACK packet
                    ack_pkt = receiver.create_ACK(seq_num)
                    receiver.udp_send(ack_pkt)
                    #Update log
                    receiver.Update_log("snd","ACK",ack_pkt)

                elif packet.seq_num not in sequence_buffer:
                    print("PACKET OKAY, SEND")
                    #Update log
                    receiver.Update_log('rcv','DATA',packet)
                    sequence_buffer.append(packet.seq_num)
                    #Send ACK for packer and update sequence number value
                    seq_num = (packet.seq_num+len(packet.data))%(2**16)
                    ack_pkt = receiver.create_ACK(seq_num)
                    receiver.udp_send(ack_pkt)
                    #Update log
                    receiver.Update_log("snd","ACK",ack_pkt)
                    

                    #Add data to final file
                    progress += len(data)
                    receiver.add_payload(data)
                    #Update trackers
                    data_recv += len(data)
                    original_segs += 1
                else:
                    print("OUT OF ORDER Packet")
                    buffer.append(packet)
                    #resend previous ack
                    duplicate_acks += 1
                    seq_num = (packet.seq_num + len(packet.data))%(2**16)
                    ack_pkt = receiver.create_ACK(seq_num)
                    receiver.udp_send(ack_pkt)

                    #Check if duplicate seg:
                    if buffer[-1].seq_num == packet.seq_num:
                        duplicate_segs += 1

        #__________Time Wait State__________
        if receiver.state == 'TIME_WAIT':
            print("\n__________STATE: TIME_WAIT")
            #Wait for two maximum segment lifetimes(MSLs) i.e. 2 seconds
            time_wait_thread = threading.Thread(target = time_wait)
            time_wait_thread.start()
            
            '''
            while receiver.state == 'TIME_WAIT':
                pass
            if receiver.recieve_stp():
            #if packet.FIN == True:
                print("Duplicate FIN")
            else: 
                print("NO")
''' 
            time.sleep(2)
            #Enter closed state 
            receiver.state = 'CLOSED'
            
            

        #__________Closed State_________
        if receiver.state == 'CLOSED':
            print("\n__________STATE: CLOSED__________")

            #Close Connection
            receiver.close_stp()
            break
    
    #Print Final file
    print("\n\n<=========={} Content==========>".format(filename))
    file = open(filename,'r')
    print(file.read())

    #Print complete log
    print("\n\n<==========RECEIVER LOG==========>")
    f = open("Receiver_log.txt","a+")

    data_recieved = "Original Data Recieved = {}\n".format(data_recv)
    segs_recieved = "Original Segments Recieved = {}\n".format(original_segs)
    dup_segs_recieved = "Dup Data Segments Recieved = {}\n".format(duplicate_segs)
    dup_acks = "Dup Ack Segments Sent = {}\n".format(duplicate_acks)

    final_str = "\n" + data_recieved + segs_recieved + dup_segs_recieved + dup_acks
    f.write(final_str)
    f.close()
    f = open("Receiver_log.txt",'r')
    print(f.read())
    f.close()
    os._exit(0)
    