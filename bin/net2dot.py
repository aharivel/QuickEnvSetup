#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2023 Robin Jarry

"""
Convert linux configuration to DOT graph. The output can be piped to dot to
convert it to SVG or other formats. Example:

    %(prog)s | dot -Tsvg > net.svg
"""

import argparse
import json
import subprocess
import sys
import re


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-4",
        "--ipv4-addresses",
        action="store_true",
        help="""
        Display IPv4 addresses.
        """,
    )
    parser.add_argument(
        "-6",
        "--ipv6-addresses",
        action="store_true",
        help="""
        Display IPv6 addresses.
        """,
    )
    parser.add_argument(
        "-l",
        "--local-addresses",
        action="store_true",
        help="""
        Display link local addresses.
        """,
    )
    args = parser.parse_args()

    conf = preprocess(get_running())

    print("// generated using net2dot")
    print("digraph {")
    print('  node [fontname=monospace]')
    print('  graph [compound=true]')
    print('  graph [style=dotted]')

    for ns in conf:
        if ns == "":
            continue
        config = conf[ns]
        print()
        print(f"  subgraph netns_{safe(ns)} {{")
        print(f'    label="netns {ns}"')
        print("    cluster=true")
        print()
        for name in config.by_name:
            link = config.by_name[name]
            attrs, _, _ = node_attrs(link, conf, ns, args)
            print(f"    {safe(ns)}_{safe(name)} [{attrs}];")
        print("  }")

    print()
    for name in conf[""].by_name:
        link = conf[""].by_name[name]
        attrs, _, _ = node_attrs(link, conf, "", args)
        print(f"  {safe(name)} [{attrs}];")

    print()
    for ns in conf:
        config = conf[ns]
        for name in config.by_name:
            link = config.by_name[name]
            _, master, dev = node_attrs(link, conf, ns, args)
            if master:
                if ns:
                    print(f"  {safe(ns)}_{safe(name)} -> {safe(master)};")
                else:
                    print(f"  {safe(name)} -> {safe(master)};")
            if dev:
                if ns:
                    print(f"  {safe(ns)}_{safe(name)} -> {safe(dev)} [style=dotted];")
                else:
                    print(f"  {safe(name)} -> {safe(dev)} [style=dotted];")

    print("}")


def safe(n):
    return re.sub(r"\W", "_", n)


def node_attrs(link, all_config, netns, args):
    dev = ""
    label = f"<b>{link.ifname}</b>"
    xlabel = ""
    attrs = {}
    if "linkinfo" in link:
        kind = link.linkinfo.info_kind
        if kind == "vxlan":
            attrs["color"] = "blue"
            label += f'<br/><font color="blue">vni {link.linkinfo.info_data.id}</font>'
            if "local" in link.linkinfo.info_data:
                label += f"<br/><i>local {link.linkinfo.info_data.local}</i>"
            if "remote" in link.linkinfo.info_data:
                label += f"<br/><i>remote {link.linkinfo.info_data.remote}</i>"
            elif "group" in link.linkinfo.info_data:
                label += f"<br/><i>group {link.linkinfo.info_data.group}</i>"
            if netns:
                dev = f"{netns}_{link.linkinfo.info_data.link}"
            else:
                dev = link.linkinfo.info_data.link
        elif kind == "bridge":
            attrs["shape"] = "diamond"
        elif kind == "bond":
            attrs["color"] = "pink"
            attrs["shape"] = "house"
            label += f'<br/><font color="pink">mode {link.linkinfo.info_data.mode}</font>'
            if link.linkinfo.info_data.get("ad_lacp_active") == "on" \
                    and link.linkinfo.info_data.get("ad_lacp_rate"):
                label += f'<br/><font color="pink">lacp {link.linkinfo.info_data.ad_lacp_rate}</font>'
        elif kind == "vlan":
            attrs["color"] = "green"
            label += f'<br/><font color="green">vlan {link.linkinfo.info_data.id}</font>'
            if netns:
                dev = f"{netns}_{link.link}"
            else:
                dev = link.linkinfo.info_data.link
        elif kind == "veth":
            attrs["color"] = "red"
            attrs["shape"] = "hexagon"
            if netns and link.link_netnsid == 0:
                dev = all_config[""].by_index[link.link_index].ifname
    if link.link_type == "loopback":
        attrs["color"] = "orange"
        attrs["shape"] = "invtriangle"
    if "master" in link:
        if netns:
            master = f"{netns}_{link.master}"
        else:
            master = link.master
    else:
        master = ""
    attrs["label"] = label
    xlabel = ""
    if link.get("addr_info"):
        for addr in link.addr_info:
            if addr.family == "inet":
                if not args.ipv4_addresses:
                    continue
                color = "blue"
            elif addr.family == "inet6":
                if not args.ipv6_addresses:
                    continue
                color = "magenta"
            else:
                color = "orange"
            if addr.scope == "global" or args.local_addresses:
                xlabel += f'<br/><font color="{color}">{addr.local}/{addr.prefixlen}</font>'
    if xlabel:
        attrs["xlabel"] = xlabel
    a = []
    for n, v in attrs.items():
        if n in ("label", "xlabel") and v.startswith("<"):
            a.append(f"{n}=<{v}>")
        else:
            a.append(f'{n}="{v}"')
    return " ".join(a), master, dev


def get_running():
    out = {
        "": ip("addr", "show"),
    }
    for ns in ip("netns", "show"):
        net = ns["name"]
        out[net] = ip("-n", net, "addr", "show")
    return out


def ip(*cmd):
    args = ["ip", "-d", "-j"] + list(cmd)
    out = subprocess.check_output(args).decode("utf-8")
    if not out.strip():
        return []
    return json.loads(out)


class attrdict(dict):
    def __getattr__(self, attr):
        return self[attr]

    def __getitem__(self, key):
        v = super().__getitem__(key)
        if isinstance(v, dict):
            return attrdict(v)
        elif isinstance(v, list):
            l = []
            for e in v:
                if isinstance(e, dict):
                    e = attrdict(e)
                l.append(e)
            return l
        return v


def preprocess(raw):
    conf = {}
    for ns, nsconfig in raw.items():
        c = {
            "by_index": {},
            "by_name": {},
        }
        for addr in nsconfig:
            c["by_index"][addr["ifindex"]] = addr
            c["by_name"][addr["ifname"]] = addr
        conf[ns] = c
    return attrdict(conf)


if __name__ == "__main__":
    sys.exit(main())
