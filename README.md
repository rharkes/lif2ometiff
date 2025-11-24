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

from lif2ometiff import save_tiff, save_tiff_tiles, slugify

folder = Path(r"D:\temp")
outfolder = Path(r"D:\temp")
file = Path(folder, "somefile.lif")
myimage = BioImage(
    file,
    reader=bioio_lif.Reader,
    reconstruct_mosaic=False,
    is_x_and_y_swapped=False,
    is_x_flipped=True,
    is_y_flipped=True,
)
for i in range(len(myimage.scenes)):
    myimage.set_scene(i)
    if "M" in myimage.dims.order:
        n_tiles = len(myimage.get_mosaic_tile_positions())
        dims = "".join([c for c in myimage.dims.order if c != "M"])
        if n_tiles > 1:
            for j in range(n_tiles):
                dask_img = myimage.get_image_dask_data(dims, M=j)
                save_tiff_tiles(
                    myimage,
                    dask_img,
                    Path(outfolder, f"{file.stem}_tile_{str(j+1)}_{slugify(myimage.current_scene)}.ome.tif"),
                )
        else:
            save_tiff(
                myimage,
                Path(outfolder, f"{file.stem}_{slugify(myimage.current_scene)}.ome.tif"),
            )
    else:
        save_tiff(
            myimage,
            Path(outfolder, f"{file.stem}_{slugify(myimage.current_scene)}.ome.tif"),
        )
```

## Build Instructions
Install with development dependencies: `uv pip install -e .[dev]`

Build with: `pyinstaller main.spec`