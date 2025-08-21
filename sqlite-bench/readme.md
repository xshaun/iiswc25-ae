# SQLite-bench

## Step 1: Download from github
> running on development manchine

```bash
cd ~/workspace
git clone https://github.com/ukontainer/sqlite-bench.git
# https://github.com/sqlite/sqlite
cd sqlite-bench
```

## Step 2: Cross-compile
> running on development manchine

#### Step 2.1: generate binaries
```bash
./sqlite-bench/cross-compile/compile
```

>The issue arises because the SQLite source code contains excessive use of (void *), which causes in-address security checks to fail. We have resolved the compilation errors, and the patched source code is available at `./src4purecap`. The other way is to use the successfully compiled binaries from the `bin` folder, taken from CheriBSD `pkg64c` and `pkg64`.


<!-- ---
SQLite 3.42.0 2023-05-16 12:36:15 831d0fb2836b71c9bc51067c49fee4b8f18047814f2ff22d817d25195cf3alt1
--- -->

#### Step 2.2: setup and generate launch script(s)
```bash
./sqlite-bench/run/setup
```

#### Step 2.3: distribute binaries
```bash
./sqlite-bench/run/distribute <destination-ip: 192.168.1.101>
```

## Step 3: Run 
> (for running on CheriBSD-Morello)

#### Step 3.1: validate binary ABIs
```bash
./sqlite-bench/run/check-abi <destination-ip: 192.168.1.101>
```

#### Step 3.2: launch
```bash
./sqlite-bench/run/launch <destination-ip: 192.168.1.101> <result-folder: ./results/sqlite-bench>
```

## Step 4: Output results
```bash
# Modify this file as needed
./sqlite-bench/run/verbose
# or
./sqlite-bench/run/verbose-list
```
