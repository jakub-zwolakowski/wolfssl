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

# Files.
compile_commands_path = "compile_commands.json"

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
    {
        "machdep": "gcc_x86_32",
        "pretty_name": "little endian 32-bit (x86)",
        "fields": {
            "address-alignment": 32,
            "compilation_cmd":
                tis.string_of_options(
                    { "-D": [ "NO_CURVED25519_128BIT", "NO_CURVED448_128BIT" ] }
                ),
        }
    },
    {
        "machdep": "gcc_x86_64",
        "pretty_name": "little endian 64-bit (x86)",
        "fields": {
            "address-alignment": 64,
        }
    },
    {
        "machdep": "gcc_ppc_64",
        "pretty_name": "big endian 64-bit (PPC64)",
        "fields": {
            "address-alignment": 64,
            "compilation_cmd":
                tis.string_of_options(
                    { "-D": [ "__BIG_ENDIAN__", "BIG_ENDIAN_ORDER" ] }
                ),
        },
    },
]

# --------------------------------------------------------------------------- #
# ---------------------------------- CHECKS --------------------------------- #
# --------------------------------------------------------------------------- #

# Initial check.
print("1. Check if all necessary directories and files exist...")
tis.check_dir("trustinsoft")
tis.check_file(compile_commands_path)
for file in files_to_copy:
    tis.check_file(file['src'])

# --------------------------------------------------------------------------- #
# -------------------- GENERATE trustinsoft/common.config ------------------- #
# --------------------------------------------------------------------------- #

def normalize_compile_command_json():
    with open(compile_commands_path, "r") as file:
        compile_commands = json.load(file)
    compile_commands.sort(key =
        lambda entry:
            entry["directory"] + " " +
            entry["file"] + " " +
            " ".join(entry["arguments"])
    )
    with open(compile_commands_path, "w") as file:
        file.write(json.dumps(compile_commands, indent=4))

def options_of_compile_command_json(options={"-D":[], "-U":[], "-I":[]}):
    D = set(options["-D"])
    U = set(options["-U"])
    I = set(options["-I"])
    with open(compile_commands_path, "r") as file:
        compile_commands = json.load(file)
        for entry in compile_commands:
            dir = path.relpath(entry["directory"])
            full_dir = path.join(
                dir,
                path.dirname(entry["file"])
            )
            for argument in entry["arguments"]:
                prefix = argument[0:2]
                value = argument[2:]
                if prefix == "-D":
                    D.add(value)
                elif prefix == "-U":
                    U.add(value)
                elif prefix == "-I":
                    I.add(path.normpath(path.join("..", dir, value)))
                    I.add(path.normpath(path.join("..", full_dir, value)))
    return {
        "-D": sorted(list(D)),
        "-I": sorted(list(I)),
        "-U": sorted(list(U)),
    }

# In case of conflicts new compile commands override old compile commands
def union_compile_commands(cc1, cc2):
    # -D
    D1 = sorted(list(set(cc1["-D"]) - set(cc2["-U"])))
    D2 = sorted(list(set(cc2["-D"]) - set(D1)))
    # -U
    U1 = sorted(list(set(cc1["-U"]) - set(cc2["-D"])))
    U2 = sorted(list(set(cc2["-U"]) - set(U1)))
    # -I
    I = sorted(list(set(cc1["-I"]) | set(cc2["-I"])))
    # All together.
    return { "-D": D1 + D2, "-U": U1 + U2, "-I": I }

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
                "arc4.c",
                "asm.c",
                "asn.c",
                # "async.c", # Generated, empty.
                "blake2b.c",
                "blake2s.c",
                "camellia.c",
                "chacha.c",
                "chacha20_poly1305.c",
                "cmac.c",
                "coding.c",
                "compress.c",
                "cpuid.c",
                "cryptocb.c",
                "curve25519.c",
                "curve448.c",
                "des3.c",
                "dh.c",
                "dsa.c",
                "ecc_fp.c",
                "ecc.c",
                "ed25519.c",
                "ed448.c",
                "error.c",
                "evp.c",
                "fe_448.c",
                "fe_low_mem.c",
                "fe_operations.c",
                # "fips_test.c", # Generated.
                # "fips.c", # Generated.
                "ge_448.c",
                "ge_low_mem.c",
                "ge_operations.c",
                "hash.c",
                "hc128.c",
                "hmac.c",
                "idea.c",
                "integer.c",
                "logging.c",
                "md2.c",
                "md4.c",
                "md5.c",
                "memory.c",
                # "misc.c", #warning misc.c does not need to be compiled when using inline (NO_INLINE not defined)
                "pkcs12.c",
                # "pkcs7.c", # ERROR
                "poly1305.c",
                "pwdbased.c",
                "rabbit.c",
                "random.c",
                "rc2.c",
                "ripemd.c",
                "rsa.c",
                # "selftest.c", # Generated.
                "sha.c",
                "sha256.c",
                "sha3.c",
                "sha512.c",
                "signature.c",
                "sp_arm32.c",
                "sp_arm64.c",
                "sp_armthumb.c",
                "sp_c32.c",
                "sp_c64.c",
                "sp_cortexm.c",
                "sp_dsp32.c",
                "sp_int.c",
                "srp.c",
                "tfm.c",
                "wc_dsp.c",
                "wc_encrypt.c",
                "wc_pkcs11.c",
                "wc_port.c",
                # "wolfcrypt_first.c", # Generated.
                # "wolfcrypt_last.c", # Generated.
                "wolfevent.c",
                "wolfmath.c",
                # === WTF are these?
                # "fe_x25519_128.i",
                # "fp_mont_small.i",
                # "fp_mul_comba_12.i",
                # "fp_mul_comba_17.i",
                # "fp_mul_comba_20.i",
                # "fp_mul_comba_24.i",
                # "fp_mul_comba_28.i",
                # "fp_mul_comba_3.i",
                # "fp_mul_comba_32.i",
                # "fp_mul_comba_4.i",
                # "fp_mul_comba_48.i",
                # "fp_mul_comba_6.i",
                # "fp_mul_comba_64.i",
                # "fp_mul_comba_7.i",
                # "fp_mul_comba_8.i",
                # "fp_mul_comba_9.i",
                # "fp_mul_comba_small_set.i",
                # "fp_sqr_comba_12.i",
                # "fp_sqr_comba_17.i",
                # "fp_sqr_comba_20.i",
                # "fp_sqr_comba_24.i",
                # "fp_sqr_comba_28.i",
                # "fp_sqr_comba_3.i",
                # "fp_sqr_comba_32.i",
                # "fp_sqr_comba_4.i",
                # "fp_sqr_comba_48.i",
                # "fp_sqr_comba_6.i",
                # "fp_sqr_comba_64.i",
                # "fp_sqr_comba_7.i",
                # "fp_sqr_comba_8.i",
                # "fp_sqr_comba_9.i",
                # "fp_sqr_comba_small_set.i",
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
    compilation_cmd = options_of_compile_command_json()
    my_options = (
        {
            "-I": [
                "include",
            ],
            "-D": [
                "volatile=",
                "WOLFSSL_UNALIGNED_64BIT_ACCESS",
                "WOLFSSL_CERT_PIV",
                "BENCH_EMBEDDED",
            ],
            "-U": [],
        }
    )
    compilation_cmd = union_compile_commands(compilation_cmd, my_options)
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


print("2. Normalize the '%s' file." % compile_commands_path)
normalize_compile_command_json()

common_config = make_common_config()
with open(common_config_path, "w") as file:
    print("3. Generate the '%s' file." % common_config_path)
    file.write(tis.string_of_json(common_config))


# ---------------------------------------------------------------------------- #
# ------------------ GENERATE trustinsoft/<machdep>.config ------------------- #
# ---------------------------------------------------------------------------- #

def make_machdep_config(machdep):
    machdep_config = {
        "machdep": machdep["machdep"]
    }
    fields = machdep["fields"]
    for field in fields:
        machdep_config[field] = fields[field]
    return machdep_config

print("4. Generate 'trustinsoft/<machdep>.config' files...")
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
    "error",
    "base64",
    "base16",
    "asn",
    "md2",
    "md5",
    "md4",
    "sha",
    "sha224",
    "sha256",
    "sha512",
    "sha384",
    # "sha3", # This one is just regrouping 4 "sha3_*" tests.
    "sha3_224",
    "sha3_256",
    "sha3_384",
    "sha3_512",
    "shake256",
    "hash",
    "hmac_md5",
    "hmac_sha",
    "hmac_sha224",
    "hmac_sha256",
    "hmac_sha384",
    "hmac_sha512",
    "hmac_sha3",
    "hkdf",
    "x963kdf",
    "arc4",
    "rc2",
    "hc128",
    "rabbit",
    "chacha",
    "XChaCha",
    "chacha20_poly1305_aead", # ?
    "XChaCha20Poly1305", # ?
    "des", # ?
    "des3",
    "aes",
    "aes192",
    "aes256",
    "aesofb",
    "cmac",
    "poly1305",
    "aesgcm",
    "aesgcm_default",
    "gmac", # ?
    "aesccm",
    "aeskeywrap",
    "camellia",
    "rsa_no_pad",
    "rsa",
    "dh",
    "dsa",
    "srp",
    "random",
    "pwdbased",
    "ripemd",
    "pbkdf1",
    "pkcs12",
    "pbkdf2",
    "scrypt",
    "ecc",
    "ecc_encrypt",
    "curve25519",
    "ed25519",
    "curve448",
    "ed448",
    "blake2b",
    "blake2s",
    # "compress", # Requires libz.
    # "pkcs7encrypted", # The C file pkcs7.c causes an error.
    # "pkcs7compressed", # The C file pkcs7.c causes an error.
    "pkcs7signed",
    "pkcs7enveloped",
    "pkcs7authenveloped",
    # "pkcs7callback", # Requires arguments.
    "cert",
    "certext",
    "decodedCertCache",
    "idea",
    "memory",
    # "mp", # Requires valgrind.
    "prime",
    "berder",
    "logging",
    "mutex",
    "memcb",
    # "blob", # Check this later...
    "cryptocb",
    "certpiv",
]

def make_test(test_name, machdep):
    return (
        {
            "include": common_config_path,
            "include_": path.join("trustinsoft", "%s.config" % machdep["machdep"]),
            "main": "%s_test" % test_name,
            "name": "%s test, %s" % (test_name, machdep["pretty_name"])
        }
    )

tis_config = list(map(
    lambda t: make_test(t[0], t[1]),
    product(tests, machdeps)
))
with open("tis.config", "w") as file:
    print("5. Generate the 'tis.config' file.")
    file.write(tis.string_of_json(tis_config))


# --------------------------------------------------------------------------- #
# ------------------------------ COPY .h FILES ------------------------------ #
# --------------------------------------------------------------------------- #

print("6. Copy generated files.")
for file in files_to_copy:
    with open(file['src'], 'r') as f_src:
        os.makedirs(path.dirname(file['dst']), exist_ok=True)
        with open(file['dst'], 'w') as f_dst:
            print("   > Copy '%s' to '%s'." % (file['src'], file['dst']))
            shutil.copyfileobj(f_src, f_dst)

# --------------------------------------------------------------------------- #
# ---------------------------- PREP OTHER FILES  ---------------------------- #
# --------------------------------------------------------------------------- #

print("6. Prepare other files.")
with open(path.join("trustinsoft", urandom_filename), 'wb') as file:
    print("   > Create the 'trustinsoft/%s' file." % urandom_filename)
    file.write(os.urandom(urandom_length))
with open(path.join("trustinsoft", null_filename), 'wb') as file:
    print("   > Create the 'trustinsoft/%s' file." % null_filename)
    file.truncate()
