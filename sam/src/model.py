import torch
import numpy as np
from PIL import Image

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

# Load the model and predictor
checkpoint = "finetuned_models/sam2_hiera_small.pt"
model_cfg = "../sam2/configs/sam2/sam2_hiera_s.yaml"
predictor = SAM2AutomaticMaskGenerator(build_sam2(model_cfg, checkpoint))

# Load your image (as a NumPy array or PIL Image, convert to RGB if needed)
your_image = Image.open("../heart_ultrasound__96373.png").convert("RGB")
image_np = np.array(your_image)

# Run prediction
with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
    masks = predictor.generate(image_np)
    

# Convert mask to uint8 and apply
mask = masks[0] # Use the first mask
mask = mask["segmentation"]
masked_image = image_np.copy()
masked_image[mask == 0] = 0  # Black out background

# Save the masked image
result = Image.fromarray(masked_image)
result.save("masked_output.png")

def mask_centroid(mask: np.ndarray) -> tuple[int,int]:
    """mask: a binary 2D array where heart pixels=1. 
    Returns (cx, cy) in pixel coords, or center if no pixels found."""
    ys, xs = np.where(mask>0)
    if len(xs)==0:
        # fallback to image center
        h, w = mask.shape
        return w//2, h//2
    return int(np.mean(xs)), int(np.mean(ys))