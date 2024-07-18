#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ===========================================================================================>
# COMP3331 - ASSIGNMENT 1
#
# Simple Transport Protocol (STP) - Sender
#
# Written by: Aryaman Sakthivel (z5455785)
# Date: 12-04-2024
#
# ===========================================================================================>

import sys 
from socket import * 
from random import *
import pickle, time
import threading

Num_Arguments = 7
Mss = 1000 

#This class is the blueprint for the packet object
class STPPacket:
    def __init__(self, data, seq_num, ACK=False, SYN=False, FIN=False):
        self.data = data
        self.seq_num = seq_num
        self.ACK = ACK
        self.SYN = SYN
        self.FIN = FIN 

class FLP:
    def __init__(self,flp):
        self.flp = flp

    def exe_flp(self):
        seed()
        probability = random()
        if probability <= flp:
            return False
        return True
    
class RLP:
    def __init__(self,rlp):
        self.rlp = rlp
    
    def exe_rlp(self):
        seed()
        probability = random()
        if probability <= rlp:
            return False
        return True
        
#Creating the Sender Class
class Sender:

    #initialize the sender
    def __init__(self,sendr_port, recv_port, filename, max_win, rto, flp, rlp):
        self.sendr_port = sendr_port
        self.recv_port = recv_port
        self.filename = filename
        self.max_win = max_win
        self.rto = rto
        self.flp = flp
        self.rlp = rlp

    #Create a socket
    Socket = socket(AF_INET,SOCK_DGRAM)

    #Get contents of the file that is to be sent
    def get_data(self):
        file = open(self.filename,'r')
        data = file.read()
        return data
    
    #Recieve packet from receiver
    def recieve_stp(self):
        data, recv_adr = self.Socket.recvfrom(2048)
        packet = pickle.loads(data)
        return packet, recv_adr
    
    #Create SYN
    def create_SYN(self, seq_num):
        print("Creating SYN...")
        SYN = STPPacket('', seq_num, ACK=False, SYN=True, FIN=False)
        return SYN
    
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

    #Send segment over UDP
    def udp_send(self, packet):
        self.Socket.sendto(pickle.dumps(packet),('',self.recv_port))

    
    #Retransmit packet
    def retransmit(self, packet):
         self.Socket.sendto(pickle.dumps(packet),('',self.recv_port))
    
    #Update Sender log
    def Update_log(self, action, pkt_type, packet):
        #Getting header feilds
        seq = packet.seq_num
        size = len(packet.data)

        #Clocking the time 
        udp_time = (time.time() - start_time) * 1000
        udp_time = f"{udp_time:.2f}"
        #Type casting variables to string type to write into the log file
        udp_time ,seq, size = str(udp_time), str(seq), str(size)

		#List of column lenghts and argumetns
        c_len = [5,8,6,8,5]
        args = [action, udp_time, pkt_type, seq, size]

        log_line = ""
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
        log_file = open("Sender_log.txt","a+")
        log_file.write(log_line)
        log_file.close()

    #Split the data into packets
    def split_data(self, data, start):
        length = len(data)
        end = progress + Mss

        #Check if under total size:
        if end < length:
            payload = data[start:end]
        #Total size exceeded 
        else:
            payload = data[start:length]
        return payload 
    

#This function checks if the port argument is a valid integer within the acceptable port number range (referenced from sample receiver.py)
def check_port(port_str,min_port=49152,max_port=65535):
    try: 
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid Port argument must be a numerical: {port_str}")

    if not (min_port <= port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")
    
    return port

#Create random ISN 
def random_isn():
    isn = int(randrange(0,(2**16)-1))
    return isn

#===============================>
#       Main Function
#===============================>
if __name__ == "__main__":

    #Check if number of arguments are valid 
    if len(sys.argv) != Num_Arguments + 1:
        sys.exit(f"Usage: {sys.argv[0]} sender_port receiver_port text_file_to_send max_win rto flp rlp")

    #Store arguments into variables for easier access
    sendr_port = check_port(sys.argv[1])
    recv_port = check_port(sys.argv[2])
    filename = sys.argv[3]
    max_win = int(sys.argv[4])
    rto = float(sys.argv[5])/1000
    flp = float(sys.argv[6])
    rlp = float(sys.argv[7])

    #Initialize Seq and Ack variables
    seq_num = 4521
    unACK_base = 0 #Oldest un-ACK segments first byte
    unACK_count = 0 #Track remaining un-ACK segments
    #Initialize timing variables
    cur_time = 0
    prev_time = 0
    
    #Sender states: CLOSED, SYN_SENT, ESTABLISHED, CLOSING, FIN_WAIT
    #Set Sender State to CLOSED
    sender_state = 'CLOSED'

    #Track packets
    prev_pkt = None
    buffer = []

    #Track packet transitions 
    num_transmitted = 0
    num_retransmitted = 0
    num_dropped = 0
    ack_dropped = 0
    num_ack_duplicate = 0

    #Create the Sender log
    sendr_log = open("Sender_log.txt",'w')
    sendr_log.close()

    #Initiate sender, create socket and get file contents
    print("Sender initiated......")
    sender = Sender(sendr_port,recv_port,filename,max_win,rto,flp,rlp)
    sender.Socket.bind(('',sendr_port))
    file_data = sender.get_data()

    #Track progess of the file
    progress = 0
    data_len = len(file_data)
    ack_data_len = 0
    print("LENGTH OF DATA =",data_len)
    
   
    #===================================>
    #           Main Loop
    #===================================>
    start_time = time.time()
    print("\n__________STATE: CLOSED__________")
    while True:
        #__________Closed State__________ 
        #Send SYN seg
        if sender_state == 'CLOSED':
            syn_pkt = sender.create_SYN(seq_num)
            result = FLP.exe_flp(flp)
            
            if result == True:
                sender.udp_send(syn_pkt)
                #Store the Start Tim for log
                start_time = time.time()
                #Update log
                sender.Update_log("snd",'SYN',syn_pkt)
                sender_state = 'SYN_SENT'
            else:
                sender.Update_log("drp","DATA",syn_pkt)

        #__________SYN Sent State__________
        #Wait for ACK seg
        if sender_state == 'SYN_SENT':
            print("\n__________STATE: SYN SENT__________")
            #sender.Socket.settimeout(rto)
            try:
                r_result = RLP.exe_rlp(rlp)
                ack_pkt, _ = sender.recieve_stp()
                if r_result == True:
                    #Check if ACK
                    if ack_pkt.ACK == True:
                        #Update Log 
                        seq_num = (seq_num+1)%(2**16)
                        sender.Update_log("rcv","ACK",ack_pkt)
                    
                    #2-way-handshake established 
                    sender_state = 'ESTABLISHED'
                else:
                    sender.Update_log('drp',"ACK",ack_pkt)
                    raise TimeoutError
            #Resend Syn if ack isnt recieved
            except TimeoutError:
                sender_state = 'CLOSED'
                continue
    
        #__________Established State_________
        if sender_state == 'ESTABLISHED':
            print("\n__________STATE: ESTABLISHED__________")
            sliding_window_size = 0
            while sliding_window_size < max_win and progress < data_len:
                #Store previous value of curr time as previous time
                prev_time = cur_time

                #Split data into packets
                payload = sender.split_data(file_data,progress)
                packet = STPPacket(payload, seq_num, ACK=False, SYN=False, FIN=False)

                #Time between last packet and this packer
                cur_time = time.time() * 1000
                time_diff = cur_time - prev_time

                print(f"CURRENT TIME = {cur_time:.2f}")
                print(f"PREVIOUS TIME = {prev_time:.2f}")
                print(f"TIME DIFFERENCE = {time_diff:.2f}")

                #FLP Calculation
                result = FLP.exe_flp(flp)

                #IF prev_packet exists and timeout reached 
                if prev_pkt != None:
                    print("PACKET RETRANSMITTING")
                    sender.retransmit(prev_pkt)
                    seq_num = (seq_num+len(payload))%(2**16)
                    sender.Update_log('snd','DATA',prev_pkt)
                    unACK_count += 1
                    buffer.append(prev_pkt)
                    num_retransmitted += 1
                    prev_pkt = None
                    result = 'Retransmitted'

                
                if result == True:
                    print("PACKET SENT")
                    sender.udp_send(packet); unACK_count += 1
                    buffer.append(packet)
                    seq_num = (seq_num+len(payload))%(2**16)
                    #Update log
                    sender.Update_log('snd','DATA',packet)
                    num_transmitted += 1

                elif result == 'Retransmitted':
                    pass

                else:
                    print("PACKET DROPPED")
                    num_dropped += 1
                    prev_pkt = packet
                    sender.Update_log("drp","DATA",packet)
                    #sliding_window_size += len(payload)
                    num_transmitted += 1
                    continue
                    
                #TIMER = tracking the oldest unacknowledged segment
                if cur_time == 0:
                    curr_time = time.time() * 1000
                    print(f"<<TIMER STARTED: {curr_time:.2f}>>")

                #Update Progress 
                progress += len(payload)
                #Update sliding window size
                sliding_window_size += len(payload)

            while unACK_count > 0:
                #RLP Calculation 
                rlp_result = RLP.exe_rlp(rlp)
                ack_pkt, _ = sender.recieve_stp()
            
                if rlp_result == True:
                    #Recieve ack
                    
                    sender.Update_log("rcv",'ACK',ack_pkt)
                    ack_data_len += len(payload)

                    if sender_state != 'CLOSING' and ack_pkt.ACK == True:
                        print("<<ACK RECEIVED>>")
                        unACK_count -= 1
                        buffer.pop(0)
                        
                        if unACK_count == 0:
                            curr_time = time.time() * 1000

                else: 
                        #print(buffer)
                        ack_dropped += 1
                        print("<<ACK DROPPED>>")
                        #ack_pkt, _ = sender.recieve_stp()
                        sender.Update_log("drp","ACK",ack_pkt)
                        pket = buffer[0]
                        sender.udp_send(pket)
                        num_retransmitted += 1
                        buffer.append(pket)
                        sender.Update_log("snd","DATA",pket)
                        num_ack_duplicate += 1
                        buffer.pop(0)
                        continue
                        #Update Log
                        #sender.Update_log("rsnd",'DATA',packet)
                        #Recieve duplicate ack
                        '''
                        if sender_state != 'CLOSING' and ack_pkt.ACK == True:
                            unACK_count -= 1
                            
                            num_ack_duplicate += 1  '''
    



            #Entire file has been sent
        if progress == data_len:
            sender_state = 'CLOSING'
            
        #Closing state
        if sender_state == 'CLOSING':
            print("\n__________STATE: CLOSING__________")
            #Send FIN
            fin_pkt = sender.create_FIN(seq_num)
            result = FLP.exe_flp(flp)
            if result == True:
                sender.udp_send(fin_pkt)
                fin_pkt = sender.create_FIN(seq_num)
                sender.udp_send(fin_pkt)
                sender.Update_log("snd","FIN",fin_pkt)
                sender_state = 'FIN_WAIT'
            else:
                sender.Update_log('drp','FIN',fin_pkt)
                

        #FIN WAIT State
        if sender_state == 'FIN_WAIT':
            
            ack_pkt, _ = sender.recieve_stp()
            r_result = RLP.exe_rlp(rlp)
            if result == True:
                if ack_pkt.ACK == True:
                    fin_retrans = False
                    sender.Update_log('rcv','ACK',ack_pkt)
                    sender_state = 'CLOSED'
                    break
            else:
                sender_state = 'CLOSING'
                continue    
                


            #CLosed state
            if sender_state == 'CLOSED':
                sender.close_stp()
                break
            
    
    # print out complete log
    print("\n\n<==========SENDER LOG==========>")
    f = open("Sender_log.txt", "a+")
    
    data = "Original Data Sent: {}\n".format(data_len)
    ackd = "Original Data Acked: {}\n".format(ack_data_len)
    seg_sent = "Original Segments Sent = {}\n".format(num_transmitted)
    seg_retrans = "Retransmitted Segments = {}\n".format(num_retransmitted)
    ack_duplicate = "Duplicate Acks Received = {}\n".format(num_ack_duplicate)
    data_dropped = "Data Segments Dropped = {}\n".format(num_dropped)
    ack_dropped = "Ack Segments Dropped = {}\n".format(ack_dropped)
   
    final_str = "\n" + data + ackd+ seg_sent + seg_retrans + ack_duplicate + data_dropped + ack_dropped
    f.write(final_str)
    f.close()
    f = open("Sender_log.txt", "r")
    print(f.read())
    f.close()       
