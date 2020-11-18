
import re # sub
import json # dumps, load
from os import path # basename, isdir, join

# Outputting JSON.
def string_of_json(obj):
    # Output standard pretty-printed JSON (RFC 7159) with 4-space indentation.
    s = json.dumps(obj, indent=4)
    # Sometimes we need to have multiple "include" fields in the outputted
    # JSON, which is unfortunately impossible in the internal python
    # representation (OK, it is technically possible, but too cumbersome to
    # bother implementing it here), so we can name these fields 'include_',
    # 'include__', etc, and they are all converted to 'include' before
    # outputting as JSON.
    s = re.sub(r'"include_+"', '"include"', s)
    return s

# Make a command line from a dictionary of lists.
def string_of_options(options):
    elts = []
    for opt_prefix in options: # e.g. opt_prefix == "-D"
        for opt_value in options[opt_prefix]: # e.g. opt_value == "HAVE_OPEN"
            elts.append(opt_prefix + opt_value) # e.g. "-DHAVE_OPEN"
    return " ".join(elts)

# Assert that a directory exists.
def check_dir(dir):
    if path.isdir(dir):
        print("   > OK! Directory '%s' exists." % dir)
    else:
        exit("   > ERROR! Directory '%s' not found." % dir)

# Assert that a file exists.
def check_file(file):
    if path.isfile(file):
        print("   > OK! File '%s' exists." % file)
    else:
        exit("   > ERROR! File '%s' not found." % file)
