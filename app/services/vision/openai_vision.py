import os
import io
import base64
from openai import OpenAI


def get_image_description(pil_image) -> str:
    """
    Takes a PIL.Image, converts it to base64, and sends it to GPT-4o-mini
    to generate a concise, searchable description of the visual content.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Image without description (OpenAI API key missing)"

    try:
        # Convert PIL image to base64
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        b64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail so it can be indexed for search. If it is a chart or graph, summarize the key data points. If it's a diagram, explain the flow. Keep it under 100 words."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                    ]
                }
            ],
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"[Vision] Error generating image description: {e}")
        return "Image description generation failed."
