import sys
import os
import fitz  # PyMuPDF

# Ensure arguments provided
if len(sys.argv) < 3:
    print("Usage: python pdfReplace.py <number> <output_filename.pdf>")
    print("  <number> selects the template: AtemoAquaCustomLabels_<number>each.pdf")
    print("  Example: python pdfReplace.py 6 output.pdf")
    sys.exit(1)

template_number = sys.argv[1]
output_arg = sys.argv[2]

# Paths
base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_file = os.path.join(base_dir, f"AtemoAquaCustomLabels_{template_number}each.pdf")  # source PDF
output_file = os.path.join(base_dir, output_arg)

# Supported image extensions to look for, in order of preference
SUPPORTED_EXTENSIONS = [
    ".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"
]

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
        print(f"⚠️  Warning: multiple '{base_name}' images found, using {matches[0]}")
    return matches[0]

new_image = find_custom_label_image(base_dir)

# Check if files exist
if not os.path.exists(pdf_file):
    print(f" Error: Template not found at {pdf_file}")
    print(f"        (expected a file named AtemoAquaCustomLabels_{template_number}each.pdf in {base_dir})")
    sys.exit(1)
if not new_image:
    exts = ", ".join(SUPPORTED_EXTENSIONS)
    print(f" Error: No 'customLabels' image found in {base_dir} (looked for extensions: {exts})")
    sys.exit(1)

print(f"  Using label image: {os.path.basename(new_image)}")

print("Opening PDF...")
doc = fitz.open(pdf_file)

for page_index, page in enumerate(doc):
    print(f"    - Processing Page {page_index + 1}...")
    image_list = page.get_images(full=True)

    for img_index, img in enumerate(image_list):
        print(f"        - Replacing image {img_index + 1} on page {page_index + 1}...")
        xref = img[0]  # reference to the image in PDF

        # Replace the image using its xref number
        page.replace_image(xref, filename=new_image)
        
print(f" Saving new file as {output_file}...")
doc.save(output_file, garbage=4, deflate=True) # garbage=4 cleans up unused resources
doc.close()
print("✅ Done!")