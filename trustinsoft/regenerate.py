#! /usr/bin/env python3

# This script regenerates TrustInSoft CI configuration.

# Run from the root of the wolfSSL project:
# $ python3 trustinsoft/regenerate.py

import tis

import re # sub
import json # dumps, load
import os # makedirs
from os import path # path.basename, path.isdir, path.join
import glob # iglob
from itertools import product  # Cartesian product of lists.
import shutil # copyfileobj

# --------------------------------------------------------------------------- #
# -------------------------------- SETTINGS --------------------------------- #
# --------------------------------------------------------------------------- #

# Directories.
common_config_path = path.join("trustinsoft", "common.config")
include_dir = path.join("trustinsoft", "include")

# Generated files which need to be a part of the repository.
def make_simple_copy_file(src_path):
    return (
        {
            "src": src_path,
            "dst": path.join(include_dir, src_path),
        }
    )

files_to_copy = [
    make_simple_copy_file("config.h"),
    make_simple_copy_file(path.join("wolfssl", "options.h")),
]

# Random file length.
urandom_filename = "urandom"
urandom_length = 4096

# Null file.
null_filename = "null"

# Architectures.
machdeps = [
    # "gcc_x86_32",
    "gcc_x86_64",
    # "gcc_ppc_64",
]

# --------------------------------------------------------------------------- #
# ---------------------------------- CHECKS --------------------------------- #
# --------------------------------------------------------------------------- #

# Initial check.
print("1. Check if all necessary directories and files exist...")
tis.check_dir("trustinsoft")
for file in files_to_copy:
    tis.check_file(file['src'])

# --------------------------------------------------------------------------- #
# -------------------- GENERATE trustinsoft/common.config ------------------- #
# --------------------------------------------------------------------------- #

def make_common_config():
    # C files.
    c_files = (
        [ path.join("..", "wolfcrypt", "test", "test.c") ] +
        [ "stub.c" ] +
        list(map(
            lambda file: path.join("..", "src", file),
            [
                "internal.c",
                "ssl.c",
                "tls.c",
            ])) +
        list(map(
            lambda file: path.join("..", "wolfcrypt", "src", file),
            [
                "aes.c",
                "asn.c",
                "chacha.c",
                "chacha20_poly1305.c",
                "coding.c",
                "ecc.c",
                "error.c",
                "hash.c",
                "hmac.c",
                "md5.c",
                "memory.c",
                "poly1305.c",
                "random.c",
                "rsa.c",
                "sha.c",
                "sha256.c",
                "sha3.c",
                "sha512.c",
                "tfm.c",
                "wc_encrypt.c",
                "wc_port.c",
            ]))
    )
    # Filesystem.
    filesystem_files = (
        [{ "name": "./certs/ntru-key.raw" }] +
        list(map(
            lambda file:
                {
                    "name": path.join(".", "certs", file),
                    "from": path.join("..", "certs", file),
                },
            [
                "server-cert.pem",
                "server-key.pem",
                "ca-cert.pem",
            ]
        )) +
        [
            {
                "name": path.join("/", "dev", "urandom"),
                "from": urandom_filename,
            },
            {
                "name": path.join("/", "dev", "null"),
                "from": null_filename,
            }
        ]
    )
    # Compilation options.
    compilation_cmd = (
        {
            "-I": [
                "include",
            ],
            "-D": [
                "volatile=",
                "WOLFSSL_UNALIGNED_64BIT_ACCESS"
            ],
            "-U": [],
        }
    )
    # Whole common.config JSON.
    config = (
        {
            "files": c_files,
            "filesystem": { "files": filesystem_files },
            "compilation_cmd": tis.string_of_options(compilation_cmd),
        }
    )
    # Done.
    return config

common_config = make_common_config()
with open(common_config_path, "w") as file:
    print("2. Generate the '%s' file." % common_config_path)
    file.write(tis.string_of_json(common_config))


# ---------------------------------------------------------------------------- #
# ------------------ GENERATE trustinsoft/<machdep>.config ------------------- #
# ---------------------------------------------------------------------------- #

def make_machdep_config(machdep):
    return (
        {
            "machdep": machdep,
        }
    )

print("3. Generate 'trustinsoft/<machdep>.config' files...")
machdep_configs = map(make_machdep_config, machdeps)
for machdep_config in machdep_configs:
    file = path.join("trustinsoft", "%s.config" % machdep_config["machdep"])
    with open(file, "w") as f:
        print("   > Generate the '%s' file." % file)
        f.write(tis.string_of_json(machdep_config))

# --------------------------------------------------------------------------- #
# --------------------------- GENERATE tis.config --------------------------- #
# --------------------------------------------------------------------------- #

tests = [
    "error_test",
    "base64_test",
    "asn_test",
    "random_test",
    "md5_test",
    "sha_test",
    "sha224_test",
    "sha256_test",
    "sha384_test",
    "sha512_test",
    "main"
]

machdep_names = {
    "gcc_x86_32": "little endian 32-bit (x86)",
    "gcc_x86_64": "little endian 64-bit (x86)",
    "gcc_ppc_64": "big endian 64-bit (PPC64)",
}

def make_test(test_name, machdep):
    return (
        {
            "include": common_config_path,
            "compilation_database": [
                "compile_commands.json"
            ],
            "include_": path.join("trustinsoft", "%s.config" % machdep),
            "main": test_name,
            "name": "'%s' from 'wolfcrypt/test/test.c' %s" % (test_name, machdep_names[machdep])
        }
    )

tis_config = list(map(
    lambda t: make_test(t[0], t[1]),
    product(tests, machdeps)
))
with open("tis.config", "w") as file:
    print("4. Generate the 'tis.config' file.")
    file.write(tis.string_of_json(tis_config))


# --------------------------------------------------------------------------- #
# ------------------------------ COPY .h FILES ------------------------------ #
# --------------------------------------------------------------------------- #

print("5. Copy generated files.")
for file in files_to_copy:
    with open(file['src'], 'r') as f_src:
        os.makedirs(path.dirname(file['dst']), exist_ok=True)
        with open(file['dst'], 'w') as f_dst:
            print("   > Copy '%s' to '%s'." % (file['src'], file['dst']))
            shutil.copyfileobj(f_src, f_dst)

# --------------------------------------------------------------------------- #
# ---------------------------- PREP OTHER FILES  ---------------------------- #
# --------------------------------------------------------------------------- #

print("5. Prepare other files.")
with open(path.join("trustinsoft", urandom_filename), 'wb') as file:
    print("   > Create the 'trustinsoft/%s' file." % urandom_filename)
    file.write(os.urandom(urandom_length))
with open(path.join("trustinsoft", null_filename), 'wb') as file:
    print("   > Create the 'trustinsoft/%s' file." % null_filename)
    file.truncate()
