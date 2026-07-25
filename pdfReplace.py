import sys
import os
import fitz  # PyMuPDF
from PIL import Image

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# Degrees to rotate images placed into "side" (tall/narrow) slots.
# Flip the sign to -90 if your sidebar image comes out upside-down.
SIDEBAR_ROTATE_DEGREES = 90

# Color used to paint over the original (stretched) placeholder image
# before drawing the new one. Must match your template's label background.
COVER_COLOR = (1, 1, 1)  # white, in 0..1 RGB

SUPPORTED_EXTENSIONS = [
    ".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"
]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def find_custom_label_image(directory, base_name="customLabels"):
    """Find a file named base_name with any supported image extension."""
    matches = []
    for ext in SUPPORTED_EXTENSIONS:
        candidate = os.path.join(directory, base_name + ext)
        if os.path.exists(candidate):
            matches.append(candidate)

    if not matches:
        return None
    if len(matches) > 1:
        print(f"  Warning: multiple '{base_name}' images found, using {matches[0]}")
    return matches[0]


def is_side_slot(rect: fitz.Rect) -> bool:
    """
    Decide whether a placement rectangle is a 'side' (sidebar) slot purely
    from its own geometry -- tall and narrow (portrait) rather than wide
    and short (landscape). No hard-coded coordinates involved.
    """
    return rect.height > rect.width


def fit_and_center(img_w: float, img_h: float, target: fitz.Rect, rotate: int = 0) -> fitz.Rect:
    """
    Compute the largest rectangle that:
      - preserves the image's aspect ratio (after accounting for `rotate`),
      - fits entirely inside `target`,
      - is centered inside `target`.

    This is the core "contain / letterbox" fit calculation, done manually
    so the result is fully deterministic and independent of any single
    library's internal fitting behavior.
    """
    rotate = rotate % 360
    if rotate in (90, 270):
        # After rotation, the image's effective footprint has its
        # width/height swapped relative to the source pixels.
        eff_w, eff_h = img_h, img_w
    else:
        eff_w, eff_h = img_w, img_h

    target_w = target.width
    target_h = target.height

    # Scale by whichever dimension is the tighter constraint.
    scale = min(target_w / eff_w, target_h / eff_h)

    new_w = eff_w * scale
    new_h = eff_h * scale

    cx = (target.x0 + target.x1) / 2.0
    cy = (target.y0 + target.y1) / 2.0

    return fitz.Rect(
        cx - new_w / 2.0,
        cy - new_h / 2.0,
        cx + new_w / 2.0,
        cy + new_h / 2.0,
    )


def cover_rect(page: fitz.Page, rect: fitz.Rect):
    """Paint over the original image's exact bounding box so none of the
    old, stretched pixels remain visible around the new image."""
    page.draw_rect(
        rect,
        color=None,          # no border stroke
        fill=COVER_COLOR,
        fill_opacity=1,
        width=0,
        overlay=True,
    )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python pdfReplace.py <number> <output_filename.pdf>")
        print("  <number> selects the template: AtemoAquaCustomLabels_<number>each.pdf")
        print("  Example: python pdfReplace.py 6 output.pdf")
        sys.exit(1)

    template_number = sys.argv[1]
    output_arg = sys.argv[2]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_file = os.path.join(base_dir, f"AtemoAquaCustomLabels_{template_number}each.pdf")
    output_file = os.path.join(base_dir, output_arg)

    new_image = find_custom_label_image(base_dir)

    if not os.path.exists(pdf_file):
        print(f" Error: Template not found at {pdf_file}")
        print(f"        (expected a file named AtemoAquaCustomLabels_{template_number}each.pdf in {base_dir})")
        sys.exit(1)
    if not new_image:
        exts = ", ".join(SUPPORTED_EXTENSIONS)
        print(f" Error: No 'customLabels' image found in {base_dir} (looked for extensions: {exts})")
        sys.exit(1)

    print(f"  Using label image: {os.path.basename(new_image)}")

    # Read the source image's true pixel dimensions once -- needed for the
    # aspect-ratio math. We pass the ORIGINAL bytes straight to PyMuPDF
    # (no PIL re-encoding / pre-rotation needed anymore).
    with Image.open(new_image) as probe:
        img_w, img_h = probe.size
    with open(new_image, "rb") as f:
        image_bytes = f.read()

    print("Opening PDF...")
    doc = fitz.open(pdf_file)

    for page_index, page in enumerate(doc):
        print(f"    - Processing Page {page_index + 1}...")

        # Snapshot every image placement on this page BEFORE we start
        # drawing on it, since get_image_info(xrefs=True) returns one
        # entry per placement rectangle even when several placements
        # share the same underlying xref (as this template does).
        placements = page.get_image_info(xrefs=True)

        if not placements:
            print("        - No images found on this page, skipping.")
            continue

        reuse_xref = None  # embed the new image once per page, reuse after that

        for slot_index, info in enumerate(placements):
            rect = fitz.Rect(info["bbox"])
            side = is_side_slot(rect)
            rotate = SIDEBAR_ROTATE_DEGREES if side else 0

            fitted = fit_and_center(img_w, img_h, rect, rotate=rotate)

            kind = "side slot (rotated)" if side else "main slot"
            print(f"        - Slot {slot_index + 1}: {kind} -> "
                  f"target={rect}, fitted={fitted}")

            # 1. Hide the old (stretched) image in this exact box.
            cover_rect(page, rect)

            # 2. Draw the new image, fitted + centered + rotated as needed.
            if reuse_xref is None:
                reuse_xref = page.insert_image(
                    fitted,
                    stream=image_bytes,
                    rotate=rotate,
                    keep_proportion=False,  # we already computed the exact fit
                    overlay=True,
                )
            else:
                page.insert_image(
                    fitted,
                    xref=reuse_xref,
                    rotate=rotate,
                    keep_proportion=False,
                    overlay=True,
                )

    print(f" Saving new file as {output_file}...")
    doc.save(output_file, garbage=4, deflate=True)
    doc.close()
    print(" Done!")


if __name__ == "__main__":
    main()
