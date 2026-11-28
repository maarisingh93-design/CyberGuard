from collections import Counter

from scapy.all import TCP, UDP, sniff

COUNT = 200
TIMEOUT = 30

print(f"Capturing up to {COUNT} packets (max {TIMEOUT} seconds) on this machine...")
packets = sniff(count=COUNT, timeout=TIMEOUT)

protocols = Counter()
ports = Counter()
flags = Counter()
total_bytes = 0

for packet in packets:
    total_bytes += len(packet)
    if packet.haslayer(TCP):
        protocols["TCP"] += 1
        ports[packet[TCP].dport] += 1
        flag_text = str(packet[TCP].flags)
        if "S" in flag_text and "A" not in flag_text:
            flags["SYN"] += 1
        if "R" in flag_text:
            flags["RST"] += 1
    elif packet.haslayer(UDP):
        protocols["UDP"] += 1
        ports[packet[UDP].dport] += 1
    else:
        protocols["Other"] += 1

print()
print("Packets captured :", len(packets))
print("Total bytes      :", total_bytes)
print("Protocols        :", dict(protocols))
print("TCP SYN packets  :", flags["SYN"])
print("TCP RST packets  :", flags["RST"])
print("Top destination ports:")
for port, count in ports.most_common(5):
    print("  ", port, "->", count)
print()
print("Note: this is a capture demo. It is not connected to the model,")
print("because the model needs 77 flow features, not raw packets.")