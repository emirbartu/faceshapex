import gradio as gr
import requests
import json

API_URL = "https://face-detection-api-o1enhc2t.devinapps.com/detect-face-shape"
API_KEY = "fs_prod_your_api_key_here"  # Replace with your actual API key

def process_image(image):
    files = {"file": ("image.jpg", image, "image/jpeg")}
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(API_URL, files=files, headers=headers)

    if response.status_code == 200:
        result = response.json()
        # Format the response for better readability
        formatted_result = json.dumps(result, indent=2)
        return formatted_result
    else:
        return f"Error: {response.status_code} - {response.text}"

iface = gr.Interface(
    fn=process_image,
    inputs=gr.Image(),
    outputs=gr.Textbox(label="API Response"),
    title="Face Shape Detection API",
    description="Upload an image to detect face shape and other features."
)

if __name__ == "__main__":
    iface.launch(share=True)
