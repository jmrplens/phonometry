---
title: "simulation.compute"
description: "Where an FDTD simulation runs: the device, its dtype and what to do if absent."
sidebar:
  label: "compute"
---

Where an FDTD simulation runs: the device, its dtype and what to do if absent.

A [`Compute`](/phonometry/reference/api/simulation/compute/#compute) record is a request. Building one imports and probes
nothing, so a record naming a GPU can be written on a machine without one;
the engine checks the request when it is built. The request comes from the
`compute=` argument, else from the innermost [`use`](/phonometry/reference/api/simulation/compute/#use) block, else from
the `PHONOMETRY_COMPUTE` environment variable, else it is NumPy in float64.

[`use`](/phonometry/reference/api/simulation/compute/#use) holds its record in a context variable. Whether a new thread or
process sees it depends on how it is started; give a worker its placement
through `compute=` or `PHONOMETRY_COMPUTE`.

The environment variable is read when a computation resolves its placement,
never at import. Its grammar is `device[:index][@host][,option...]` with the
options `float32`, `float64` and `fallback`: `cupy`, `cupy:1`,
`torch:cuda:1,fallback`, `torch:mps,float32`, `cupy@nas`. A host is a
name in the hosts file (see the guide on remote nodes); only
[`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) and
[`elastic_fdtd_simulation`](/phonometry/reference/api/simulation/elastic-fdtd/#elastic_fdtd_simulation) run on one.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## Compute

```python
Compute(
    *,
    device: Literal['cpu', 'cupy', 'torch:cpu', 'torch:cuda', 'torch:mps'] = 'cpu',
    device_index: int = 0,
    dtype: Literal['float64', 'float32'] = 'float64',
    fallback: bool = False,
    host: str | None = None,
    timeout_s: float | None = None,
)
```

Where an FDTD simulation steps, in which dtype, and whether it may fall back.

**Parameters**

| Name | Description |
| :--- | :--- |
| `device` | The array library and device: `"cpu"` (NumPy, the default), `"cupy"` (an NVIDIA GPU through CuPy), `"torch:cpu"`, `"torch:cuda"` or `"torch:mps"` (Apple silicon, float32 only). |
| `device_index` | Which GPU, for `"cupy"` and `"torch:cuda"`. |
| `dtype` | `"float64"` (default) or `"float32"`. |
| `fallback` | Run on NumPy, with a [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning), when the device is not available, instead of raising. |
| `host` | The node the run goes to, by its name in the hosts file, or `None` (default) to run on this machine. Only [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) and [`elastic_fdtd_simulation`](/phonometry/reference/api/simulation/elastic-fdtd/#elastic_fdtd_simulation) run on a node; an engine built here refuses a host. |
| `timeout_s` | The longest a remote run may take, from connecting to the result [s], or `None` for the hosts file's value (no limit when the file names none). Only with a `host`. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a `device` or `dtype` that is not text, a `device_index` that is not a number (a bool is not one), a `fallback` that is not `True` or `False`, a `host` that is neither text nor `None`, or a `timeout_s` that is not one number. |
| ValueError | for an unknown device or dtype, `"torch:mps"` in float64, an index on a device that has one instance, an index that is not a whole number of 0 or more, a `host` that is not a name the hosts file can hold, a `timeout_s` without a host or not positive, or a fallback asked of `"cpu"` on this machine. |

## ComputeDeviceError

A requested device is not present or cannot be used.

## ComputeFallbackWarning

A requested device was not available and the run went to NumPy.

## ComputeImportError

The library a requested device needs is not installed, or does not import.

## ComputeRemoteError

A run sent to a node failed in the connection or on the node.

Raised for a transport failure (no ssh client, a node that cannot be
reached, a stream that breaks the protocol, a run past its timeout) and
for a failure on the node (an image or a Python environment that cannot
run the package, an exception raised by the run itself). A wrong
argument is never one: it raises its own `TypeError` or `ValueError`
before anything connects.

**Attributes**

| Name | Description |
| :--- | :--- |
| `host` | The node's name in the hosts file. |
| `node_traceback` | The traceback the node printed, as text, when the run raised there; it is also attached as a note, so a traceback printed here shows it. |

## RunProvenance

```python
RunProvenance(
    *,
    host: str | None,
    device: Literal['cpu', 'cupy', 'torch:cpu', 'torch:cuda', 'torch:mps'],
    device_index: int,
    dtype: Literal['float64', 'float32'],
    numpy_version: str,
    array_library: str | None,
    cuda_runtime: str | None,
    cuda_driver_api: str | None,
    gpu: str | None,
    package_digest: str | None,
)
```

Where a run actually stepped, recorded by the result.

**Attributes**

| Name | Description |
| :--- | :--- |
| `host` | The node the run went to, or `None` for this machine. |
| `device` | The device that stepped the fields. |
| `device_index` | Which GPU, `0` where there is one. |
| `dtype` | The dtype of the fields. |
| `numpy_version` | NumPy's version where the run stepped. |
| `array_library` | The array library and its version (`"cupy 14.2.0"`), or `None` for NumPy. |
| `cuda_runtime` | The CUDA runtime the array library uses, as `"major.minor"` (`"13.2"`), or `None` off a CUDA device. |
| `cuda_driver_api` | The CUDA version the GPU driver supports, as `"major.minor"` (`"13.3"`), where the array library reports it (CuPy), else `None`. It is not the NVIDIA driver's own version. |
| `gpu` | The GPU's name, or `None`. |
| `package_digest` | The SHA-256 of the package the node ran, in lowercase hex, or `None` for a run on this machine. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a `device` or `dtype` that is not text, a `device_index` that is not a number (a bool is not one), a `numpy_version` that is not text, or a `host`, `array_library`, `cuda_runtime`, `cuda_driver_api`, `gpu` or `package_digest` that is neither text nor `None`. |
| ValueError | for an unknown device or dtype, `"torch:mps"` in float64, an index on a device that has one instance, an index that is not a whole number of 0 or more, or a `package_digest` that is not 64 lowercase hexadecimal digits. |

## use

```python
use(compute: Compute) -> Iterator[Compute]
```

Make *compute* the placement of every simulation built in this block.

The record lives in a context variable. Whether a new thread or process
sees it depends on how it is started; give a worker its placement through
`compute=` or `PHONOMETRY_COMPUTE`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `compute` | The placement. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for anything but a [`Compute`](/phonometry/reference/api/simulation/compute/#compute). |
