#!/bin/bash

#-- CLONE
git clone https://github.com/wolfSSL/wolfssl.git
cd wolfssl
# DO: on GitHub: fork the wolfssl project
git remote add private https://github.com/jakub-zwolakowski/wolfssl.git
git fetch private

#-- COMPILE & INSTALL (following instructions in the `INSTALL` file)
./autogen.sh
./configure --enable-singlethreaded
bear make
# Remove absolute paths in compile_commands.json
make check
# sudo make install

#-- PREPARE
tis-prepare all-symbol-table -t 6 -- -64 -cpp-tool gcc
#-- DO: Write tis_config.json
tis-prepare tis-config tis_config.json -- --interpreter -64 -cpp-tool gcc

#-- TIS-CI
cp tis_config.json_generated tis.config
# git add tis.config tis_config.json


#-- CHECK
tis-analyzer --interpreter -cpp-tool gcc -tis-config-load tis.config -tis-config-select 1
tis-analyzer --interpreter -cpp-tool gcc -tis-config-load tis.config -tis-config-select 2
tis-analyzer --interpreter -cpp-tool gcc -tis-config-load tis.config -tis-config-select 3
