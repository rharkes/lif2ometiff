import argparse
from pathlib import Path

import bioio_lif
from bioio import BioImage

from lif2ometiff import __version__, save_tiff, save_tiff_tiles, slugify


def get_args() -> argparse.Namespace:
    myparser = argparse.ArgumentParser(
        prog="lif2ometiff",
        description="Converts leica .lif files to .ome.tiff files",
        epilog="By R.Harkes - NKI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    myparser.add_argument(
        "-i",
        "--input",
        type=str,
        help="The input folder containing the .lif files",
        default=Path.cwd(),
    )

    myparser.add_argument(
        "-o",
        "--output",
        type=str,
        help="The output folder where .ome.tiff files will be stored",
        default=Path.cwd(),
    )

    myparser.add_argument(
        "-m",
        "--mosaic",
        type=bool,
        help="Whether to perform a basic merge of mosaic scans. Crops pixels when True! Default False",
        default=False,
    )

    myparser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Display the version of lif2ometiff",
        default=False,
    )
    return myparser.parse_args()


if __name__ == "__main__":
    args = get_args()
    if args.version:
        print(f"lif2ometiff version: {__version__}")
    else:
        liffiles = [x for x in Path(args.input).glob("*.lif")]
        print(f"Found {len(liffiles)} liffiles.")
        for liffile in liffiles:
            myimage = BioImage(
                liffile,
                reader=bioio_lif.Reader,
                reconstruct_mosaic=args.mosaic,
                is_x_and_y_swapped=False,
                is_x_flipped=True,
                is_y_flipped=True,
            )
            for i in range(len(myimage.scenes)):
                myimage.set_scene(i)
                save_tiff(
                    myimage,
                    Path(
                        Path(args.output),
                        f"{liffile.stem}_{slugify(myimage.current_scene)}.ome.tif",
                    ),
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
                                Path(
                                    Path(args.output),
                                     f"{liffile.stem}_tile_{str(j + 1)}_{slugify(myimage.current_scene)}.ome.tif"),
                            )
                    else:
                        save_tiff(
                            myimage,
                            Path(
                                Path(args.output),
                                f"{liffile.stem}_{slugify(myimage.current_scene)}.ome.tif",
                            ),
                        )
                else:
                    save_tiff(
                        myimage,
                        Path(
                            Path(args.output),
                            f"{liffile.stem}_{slugify(myimage.current_scene)}.ome.tif",
                        ),
                    )
