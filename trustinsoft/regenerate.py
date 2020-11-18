#! /usr/bin/env python3

# This script regenerates TrustInSoft CI configuration.

# Run from the root of the wolfSSL project:
# $ python3 trustinsoft/regenerate.py

import tis

import re # sub
import json # dumps, load
from os import path # basename, isdir, join
import glob # iglob

# Directories.
common_config_path = path.join("trustinsoft", "common.config")

# --------------------------------------------------------------------------- #
# ---------------------------------- CHECKS --------------------------------- #
# --------------------------------------------------------------------------- #

# Initial check.
print("1. Check if all necessary directories and files exist...")
tis.check_dir("trustinsoft")

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
                "from": "urandom_1",
            },
            {
                "name": path.join("/", "dev", "null"),
                "from": "null_1",
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

# --------------------------------------------------------------------------- #
# -------------------------------- tis.config ------------------------------- #
# --------------------------------------------------------------------------- #

# tis_config = ()
# with open("tis.config", "w") as file:
#     print("4. Generate the 'tis.config' file.")
#     file.write(string_of_json(tis_config))
