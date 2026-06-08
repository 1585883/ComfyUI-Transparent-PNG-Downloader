import os
import io
import time
from urllib.parse import urlparse

import numpy as np
import requests
import torch
from PIL import Image, ImageOps

try:
    import folder_paths
except Exception:
    folder_paths = None


class TransparentPNGDownloader:
    """Download a PNG/WebP image from a URL, preserve transparency, and output IMAGE + MASK."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_url": ("STRING", {"multiline": False, "default": "https://example.com/image.png"}),
                "filename_prefix": ("STRING", {"default": "transparent_png"}),
                "timeout": ("INT", {"default": 30, "min": 5, "max": 120, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "alpha_mask", "saved_path")
    FUNCTION = "download"
    CATEGORY = "image/download"

    def _get_output_dir(self):
        if folder_paths is not None:
            return folder_paths.get_output_directory()
        return os.path.join(os.getcwd(), "output")

    def _safe_filename(self, prefix):
        clean = "".join(c if c.isalnum() or c in "-_" else "_" for c in prefix).strip("_")
        if not clean:
            clean = "transparent_png"
        return f"{clean}_{int(time.time())}.png"

    def _pil_to_comfy(self, pil_image):
        rgba = pil_image.convert("RGBA")

        rgb = rgba.convert("RGB")
        image_np = np.asarray(rgb).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]

        alpha = np.asarray(rgba.getchannel("A")).astype(np.float32) / 255.0
        # ComfyUI masks normally use white as masked/transparent area.
        # For alpha compositing later, 1 - alpha is usually expected by SaveImage-style nodes.
        mask_tensor = torch.from_numpy(1.0 - alpha)[None,]
        return image_tensor, mask_tensor

    def download(self, image_url, filename_prefix="transparent_png", timeout=30):
        if not image_url.lower().startswith(("http://", "https://")):
            raise ValueError("image_url must start with http:// or https://")

        headers = {"User-Agent": "ComfyUI-Transparent-PNG-Downloader/1.0"}
        response = requests.get(image_url, headers=headers, timeout=timeout)
        response.raise_for_status()

        image = Image.open(io.BytesIO(response.content))
        image = ImageOps.exif_transpose(image).convert("RGBA")

        output_dir = self._get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        filename = self._safe_filename(filename_prefix)
        saved_path = os.path.join(output_dir, filename)
        image.save(saved_path, "PNG")

        image_tensor, mask_tensor = self._pil_to_comfy(image)
        return (image_tensor, mask_tensor, saved_path)


class SaveTransparentPNG:
    """Save a ComfyUI IMAGE + MASK as a real transparent PNG."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "filename_prefix": ("STRING", {"default": "transparent_output"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("saved_path",)
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "image/save"

    def _get_output_dir(self):
        if folder_paths is not None:
            return folder_paths.get_output_directory()
        return os.path.join(os.getcwd(), "output")

    def _safe_filename(self, prefix, index):
        clean = "".join(c if c.isalnum() or c in "-_" else "_" for c in prefix).strip("_")
        if not clean:
            clean = "transparent_output"
        return f"{clean}_{int(time.time())}_{index:03d}.png"

    def save(self, image, mask, filename_prefix="transparent_output"):
        output_dir = self._get_output_dir()
        os.makedirs(output_dir, exist_ok=True)

        saved_paths = []
        batch_size = image.shape[0]

        for i in range(batch_size):
            rgb_np = np.clip(255.0 * image[i].cpu().numpy(), 0, 255).astype(np.uint8)
            rgb = Image.fromarray(rgb_np, "RGB").convert("RGBA")

            current_mask = mask[i if mask.shape[0] > 1 else 0].cpu().numpy()
            # In ComfyUI mask: 0 = keep/opaque, 1 = masked/transparent.
            alpha_np = np.clip((1.0 - current_mask) * 255.0, 0, 255).astype(np.uint8)
            alpha = Image.fromarray(alpha_np, "L").resize(rgb.size)
            rgb.putalpha(alpha)

            filename = self._safe_filename(filename_prefix, i)
            saved_path = os.path.join(output_dir, filename)
            rgb.save(saved_path, "PNG")
            saved_paths.append(saved_path)

        return ("\n".join(saved_paths),)


NODE_CLASS_MAPPINGS = {
    "TransparentPNGDownloader": TransparentPNGDownloader,
    "SaveTransparentPNG": SaveTransparentPNG,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TransparentPNGDownloader": "Download Transparent PNG",
    "SaveTransparentPNG": "Save Transparent PNG",
}
