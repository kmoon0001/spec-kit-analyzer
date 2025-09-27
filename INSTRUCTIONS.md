




# OCR Configuration
# Instructions for a Workaround

My apologies for the repeated failures. The testing environment is proving to be very difficult, causing the Python interpreter itself to crash when we try to test the application's GUI.

However, I have a reliable workaround that will allow us to verify the new AI analysis feature without touching the fragile GUI testing parts. I have created a new test file that calls the analysis logic directly.

## Step 1: Review the New Test File

I have created a new file at `tests/test_logic.py`. Please look at it. It contains a single test that:
1.  Loads the AI models.
2.  Creates a "mock" version of the main window to hold the services.
3.  Calls the core `run_analyzer` function with a test document.
4.  Asserts that the results are correct and include the new "reasoning" field from the LLM.

Here is the code for that file for your reference:

```python
import osC 
import sys
import pytest
from types import SimpleNamespace

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

This document explains how to configure the OCR (Optical Character Recognition) settings for the application. These settings allow you to fine-tune the performance of the OCR engine, especially for scanned documents.

## Configuration File

The OCR settings are located in the `config.yaml` file, under the `ocr` section.

```yaml
ocr:
  preprocessing: true
  deskew: true
  resolution: 300
```

### Options

- `preprocessing`: Enable or disable advanced image preprocessing. When enabled, the application will perform a series of image enhancement techniques to improve OCR accuracy.
  - `true`: Enable preprocessing (default).
  - `false`: Disable preprocessing.

- `deskew`: Enable or disable image deskewing. Deskewing is the process of straightening a skewed image. This can significantly improve OCR accuracy on scanned documents that are not perfectly aligned.
  - `true`: Enable deskewing (default).
  - `false`: Disable deskewing.

- `resolution`: Set the resolution (in DPI) for rendering PDF pages as images. Higher values will result in better image quality, but will also increase processing time.
  - `300`: Default resolution.
  - `150`: Lower resolution, faster processing.
  - `600`: Higher resolution, slower processing.

## Best Practices

- For most scanned documents, the default settings should provide good results.
- If you are processing a large number of high-quality digital PDFs, you can disable preprocessing to speed up the process.
- If you are getting poor OCR results on skewed documents, make sure that `deskew` is enabled.
- If you are processing documents with very small text, you can try increasing the `resolution` to `600`.
