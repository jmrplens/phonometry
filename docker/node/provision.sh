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
# Ubuntu 24.04 ships Python 3.12, so Python 3.13 comes from that PPA; its
# signing key is fetched by its full fingerprint, and the build stops unless
# the file holds that one key.
#
# ffmpeg is not Ubuntu's, whose 6.1 carries SVT-AV1 1.7: the documentation
# clips' SVT-AV1 setting is calibrated on SVT-AV1 4, and a CRF means
# something else from one SVT-AV1 major release to the next. The download is
# checked against the SHA-256 the Dockerfile pins before anything in it is
# unpacked, and the build stops on a different sum, a failed download or an
# empty pin. Only ffmpeg, ffprobe and the build's licence are kept.
set -eu
: "${FFMPEG_URL:?docker/node/Dockerfile pins it}" "${FFMPEG_SHA256:?docker/node/Dockerfile pins it}"
key=F23C5A6CF475977595C89F51BA6932366A755776
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg make xz-utils fonts-dejavu-core fontconfig
curl -fsSL --proto '=https' --retry 3 -o /tmp/ffmpeg.tar.xz "$FFMPEG_URL"
printf '%s  %s\n' "$FFMPEG_SHA256" /tmp/ffmpeg.tar.xz | sha256sum -c -
mkdir /tmp/ffmpeg
tar -xJf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1
install -m 0755 /tmp/ffmpeg/bin/ffmpeg /tmp/ffmpeg/bin/ffprobe /usr/local/bin/
install -D -m 0644 /tmp/ffmpeg/LICENSE.txt /usr/local/share/doc/ffmpeg/LICENSE.txt
rm -rf /tmp/ffmpeg /tmp/ffmpeg.tar.xz
install -d -m 0755 /etc/apt/keyrings
curl -fsSL --proto '=https' --retry 3 -o /etc/apt/keyrings/deadsnakes.asc \
    "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$key"
gpg --show-keys --with-colons /etc/apt/keyrings/deadsnakes.asc > /tmp/deadsnakes.keys
test "$(grep -c '^pub:' /tmp/deadsnakes.keys)" = 1
grep -q "^fpr:::::::::$key:\$" /tmp/deadsnakes.keys
rm -rf /tmp/deadsnakes.keys /root/.gnupg
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
