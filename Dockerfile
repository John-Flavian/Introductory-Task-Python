FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y systemd nano nginx

# Add a custom service file
COPY server.service /etc/systemd/system/server.service

# Add a script to start systemd
COPY start-systemd.sh /start-systemd.sh
RUN chmod +x /start-systemd.sh

VOLUME [ "/sys/fs/cgroup" ]

CMD ["/start-systemd.sh"]


