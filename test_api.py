import requests
import base64
from PIL import Image
import io

# API key configuration
API_KEY = "fs_prod_your_api_key_here"  # Replace with the actual API key

# Test the API endpoint with the downloaded face image
url = 'http://localhost:8000/detect-face-shape'
files = {'file': open('test_face.jpg', 'rb')}
headers = {'Authorization': f'Bearer {API_KEY}'}
response = requests.post(url, files=files, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response JSON: {response.json()}")

# Test Gradio interface
print("\nTesting Gradio interface...")
gradio_url = 'http://localhost:8000'
print(f"Gradio interface should be accessible at: {gradio_url}")
print("Please manually verify the Gradio interface in a web browser.")

# Test daily report generation
print("\nTesting daily report generation...")
daily_report_url = 'http://localhost:8000/daily-report'
daily_report_response = requests.get(daily_report_url, headers=headers)
print(f"Daily Report Status Code: {daily_report_response.status_code}")
print(f"Daily Report JSON: {daily_report_response.json()}")
