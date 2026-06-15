# build.spec — PyInstaller configuration for AutoBIDSify ExecVal (Tkinter)
#
# Build (run from the execval/ directory):
#     pyinstaller build.spec
#
# Produces dist/AutoBIDSify/ (onedir). The GUI is pure Tkinter (bundled with
# Python), so there is NO pywebview / pythonnet / .NET / Qt / GTK to collect.
# This makes Windows packaging reliable (no "Python.Runtime.Loader" errors).

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# --- Data files: ship the vendored autobidsify source ---
datas = [
    ("vendor/autobidsify", "vendor/autobidsify"),  # trimmed library
]

# Scientific libraries load some modules dynamically; collect their data files.
for pkg in ["bids_validator", "bidsschematools", "snirf", "nibabel"]:
    datas += collect_data_files(pkg)

# --- Hidden imports: things PyInstaller's static analysis misses ---
hidden = []
for pkg in ["scipy", "h5py", "nibabel", "snirf", "bjdata",
            "bids_validator", "bidsschematools", "yaml", "numpy"]:
    hidden += collect_submodules(pkg)

# --- Excludes: drop large modules we never use, to shrink the package ---
# NOTE: tkinter is NOT excluded here — it is the GUI.
excludes = [
    "matplotlib",
    "pytest", "_pytest",
    "PyQt5", "PyQt6", "PySide2", "PySide6", "qtpy",
    "webview", "pywebview", "clr", "pythonnet", "clr_loader",  # not used anymore
    "IPython", "jupyter", "notebook",
    "pandas",
    "PIL", "Pillow",
    "scipy.spatial", "scipy.optimize", "scipy.signal",
    "scipy.stats", "scipy.fft", "scipy.interpolate",
]

a = Analysis(
    ["main.py"],
    pathex=["vendor"],     # so 'import autobidsify' resolves to vendored copy
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoBIDSify",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    # icon="resources/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="AutoBIDSify",
)
