FROM ubuntu:19.10

WORKDIR /app

RUN apt update && apt install ca-certificates -y && \
    /usr/lib/apt/apt-helper download-file https://debian.sur5r.net/i3/pool/main/s/sur5r-keyring/sur5r-keyring_2019.02.01_all.deb keyring.deb SHA256:176af52de1a976f103f9809920d80d02411ac5e763f695327de9fa6aff23f416 && \
    dpkg -i ./keyring.deb && \
    echo "deb http://debian.sur5r.net/i3/ $(grep '^DISTRIB_CODENAME=' /etc/lsb-release | cut -f2 -d=) universe" >> /etc/apt/sources.list.d/sur5r-i3.list && \
    apt install i3-wm python3-pip xvfb -y

RUN pip3 install python-xlib pytest pytest-asyncio pytest-timeout

ADD . /app

CMD ["./run-tests.py"]
