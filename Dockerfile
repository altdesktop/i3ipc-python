FROM ubuntu:20.04

WORKDIR /app

RUN echo force-unsafe-io > /etc/dpkg/dpkg.cfg.d/docker-apt-speedup
RUN echo 'APT::Acquire::Retries "5";' > /etc/apt/apt.conf.d/80retry

RUN export DEBIAN_FRONTEND=noninteractive; \
    export DEBCONF_NONINTERACTIVE_SEEN=true; \
    echo 'tzdata tzdata/Areas select Etc' | debconf-set-selections; \
    echo 'tzdata tzdata/Zones/Etc select UTC' | debconf-set-selections; \
    apt update && apt install -y --no-install-recommends \
    build-essential git automake autotools-dev libev-dev libxcb1-dev \
    libxcb-util-dev ca-certificates libxkbcommon-dev libxkbcommon-x11-dev \
    libyajl-dev libstartup-notification0-dev libxcb-xinerama0-dev \
    libxcb-randr0-dev libxcb-shape0-dev libxcb-cursor-dev libxcb-keysyms1-dev \
    libxcb-icccm4-dev libxcb-xrm-dev libpcre3-dev libpango1.0-dev \
    libpangocairo-1.0-0 xvfb python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install python-xlib pytest pytest-asyncio pytest-timeout

RUN git clone https://github.com/i3/i3 && \
    cd ./i3 && \
    git checkout cf505ea && \
    autoreconf -fi && \
    ./configure --prefix=/usr && \
    cd ./x86_64-pc-linux-gnu && \
    make -j8 && \
    make install

ADD . /app

#CMD ["bash", "-c", "./run-tests.py ./test/aio/test_window.py"]
CMD ["bash", "-c", "./run-tests.py"]
