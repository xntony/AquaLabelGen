# Aqua Label Generator

This tool replaces the placeholder images in a label template PDF with your
custom label artwork (`customLabels.*`) and saves the result as a new,
print-ready PDF.

## 1. One-time setup

### Create a virtual environment

**Windows:**
```
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```
python3 -m venv venv
source venv/bin/activate
```


### Install PyMuPDF

With the virtual environment active:

```
pip install PyMuPDF
```

Verify it installed correctly:

```
python -c "import fitz; print(fitz.__doc__)"
```


## 2. Running the script

Basic usage:

```
python pdfReplace.py <number> <output_filename.pdf>
```

- `<number>` — which template to use: `2`, `3`, `4`, `6`, or `8`
  (matches the `AtemoAquaCustomLabels_<number>each.pdf` files above)
- `<output_filename.pdf>` — name of the file to generate

Example

```
python pdfReplace.py 2 order_20L.pdf
python pdfReplace.py 4 order_4pack.pdf
python pdfReplace.py 6 order_6pack.pdf
python pdfReplace.py 8 order_8pack.pdf
```

The script supports `customLabels` extensions (`.jpg`, `.jpeg`, `.png`, `.bmp`,
`.tiff`, `.tif`, `.gif`, `.webp`)



## 3. Running the web page (local server)
 
Instead of the command line, you can use `index.html` — a simple page with
an image upload box, a label-count dropdown, and a generate button — backed
by `server.py`, which runs `pdfReplace.py` for you and sends back the
finished PDF.
 
### Start the server
 
With the virtual environment active, and `pdfReplace.py`, `server.py`,
`index.html`, and all the template PDFs in the same folder:
 
```
python server.py
```
 
You should see output like:
 
```
 * Running on http://127.0.0.1:5000
 * Debugger is active!
```
 
### Open the page
 
Go to **http://localhost:5000** in your browser. Upload an image, choose a
label count, and click **GEN** — the generated PDF downloads automatically.
 
### Stop the server
 
`Ctrl+C` in the terminal.



## 4. Deactivating the virtual environment

When you're done:

```
deactivate
```

## Troubleshooting

| Message | Meaning |
|---|---|
| `Error: Template not found at ...` | The `<number>` you passed doesn't match a template file in the folder. Check spelling/number and that the PDF is present. |
| `Error: No 'customLabels' image found ...` | No file named `customLabels.<ext>` exists in the folder, or it's an unsupported format. |
| `ModuleNotFoundError: No module named 'fitz'` | PyMuPDF isn't installed in your active environment. Make sure your venv is activated, then re-run `pip install PyMuPDF`. |
