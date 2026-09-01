FROM kalilinux/kali-rolling:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV GOPATH=/home/xteam_user/go
ENV PATH=$PATH:/home/xteam_user/go/bin

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      wget \
      git \
      gnupg \
      python3 \
      python3-pip \
      figlet \
      lolcat \
      nmap \
      theharvester \
      golang-go \
      tmux \
      gcc \
      make \
      pkg-config \
      # weasyprint / PDF generation deps
      libpango-1.0-0 \
      libharfbuzz0b \
      libcairo2 \
      libgdk-pixbuf2.0-0 \
      libffi-dev \
      shared-mime-info \
      # chromium for headless tools / nuclei
      chromium \
      fonts-liberation \
      fonts-noto-color-emoji \
      # network tools
      dnsutils \
      netcat-openbsd \
      # wireless stack (airgeddon runtime deps)
      aircrack-ng \
      macchanger \
      # cleanup
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash xteam_user && \
    echo "xteam_user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /home/xteam_user

COPY --chown=xteam_user:xteam_user . /home/xteam_user/Xteam

USER xteam_user
RUN pip3 install --no-cache-dir -r /home/xteam_user/Xteam/requirements.txt || true

# Pre-install nuclei to speed up first run
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest || true

EXPOSE 3333 443

ENTRYPOINT ["/bin/bash", "/home/xteam_user/Xteam/Xteam.sh"]
