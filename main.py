import argparse
from pathlib import Path

import bioio_lif
from bioio import BioImage

from lif2ometiff import save_tiff, slugify


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
    return myparser.parse_args()


if __name__ == "__main__":
    args = get_args()
    liffiles = [x for x in Path(args.input).glob("*.tif")]
    print(f"Found {len(liffiles)} liffiles.")
    for liffile in liffiles:
        myimage = BioImage(liffile, reader=bioio_lif.Reader)
        for i in range(len(myimage.scenes)):
            myimage.set_scene(i)
            save_tiff(
                myimage,
                Path(
                    Path(args.output),
                    f"{liffile.stem}_{slugify(myimage.current_scene)}.ome.tif",
                ),
            )
