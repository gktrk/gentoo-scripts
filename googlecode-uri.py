#!/usr/bin/env python3

# Gokturk Yuksek <gokturk@gentoo.org>
# Released into public domain

import portage
import os, os.path
import re

verbose=False
no_version=True
portdir="/usr/portage"

def get_portdb():
    return portage.portdb

def get_cp_all(portdb):
    return portdb.cp_all(trees=[portdir]) 

def get_cpv_all(portdb, cp):
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

def get_maintainers(atom):
    metadata = os.path.join(portdir, atom, "metadata.xml")
    xml = portage.xml.metadata.MetaDataXML(metadata, None)
    return xml.maintainers()

def main():
    regex = re.compile(".*(code.google.com|googlecode.com).*")
    portdb = get_portdb()
    cp_list = get_cp_all(portdb)

    for cp in cp_list:
        cpv_list = get_cpv_all(portdb, cp)
        for cpv in cpv_list:
            fetchmap = filter_fetchmap(get_fetchmap(portdb, cpv), regex)
            if (bool(fetchmap)):
                maintainers = get_maintainers(cp)
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
