import math
import re
import unicodedata
import xml.etree.ElementTree as etree
from pathlib import Path

import numpy as np
from bioio import BioImage
from dask.array import Array
from tifffile import TiffWriter


def save_tiff(image: BioImage, pth: Path) -> None:
    """
    pixelsize, channelnames, dimensions
    :param image:
    :param pth:
    :return:
    """
    with open(Path(pth.parent, pth.stem[0:-4] + ".xml"), "wb") as fp:
        fp.write(etree.tostring(image.metadata))
    with TiffWriter(pth, bigtiff=True, ome=True) as tif:
        subresolutions = max([0, math.floor(math.log2(max(image.shape))) - 9])
        print(f"Writing {subresolutions + 1} subresolutions.")
        dims = image.dims.order
        if not ((dims[-2::] == "XY") | (dims[-2::] == "YX")):
            raise ValueError(f"Dimension order {dims} is not supported.")
        dims_squeeze = "".join([x for i, x in enumerate(dims) if image.shape[i] != 1])
        channelnames = [str(x) for x in image.channel_names]
        metadata = {
            "axes": dims_squeeze,
            "SignificantBits": 8 * image.dtype.itemsize,
            "PhysicalSizeX": image.physical_pixel_sizes.X,
            "PhysicalSizeXUnit": "µm",
            "PhysicalSizeY": image.physical_pixel_sizes.Y,
            "PhysicalSizeYUnit": "µm",
            "Channel": {"Name": channelnames},
        }
        if image.time_interval:
            metadata["TimeIncrement"] = image.time_interval
            metadata["TimeIncrementUnit"] = "s"
        if image.physical_pixel_sizes.Z:
            metadata["PhysicalSizeZ"] = image.physical_pixel_sizes.Z
            metadata["PhysicalSizeZUnit"] = "µm"
        print(f"Loading data: {image.shape} pixels: {dims}")
        data = np.squeeze(image.data)
        print(f"Writing data: {data.shape} pixels: {dims_squeeze}")
        physical_pixel_size_x = (
            (1e4 / image.physical_pixel_sizes.X) if image.physical_pixel_sizes.X else 1
        )
        physical_pixel_size_y = (
            (1e4 / image.physical_pixel_sizes.Y) if image.physical_pixel_sizes.Y else 1
        )
        tif.write(
            data,
            subifds=subresolutions,
            resolution=(
                physical_pixel_size_x,
                physical_pixel_size_y,
            ),
            metadata=metadata,
            tile=(512, 512),
            photometric="minisblack",
            compression="zlib",
            resolutionunit="CENTIMETER",
        )
        for level in range(subresolutions):
            mag = 2 ** (level + 1)
            tif.write(
                data[..., ::mag, ::mag],
                subfiletype=1,
                resolution=(
                    physical_pixel_size_x * mag,
                    physical_pixel_size_y * mag,
                ),
                tile=(512, 512),
                photometric="minisblack",
                compression="zlib",
                resolutionunit="CENTIMETER",
            )


def save_tiff_tiles(image: BioImage, pth: Path) -> None:
    """
    pixelsize, channelnames, dimensions
    :param image:
    :param pth:
    :return:
    """
    n_tiles = len(image.get_mosaic_tile_positions())
    dims = "".join([c for c in image.dims.order if c != "M"])
    for i in range(n_tiles):
        img_dask = image.get_image_dask_data(dims, M=i)
        pth_tile = Path(pth.parent, f"{pth.stem}_{slugify(image.current_scene)}_tile_{str(i+1)}.ome.tif")
        with open(Path(pth_tile.parent, pth_tile.stem[0:-4] + ".xml"), "wb") as fp:
            fp.write(etree.tostring(image.metadata))
        with TiffWriter(pth_tile, bigtiff=True, ome=True) as tif:
            if not ((dims[-2::] == "XY") | (dims[-2::] == "YX")):
                raise ValueError(f"Dimension order {dims} is not supported.")
            dims_squeeze = "".join([x for i, x in enumerate(dims) if img_dask.shape[i] != 1])
            channelnames = [str(x) for x in image.channel_names]
            metadata = {
                "axes": dims_squeeze,
                "SignificantBits": 8 * image.dtype.itemsize,
                "PhysicalSizeX": image.physical_pixel_sizes.X,
                "PhysicalSizeXUnit": "µm",
                "PhysicalSizeY": image.physical_pixel_sizes.Y,
                "PhysicalSizeYUnit": "µm",
                "Channel": {"Name": channelnames},
            }
            if image.time_interval:
                metadata["TimeIncrement"] = image.time_interval
                metadata["TimeIncrementUnit"] = "s"
            if image.physical_pixel_sizes.Z:
                metadata["PhysicalSizeZ"] = image.physical_pixel_sizes.Z
                metadata["PhysicalSizeZUnit"] = "µm"
            print(f"Loading data: {img_dask.shape} pixels: {dims}")
            data = np.squeeze(img_dask)
            print(f"Writing data: {data.shape} pixels: {dims_squeeze}")
            physical_pixel_size_x = (
                (1e4 / image.physical_pixel_sizes.X) if image.physical_pixel_sizes.X else 1
            )
            physical_pixel_size_y = (
                (1e4 / image.physical_pixel_sizes.Y) if image.physical_pixel_sizes.Y else 1
            )
            tif.write(
                data,
                resolution=(
                    physical_pixel_size_x,
                    physical_pixel_size_y,
                ),
                metadata=metadata,
                tile=(512, 512),
                photometric="minisblack",
                compression="zlib",
                resolutionunit="CENTIMETER",
            )


def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
