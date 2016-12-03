#!/usr/bin/env python3

import portage
import os, os.path
import re
import random
import urllib.request
import multiprocessing.pool

# unavailable or fetch restricted patches
blacklist=["ut2004-lnxpatch3369-2.tar.bz2",
           "ambertools-1.5-bugfix_1-10.patch.xz"]

portdir="/usr/portage"

def get_portdb():
    return portage.portdb

def get_cpv(portdb):
    cpv_list = list()

    for cp in portdb.cp_all(trees=[portdir]):
        cpv_list.extend(portdb.cp_list(cp))

    return cpv_list

def get_fetchmap(portdb, atom):
    return portdb.getFetchMap(atom)

def filter_fetchmap(fetchmap, regex):
    for key in fetchmap:
        if not regex.match(key):
            fetchmap.pop(key)
        if key in blacklist:
            fetchmap.pop(key)

    return fetchmap

def __expand_mirror__(portdb, uri):
    if not uri[:9] == "mirror://":
        return [uri]

    eidx = uri.find("/", 9)
    mirrorname = uri[9:eidx]
    path = uri[eidx+1:]
    thirdpartymirrors = portdb.settings.thirdpartymirrors()

    return [mirror_uri.rstrip("/") + "/" + path
            for mirror_uri in thirdpartymirrors[mirrorname]]

def expand_mirrors(portdb, fetchmap):
    for f in fetchmap:
        fetchlist = list()
        for uri in fetchmap[f]:
            fetchlist.extend(__expand_mirror__(portdb, uri))

        random.shuffle(fetchlist)
        # Try gentoo distfiles as a last resort
        fetchlist.append("http://distfiles.gentoo.org/distfiles/" + f)

        fetchmap[f] = fetchlist

    return fetchmap

def retrieve_uri(uri_list, path):
    if os.path.exists(path):
        return ""

    for uri in uri_list:
        try:
            urllib.request.urlretrieve(uri, path)
            return uri
        except:
            print("uri failed: " + uri)
            continue

    raise Exception("Unable to fetch the patch: " + path)

def get_compression_extension(path):
    return path[path.rindex(".")+1:]

def get_uncompressed_path(path):
    return path[:path.rindex(".")]

def get_file_size(path):
    return os.path.getsize(path)

def retrieve_fetchmap(fetchmap, basedir):
    ret = dict()

    for f in fetchmap:
        p = get_uncompressed_path(f)
        ext = get_compression_extension(f)
        ret[p] = dict()

        ret[p]["basedir"] = basedir
        ret[p]["extensions"] = [ext]
        ret[p][ext + "_path"] = os.path.join(basedir, f)

        ret[p]["uri"] = retrieve_uri(fetchmap[f], ret[p][ext + "_path"])
        ret[p][ext + "_size"] = get_file_size(ret[p][ext + "_path"])

    return ret

def decompress_xz(s_path, d_path):
    os.system("xzcat -k {} > {}".format(s_path, d_path))

def decompress_bz2(s_path, d_path):
    os.system("bunzip2 < {} > {}".format(s_path, d_path))

def decompress_patch(s_path, d_path, ext):
    if ext == "xz":
        decompress_xz(s_path, d_path)
    elif ext == "bz2":
        decompress_bz2(s_path, d_path)
    else:
        raise Exception("Unknown compression format: " + ext)

def decompress_patches(patches):
    for patch in patches:
        ext = patches[patch]["extensions"][0] # any type is ok
        s_path = patches[patch][ext + "_path"]
        d_path = os.path.join(patches[patch]["basedir"], patch)

        if not os.path.exists(d_path):
            decompress_patch(s_path, d_path, ext)

        patches[patch]["path"] = d_path
        patches[patch]["size"] = get_file_size(d_path)

    return patches

def compress_xz(s_path, d_path):
    os.system("xz -c {} > {}".format(s_path, d_path))

def compress_bz2(s_path, d_path):
    os.system("bzip2 -c {} > {}".format(s_path, d_path))

def populate_compressed_variations(patches, extensions):
    for patch in patches:
        for ext in extensions:
            if ext in patches[patch]["extensions"]:
                continue

            p = patches[patch]["path"] + "." + ext
            if not os.path.exists(p):
                if ext == "xz":
                    compress_xz(patches[patch]["path"], p)
                elif ext == "bz2":
                    compress_bz2(patches[patch]["path"], p)
                else:
                    raise Exception("Unknown compression format: " + ext)

            patches[patch]["extensions"].append(ext)
            patches[patch][ext + "_path"] = p
            patches[patch][ext + "_size"] = get_file_size(p)

    return patches

def flatten_patches(patches_collection):
    ret = dict()

    # First level is a map generated from fetchmaps
    for patches in patches_collection:
        # Second level is a dict of patches generated from a fetchmap
        for patch in patches:
            ret[patch] = patches[patch]

    return ret

def report(patches):
    for patch in patches:
        ext_0 = patches[patch]["extensions"][0]
        ext_1 = patches[patch]["extensions"][1]

        if patches[patch][ext_1 + "_size"] < patches[patch][ext_0 + "_size"]:
            print("{},{},{},{}".format(patch, ext_0, patches[patch][ext_0 + "_size"], patches[patch][ext_1 + "_size"]))

def main():
    regex = re.compile(".*(patch|patches).*[.](xz|bz2)")
    portdb = get_portdb()
    atoms = get_cpv(portdb)
    basedir="/tmp/patch-compressibility"
    extensions=["bz2", "xz"]
    thread_pool = multiprocessing.pool.ThreadPool()

    def __get_filtered_fetchmap__(atom):
        fetchmap = get_fetchmap(portdb, atom)
        fetchmap = filter_fetchmap(fetchmap, regex)
        return fetchmap

    def __expand_mirrors__(fetchmap):
        return expand_mirrors(portdb, fetchmap)

    def __retrieve_fetchmap__(fetchmap):
        return retrieve_fetchmap(fetchmap, basedir)

    def __populate_compressed_variations__(patches):
        return populate_compressed_variations(patches, extensions)

    os.makedirs(basedir, exist_ok=True)
    fetchmaps = map(__get_filtered_fetchmap__, atoms)
    # Cleanup empty fetchmaps
    fetchmaps = [fetchmap for fetchmap in fetchmaps if bool(fetchmap) is True]
    fetchmaps = map(__expand_mirrors__, fetchmaps)
    patches = thread_pool.map(__retrieve_fetchmap__, fetchmaps)
    patches = thread_pool.map(decompress_patches, patches)
    patches = thread_pool.map(__populate_compressed_variations__, patches)
    # Flatten nested dictionaries
    patches = flatten_patches(patches)

    report(patches)

if __name__ in "__main__":
    exit(main())
