## Build docker image
run in the `notebook` folder:
```bash
docker build --network=host -t iiswc25ae-base .
docker run -it --rm --network=host -v /home/:/host-machine/ --user scxs iiswc25ae-base
```

copy the files in host-machine into docker container:
- ~/cheri/build/morello-llvm-project-build
- ~/cheri/output/rootfs-morello-purecap
- ~/cheri/output/morello-sdk
- ~/workspace/workload-characterization-on-morello
- ~/workspace/llama-cpp
- ~/workspace/matrix-multiply
- ~/workspace/quickjs
- ~/workspace/SPEC/cpu2017-1.1.0/
- ~/workspace/sqlite-bench

```bash
docker commit <my_container> iiswc25ae-image
docker save -o iiswc25ae-image.tar iiswc25ae-image
```

## Deploy
Run the following commands in development machine with public IP.
```bash
# scp into another machine
docker load -i iiswc25ae-image.tar
docker run -d --network=host --name iiswc25ae -v /home/:/host-machine/ --user scxs iiswc25ae-image:v2 tail -f /dev/null

jupyter notebook --generate-config
jupyter notebook password

jupyter notebook --no-browser --ip=0.0.0.0 --port=8888 iiswc25ae.ipynb
```

Run the following command in Morello
```bash
autossh -M 0 -NT \
  -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -o "ExitOnForwardFailure yes" \
  -R 127.0.0.1:2201:localhost:22 \
  xshaun@35.193.148.121

# Start (as root or a dedicated user)
env AUTOSSH_GATETIME=0 \
/usr/sbin/daemon -r -R 5 \
  -P /var/run/autossh_2201.supervisor.pid \
  -t autossh_2201 \
  /usr/local/bin/autossh -M 0 -NT \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -R 127.0.0.1:2201:localhost:22 \
    xshaun@35.193.148.121
```

Configure ssh inside the container:
```bash
Host *
  Port 2201
```

Run the following command inside the container:
```bash
ssh-copy-id root@127.0.0.1
ssh-copy-id scxs@127.0.0.1
```