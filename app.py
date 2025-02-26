from flask import Flask, request, jsonify, send_file, render_template  # Ensure this import is present
import cv2
import numpy as np
import os

app = Flask(__name__)

def to_bin(data):
    return ''.join(format(ord(i), '08b') for i in data)

def encode_image(image, message, password):
    secret_message = password + ":" + message
    binary_message = f"{len(secret_message):016b}" + to_bin(secret_message)

    # Read Image
    image_data = np.frombuffer(image.read(), np.uint8)
    
    # Decode Image
    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    # If image loading fails, return error
    if img is None:
        print("❌ Error: Could not decode image!")  # Debugging
        return "❌ Error: Invalid image file."

    data_index = 0
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            for channel in range(3):
                if data_index < len(binary_message):
                    pixel_bin = format(img[i, j, channel], '08b')
                    img[i, j, channel] = int(pixel_bin[:-1] + binary_message[data_index], 2)
                    data_index += 1
                else:
                    break
        if data_index >= len(binary_message):
            break

    cv2.imwrite("encoded_image.png", img)
    return "encoded_image.png"

def decode_image(image, password):
    img = cv2.imdecode(np.frombuffer(image.read(), np.uint8), cv2.IMREAD_COLOR)
    binary_data = ""
    message_length = None

    print("Decoding image...")  # Debugging

    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            for channel in range(3):
                binary_data += format(img[i, j, channel], '08b')[-1]
                if len(binary_data) == 16 and message_length is None:
                    message_length = int(binary_data, 2)
                    binary_data = ""
                    print(f"Message length detected: {message_length}")  # Debugging

                if message_length and len(binary_data) == message_length * 8:
                    print("Full message detected.")  # Debugging
                    break
            if message_length and len(binary_data) == message_length * 8:
                break
        if message_length and len(binary_data) == message_length * 8:
            break

    if not binary_data:
        return "❌ No data found."

    extracted_message = "".join(chr(int(binary_data[i:i+8], 2)) for i in range(0, len(binary_data), 8))
    
    if ":" in extracted_message:
        stored_password, extracted_message = extracted_message.split(":", 1)
    else:
        return "❌ Invalid format."

    if stored_password == password:
        return extracted_message
    else:
        return "❌ Incorrect Password."
        
@app.route("/")
def home():
    return render_template("index.html")  # Ensure index.html is in a 'templates' folder

@app.route('/encode', methods=['POST'])
def encode():
    image = request.files.get('image')

    if not image:
        return jsonify({"error": "❌ No file uploaded."}), 400

    print("📂 Uploaded File Name:", image.filename)  # Debugging

    message = request.form.get('message', '')
    password = request.form.get('password', '')

    output_path = encode_image(image, message, password)

    if output_path == "❌ Error: Invalid image file.":
        return jsonify({"error": output_path}), 400

    return send_file(output_path, mimetype='image/png')

@app.route('/decode', methods=['POST'])
def decode():
    image = request.files['image']
    password = request.form['password']
    decoded_message = decode_image(image, password)
    return jsonify({'message': decoded_message})

if __name__ == '__main__':
    app.run(debug=True)