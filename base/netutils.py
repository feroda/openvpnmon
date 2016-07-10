#!/usr/bin/python

import socket, struct

#--------------------------------------------------------------------------------------------
# Ip utility


def addr_ntoa(n_addr):
    try:
        addr_ntoa = socket.inet_ntoa(struct.pack('!L', n_addr))
    except socket.error:
        raise  #ValueError, "La stringa %s non e' un valido indirizzo IP"	 % addr

    return addr_ntoa


inet_ntoa = addr_ntoa


def addr_aton(addr):
    try:
        addr_aton = struct.unpack('!L', socket.inet_aton(addr))[0]
    except socket.error:
        raise ValueError, "La stringa %s non e' un valido indirizzo IP" % addr

    return addr_aton


inet_aton = addr_aton


def get_aton_bounds_from_cidr(base, bits):
    aton_base = inet_aton(base)
    full_aton_mask = 2**32 - 1
    aton_mask = 2**(32 - bits) - 1

    aton_haddr = aton_base | aton_mask
    aton_laddr = aton_base & (full_aton_mask - aton_mask)

    return (aton_laddr, aton_haddr)


def get_bounds_from_cidr(base, bits):
    aton_laddr, aton_haddr = get_aton_bounds_from_cidr(base, bits)
    return addr_ntoa(aton_laddr), addr_ntoa(aton_haddr)


def get_aton_bounds_from_ip_mask(ip, mask):
    aton_base = inet_aton(ip)
    aton_mask = 2**32 - 1 - inet_aton(mask)
    full_aton_mask = 2**32 - 1

    aton_haddr = aton_base | aton_mask
    aton_laddr = aton_base & (full_aton_mask - aton_mask)

    return (aton_laddr, aton_haddr)


def ip_is_inside_inet_aton_range(ip, laddr_aton, haddr_aton):
    ip_aton = addr_aton(ip)
    if (ip_aton <= haddr_aton) and (ip_aton >= laddr_aton):
        return True
    else:
        return False


def ip_is_inside_inet_aton_ranges(ip, aton_ranges):
    ip_aton = addr_aton(ip)
    for laddr_aton, haddr_aton in aton_ranges:
        if (ip_aton <= haddr_aton) and (ip_aton >= laddr_aton):
            return True
    return False


def ip_is_inside_range(ip, laddr, haddr):
    laddr_aton = addr_aton(laddr)
    haddr_aton = addr_aton(haddr)

    return ip_is_inside_inet_aton_range(ip, laddr_aton, haddr_aton)


def explode_ip_range(laddr, haddr):
    laddr_aton = addr_aton(laddr)
    haddr_aton = addr_aton(haddr)

    ip_addrs = map(lambda x: addr_ntoa(x), range(laddr_aton, haddr_aton))
    return ip_addrs


private_ip_ranges = [
    ('192.168.0.0', '192.168.255.255'), ('172.16.0.0', '172.31.255.255'),
    ('10.0.0.0', '10.255.255.255')
]

exp_ip_ranges = [('224.0.0.0', '255.255.255.255')]
aton_private_ranges = map(lambda r: (addr_aton(r[0]), addr_aton(r[1])),
                          private_ip_ranges)
aton_exp_ip_ranges = map(lambda r: (addr_aton(r[0]), addr_aton(r[1])),
                         exp_ip_ranges)

#------------------------------------------------------------------------------
# TEST network utilities


def aaaa(addr):
    public_srv_addrs = []
    c = 0
    for aton_r in aton_private_ranges:
        if ip_is_inside_inet_aton_range(addr, aton_r[0], aton_r[1]):
            break
        else:
            c += 1
    if c == len(aton_private_ranges):
        public_srv_addrs.append(addr)
    return public_srv_addrs


if __name__ == "__main__":

    example_addresses = ['10.0.0.10', '192.168.0.1', '232.10.11.20']

    for addr in example_addresses:
        print "Indirizzo %s " % addr
        if len(aaaa(addr)):
            print "pubblico"
        else:
            print "privato"
