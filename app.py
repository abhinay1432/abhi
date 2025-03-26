import streamlit as st
import numpy as np
import tensorflow as tf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import io
from PIL import Image
import time

# Load the trained model
model = tf.keras.models.load_model("fire_detection_model.keras")

# Function to preprocess image
def preprocess_image(image):
    image = image.resize((180, 180))  # Resize to match model input size
    image = np.array(image)  # Convert to NumPy array
    image = image / 255.0  # Normalize pixel values
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image

# Function to send email with image and GPS location
def send_email(latitude, longitude, image, recipient_email="abhinaypyasi@gmail.com"):
    sender_email = "a80614436@gmail.com"
    sender_password = "fulf cqad ktxf nzyy"  # Use App Password for security
    subject = "🔥 Fire Alert with Live Location!"

    # Create Google Maps link
    google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    location_text = f"Latitude: {latitude}, Longitude: {longitude}"

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Email body
    body = f"Fire detected! 🚨\nLocation: {location_text}\nGoogle Maps: {google_maps_link}\nPlease take immediate action!"
    msg.attach(MIMEText(body, "plain"))

    # Convert image to bytes
    img_byte_array = io.BytesIO()
    image.save(img_byte_array, format="JPEG")
    img_byte_array.seek(0)

    # Attach image
    part = MIMEBase("application", "octet-stream")
    part.set_payload(img_byte_array.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=fire_detected.jpg")
    msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return "✅ Email with live GPS location sent successfully!"
    except Exception as e:
        return f"❌ Error sending email: {e}"

# Streamlit UI
st.title("🔥 Fire Detection App 🔥")
st.write("Upload an image to check if fire is present.")

# JavaScript to Fetch GPS Coordinates using Streamlit components
get_location_script = """
<script>
navigator.geolocation.getCurrentPosition(
    (position) => {
        let coords = position.coords.latitude + "," + position.coords.longitude;
        document.getElementById("location-data").value = coords;
    },
    (error) => {
        document.getElementById("location-data").value = "0,0";
    }
);
</script>
<input type="text" id="location-data" name="location" value="0,0">
"""

st.components.v1.html(get_location_script, height=50)

# **Wait for GPS location to load**
time.sleep(2)  # Wait for script execution

# Read GPS Coordinates
location_input = st.text_input("📍 Live Location (Latitude,Longitude):", "0,0")
latitude, longitude = map(float, location_input.split(","))

# Display location
if latitude == 0 and longitude == 0:
    st.warning("⚠️ GPS location not captured. Please enable location access and refresh the page.")
else:
    st.success(f"📍 Live Location: Latitude {latitude}, Longitude {longitude}")
    st.markdown(f"[🔗 View on Google Maps](https://www.google.com/maps?q={latitude},{longitude})")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Preprocess and make prediction
    processed_image = preprocess_image(image)
    prediction = model.predict(processed_image)

    # Interpret the result
    fire_probability = prediction[0][0]

    if fire_probability < 0.5:  # Fire detected if probability > 0.5
        st.error("🔥 Fire Detected!")

        if latitude != 0 and longitude != 0:
            # Send email alert with GPS location
            email_status = send_email(latitude, longitude, image)
            st.info(email_status)
        else:
            st.warning("⚠️ Cannot send email: GPS location not available.")
    else:
        st.success("✅ No Fire Detected.")
