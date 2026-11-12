# The node image a remote simulation runs in. Two stages build it with one
# provisioning script: `gpu`, on the CUDA runtime, for a node with an NVIDIA
# GPU, and `cpu`, on plain Ubuntu, for a node without one and for the CI job
# that proves a remote run equals a local one. It is built on the machine
# that runs it (make node-image HOST=<name> [TARGET=cpu]); nothing is
# published to a registry. Each base is pinned by digest, ffmpeg by URL and
# SHA-256, and the signing key of the deadsnakes PPA, which Python 3.13 comes
# from, is a file of the repository checked by its fingerprint, so a rebuild
# cannot change them unseen.
#
# docker/node/provision.sh installs what both stages share: Python 3.13, the
# pinned requirements with the figure stack, the DejaVu fonts, ffmpeg and
# make. The gpu stage then adds the CUDA headers CuPy compiles its kernels
# with, pinned to the cudart the base image carries, and CuPy with its one
# open requirement pinned beside it. CuPy goes in without its requirements,
# so pip cannot swap the pinned NumPy for one in CuPy's range: pip check
# stops the build instead when the pinned NumPy falls outside it. Both
# stages copy the bootstrap a node runs first from the package, to the path
# the client runs it at.
#
# CUDA 13.3.1 is the CUDA of the node's driver, 610.57.04, which reports
# 13.3, so nothing in the image leans on the driver running a newer minor
# than its own. NVIDIA_DRIVER_CAPABILITIES adds video, without which the
# container has no NVENC. The image keeps a copy of this file, from which
# scripts/gpu_parity.py records the base image a proof ran on.
#
# ffmpeg is a static build from BtbN's FFmpeg-Builds (GPL, linux64), with
# SVT-AV1 4, NVENC, VP9, dav1d and VMAF. Ubuntu's ffmpeg 6.1 carries SVT-AV1
# 1.7, and the documentation clips' SVT-AV1 setting is calibrated on SVT-AV1
# 4. The pin names a month-end release, which BtbN keeps for about two years
# (its daily ones for two weeks). Dependabot cannot move a URL: the workflow
# node-ffmpeg.yml says each month whether a newer month-end build is out, or
# whether this one has gone. To move the pin, take that build's URL and the
# SHA-256 its release's checksums.sha256 lists for it, rebuild the image on a
# node with make node-image, and check there that ffmpeg -version names the
# new release and that a libsvtav1 encode reports SVT-AV1 4. A build with
# another SVT-AV1 major waits until the clips' setting is calibrated on it.
#
# The PPA's key, docker/node/deadsnakes.asc, is the export Launchpad gives at
# https://api.launchpad.net/devel/~deadsnakes/+archive/ubuntu/ppa?ws.op=getSigningKeyData
# (a JSON string of the armored key), byte for byte. Its fingerprint,
# F23C5A6CF475977595C89F51BA6932366A755776, is the one the PPA's page on
# Launchpad shows and the PPA's record in that API gives as
# signing_key_fingerprint; keyserver.ubuntu.com serves the same key. Both
# stages copy it in, the build reaches no keyserver, and provision.sh stops
# the build unless the file holds that one key alone. Should Launchpad sign
# the PPA with another key, apt stops at the PPA's index: take the new
# export, check its fingerprint against the PPA's page, and move together
# the file and every place that names its fingerprint: this paragraph,
# provision.sh's key and tests/test_node_image.py, which fails while this
# file or provision.sh names any other key.
ARG FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-10-31-12-59/ffmpeg-n9.0.2-39-g7adfbe40dc-linux64-gpl-9.0.tar.xz
ARG FFMPEG_SHA256=73e29a56974ae5a651133a04584c7483b21afe941e17dc91d79814a758b608d3

FROM nvidia/cuda:13.3.1-runtime-ubuntu24.04@sha256:63da350831208559df18c7b8f3e0d5d1c984eaa815cdde690aacd6606cd0cb11 AS gpu
ARG FFMPEG_URL
ARG FFMPEG_SHA256
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
COPY docker/node/provision.sh docker/node/deadsnakes.asc requirements.txt requirements-figures.txt /tmp/node/
RUN sh /tmp/node/provision.sh
RUN apt-get update \
    && apt-get install -y --no-install-recommends cuda-cudart-dev-13-3=13.3.29-1 \
    && rm -rf /var/lib/apt/lists/*
ENV PATH=/opt/venv/bin:$PATH
RUN pip install --no-cache-dir --no-deps cupy-cuda13x==14.2.0 cuda-pathfinder==1.8.3 \
    && pip check
COPY src/phonometry/simulation/_remote/bootstrap.py /usr/local/share/phonometry-node/bootstrap.py
COPY docker/node/Dockerfile /usr/local/share/phonometry-node/Dockerfile

FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852 AS cpu
ARG FFMPEG_URL
ARG FFMPEG_SHA256
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1
COPY docker/node/provision.sh docker/node/deadsnakes.asc requirements.txt requirements-figures.txt /tmp/node/
RUN sh /tmp/node/provision.sh
ENV PATH=/opt/venv/bin:$PATH
COPY src/phonometry/simulation/_remote/bootstrap.py /usr/local/share/phonometry-node/bootstrap.py
COPY docker/node/Dockerfile /usr/local/share/phonometry-node/Dockerfile
