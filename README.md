<div class="Image" align="center">
  <img src="https://media.geeksforgeeks.org/wp-content/uploads/20240226104348/UDP-gif.gif" alt="Logo" width="350" height="180">
</div>
<h1 align="center">Simple-Transport-Protocol</h1>

## About: 
This project is an implementation of a reliable transport protocol, Simple Transport Protocol (STP), built over the UDP protocol. The STP protocol ensures reliable, end-to-end delivery of data using mechanisms such as sequence numbers, acknowledgments (ACKs), and a sliding window protocol. This implementation is asymmetric, with a sender and a receiver, where data flows from the sender to the receiver, and ACKs flow from the receiver to the sender.

## Built With: 
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) 
![UDP Sockets](https://img.shields.io/badge/UDP%20Sockets-EF0092?logo=rsocket&logoColor=fff&style=for-the-badge)
![Threads](https://img.shields.io/badge/Threads-000?logo=threads&logoColor=fff&style=for-the-badge)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)

## Usage:
### Sender
To run the sender program:
```sh
  # For Python 
  python3 sender.py sender_port receiver_port txt_file_to_send max_win rto flp rlp
```
* **sender_port:** UDP port number for the sender.
* **receiver_port:** UDP port number for the receiver.
* **txt_file_to_send:** Name of the text file to be transferred.
* **max_win:** Maximum window size in bytes.
* **rto:** Retransmission timeout in milliseconds.
* **flp:** Forward loss probability.
* **rlp:** Reverse loss probability.

### Receiver
To run the receiver program:
```sh
  # For Python
  python3 receiver.py receiver_port sender_port txt_file_received max_win
```
* **receiver_port:** UDP port number for the receiver.
* **sender_port:** UDP port number for the sender.
* **txt_file_received:** Name of the file to save the received data.
* **max_win:** Maximum window size in bytes.

## Conclusion:
This project provides a practical understanding of how reliable transport protocols function and offers experience with socket programming using the UDP protocol. By implementing STP, you gain insights into the design and operation of transport layer protocols and how they ensure reliable data transfer.
