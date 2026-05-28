from fastapi import FastAPI
import gradio as gr

app = FastAPI()

def greet(name, mood):
    return f"Hello {name}, you seem {mood} today!"

def analyze_image(image):
    if image is None:
        return "No image uploaded."
    return f"Image uploaded with size: {image.size}"

with gr.Blocks() as demo:
    gr.Markdown("## Sample Gradio Site")

    with gr.Row():
        name = gr.Textbox(label="Enter your name")
        mood = gr.Dropdown(choices=["Happy", "Sad", "Excited"], label="Your mood")

    greet_btn = gr.Button("Greet Me")
    output = gr.Textbox(label="Greeting")

    greet_btn.click(fn=greet, inputs=[name, mood], outputs=output)

    with gr.Row():
        img = gr.Image(type="pil", label="Upload an image")
        analyze_btn = gr.Button("Analyze Image")
        img_output = gr.Textbox(label="Image Info")

    analyze_btn.click(fn=analyze_image, inputs=img, outputs=img_output)

app = gr.mount_gradio_app(app, demo, path="/")
