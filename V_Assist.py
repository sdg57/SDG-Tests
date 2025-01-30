import streamlit as st
import openai
from PIL import Image
import os
from io import BytesIO
import requests

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to analyze images and extract style preferences
def analyze_images(images):
    style_descriptions = []
    for image in images:
        # Convert the image to a byte array for API submission
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        image_bytes = buffered.getvalue()

        # Integration with a supported image analysis API (Azure Computer Vision API example)
        subscription_key = "DECoPanxldT1FMeoqg1fU0FrCsMClH1b1xBmjFyOAUIVSUX39uSIJQQJ99BAACYeBjFXJ3w3AAAFACOG9xHH"
        endpoint = "https://sdgvassist.cognitiveservices.azure.com/"
        print(endpoint)
        analyze_url = f"{endpoint}/vision/v3.1/analyze"

        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-Type': 'application/octet-stream'
        }
        params = {
            'visualFeatures': 'Description,Tags'
        }
        response = requests.post(analyze_url, headers=headers, params=params, data=image_bytes)
        response.raise_for_status()
        analysis = response.json()

        # Extract and process style information from the API response
        style_description = analysis.get("description", {}).get("captions", [{}])[0].get("text", "Unable to determine style")
        style_descriptions.append(style_description)
    return style_descriptions

# Function to recommend clothing based on style, occasion, and retailer
def recommend_clothing(style_preferences, occasion, retailer):
    # Use the new ChatCompletion API
    messages = [
        {"role": "system", "content": "You are a highly intelligent virtual stylist."},
        {"role": "user", "content": f"Based on the style: {style_preferences}, the occasion: {occasion}, and the retailer: {retailer}, suggest some clothing options."}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Use "gpt-4" or "gpt-3.5-turbo" depending on your plan
        messages=messages,
        max_tokens=200
    )
    return response['choices'][0]['message']['content'].strip()


# Streamlit app
st.title("Virtual Stylist Agent")
st.write("Upload a few images, specify your occasion, and choose your favorite retailer to get personalized clothing recommendations!")

# Image upload
uploaded_files = st.file_uploader("Upload your images (up to 3)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    images = []
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        st.image(image, caption=uploaded_file.name, use_column_width=True)
        images.append(image)

# Occasion input
occasion = st.text_input("What is the occasion?", placeholder="e.g., Wedding, Office Party, Casual Day Out")

# Retailer selection
retailers = ["Zara", "H&M", "Nordstrom", "ASOS", "Macy's"]
retailer = st.selectbox("Select your preferred retailer", retailers)

# Generate recommendations
if st.button("Get Recommendations"):
    if not uploaded_files:
        st.warning("Please upload at least one image.")
    elif not occasion:
        st.warning("Please specify the occasion.")
    else:
        style_preferences = analyze_images(images)
        combined_style = ", ".join(style_preferences)
        recommendations = recommend_clothing(combined_style, occasion, retailer)
        st.subheader("Recommended Clothing:")
        st.write(recommendations)
