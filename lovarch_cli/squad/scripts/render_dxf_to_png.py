#!/usr/bin/env python3
"""Render stato-attuale.dxf to PNG using ezdxf + matplotlib."""

from pathlib import Path
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DXF_PATH = ROOT / "data" / "sample-input" / "stato-attuale.dxf"
OUT_PATH = ROOT / "data" / "sample-input" / "stato-attuale.png"


def main():
    print(f"Loading DXF: {DXF_PATH}")
    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()

    fig, ax = plt.subplots(figsize=(16, 12), dpi=150)
    ax.set_facecolor("#0A0A0A")
    fig.patch.set_facecolor("#0A0A0A")

    ctx = RenderContext(doc)
    ctx.set_current_layout(msp)

    # Customize layer colors for dark background
    for layer in doc.layers:
        name = layer.dxf.name.upper()
        if "MURI" in name or "WALL" in name or "MURO" in name:
            layer.color = 7  # white-ish
        elif "PORTE" in name or "DOOR" in name:
            layer.color = 3  # green
        elif "FINESTRE" in name or "WINDOW" in name:
            layer.color = 5  # blue
        elif "QUOTE" in name or "DIM" in name:
            layer.color = 2  # yellow
        elif "TESTI" in name or "TEXT" in name:
            layer.color = 6  # magenta
        elif "ARRED" in name or "FURN" in name:
            layer.color = 8  # grey
        else:
            layer.color = 7

    out_backend = MatplotlibBackend(ax)
    Frontend(ctx, out_backend).draw_layout(msp, finalize=True)

    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor="#0A0A0A", pad_inches=0.2)
    print(f"✓ saved: {OUT_PATH}")
    print(f"  size: {OUT_PATH.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
