# Mask Overlay and Segmentation Tool

## Description

This tool lets you quickly add new objects to a segmentation dataset: you overlay an object onto a background, and the mask is updated automatically.

## Main Features

- **Interactive interface:**  
  Select background, object, and mask through a simple window.

- **Manual placement and scaling:**  
  Click to place the object, use the mouse wheel to resize.

- **Automatic mask update:**  
  After overlaying, the object is automatically marked on the mask with the required color.

## How to Use

1. Run the script:
   ```bash
   python mask.py
   ```
2. Select folders with backgrounds, objects, and masks.
3. Place the object on the background, scale if needed.
4. Save the result and the updated mask.

## Requirements

- Python 3.x
- Pillow (install with: `pip install pillow`)

## Example

If you want to add a new class (for example, “tombstone”)—just overlay it on the background, and the mask will update automatically.

**This tool saves time and simplifies dataset expansion for segmentation tasks.**

![image](https://github.com/user-attachments/assets/2d705514-1c91-44af-a762-ec649491a033)
