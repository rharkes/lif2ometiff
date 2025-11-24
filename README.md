[![Mypy](https://github.com/rharkes/lif2ometiff/actions/workflows/mypy.yml/badge.svg)](https://github.com/rharkes/lif2ometiff/actions/workflows/mypy.yml)
[![Ruff](https://github.com/rharkes/lif2ometiff/actions/workflows/ruff.yml/badge.svg)](https://github.com/rharkes/lif2ometiff/actions/workflows/ruff.yml)
# lif2ometif
Converts a .lif file to a pyramidal tiled compressed .ome.tif file, and saves the meta-data as .xml file.

## Installation
* Download the executable for linux or windows at [releases](https://github.com/rharkes/lif2ometiff/releases/latest).
* Put somewhere that is present in the Path.
* Run `lif2ometiff` or `lif2ometiff -h` for help. 

## Running code
Clone repository and install:
`uv pip install .`

### Example
To convert all scenes to seperate files:
```python
from pathlib import Path

import bioio_lif
from bioio import BioImage

from lif2ometiff import save_tiff, slugify

folder = Path(r"D:\temp")
outfolder = Path(r"D:\temp")
file = Path(folder, "somefile.lif")
myimage = BioImage(
    file,
    reader=bioio_lif.Reader,
    is_x_and_y_swapped=False,
    is_x_flipped=True,
    is_y_flipped=True
)
for i in range(len(myimage.scenes)):
    myimage.set_scene(i)
    save_tiff(
        myimage,
        Path(outfolder, f"{file.stem}_{slugify(myimage.current_scene)}.ome.tif"),
    )
```

## Build Instructions
Install with development dependencies: `uv pip install -e .[dev]`

Build with: `pyinstaller main.spec`