import argparse
import socket

from utils import PacketHeader, compute_checksum


sender_ip = "127.0.0.1"  
receiver_ip = "127.0.0.1"
receiver_port = 10000
sender_port = 10001

def verify_checksum(pkt):
    pkt_checksum_saved = pkt.checksum
    pkt.checksum = 0
    computed_checksum = compute_checksum(pkt)
    return computed_checksum == pkt_checksum_saved


def receiver(receiver_ip, receiver_port, window_size):
    """TODO: Listen on socket and print received message to sys.stdout."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((receiver_ip, receiver_port))
    state = "START"
    while True:
        if state == "START":
            # Receive packet; address includes both IP and port
            start_pkt, address = s.recvfrom(2048)

            # Extract header and payload
            start_pkt = PacketHeader(start_pkt[:16])

            #verify start package
            if start_pkt.type != 0 or start_pkt.seq_num != 0 or start_pkt.length != 0:
                print("Havent started yet")
                continue

            # Verity checksum
            pkt_checksum = start_pkt.checksum
            start_pkt.checksum = 0
            computed_checksum = compute_checksum(start_pkt)
            if pkt_checksum != computed_checksum:
                print("checksums not match")
                continue

            # resent ack of start
            ack_header = PacketHeader(type=3, seq_num= start_pkt.seq_num + 1, length=0)
            ack_header.checksum = compute_checksum(ack_header)
            s.sendto(bytes(ack_header), (sender_ip, sender_port))
            #set new state to data
        elif state == "DATA":
            print(1)

        
        

receiver(receiver_ip, receiver_port, 4)

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

#     receiver(args.receiver_ip, args.receiver_port, args.window_size)


# if __name__ == "__main__":
#     main()
