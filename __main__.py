import argparse
import time

from cc1101.config import RXConfig, Modulation 
from cc1101 import CC1101

from .common import FREQUENCY, BAUD_RATE, SYNC_WORD, PACKET_LENGTH, Message, decode_rx_bytes, message_vote

def rx(args: argparse.Namespace) -> None:
    rx_config = RXConfig(FREQUENCY, Modulation.OOK, BAUD_RATE, SYNC_WORD, PACKET_LENGTH)
    radio = CC1101(args.device, rx_config) 

    print("Receiving Packets")
    while True:
        for rx_bytes in radio.receive():

            messages = []
            for packet in decode_rx_bytes(rx_bytes):
                try:
                    messages.append(Message.from_packet(packet))
                except ValueError:
                    pass

            if len(messages) > 0:
                message = message_vote(messages)
                print(message)

        time.sleep(1)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

rx_parser = subparsers.add_parser("rx", help="Receive packets")
rx_parser.add_argument("device", help='CC1101 Device')
rx_parser.set_defaults(func=rx)

args = parser.parse_args()

if "func" in args:
    args.func(args)
else:
    parser.print_help()