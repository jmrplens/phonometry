# The node image a remote simulation runs in. Two stages build it with one
# provisioning script: `gpu`, on the CUDA runtime, for a node with an NVIDIA
# GPU, and `cpu`, on plain Ubuntu, for a node without one and for the CI job
# that proves a remote run equals a local one. It is built on the machine
# that runs it (make node-image HOST=<name> [TARGET=cpu]); nothing is
# published to a registry. Each base is pinned by digest, and ffmpeg by URL
# and SHA-256, so a rebuild cannot change them unseen.
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
ARG FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-09-30-13-08/ffmpeg-n9.0.2-17-g2a571b6068-linux64-gpl-9.0.tar.xz
ARG FFMPEG_SHA256=68ee646831adaae2495618346f3bba94ff207ff83bbd34d643e7004730d66269

FROM nvidia/cuda:13.3.1-runtime-ubuntu24.04@sha256:63da350831208559df18c7b8f3e0d5d1c984eaa815cdde690aacd6606cd0cb11 AS gpu
ARG FFMPEG_URL
ARG FFMPEG_SHA256
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
COPY docker/node/provision.sh requirements.txt requirements-figures.txt /tmp/node/
RUN sh /tmp/node/provision.sh
RUN apt-get update \
    && apt-get install -y --no-install-recommends cuda-cudart-dev-13-3=13.3.29-1 \
    && rm -rf /var/lib/apt/lists/*
ENV PATH=/opt/venv/bin:$PATH
RUN pip install --no-cache-dir --no-deps cupy-cuda13x==14.2.0 cuda-pathfinder==1.8.3 \
    && pip check
COPY src/phonometry/simulation/_remote/bootstrap.py /usr/local/share/phonometry-node/bootstrap.py
COPY docker/node/Dockerfile /usr/local/share/phonometry-node/Dockerfile

FROM ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac AS cpu
ARG FFMPEG_URL
ARG FFMPEG_SHA256
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1
COPY docker/node/provision.sh requirements.txt requirements-figures.txt /tmp/node/
RUN sh /tmp/node/provision.sh
ENV PATH=/opt/venv/bin:$PATH
COPY src/phonometry/simulation/_remote/bootstrap.py /usr/local/share/phonometry-node/bootstrap.py
COPY docker/node/Dockerfile /usr/local/share/phonometry-node/Dockerfile
