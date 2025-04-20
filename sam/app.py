from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
import numpy as np
import cv2
import base64
from typing import Optional
import io
from PIL import Image
import os
import anthropic
from src.prompts import get_navigation_prompt, get_ultrasound_diagnostic_prompt




CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

app = FastAPI(title="Image and Text Processing API")

# Pydantic models for request validation
class NavigateRequest(BaseModel):
    text: str

class IdentifyImageRequest(BaseModel):
    entity_name: str
    image: Optional[str] = None  # Base64 encoded image

# Helper function to decode base64 images
def decode_image(base64_string):
    try:
        # Remove potential data URL prefix
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
            
        # Decode base64 string to bytes
        img_data = base64.b64decode(base64_string)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

# Helper function for image identification logic
def identify_entity_in_image(image, entity_name):
    """
    Identify if the specified entity is present in the image using Claude's API.
    """
    # Convert OpenCV image to base64 for API request
    if isinstance(image, np.ndarray):
        # Convert from BGR to RGB (OpenCV uses BGR by default)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
    else:
        image_pil = image
    
    # Convert image to base64
    buffer = io.BytesIO()
    image_pil.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Using GPT-4 Vision API for identification
    payload = {
        "model": "claude-3-sonnet-20240229",  # or the latest vision model
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Is there a {entity_name} in this image? Please respond with only 'true' or 'false'."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 10  # Keep response concise
    }

    try:
        response = anthropic_client.messages.create(**payload)
        response_text = response.choices[0].message.content
        
        # Determine if the entity was found based on the response
        if "true" in response_text.lower():
            return True
        elif "false" in response_text.lower():
            return False
        else:
            # If response is unclear, default to False
            return False
            
    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error in Claude API call: {str(e)}")
        # Default to False on error
        return False

# Helper function for image description
def generate_description(image):
    """
    Generate a detailed description of the image content using Claude's API.
    """
    # Convert OpenCV image to base64 for API request
    if isinstance(image, np.ndarray):
        # Convert from BGR to RGB (OpenCV uses BGR by default)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
    else:
        image_pil = image
    
    # Convert image to base64
    buffer = io.BytesIO()
    image_pil.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Using GPT-4 Vision API for image description
    payload = {
        "model": "claude-3-sonnet-20240229",  # or the latest vision model
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": get_ultrasound_diagnostic_prompt()
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096  # Adjust based on desired description length
    }
    
    try:
        response = anthropic_client.completions.create(**payload)
        description = response.choices[0].message.content
        return description
            
    except Exception as e:
        # Log the error (in a production environment)
        print(f"Error in Claude API call: {str(e)}")
        
        # Fallback to basic description on error
        width, height = image_pil.size
        return f"Error generating AI description. Basic info: {width}x{height} image."

# Endpoint 1: Identify image
@app.post("/identify", response_class=JSONResponse)
async def identify_image(entity_name: str = Form(...), image: UploadFile = File(...)):
    """
    Identify if a specific entity exists in an image.
    
    Parameters:
    - entity_name (str): The name of the entity to search for
    - image (File): The uploaded image file
    
    Returns:
    - JSON with identification result (True/False)
    """
    try:
        # Read image file
        content = await image.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Perform entity identification
        result = identify_entity_in_image(img, entity_name)
        
        return {"found": result, "entity": entity_name}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 1 Alternative: Identify image with base64
@app.post("/identify_base64")
async def identify_image_base64(request: IdentifyImageRequest):
    """
    Identify if a specific entity exists in a base64-encoded image.
    
    Parameters:
    - request (IdentifyImageRequest): Contains entity_name and base64-encoded image
    
    Returns:
    - JSON with identification result (True/False)
    """
    try:
        if not request.image:
            raise HTTPException(status_code=400, detail="Image data is required")
        
        # Decode base64 image
        img = decode_image(request.image)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Perform entity identification
        result = identify_entity_in_image(img, request.entity_name)
        
        return {"found": result, "entity": request.entity_name}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 2: Navigate - FIXED to correctly handle image UploadFile
@app.post("/navigate", response_class=JSONResponse)
async def navigate(entity_name: str = Form(...), image: UploadFile = File(...)):
    """
    Process image and provide navigation instructions to locate a specific entity.
    
    Parameters:
    - entity_name (str): The name of the entity to navigate to
    - image (File): The uploaded image file
    
    Returns:
    - JSON with navigation response
    """
    try:
        # Read image file
        content = await image.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Convert OpenCV image to base64 for API request
        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        
        buffer = io.BytesIO()
        image_pil.save(buffer, format="JPEG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # This would typically connect to a navigation service or NLP model
        payload = {
            "model": "claude-3-sonnet-20240229",  # or the latest vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": get_navigation_prompt(entity_name)
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096  # Adjust based on desired description length
        }
        response = anthropic_client.completions.create(**payload)
        
        return {"response": response.choices[0].message.content}
    
    except Exception as e:
        print(f"Error in navigate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 3: Describe
@app.post("/describe", response_class=JSONResponse)
async def describe_image(target_organ: str = Form(...), image: UploadFile = File(...)):
    """
    Generate a description of an uploaded image.
    
    Parameters:
    - image (File): The uploaded image file
    
    Returns:
    - JSON with image description
    """
    try:
        # Read image file
        content = await image.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Convert OpenCV image to base64 for API request
        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        
        buffer = io.BytesIO()
        image_pil.save(buffer, format="JPEG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # This would typically connect to a navigation service or NLP model
        payload = {
            "model": "claude-3-sonnet-20240229",  # or the latest vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": get_ultrasound_diagnostic_prompt(target_organ)
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096  # Adjust based on desired description length
        }
        
        response = anthropic.chat.completions.create(**payload)
        print(response.choices[0].message.content)
        
        return {"description": response.choices[0].message.content}
    
    except Exception as e:
        print(f"Error in describe endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint for API information
@app.get("/", response_class=JSONResponse)
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "api": "Image and Text Processing API",
        "version": "1.0",
        "endpoints": [
            {"path": "/identify", "method": "POST", "description": "Identify entities in images"},
            {"path": "/identify_base64", "method": "POST", "description": "Identify entities in base64-encoded images"},
            {"path": "/navigate", "method": "POST", "description": "Process navigation for entities in images"},
            {"path": "/describe", "method": "POST", "description": "Generate descriptions for images"}
        ]
    }

# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)