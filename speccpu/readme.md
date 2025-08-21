# SPEC CPU 2017

## Step 1: Install SPEC on development machine

```bash
cd SPEC/cpu2017-1.1.0
./install.sh

source shrc  
# or
# source cshrc # it depends on which one is right to your current default terminal bash

# if missing <path>/SPEC/cpu2017-1.1.0/config/flags/clang.xml, copy <path>/SPEC/cpu2017-1.1.0/config/flags/gcc.xml to it.
```

## Step 2: Cross-compile

#### Step 2.1: generate binaries
> running on development manchine
```bash
./speccpu/cross-compile/compile all
# or
./speccpu/cross-compile/compile <benchmark name>
```

or

You can run commands at `SPEC/cpu2017-1.1.0/` folder. (For example)

```bash
# --size: Select data set(s): test, train, ref

# remove the related binary files
runcpu --action clobber --loose --size train --config /home/iiswc/workspace/workload-characterization-on-morello/configs/clang-linux-x86.cfg 538

# compile
runcpu --action runsetup --loose --size train --config /home/iiswc/workspace/workload-characterization-on-morello/configs/clang-linux-x86.cfg 538

```

#### Step 2.2: setup and generate launch script(s)
> running on development manchine
```bash
./specrun/run/setup all
```

#### Step 2.3: distribute binaries
> running on development manchine
```bash
./specrun/run/distribute all <destination-ip: 192.168.1.101>
```

## Step 3: Run 
> running on CheriBSD-Morello

#### Step 3.1: validate binary ABIs
```bash
./specrun/run/check-abi all <destination-ip: 192.168.1.101>
```

#### Step 3.2: launch
```bash
./specrun/run/launch all <destination-ip: 192.168.1.101> <result-folder: ./results/speccpu> <size: test/train/ref>

# for example
./speccpu/run/launch all 192.168.1.101 results/speccpu-train-round-1 train
```

If the `hwpmc` module is not already loaded in CheriBSD-Morello, please run the following commands first.

```bash
kldstat | grep hwpmc
kldload hwpmc
```

## Step 4: Output results
```bash
# Modify this file as needed
./specrun/run/verbose
# or
./specrun/run/verbose-list
```