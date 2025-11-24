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


def save_tiff_tiles(image: BioImage, img_tile_dask: Array, pth: Path) -> None:
    """
    pixelsize, channelnames, dimensions
    :param image:
    :param img_tile_dask:
    :param pth:
    :return:
    """
    with open(Path(pth.parent, pth.stem[0:-4] + ".xml"), "wb") as fp:
        fp.write(etree.tostring(image.metadata))
    with TiffWriter(pth, bigtiff=True, ome=True) as tif:
        dims = "".join([c for c in image.dims.order if c != "M"])
        if not ((dims[-2::] == "XY") | (dims[-2::] == "YX")):
            raise ValueError(f"Dimension order {dims} is not supported.")
        dims_squeeze = "".join([x for i, x in enumerate(dims) if img_tile_dask.shape[i] != 1])
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
        print(f"Loading data: {img_tile_dask.shape} pixels: {dims}")
        data = np.squeeze(np.asarray(img_tile_dask))
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
