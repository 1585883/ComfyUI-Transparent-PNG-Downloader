# ComfyUI Transparent PNG Downloader

A simple custom node plugin for ComfyUI that downloads transparent PNG/WebP images from a URL, preserves the alpha channel, and saves the result as a real transparent PNG.

## Nodes

### Download Transparent PNG

Downloads an online image and outputs:

- `image`: RGB image for ComfyUI
- `alpha_mask`: transparency mask
- `saved_path`: local saved PNG path

### Save Transparent PNG

Saves a ComfyUI `IMAGE + MASK` as a real transparent PNG file.

This is useful when another API or node returns a foreground image plus mask, and you need the final output to be a transparent PNG instead of a white-background image.

## Installation

Clone this repository into your ComfyUI custom nodes folder:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/YOUR_USERNAME/ComfyUI-Transparent-PNG-Downloader.git
cd ComfyUI-Transparent-PNG-Downloader
pip install -r requirements.txt
```

Restart ComfyUI.

## Usage

### Download transparent image from URL

1. Add node: `Download Transparent PNG`
2. Paste your image URL
3. Run workflow
4. The PNG will be saved to your ComfyUI `output` folder

### Save transparent PNG from image and mask

1. Connect your `IMAGE` output to `Save Transparent PNG`
2. Connect the corresponding `MASK` output to `Save Transparent PNG`
3. Run workflow
4. The transparent PNG will be saved to your ComfyUI `output` folder

## Important Notes

ComfyUI's `IMAGE` type is RGB and does not directly carry an alpha channel. To preserve transparency, this plugin outputs and accepts a separate `MASK`.

For transparent PNG output:

- White-background images are not transparent.
- You need a real alpha channel or a valid mask.
- Use `Save Transparent PNG` to combine image + mask into one transparent PNG.

## License

MIT License
