#!/usr/bin/env python3

# Gokturk Yuksek <gokturk@gentoo.org>
# Released into public domain

import portage
import os, os.path
import sys
import re
import argparse

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

def match_maintainer(maintainers, maintainer_regex, match_orphaned):
    if match_orphaned:
        if not bool(maintainers):
            return True
        else:
            return False
    else:
        for m in maintainers:
            if maintainer_regex.match(m.email):
                return True

def parse_cmdline():
    parser = argparse.ArgumentParser()

    parser.add_argument("--portdir", type=str, default="/usr/portage",
                        help="Path to the portdir")
    parser.add_argument("-n", "--no-version", action="store_true",
                        help="Print results per package instead of per version")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="""
                        Print the SRC_URI links as well.
                        Negates '--no-version'""")
    parser.add_argument("-m", "--maintainer-email", type=str, default="",
                        help="Filter packages by maintainer email")
    parser.add_argument("--orphaned", action="store_true",
                        help="Match only orphaned (maintainer-needed) packages")

    return parser.parse_args()

def main():
    portdb = get_portdb()
    regex = re.compile(".*(code.google.com|googlecode.com).*")

    args = parse_cmdline()
    portdir = args.portdir
    no_version = args.no_version
    verbose = args.verbose
    maintainer_regex = re.compile(args.maintainer_email)
    match_orphaned = args.orphaned

    if verbose:
        if no_version:
            print("Option '--verbose' is given, ignoring '--no-version'",
                  file=sys.stderr)
            no_version = False

    cp_list = get_cp_all(portdb, portdir)
    for cp in cp_list:
        cpv_list = get_cpv_all(portdb, portdir, cp)
        for cpv in cpv_list:
            fetchmap = filter_fetchmap(get_fetchmap(portdb, cpv), regex)
            if (bool(fetchmap)):
                maintainers = get_maintainers(portdir, cp)
                s = ""

                if not match_maintainer(maintainers, maintainer_regex,
                                        match_orphaned):
                    continue
                else:
                    for m in maintainers:
                        s += m.email + " "

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
