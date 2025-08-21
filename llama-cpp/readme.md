# LLaMA-CPP

## Step 1: Download from github
> running on development manchine
```bash
cd ~/workspace
git clone https://github.com/ggml-org/llama.cpp.git llama-cpp
cd llama-cpp
git fetch --tags
git checkout -b b3304 b3304
```
>branch: tag b3304

## Step 2: Cross-compile
> (for running on development manchine)

#### Step 2.1: generate binaries
```bash
./llama-cpp/cross-compile/compile
```

#### Step 2.2: setup and generate launch script(s)
```bash
./llama-cpp/run/setup
```

#### Step 2.3: distribute binaries
```bash
./llama-cpp/run/distribute <destination-ip: 192.168.1.101>
```

## Step 3: Run 
> running on CheriBSD-Morello

#### Step 3.1: validate binary ABIs
```bash
./llama-cpp/run/check-abi <destination-ip: 192.168.1.101>
```

#### Step 3.2: launch
```bash
./llama-cpp/run/launch <destination-ip: 192.168.1.101> <result-folder: ./results/llama-cpp>
```

## Step 4: Output results
```bash
# Modify this file as needed
./llama-cpp/run/verbose
# or
./llama-cpp/run/verbose-list
```