import openai
import streamlit as st
import os
from dotenv import load_dotenv
from fpdf import FPDF
import requests

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize session state for the text input
if "story_prompt" not in st.session_state:
    st.session_state.story_prompt = "Once upon a time in a magical forest..."

def clear_default():
    if st.session_state.story_prompt == "Once upon a time in a magical forest...":
        st.session_state.story_prompt = ""  # Clear the default text

def generate_pdf(story, image_urls):
    """
    Generates a PDF containing the story and images.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Add title
    pdf.set_font("Arial", size=16, style="B")
    pdf.cell(0, 10, "AI Storyteller Output", ln=True, align="C")
    pdf.ln(10)

    # Add the story
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, story)
    pdf.ln(10)

    # Add images
    for idx, url in enumerate(image_urls):
        try:
            # Download image
            response = requests.get(url, stream=True)
            image_path = f"image_{idx + 1}.jpg"
            with open(image_path, "wb") as f:
                f.write(response.content)
            
            # Add image to PDF
            pdf.add_page()
            pdf.image(image_path, x=10, y=30, w=180)
            pdf.ln(85)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"Scene {idx + 1}", ln=True, align="C")

        except Exception as e:
            print(f"Error downloading or adding image {idx + 1}: {e}")

    return pdf.output(dest="S").encode("latin1")  # Return PDF as bytes

# Streamlit App Title
st.title("AI Storyteller with Visuals (Powered by GPT-3.5 and OpenAI)")

# Genre Selector
genre = st.selectbox(
    "Select a Genre",
    ["Fantasy", "Sci-Fi", "Horror", "Adventure", "Mystery"]
)

# Input for the story prompt with auto-clear functionality
story_prompt = st.text_input(
    "Enter a story prompt",
    st.session_state.story_prompt,
    on_change=clear_default,
    key="story_prompt"
)

# Button to generate story and images
if st.button("Generate Story and Images"):
    with st.spinner("Generating your story and images..."):
        try:
            # Combine genre and prompt
            full_prompt = f"Write a {genre.lower()} story. {story_prompt}"

            # Generate Story using GPT-3.5-turbo
            story_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative storyteller."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=500  # Limit the response length
            )
            story = story_response['choices'][0]['message']['content']
            st.subheader("Your Story:")
            st.write(story)

            # Split the story into scenes
            scenes = story.split(".")[:3]  # First 3 sentences as scenes

            # Generate an image for each scene using OpenAI DALL·E
            image_urls = []
            st.subheader("Story Scenes:")
            for idx, scene in enumerate(scenes):
                if scene.strip():  # Skip empty scenes
                    with st.spinner(f"Generating image for Scene {idx + 1}..."):
                        image_response = openai.Image.create(
                            prompt=f"An illustration of: {scene.strip()}",
                            n=1,
                            size="1024x1024"
                        )
                        image_url = image_response['data'][0]['url']
                        image_urls.append(image_url)
                        st.image(image_url, caption=f"Scene {idx + 1}: {scene.strip()}", use_container_width=True)

            # Add a download button for the story and images as a PDF
            pdf_data = generate_pdf(story, image_urls)
            st.download_button(
                label="Download Story as PDF",
                data=pdf_data,
                file_name="story_with_images.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Error: {e}")
