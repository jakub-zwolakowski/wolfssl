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
    "base16_test",
    "asn_test",
    "md2_test",
    "md5_test",
    "md4_test",
    "sha_test",
    "sha224_test",
    "sha256_test",
    "sha512_test",
    "sha384_test",
    "sha3_test",
    "shake256_test",
    "hash_test",
    "hmac_md5_test",
    "hmac_sha_test",
    "hmac_sha224_test",
    "hmac_sha256_test",
    "hmac_sha384_test",
    "hmac_sha512_test",
    "hmac_sha3_test",
    "hkdf_test",
    "x963kdf_test",
    "arc4_test",
    "rc2_test",
    "hc128_test",
    "rabbit_test",
    "chacha_test",
    "XChaCha_test",
    "chacha20_poly1305_aead_test",
    "XChaCha20Poly1305_test",
    "des_test",
    "des3_test",
    "aes_test",
    "aes192_test",
    "aes256_test",
    "aesofb_test",
    "cmac_test",
    "poly1305_test",
    "aesgcm_test",
    "aesgcm_default_test",
    "gmac_test",
    "aesccm_test",
    "aeskeywrap_test",
    "camellia_test",
    "rsa_no_pad_test",
    "rsa_test",
    "dh_test",
    "dsa_test",
    "srp_test",
    "random_test",
    "pwdbased_test",
    "ripemd_test",
    "pbkdf1_test",
    "pkcs12_test",
    "pbkdf2_test",
    "scrypt_test",
    "ecc_test",
    "ecc_encrypt_test",
    "curve25519_test",
    "ed25519_test",
    "curve448_test",
    "ed448_test",
    "blake2b_test",
    "blake2s_test",
    "compress_test",
    "pkcs7encrypted_test",
    "pkcs7compressed_test",
    "pkcs7signed_test",
    "pkcs7enveloped_test",
    "pkcs7authenveloped_test",
    "pkcs7callback_test",
    "cert_test",
    "certext_test",
    "decodedCertCache_test",
    "idea_test",
    "memory_test",
    "mp_test",
    "prime_test",
    "berder_test",
    "logging_test",
    "mutex_test",
    "memcb_test",
    "blob_test",
    "cryptocb_test",
    "certpiv_test",
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
