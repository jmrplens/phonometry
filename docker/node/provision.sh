#!/bin/sh
# Provision a phonometry node image: Python 3.13 with the pinned requirements
# and the figure stack, the DejaVu fonts the figures are drawn with, a static
# ffmpeg build and make. Run once by each stage of docker/node/Dockerfile, on
# Ubuntu 24.04 with or without CUDA, with FFMPEG_URL and FFMPEG_SHA256 set by
# the Dockerfile.
#
# The apt packages go unpinned: Ubuntu replaces them with each security fix,
# and the deadsnakes PPA keeps only the latest build of each Python patch
# release, so an exact version would stop the image building at the next one.
# Ubuntu 24.04 ships Python 3.12, so Python 3.13 comes from that PPA. Its
# signing key is docker/node/deadsnakes.asc, which the Dockerfile copies in
# beside this script: the key Launchpad publishes for the PPA, whose
# fingerprint is set below as key, kept in the repository so that a build
# reaches no keyserver. A build that fetched it stopped whenever
# keyserver.ubuntu.com did not answer. The build stops unless the file holds
# that one key and nothing else, before it reaches apt's keyrings.
#
# ffmpeg is not Ubuntu's, whose 6.1 carries SVT-AV1 1.7: the documentation
# clips' SVT-AV1 setting is calibrated on SVT-AV1 4, and a CRF means
# something else from one SVT-AV1 major release to the next. The download is
# checked against the SHA-256 the Dockerfile pins before anything in it is
# unpacked, and the build stops on a different sum, a failed download or an
# empty pin. A try that fails is repeated, up to five times, after waits of
# 1, 2, 4, 8 and 16 seconds, or what a server's Retry-After asks. --retry
# alone would give up at once on a connection refused or unreachable, curl's
# exit 7, which --retry-all-errors retries with any other failure, and each
# try gives up on a connection not made within 30 seconds, so a host that
# does not answer stops the build after about three and a half minutes. Only
# ffmpeg, ffprobe and the build's licence are kept.
set -eu
: "${FFMPEG_URL:?docker/node/Dockerfile pins it}" "${FFMPEG_SHA256:?docker/node/Dockerfile pins it}"
key=F23C5A6CF475977595C89F51BA6932366A755776
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg make xz-utils fonts-dejavu-core fontconfig
curl -fsSL --proto '=https' --retry 5 --retry-all-errors --connect-timeout 30 \
    -o /tmp/ffmpeg.tar.xz "$FFMPEG_URL"
printf '%s  %s\n' "$FFMPEG_SHA256" /tmp/ffmpeg.tar.xz | sha256sum -c -
mkdir /tmp/ffmpeg
tar -xJf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1
install -m 0755 /tmp/ffmpeg/bin/ffmpeg /tmp/ffmpeg/bin/ffprobe /usr/local/bin/
install -D -m 0644 /tmp/ffmpeg/LICENSE.txt /usr/local/share/doc/ffmpeg/LICENSE.txt
rm -rf /tmp/ffmpeg /tmp/ffmpeg.tar.xz
gpg --show-keys --with-colons /tmp/node/deadsnakes.asc > /tmp/deadsnakes.keys
test "$(grep -c '^pub:' /tmp/deadsnakes.keys)" = 1
test "$(grep '^fpr:' /tmp/deadsnakes.keys)" = "fpr:::::::::$key:"
rm -rf /tmp/deadsnakes.keys /root/.gnupg
install -D -m 0644 /tmp/node/deadsnakes.asc /etc/apt/keyrings/deadsnakes.asc
printf '%s\n' "Types: deb" \
    "URIs: https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu" \
    "Suites: noble" "Components: main" \
    "Signed-By: /etc/apt/keyrings/deadsnakes.asc" \
    > /etc/apt/sources.list.d/deadsnakes.sources
apt-get update
apt-get install -y --no-install-recommends python3.13 python3.13-venv
apt-get purge -y curl
apt-get autoremove -y
rm -rf /var/lib/apt/lists/*
python3.13 -m venv /opt/venv
/opt/venv/bin/pip install --no-cache-dir \
    -r /tmp/node/requirements.txt -r /tmp/node/requirements-figures.txt
rm -rf /tmp/node
