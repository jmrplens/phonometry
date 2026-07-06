# PyOctaveBand → phonometry

**PyOctaveBand has been renamed to [phonometry](https://pypi.org/project/phonometry/).**

This is a transition package: installing or upgrading `PyOctaveBand` installs
`phonometry` and provides a `pyoctaveband` module that re-exports the full,
unchanged API with a `DeprecationWarning`. Your existing code keeps working,
but new code should use the new name:

```bash
pip install phonometry
```

```python
import phonometry  # instead of: import pyoctaveband
```

The API is identical — renaming the import is a complete migration.

- Documentation: https://jmrplens.github.io/phonometry/
- Repository: https://github.com/jmrplens/phonometry
- Last release under the old name: [`pyoctaveband-v2` branch](https://github.com/jmrplens/phonometry/tree/pyoctaveband-v2)
