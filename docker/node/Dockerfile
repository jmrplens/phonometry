# The GPU node image: the CUDA runtime, Python 3.13, CuPy, make and the
# library's pinned dependencies, for `make gpu-parity` on an NVIDIA GPU. It is
# built on the machine that runs it; nothing is published to a registry. The
# base is pinned by digest so a rebuild cannot pick up a different CUDA
# without a change here.
#
# CUDA 13.3.1 is the CUDA of the node's driver, 610.57.04, which reports 13.3,
# so nothing in the image leans on the driver running a newer minor than its
# own. CuPy is the cupy-cuda13x wheel for that major, with its one open
# requirement, cuda-pathfinder, pinned beside it. CuPy compiles its kernels
# when they are first used, with the CUDA headers, which the runtime image
# leaves out: cuda-cudart-dev, at the base image's own cudart version, adds
# them. Ubuntu 24.04 ships Python 3.12, so Python 3.13 comes from the
# deadsnakes PPA. Its signing key is fetched by its full fingerprint, and the
# build stops unless the file holds that one key.
#
# The image keeps a copy of this file, from which scripts/gpu_parity.py
# records the base image a proof ran on.
FROM nvidia/cuda:13.3.1-runtime-ubuntu24.04@sha256:63da350831208559df18c7b8f3e0d5d1c984eaa815cdde690aacd6606cd0cb11
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1
# ca-certificates, curl, make, python3.13 and python3.13-venv go unpinned:
# Ubuntu replaces the first three with each security fix, and the PPA keeps
# only the latest build of each Python patch release, so an exact version
# would stop the image building at the next one. The CUDA headers are pinned,
# to the cudart the base image carries.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl make \
        cuda-cudart-dev-13-3=13.3.29-1 \
    && key=F23C5A6CF475977595C89F51BA6932366A755776 \
    && install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL -o /etc/apt/keyrings/deadsnakes.asc \
        "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$key" \
    && gpg --show-keys --with-colons /etc/apt/keyrings/deadsnakes.asc \
        > /tmp/deadsnakes.keys \
    && test "$(grep -c '^pub:' /tmp/deadsnakes.keys)" = 1 \
    && grep -q "^fpr:::::::::$key:\$" /tmp/deadsnakes.keys \
    && rm -rf /tmp/deadsnakes.keys /root/.gnupg \
    && printf '%s\n' "Types: deb" \
        "URIs: https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu" \
        "Suites: noble" "Components: main" \
        "Signed-By: /etc/apt/keyrings/deadsnakes.asc" \
        > /etc/apt/sources.list.d/deadsnakes.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3.13 python3.13-venv \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
RUN python3.13 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    cupy-cuda13x==14.2.0 cuda-pathfinder==1.8.3
COPY docker/node/Dockerfile /usr/local/share/phonometry-node/Dockerfile
