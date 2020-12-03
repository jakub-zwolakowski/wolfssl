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
                    {
                        "-D":
                            [
                                "PIC",
                                "NO_CURVED25519_128BIT",
                                "NO_CURVED448_128BIT",
                            ],
                        "-U": [ "__x86_64__" ],
                        "-I": [ "gcc_x86_32/include" ],
                    }
                ),
        }
    },
    {
        "machdep": "gcc_x86_64",
        "pretty_name": "little endian 64-bit (x86)",
        "fields": {
            "address-alignment": 64,
            "compilation_cmd":
                tis.string_of_options(
                    {
                        "-D":
                            [
                                "PIC",
                                "HAVE___UINT128_T=1",
                                "USE_FAST_MATH",
                                "WOLFSSL_BASE64_ENCODE",
                                "WOLFSSL_X86_64_BUILD",
                            ],
                        "-I": [ "gcc_x86_64/include" ],
                    }
                ),
        }
    },
    {
        "machdep": "gcc_ppc_32",
        "pretty_name": "big endian 32-bit (PPC32)",
        "fields": {
            "address-alignment": 32,
            "compilation_cmd":
                tis.string_of_options(
                    {
                        "-D":
                            [
                                "PIC",
                                "__BIG_ENDIAN__",
                                "BIG_ENDIAN_ORDER",
                                "NO_CURVED25519_128BIT",
                                "NO_CURVED448_128BIT",
                            ],
                         "-U":
                            [
                                "__x86_64__",
                                "HAVE_POLY1305",
                            ],
                         "-I": [ "gcc_ppc_32/include" ],
                    }
                ),
        },
    },
    {
        "machdep": "gcc_ppc_64",
        "pretty_name": "big endian 64-bit (PPC64)",
        "fields": {
            "address-alignment": 64,
            "compilation_cmd":
                tis.string_of_options(
                    {
                        "-D":
                            [
                                "__BIG_ENDIAN__",
                                "BIG_ENDIAN_ORDER",
                                "HAVE___UINT128_T=1",
                            ],
                        "-I": [ "gcc_ppc_64/include" ],
                    }
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
if False:
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
                "dh2048.der",
                "test/cert-ext-nc.der",
                "test/cert-ext-ia.der",
                "test/cert-ext-nct.der",
                "client-key.der",
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
    # THIS DOES NOT WORK, BECAUSE compile_command.json DIFFERS FOR EACH machdep
    # compilation_cmd = options_of_compile_command_json()
    compilation_cmd = (
        {
            "-I": [
                "..",
                "../examples/client",
                "../examples/echoclient",
                "../examples/echoserver",
                "../examples/server",
                "../src",
                "../tests",
                "../testsuite",
                "../wolfcrypt/benchmark",
                "../wolfcrypt/src",
                "../wolfcrypt/test",
            ],
            "-D": [
                "ASN_BER_TO_DER",
                "ATOMIC_USER",
                "BUILDING_WOLFSSL",
                "ECC_SHAMIR",
                "ECC_TIMING_RESISTANT",
                "FP_ECC",
                "FP_MAX_BITS=8192",
                "HAVE_AESCCM",
                "HAVE_AESGCM",
                "HAVE_AES_DECRYPT",
                "HAVE_AES_ECB",
                "HAVE_AES_KEYWRAP",
                "HAVE_ALPN",
                "HAVE_ANON",
                "HAVE_BLAKE2",
                "HAVE_BLAKE2B",
                "HAVE_BLAKE2S",
                "HAVE_CAMELLIA",
                "HAVE_CERTIFICATE_STATUS_REQUEST",
                "HAVE_CERTIFICATE_STATUS_REQUEST_V2",
                "HAVE_CHACHA",
                "HAVE_COMP_KEY",
                "HAVE_CONFIG_H",
                "HAVE_CRL",
                "HAVE_CURVE25519",
                "HAVE_CURVE448",
                "HAVE_DH_DEFAULT_PARAMS",
                "HAVE_ECC",
                "HAVE_ECC_ENCRYPT",
                "HAVE_ED25519",
                "HAVE_ED448",
                "HAVE_ENCRYPT_THEN_MAC",
                "HAVE_EXTENDED_MASTER",
                "HAVE_FFDHE_2048",
                "HAVE_FFDHE_3072",
                "HAVE_HASHDRBG",
                "HAVE_HC128",
                "HAVE_HKDF",
                "HAVE_IDEA",
                "HAVE_MAX_FRAGMENT",
                "HAVE_NULL_CIPHER",
                "HAVE_OCSP",
                "HAVE_ONE_TIME_AUTH",
                "HAVE_OPENSSL_CMD",
                "HAVE_PKCS7",
                "HAVE_PK_CALLBACKS",
                "HAVE_POLY1305",
                "HAVE_RABBIT",
                "HAVE_SCRYPT",
                "HAVE_SNI",
                "HAVE_SUPPORTED_CURVES",
                "HAVE_THREAD_LS",
                "HAVE_TLS_EXTENSIONS",
                "HAVE_TRUNCATED_HMAC",
                "HAVE_TRUSTED_CA",
                "HAVE_WC_INTROSPECTION",
                "HAVE_X963_KDF",
                "HAVE_XCHACHA",
                "KEEP_PEER_CERT",
                "NDEBUG",
                "NO_CHACHA_ASM",
                "NO_MAIN_DRIVER",
                "SESSION_CERTS",
                "SINGLE_THREADED",
                "TFM_ECC256",
                "TFM_NO_ASM",
                "TFM_TIMING_RESISTANT",
                "WC_NO_ASYNC_THREADING",
                "WC_RC2",
                "WC_RSA_BLINDING",
                "WC_RSA_PSS",
                "WOLFCRYPT_HAVE_SRP",
                "WOLFSSL_AES_CFB",
                "WOLFSSL_AES_COUNTER",
                "WOLFSSL_AES_DIRECT",
                "WOLFSSL_AES_OFB",
                "WOLFSSL_AES_XTS",
                "WOLFSSL_ALT_NAMES",
                "WOLFSSL_CERT_EXT",
                "WOLFSSL_CERT_GEN",
                "WOLFSSL_CERT_GEN_CACHE",
                "WOLFSSL_CERT_REQ",
                "WOLFSSL_CMAC",
                "WOLFSSL_CUSTOM_CURVES",
                "WOLFSSL_DER_LOAD",
                "WOLFSSL_ENCRYPTED_KEYS",
                "WOLFSSL_HASH_FLAGS",
                "WOLFSSL_KEY_GEN",
                "WOLFSSL_MD2",
                "WOLFSSL_MULTI_ATTRIB",
                "WOLFSSL_NO_ASM",
                "WOLFSSL_RIPEMD",
                "WOLFSSL_SEP",
                "WOLFSSL_SHA224",
                "WOLFSSL_SHA3",
                "WOLFSSL_SHA384",
                "WOLFSSL_SHA512",
                "WOLFSSL_SHAKE256",
                "WOLFSSL_TEST_CERT",
                "WOLFSSL_TLS13",
                "WOLFSSL_VALIDATE_ECC_IMPORT",
                "WOLFSSL_VALIDATE_ECC_KEYGEN",
                "WOLF_CRYPTO_CB",
            ],
            "-U": []
        }
    )
    my_options = (
        {
            "-I": [],
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
    # "rsa_no_pad", # I think it needs ./configure --enable-opensslall
    "rsa",
    "dh",
    "dsa",
    "srp",
    "random",
    # "pwdbased", # Aggregates 4 tests: pbkdf1, pbkdf2, pkcs12, scrypt.
    "ripemd",
    "pbkdf1",
    "pkcs12",
    "pbkdf2",
    "scrypt", # VERY reduced.
    # "ecc", # Very large and complex.
    # "ecc_encrypt", # Very long, though there is an UB here after 1 hour 20 min (in "ret = -10004")
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
    # "certext", # Requires cert.der file written by rsa_test (I think).
    # "decodedCertCache", # Requires cert.der file written by rsa_test (I think).
    "idea",
    "memory",
    # "mp", # Requires valgrind.
    # "prime", # I think it needs ./configure --enable-keygen ?
    "berder",
    "logging",
    "mutex",
    "memcb",
    # "blob", # Check this later...
    # "cryptocb", # Requires some kind of a device?
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

if False: # TMP
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
if False: # TMP
    with open(path.join("trustinsoft", urandom_filename), 'wb') as file:
        print("   > Create the 'trustinsoft/%s' file." % urandom_filename)
        file.write(os.urandom(urandom_length))
with open(path.join("trustinsoft", null_filename), 'wb') as file:
    print("   > Create the 'trustinsoft/%s' file." % null_filename)
    file.truncate()
