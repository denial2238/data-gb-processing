import requests
import streamlit as st
import subprocess
import time

def start_flask_app():
    # Start the Flask app as a subprocess
    process = subprocess.Popen(['python', 'flask_app.py'])
    time.sleep(2)  # Wait for a moment to ensure Flask has started
    return process

# Update this URL to match your deployed Flask API
FLASK_API_URL = 'https://data-gb-processing-dfbj772djxhxjzv5knkrft.streamlit.app'

def main():
    st.title("Healthcare Assistant")

    # Start the Flask app when Streamlit app starts
    flask_process = start_flask_app()

    persona_data = st.text_area("Enter Persona Data:")
    query = st.text_input("Enter your query:")

    if st.button("Submit"):
        try:
            # Interact with the Flask API
            persona_response = requests.post(f'{FLASK_API_URL}/persona', json={'persona_data': persona_data})
            persona_response.raise_for_status()  # Check for request errors
            persona = persona_response.json().get('persona')

            query_response = requests.post(f'{FLASK_API_URL}/query', json={'query': query})
            query_response.raise_for_status()
            context = query_response.json().get('context')

            recommendation_response = requests.post(f'{FLASK_API_URL}/recommendation', json={'context': context})
            recommendation_response.raise_for_status()
            recommended_category = recommendation_response.json().get('recommended_category')
            product_recommendation = recommendation_response.json().get('product_recommendation')

            st.subheader("Response to User:")
            st.write(persona)

            st.subheader("Recommended Category:")
            st.write(recommended_category)

            st.subheader("Recommended Product:")
            st.write(product_recommendation)

        except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with Flask app: {e}")

    # Optionally, you can terminate the Flask app when the Streamlit app is stopped
    if st.button("Stop Flask App"):
        flask_process.terminate()

if __name__ == "__main__":
    main()
