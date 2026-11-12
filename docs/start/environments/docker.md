← [Documentation index](../../README.md)

# Docker and servers

phonometry needs nothing from the operating system beyond Python on a
`python:*-slim` image: every extra installs from wheels there, libsndfile
inside the soundfile wheel included. The one system package worth adding is
ffmpeg, and only for videos. An Alpine image, built on musl, needs more, since
python-soundfile has no wheel there that carries libsndfile and numba none at
all; [Getting Started](../getting-started.md#installation)
says what each extra takes there.

## An image

```dockerfile
FROM python:3.13-slim
RUN python -m venv /opt/venv \
 && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/python -m pip install --no-cache-dir "phonometry[full]"
ENV PATH=/opt/venv/bin:$PATH MPLCONFIGDIR=/tmp/matplotlib
COPY analyse.py /app/analyse.py
WORKDIR /tmp
CMD ["python", "/app/analyse.py"]
```

The virtual environment keeps pip's warning about running as root out of the
build log. `analyse.py` stands for your own job; this one writes a band
spectrum, its figure and a fiche:

```python
"""A batch job: a one-third-octave analysis, its figure and a fiche."""
from pathlib import Path

import numpy as np

from phonometry import building, filters

out = Path("out")
out.mkdir(exist_ok=True)

fs = 48000
t = np.arange(2 * fs) / fs
x = 0.1 * np.sin(2 * np.pi * 1000 * t)

bands = filters.octave_filter(x, fs, fraction=3)
bands.plot().figure.savefig(out / "bands.png")
impulse = filters.time_weighting(x, fs, mode="impulse")
rating = building.weighted_rating(
    [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58]
)
rating.report(out / "rating.pdf")
print(f"{len(bands.frequencies)} bands, impulse maximum {float(np.max(impulse)):.4f}")
print("wrote", sorted(p.name for p in out.iterdir()))
```

```bash
docker build -t acoustics .
mkdir -p out
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/tmp/out" acoustics
```

```text
33 bands, impulse maximum 0.0092
wrote ['bands.png', 'rating.pdf']
```

The job writes into `out` under its working directory, `/tmp/out` in the
container, and `--rm` deletes the container with its files when the job ends.
The `-v` mount gives that folder to the host as `out` in the directory you run
from, where the figure and the fiche stay. With a Docker daemon that runs as
root, `--user` runs the job as you, so the files are yours and not root's.
Make the folder first: one that such a daemon makes for the mount belongs to
root, and the job, running as you, cannot write in it.

Rootless Docker and rootless Podman already run the container's root as you,
and map every other user id of the container, your own included, to a
subordinate id of the host that cannot write in your `out`: there `--user`
stops the job with a `PermissionError`. Leave it out, or pass
`--userns=keep-id` under Podman, and the files are yours. The folder made
first serves both: rootless Docker would make a missing one as you, and
Podman refuses to mount one that does not exist.

matplotlib picks its Agg backend by itself in a container with no display,
so nothing has to set `MPLBACKEND`.

## Any user, any file system

The image runs the same job as root, as an arbitrary user id
(`docker run --user 12345:12345`), as `nobody`, and on a read-only root file
system with a writable `/tmp` (`docker run --read-only --tmpfs /tmp`). A
folder mounted for the results has to be writable by the user the job runs
as, as `out` is for you above. Two caches and one directory decide how
quietly it does so:

- **`MPLCONFIGDIR`.** matplotlib keeps its configuration and cache under the
  user's home. For a user with no writable home it prints "Matplotlib created
  a temporary cache directory at ..." each time it starts; the `ENV` line
  above points it at `/tmp` instead, and it says nothing.
- **numba's cache.** numba keeps the compiled `impulse` kernel beside the
  package or under the home directory. Where it can write to neither, it
  compiles the kernel once in each process instead and says nothing. With
  `NUMBA_CACHE_DIR=/tmp/numba` it writes the kernel there, for the processes
  that follow in the same container.
- **A read-only root.** The job needs somewhere to write: here its working
  directory, `/tmp`, which `--tmpfs /tmp` keeps writable, and the `out`
  folder mounted inside it from the host. With no writable mount at all, the
  job stops at its own `out.mkdir`.

## Videos

`io.write_video` and the FDTD animation writers run ffmpeg. Install it from
the image's own packages before the virtual environment:

```dockerfile
FROM python:3.13-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv \
 && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/python -m pip install --no-cache-dir "phonometry[full]"
ENV PATH=/opt/venv/bin:$PATH MPLCONFIGDIR=/tmp/matplotlib
```

WebM and MP4 then encode on the CPU, as `nobody` and on a read-only root
with a writable `/tmp` alike. [Writing videos](../../io/videos.md) covers
the encoders and a node that has a GPU.

## Servers and threads

A server that handles requests in a thread pool may import the domains it
needs from those threads, several at once. [Sending a simulation to a remote
node](../../simulation/remote-node.md) covers an FDTD run the server
should not step itself.
