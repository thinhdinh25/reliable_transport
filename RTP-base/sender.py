import argparse
import socket

from utils import PacketHeader, compute_checksum


sender_ip = "127.0.0.1"  
receiver_ip = "127.0.0.1"
receiver_port = 10000
sender_port = 10001

text = "thisisaverylongtextthatyoucanneverimageinyourmind"



s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def verify_checksum(pkt):
    pkt_checksum_saved = pkt.checksum
    pkt.checksum = 0
    computed_checksum = compute_checksum(pkt)
    return computed_checksum == pkt_checksum_saved


def sender(receiver_ip, receiver_port, window_size):
    #initialization
    s.bind((sender_ip, sender_port))
    s.settimeout(0.5)
    sender_start()

def sender_start():
    #send start package
    start_header = PacketHeader(type=0, seq_num=0, length=0)
    start_header.checksum = compute_checksum(start_header)
    s.sendto(bytes(start_header), (receiver_ip, receiver_port))
    #check ack start
    while True:
        try:
            ack, address = s.recvfrom(2048)
        except socket.timeout:
            # resend packet
            print("Timed out, need to resent")
            s.sendto(bytes(start_header), (receiver_ip, receiver_port))
            continue
            
        # Extract header and payload
        ack_header = PacketHeader(ack[:16])

        #verify ack detail
        if ack_header.type != 3 or ack_header.seq_num != 1 or ack_header.length != 0:
            print("Not ACK")
            continue

        # Verify checksum
        if verify_checksum(ack_header) == True:
            print("ACK checksums not match")
            continue
        break

def sender_data():





sender(receiver_ip, receiver_port, 4)


# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument(
#         "receiver_ip", help="The IP address of the host that receiver is running on"
#     )
#     parser.add_argument(
#         "receiver_port", type=int, help="The port number on which receiver is listening"
#     )
#     parser.add_argument(
#         "window_size", type=int, help="Maximum number of outstanding packets"
#     )
#     args = parser.parse_args()

#     sender(args.receiver_ip, args.receiver_port, args.window_size)


# if __name__ == "__main__":
#     main()
