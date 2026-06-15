# build.spec — PyInstaller configuration for AutoBIDSify ExecVal
#
# Build (run from the execval/ directory):
#     pyinstaller build.spec
#
# Produces dist/AutoBIDSify/ (onedir). Onedir is chosen over onefile for
# faster startup and fewer antivirus false positives.
#
# This app uses pywebview, which renders the UI in the OS-native WebView
# (Edge WebView2 on Windows, WebKit on macOS, WebKitGTK on Linux), so no
# browser engine is bundled — that keeps the package small.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# --- Data files: ship the web UI and the vendored autobidsify source ---
datas = [
    ("web", "web"),                       # HTML/CSS/JS UI
    ("vendor/autobidsify", "vendor/autobidsify"),  # trimmed library
]

# Scientific libraries load some modules dynamically; collect their data
# files so they resolve at runtime inside the bundle.
for pkg in ["bids_validator", "bidsschematools", "snirf", "nibabel"]:
    datas += collect_data_files(pkg)

# --- Hidden imports: things PyInstaller's static analysis misses ---
hidden = []
for pkg in ["scipy", "h5py", "nibabel", "snirf", "bjdata",
            "bids_validator", "bidsschematools", "yaml", "numpy"]:
    hidden += collect_submodules(pkg)

# pywebview backend hooks (Windows uses the EdgeChromium / WebView2 backend).
hidden += [
    "webview",
    "webview.platforms.winforms",   # Windows backend
    "clr_loader",                   # pythonnet loader used by winforms backend
    "proxy_tools",
    "bottle",
]

# --- Excludes: drop large modules we never use, to shrink the package ---
excludes = [
    "tkinter",
    "matplotlib",
    "pytest", "_pytest",
    "PyQt5", "PyQt6", "PySide2", "PySide6", "qtpy",  # not used (pywebview WebView2)
    "IPython", "jupyter", "notebook",
    "pandas",          # not used by the execute/validate path
    "PIL", "Pillow",
    "scipy.spatial", "scipy.optimize", "scipy.signal",  # unused scipy subpkgs
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
    upx=False,           # UPX off: avoids antivirus false positives
    console=False,       # GUI app: no console window
    # icon="resources/icon.ico",   # uncomment when you add an icon
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
