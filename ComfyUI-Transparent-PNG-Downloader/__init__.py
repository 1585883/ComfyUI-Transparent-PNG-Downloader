print("=== PhotoRoom Transparent PNG Nodes Loaded ===")

import os
import time
import requests
import torch
import numpy as np
from PIL import Image
from io import BytesIO

try:
    import folder_paths
except Exception:
    folder_paths = None


class PhotoRoomRemoveBGTransparent:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "alpha_mask")
    FUNCTION = "remove_bg"
    CATEGORY = "PhotoRoom"

    def remove_bg(self, image, api_key):
        if not api_key:
            raise Exception("Please enter your PhotoRoom API key")

        img = image[0].cpu().numpy()
        img = (img * 255).clip(0, 255).astype(np.uint8)
        pil_img = Image.fromarray(img).convert("RGB")

        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        buffer.seek(0)

        response = requests.post(
            "https://sdk.photoroom.com/v1/segment",
            headers={
                "x-api-key": api_key,
                "Accept": "image/png"
            },
            files={
                "image_file": ("input.png", buffer, "image/png")
            },
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"PhotoRoom API Error {response.status_code}: {response.text}")

        rgba = Image.open(BytesIO(response.content)).convert("RGBA")
        arr = np.array(rgba).astype(np.float32) / 255.0

        rgb = arr[:, :, :3]
        alpha = arr[:, :, 3]

        image_tensor = torch.from_numpy(rgb.astype(np.float32))[None,]
        mask_tensor = torch.from_numpy(alpha.astype(np.float32))[None,]

        return (image_tensor, mask_tensor)


class SaveTransparentPNG:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "alpha_mask": ("MASK",),
                "filename_prefix": ("STRING", {"default": "photoroom_transparent"}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_png"
    OUTPUT_NODE = True
    CATEGORY = "PhotoRoom"

    def save_png(self, image, alpha_mask, filename_prefix):
        if folder_paths is not None:
            output_dir = folder_paths.get_output_directory()
        else:
            output_dir = os.path.join(os.getcwd(), "output")

        os.makedirs(output_dir, exist_ok=True)

        results = []

        image_np = image.detach().cpu().numpy()
        mask_np = alpha_mask.detach().cpu().numpy()

        batch = image_np.shape[0]

        for i in range(batch):
            rgb = (image_np[i] * 255).clip(0, 255).astype(np.uint8)

            mask = mask_np[i]
            if mask.ndim == 3:
                mask = mask[:, :, 0]

            alpha = (mask * 255).clip(0, 255).astype(np.uint8)

            if alpha.shape[:2] != rgb.shape[:2]:
                alpha_img = Image.fromarray(alpha).resize(
                    (rgb.shape[1], rgb.shape[0]),
                    Image.Resampling.LANCZOS
                )
                alpha = np.array(alpha_img).astype(np.uint8)

            rgba = np.dstack((rgb, alpha))
            pil = Image.fromarray(rgba, mode="RGBA")

            timestamp = int(time.time() * 1000)
            filename = f"{filename_prefix}_{timestamp}_{i:03d}.png"
            filepath = os.path.join(output_dir, filename)

            pil.save(filepath, "PNG")

            results.append({
                "filename": filename,
                "subfolder": "",
                "type": "output"
            })

        return {"ui": {"images": results}}


NODE_CLASS_MAPPINGS = {
    "PhotoRoomRemoveBGTransparent": PhotoRoomRemoveBGTransparent,
    "SaveTransparentPNG": SaveTransparentPNG,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhotoRoomRemoveBGTransparent": "PhotoRoom Remove Background Transparent",
    "SaveTransparentPNG": "Save Transparent PNG",
}
