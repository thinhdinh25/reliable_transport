import argparse
import socket
import sys

from utils import PacketHeader, compute_checksum


sender_ip = "127.0.6"  
receiver_ip = "127.0.6"
receiver_port = 10000
sender_port = 10001
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
window_size = 4

def send_ack(seq_num):
    ack_header = PacketHeader(type=3, seq_num=seq_num, length=0)
    ack_header.checksum = compute_checksum(ack_header)
    s.sendto(bytes(ack_header), (sender_ip, sender_port))

def verify_checksum(pkt):
    pkt_header = PacketHeader(pkt[:16])
    msg = pkt[16 : 16 + pkt_header.length]
    # Verity checksum
    pkt_checksum = pkt_header.checksum
    pkt_header.checksum = 0
    computed_checksum = compute_checksum(pkt_header / msg)
    return pkt_checksum == computed_checksum

def receive_start():
    global sender_ip
    global sender_port
    while True:
        # Receive packet; address includes both IP and port
        start_pkt, address = s.recvfrom(2048)
        sender_ip = address[0]
        sender_port = address[1]
        # Extract header and payload
        start_header = PacketHeader(start_pkt[:16])
        #verify start packet
        if start_header.type != 0 or start_header.seq_num != 0 or start_header.length != 0:
            print("Not Start Package", file=sys.stderr)
            continue
        # Verify checksum
        if verify_checksum(start_pkt) == False:
            print("Start checksums not match", file=sys.stderr)
            continue
        # resent ack of start
        send_ack(1)
        #set new state to data
        break

def receive_data():
    expect_seq = 1
    buffer = {}

    while True:
        data_pkt, address = s.recvfrom(2048)
        data_header = PacketHeader(data_pkt[:16])

        #verify checksum
        if verify_checksum(data_pkt) == False:
            continue

        #verify packet type
        if data_header.type == 0:
            continue

        #end condition 
        elif data_header.type == 1:
            send_ack(expect_seq + 1)
            print("received all file", file=sys.stderr)
            break

        elif data_header.type == 2:
            received_seq = data_header.seq_num
            if received_seq >= expect_seq + window_size:
                send_ack(expect_seq)
            elif received_seq < expect_seq:
                send_ack(expect_seq)
            else:
                buffer[received_seq] = data_pkt[16 : 16 + data_header.length]
                while expect_seq in buffer:
                    sys.stdout.buffer.write(buffer[expect_seq])
                    sys.stdout.flush()
                    expect_seq += 1
                send_ack(expect_seq)
            



def receiver():
    s.bind((receiver_ip, receiver_port))
    while True:
        receive_start()
        receive_data()

        


def main():
    global receiver_ip, receiver_port, window_size
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    receiver_ip = args.receiver_ip
    receiver_port = args.receiver_port
    window_size = args.window_size

    receiver()


if __name__ == "__main__":
    main()
