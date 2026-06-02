import argparse
import socket
import sys

from utils import PacketHeader, compute_checksum

sender_ip = "0"
receiver_ip = "127.0.0.1"
receiver_port = 10000
sender_port = 10001

text = ""

chunks = []
payload_size = 1400
seq_num = 1

window_size = 4 


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def verify_checksum(pkt):
    pkt_header = PacketHeader(pkt[:16])
    msg = pkt[16 : 16 + pkt_header.length]
    # Verity checksum
    pkt_checksum = pkt_header.checksum
    pkt_header.checksum = 0
    computed_checksum = compute_checksum(pkt_header / msg)
    return pkt_checksum == computed_checksum


def sender():
    local_seq = 1
    #split text into chunks 
    for i in range(0, len(text), payload_size):
        chunk = text[i:i + payload_size]

        data_header = PacketHeader(
            type=2,
            seq_num=local_seq,
            length=len(chunk)
        )

        data_header.checksum = compute_checksum(data_header / chunk)

        chunks.append(data_header / chunk)

        local_seq += 1

    #initialization
    s.settimeout(0.5)

    #start sending
    sender_start()


def handle_start():
    #create start packet
    start_header = PacketHeader(type=0, seq_num=0, length=0)
    start_header.checksum = compute_checksum(start_header)

    #send start packet
    s.sendto(bytes(start_header), (receiver_ip, receiver_port))

    #wait for ack
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
            print("Not Start ACK")
            continue
        # Verify checksum
        if verify_checksum(ack) == False:
            print("Start ACK checksums not match")
            continue
        break

def handle_data():
    base = 1
    next_seq = 1
    total = len(chunks)
    acked_packets = set()

    #send all packet in 1 window
    while base <= total:
        while next_seq < base + window_size and next_seq <= total:
            s.sendto( bytes(chunks[next_seq - 1]), (receiver_ip, receiver_port))
            next_seq += 1
            
            #wait for ack
        try:
            ack, address = s.recvfrom(2048)
        except socket.timeout:
            # resend packet
            print("Timed out, need to resent missing packet")
            for seq in range(base, next_seq):
                if seq not in acked_packets:
                    s.sendto(bytes(chunks[seq - 1]), (receiver_ip, receiver_port))
            continue
        # Extract header and payload
        ack_header = PacketHeader(ack[:16])
        #verify ack detail
        if ack_header.type != 3 or ack_header.length != 0:
            print("Received packet NOT ACK")
            continue
        #verify correct next_seq
        if ack_header.seq_num < base or ack_header.seq_num > next_seq:
            print("Wrong seq number")
            continue
        # Verify checksum
        if verify_checksum(ack) == False:
            print("ACK checksums not match")
            continue
        received_ack_seq = ack_header.seq_num
        if received_ack_seq >= base and received_ack_seq < next_seq:
            acked_packets.add(received_ack_seq)
        while base in acked_packets:
            acked_packets.remove(base) 
            base += 1


def handle_end():
    end_seq = len(chunks) + 1

    #create end packet
    end_header = PacketHeader(type=1, seq_num=end_seq, length=0)
    end_header.checksum = compute_checksum(end_header)

    #send end packet
    s.sendto(bytes(end_header), (receiver_ip, receiver_port))

    #wait for ack
    while True:
        try:
            ack, address = s.recvfrom(2048)
        except socket.timeout:
            # resend packet
            print("Timed out, leaving")
            break
            
        # Extract header and payload
        ack_header = PacketHeader(ack[:16])
        #verify ack detail
        if ack_header.type != 3 or ack_header.seq_num != end_seq +1 or ack_header.length != 0:
            print("Not End ACK")
            continue
        # Verify checksum
        if verify_checksum(ack) == False:
            print("End ACK checksums not match")
            continue
        break               


def sender_start():
    handle_start()
    handle_data()
    handle_end()


def main():
    global receiver_ip, receiver_port, window_size, text
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
    text = sys.stdin.buffer.read()
    sender()


if __name__ == "__main__":
    main()
