#!/usr/bin/env python
import argparse
import IPy
import os
import sys
import time
from novaclient import client as novaclient
from neutronclient.neutron import client as neutronclient

"""
Various utils
"""

def get_nova_creds_from_env():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    d['region_name'] = os.environ.get('OS_REGION_NAME')
    d['cacert'] = os.environ.get('OS_CACERT', None)
    return d

def get_neutron_creds_from_env():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    d['region_name'] = os.environ.get('OS_REGION_NAME')
    return d

def get_nova_client():
    return novaclient.Client("2", **get_nova_creds_from_env())

def get_neutron_client():
    return neutronclient.Client("2.0", **get_neutron_creds_from_env())

def is_rfc1918(ip_string):
    return IPy.IP(ip_string).iptype() != "PUBLIC"

def is_ipv4(ip_string):
    return IPy.IP(ip_string).version() == 4

def get_ip_of_node(nova_client, names):
    ip = None

    ##
    # Make sure it can return the node list, this will make sure get_ip_of_node
    # will allways return the IP if the server exists
    ##
    while True:
        try:
            servers = nova_client.servers.list()
            break
        except Exception as e:
            print >> sys.stderr, 'Failed on nova list', e
            time.sleep(5)

    nodes = {}

    for server in servers:
        if server.name in names:
            for network in server.networks.values():
                for ip in network:
                    if is_ipv4(ip) and not is_rfc1918(ip):
                        nodes.update({server.name: ip})
            # Fallthrough... If none are non-rfc1918 just return whatever
            if server.name not in nodes:
                nodes.update({server.name: ip})

    if set(names) != set(nodes.keys()):
        raise Exception('Servers not found - %s' % list(set(names).difference(set(nodes.keys()))))

    return nodes


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(dest='action', help='Action to perform')

    get_ip_of_node_parser = subparsers.add_parser('get_ip_of_node', help='Get IP for node')
    get_ip_of_node_parser.add_argument('node_name', help='Node name')

    args = argparser.parse_args()
    nova_client = get_nova_client()

    if args.action == 'get_ip_of_node':
        print ''.join(get_ip_of_node(nova_client, args.node_name.split()).values())
