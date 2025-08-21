FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install sudo (optional)
RUN apt-get update && apt-get install -y sudo python3 python3-pip\
    && rm -rf /var/lib/apt/lists/*

# Create a new user
RUN useradd -ms /bin/bash scxs \
    && adduser scxs sudo \
    && mkdir -p /etc/sudoers.d \
    && echo "scxs ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/99-scxs

# Switch to this user
USER scxs
WORKDIR /home/scxs

CMD ["bash"]
