# %% [markdown]
# # Setup check
#
# Run this once before Day 1. It imports what the labs use, reads the data of the case study, checks that the data
# matches its generator and says whether the one optional live step (Lab 2.1, step 4) has a key. Nothing here
# needs a key, a model or an accelerator.

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-312.git"
    if not Path("/content/ae-312").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ae-312"], check=True)
    os.chdir("/content/ae-312/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("mawj.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

# %%
import importlib

missing = []
for name in ("pandas", "numpy", "duckdb", "matplotlib", "nbclient"):
    try:
        module = importlib.import_module(name)
        print(f"✅ {name} {getattr(module, '__version__', '')}")
    except ImportError:
        missing.append(name)
        print(f"❌ {name} is missing: run `uv sync` in labs/ (in Colab, rerun the first cell)")
print(f"Python {sys.version.split()[0]}")

# %%
import mawj as M
import maabar

u = M.usage()
inv = M.invoice()
print(f"✅ usage log: {len(u):,} requests | invoice: {M.sar(inv.amount_sar.sum())} in {len(inv)} lines")
print(f"✅ tasks: " + ", ".join(f"{app} {len(M.tasks(app))}" for app in ("anis", "khulasa", "fasil")))
print(f"✅ gateway model: {maabar.Gateway.__name__} | reference results: {len(list(M.REF.glob('*.json')))} files")

# %%
done = subprocess.run([sys.executable, "prepare_data.py", "--check"], capture_output=True, text=True)
print(("✅ " if done.returncode == 0 else "❌ ") + (done.stdout or done.stderr).strip())

# %%
if M.live():
    print("A key is set: Lab 2.1, step 4 will call these free hosted models:", M.LIVE_MODELS)
else:
    print("No key: Lab 2.1, step 4 will use the supplied outputs and say so. Every other step of every lab runs without a model.")
print("\nSetup is complete." if not missing else f"\nMissing: {missing}")
