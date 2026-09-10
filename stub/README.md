# PyOctaveBand is now [phonometry](https://pypi.org/project/phonometry/)

Same author, same project, grown well past what the old name described. The
package you installed for fractional octave-band filtering now runs 995
conformance checks across 77 domains and 408 standards, and reaches from
filters, weighting and sound level metrology to psychoacoustics, rooms and
buildings, materials, vibration, environmental, aircraft and underwater
acoustics, electroacoustics and wave simulation. Every metric is implemented
from its governing standard and pinned to a number printed in it.

```bash
pip install phonometry[full]
```

```python
import phonometry  # instead of: import pyoctaveband
```

## What this package is

A bridge, not the library. Installing or upgrading `PyOctaveBand` installs
phonometry and gives you a `pyoctaveband` module that re-exports it with a
`FutureWarning`, which Python shows by default so the notice actually reaches
you.

It resolves `phonometry>=3.0.0,<4`, the last line whose API is the API of the
final release under the old name. Within it the old name and the new one
expose the same functions, which is what makes the shim honest.

The bridge ends there, and on purpose. phonometry 4.0 moved every name into
the module of its domain, so a `PyOctaveBand` that installed 4.x would resolve
to a library that raises `AttributeError` for names `pyoctaveband` promises.
This package will not follow it. Install phonometry under its own name and
take the guide below: it maps every 3.x name to its new home, and it names the
three places where the obvious fix is the wrong one.

- Upgrading to 4.0: https://jmrplens.github.io/phonometry/start/upgrading/
- Documentation: https://jmrplens.github.io/phonometry/
- Package: https://pypi.org/project/phonometry/
- Repository: https://github.com/jmrplens/phonometry
- Last release under the old name: [`pyoctaveband-v2` branch](https://github.com/jmrplens/phonometry/tree/pyoctaveband-v2)
