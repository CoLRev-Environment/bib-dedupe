Installation
====================================

This guide provides instructions for installing the `bib-dedupe` library on different platforms, including Windows, MacOS, and Linux. Follow the steps for your operating system.

Installing Python
----------------------------

**Windows:**

1. Check if Python v3.8+ is installed:
   - Open the search field of Windows and enter ``CMD``. Click on Command Prompt.
   - Write ``python --version`` in the Command Prompt and press ENTER.
   - If this returns a number higher than 3.8, Python is installed, and you can proceed with installing `bib-dedupe`. If not, see the installation steps below.

2. Install Python:
   - Go to https://python.org/downloads to download Python for Windows.
   - Install Python for Windows. **IMPORTANT:** Check the box "Add Python to your PATH environment variable" during the installation.

**MacOS:**

1. Check if Python v3.8+ is installed:
   - Open your Launchpad (in your Dock) and search for "Terminal". Click on Terminal.
   - Write ``python --version`` in the Terminal and press ENTER.
   - If this returns a number higher than 3.8, Python is installed, and you can proceed with installing `bib-dedupe`. If not, see the installation steps below.

2. Install Python:
   - Go to https://docs.conda.io/en/latest/miniconda.html#macosx-installers to download the latest version.
   - Install Miniconda for MacOS.

**Linux:**

1. Check if Python v3.8+ is installed:
   - Open a terminal window.
   - Write ``python3 --version`` or ``python --version`` in the terminal and press ENTER.
   - If this returns a number higher than 3.8, Python is installed, and you can proceed with installing `bib-dedupe`. If not, proceed to the next step.

2. Install Python:
   - Use your distribution's package manager to install Python 3.8 or newer. For example, on Ubuntu or Debian-based systems, you can use:

   .. code-block:: bash

      sudo apt update
      sudo apt install python3 python3-pip

   - This will install Python and `pip`, the Python package manager, which is required for the next steps.

Installing pip
--------------

`pip` is automatically installed with Python versions 3.4 and above when using the official Python installer for Windows and MacOS, and through package managers for Linux distributions. If you need to manually install or upgrade `pip`, you can do so by running:

.. code-block:: bash

   python3 -m ensurepip --upgrade

Installing bib-dedupe
---------------------

With Python v3.8+ and `pip` installed, you can now install `bib-dedupe`:

1. Open the Command Prompt (Windows) or Terminal (MacOS/Linux).
2. Install `bib-dedupe` using pip:

.. code-block:: bash

   pip install bib-dedupe

Starting bib-dedupe
-------------------

After installation, you can start using `bib-dedupe` in a Python script, Jupyter notebook, or another Python package. To use `bib-dedupe` in a Python script, you can create a new file (e.g., `deduplication.py`) with the following content:

.. code-block:: python

   import pandas as pd
   from bib_dedupe.bib_dedupe import merge

   # Load your bibliographic dataset into a pandas DataFrame
   records_df = pd.read_csv("records.csv")

   # Get the merged_df
   merged_df = merge(records_df)

   merged_df.to_csv("merged_records.csv", index=False)


Replace `records.csv` with the path to your bibliographic dataset. Run the script using the following command:

.. code-block:: bash

   python deduplication.py
