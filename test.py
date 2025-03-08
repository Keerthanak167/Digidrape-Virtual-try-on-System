import gradio as gr
from PIL import Image
import os
import mysql.connector
import io

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="threaderz_store"
    )

# Fetch cloth image path from database
def get_cloth_image_path(cloth_key):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT image_path FROM cloth_table WHERE cloth_key = %s"
    cursor.execute(query, (cloth_key,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result[0] if result else None

# Fetch processed try-on result from database
def fetch_processed_image(product_id, human_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT output_image FROM tryon_results WHERE product_id = %s AND human_id = %s"
    cursor.execute(query, (product_id, human_id))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return Image.open(io.BytesIO(result[0]))  # Convert BLOB to PIL Image
    else:
        return None

# Convert PNG to JPG if necessary
def convert_png_to_jpg(input_path, output_path):
    try:
        image = Image.open(input_path) if isinstance(input_path, str) else input_path
        if image.mode == 'RGBA':
            image = image.convert("RGB")
        image.save(output_path, format="JPEG")
    finally:
        print("Conversion completed.")

# Run function
def run(request: gr.Request, cloth_key, model):
    query_params = request.query_params
    cloth_key = query_params.get("cloth", "Cloth 101")

    # Fetch cloth image path from database
    image_path = get_cloth_image_path(cloth_key)
    
    if not image_path:
        return "Cloth image not found in database.", None

    cloth = Image.open(image_path)
    
    # Save human image
    model.save("temp_model.jpg")

    # Convert cloth image to JPG
    output_file = "temp_cloth2.jpg"
    convert_png_to_jpg(input_path=cloth, output_path=output_file)

    # Fetch processed image using product_id and human_id (assume they are provided)
    product_id, human_id = 1, 1  # Replace with actual IDs
    masked_image = fetch_processed_image(product_id, human_id)

    return cloth, masked_image if masked_image else "No processed image found in the database."

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# DigiDrape Virtual Try-On System")

    cloth_key_input = gr.Textbox(label="Cloth Key", value=None, visible=False)
    cloth_image_output = gr.Image(label="Selected Cloth")

    with gr.Row():
        human_image_input = gr.Image(label="Upload Human Image", type="pil")
        combined_image_output = gr.Image(label="Combined Result")

    submit_button = gr.Button("Combine and Display")

    submit_button.click(
        run,
        inputs=[cloth_key_input, human_image_input],
        outputs=[cloth_image_output, combined_image_output],
    )

demo.launch(share=True, debug=True)
