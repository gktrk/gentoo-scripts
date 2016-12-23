#!/usr/bin/env python3

# Gokturk Yuksek <gokturk@gentoo.org>
# Released into public domain

import portage
import os, os.path
import re
import argparse

verbose=False
no_version=True

def get_portdb():
    return portage.portdb

def get_cp_all(portdb, portdir):
    return portdb.cp_all(trees=[portdir]) 

def get_cpv_all(portdb, portdir, cp):
    return portdb.cp_list(cp, mytree=portdir)

def get_fetchmap(portdb, atom):
    return portdb.getFetchMap(atom)

def filter_fetchmap(fetchmap, regex):
    for key in fetchmap:
        pop=True
        for val in fetchmap[key]:
            if regex.match(val):
                pop=False
        if pop:
            fetchmap.pop(key)

    return fetchmap

def get_maintainers(portdir, atom):
    metadata = os.path.join(portdir, atom, "metadata.xml")
    xml = portage.xml.metadata.MetaDataXML(metadata, None)
    return xml.maintainers()

def parse_cmdline():
    parser = argparse.ArgumentParser()

    parser.add_argument("--portdir", type=str, default="/usr/portage",
                        help="Path to the portdir")

    return parser.parse_args()

def main():
    portdb = get_portdb()
    regex = re.compile(".*(code.google.com|googlecode.com).*")

    args = parse_cmdline()
    portdir = args.portdir
    cp_list = get_cp_all(portdb, portdir)

    for cp in cp_list:
        cpv_list = get_cpv_all(portdb, portdir, cp)
        for cpv in cpv_list:
            fetchmap = filter_fetchmap(get_fetchmap(portdb, cpv), regex)
            if (bool(fetchmap)):
                maintainers = get_maintainers(portdir, cp)
                s = ""
                for m in maintainers:
                    s += m.email + " "
                if s == "":
                    s = "maintainer-needed@gentoo.org"
                if no_version:
                    print("{}: {}".format(cp, s))
                    break
                else:
                    print("{}: {}".format(cpv, s))
                    if verbose:
                        for key in fetchmap:
                            print("\t{}".format(key))
                            for val in fetchmap[key]:
                                print("\t\t{}".format(val))

if __name__ in "__main__":
    exit(main())
