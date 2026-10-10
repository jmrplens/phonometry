// Copyright (c) 2026. Jose Manuel Requena Plens
//
// phonometry in Pyodide, the Python that JupyterLite runs in the browser.
//
//   node tests/pyodide/smoke.mjs install dist/phonometry-<version>-py3-none-any.whl
//   node tests/pyodide/smoke.mjs run dist/phonometry-<version>-py3-none-any.whl
//
// A JupyterLite user installs a package with micropip, which resolves numpy,
// scipy and matplotlib to the WebAssembly builds Pyodide ships, whatever PyPI
// holds, and a pure Python package such as reportlab from PyPI. `install` does
// what that user does: micropip.install of the wheel with its requirements,
// then of the requirements of each extra a notebook uses (`plot` for .plot(),
// `report` for .report()), each with keep_going, so every requirement Pyodide
// cannot meet is named at once; for each one that is not met it also says
// which floor of the wheel the Pyodide build falls short of, read from the
// wheel and from Pyodide's own lock file. `run` installs the wheel without its
// requirements, on the numpy and scipy Pyodide ships, imports the package and
// runs a one-third-octave filter bank on a 1 kHz tone: whether the code itself
// runs there, apart from whether the floors let it install. Each exits
// non-zero on failure, with a GitHub annotation naming it.

import { readFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { loadPyodide } from "pyodide";

const [phase, wheelPath] = process.argv.slice(2);
if (!["install", "run"].includes(phase) || !wheelPath) {
  console.error("usage: node smoke.mjs install|run <wheel>");
  process.exit(2);
}

const lockPath = join(
  dirname(fileURLToPath(import.meta.resolve("pyodide"))),
  "pyodide-lock.json",
);
const pyodide = await loadPyodide();
await pyodide.loadPackage(["micropip", "packaging"]);
const wheel = `/wheels/${basename(wheelPath)}`;
pyodide.FS.mkdirTree("/wheels");
pyodide.FS.writeFile(wheel, readFileSync(wheelPath));
pyodide.globals.set("WHEEL", wheel);
pyodide.globals.set("LOCK", readFileSync(lockPath, "utf8"));
pyodide.globals.set("PYODIDE_VERSION", pyodide.version);

// The extras a notebook user installs beside the package.
const EXTRAS = ["plot", "report"];

// Install the wheel with its requirements, then the requirements of each
// extra, as a JupyterLite user would; for every install that fails, the
// message micropip gave and the floors of the wheel that the builds Pyodide
// ships fall short of. The result is JSON: {"": ..., "plot": ..., ...}, one
// entry per install, null for one that succeeded.
const INSTALL = `
import json
import zipfile

import micropip
from packaging.requirements import Requirement
from packaging.version import Version

shipped = {
    name.lower(): package["version"]
    for name, package in json.loads(LOCK)["packages"].items()
}
with zipfile.ZipFile(WHEEL) as archive:
    metadata = next(
        name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
    )
    lines = archive.read(metadata).decode().splitlines()
requires = [
    Requirement(line.partition(":")[2].strip())
    for line in lines
    if line.startswith("Requires-Dist:")
]


def core(requirement):
    return requirement.marker is None or requirement.marker.evaluate({"extra": ""})


def spelled(requirement):
    extras = "[" + ",".join(sorted(requirement.extras)) + "]" if requirement.extras else ""
    return f"{requirement.name}{extras}{requirement.specifier}"


def shortfall(requirements):
    out = []
    for requirement in requirements:
        version = shipped.get(requirement.name.lower())
        if version is not None and Version(version) not in requirement.specifier:
            out.append(f"{spelled(requirement)} (Pyodide ships {version})")
    return out


groups = {"": [requirement for requirement in requires if core(requirement)]}
for extra in EXTRAS.to_py():
    groups[extra] = [
        requirement
        for requirement in requires
        if not core(requirement) and requirement.marker.evaluate({"extra": extra})
    ]

outcome = {}
for group, requirements in groups.items():
    try:
        if group:
            await micropip.install([spelled(r) for r in requirements], keep_going=True)
        else:
            await micropip.install("emfs:" + WHEEL, keep_going=True)
        outcome[group] = None
    except Exception as error:  # micropip names every requirement it could not meet
        outcome[group] = {"message": str(error), "shortfall": shortfall(requirements)}
json.dumps(outcome)
`;

// An import and a one-third-octave bank on a 1 kHz tone of amplitude 1,
// whose band reads 20 log10((1/sqrt 2) / 20 uPa) = 90.97 dB less the
// filter's own loss, a few hundredths; and the table a notebook shows.
const RUN = `
import numpy as np
import scipy

import phonometry
from phonometry import filters

fs = 48000
tone = np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)
bank = filters.octave_filter(tone, fs=fs, fraction=3)
level = float(bank.levels[bank.frequencies.index(1000.0)])
if abs(level - 90.97) > 0.1 or level < float(np.max(bank.levels)):
    raise RuntimeError(f"the 1 kHz band reads {level} dB")
if '<div class="phonometry-record">' not in bank._repr_html_():
    raise RuntimeError("the result does not display as its table")
f"phonometry {phonometry.__version__} on numpy {np.__version__} and scipy " \\
    f"{scipy.__version__}: the 1 kHz band of a unit tone reads {level:.2f} dB"
`;

if (phase === "install") {
  pyodide.globals.set("EXTRAS", EXTRAS);
  const outcome = JSON.parse(await pyodide.runPythonAsync(INSTALL));
  const wheelName = basename(wheelPath);
  const shortfalls = [];
  let unexplained = false;
  for (const [group, failure] of Object.entries(outcome)) {
    const what = group ? `the ${group} extra of ${wheelName}` : wheelName;
    if (failure === null) {
      console.log(`ok  ${what} installs in Pyodide ${pyodide.version} with its requirements`);
      continue;
    }
    console.log(`${what} does not install: ${failure.message}`);
    if (failure.shortfall.length === 0) {
      unexplained = true;
    } else {
      const needs = failure.shortfall.join("; ");
      shortfalls.push(group ? `its ${group} extra requires ${needs}` : `it requires ${needs}`);
    }
  }
  if (shortfalls.length > 0) {
    console.log(
      `::error::${wheelName} cannot be installed in Pyodide ${pyodide.version}, ` +
        `so not in JupyterLite with its extras: ${shortfalls.join("; ")}. ` +
        "It installs there once the floors in pyproject.toml are within what " +
        "Pyodide ships, or once Pyodide ships newer builds.",
    );
  }
  if (unexplained) {
    console.log(`::error::phonometry fails to install in Pyodide ${pyodide.version}`);
  }
  process.exit(shortfalls.length > 0 || unexplained ? 1 : 0);
}

try {
  await pyodide.loadPackage(["numpy", "scipy"]);
  await pyodide.runPythonAsync(`
import micropip
await micropip.install("emfs:" + WHEEL, deps=False)
`);
  const line = await pyodide.runPythonAsync(RUN);
  console.log(`ok  ${line} in Pyodide ${pyodide.version}`);
} catch (error) {
  console.log(String(error.message ?? error));
  console.log(`::error::phonometry fails in Pyodide ${pyodide.version} (run)`);
  process.exit(1);
}
