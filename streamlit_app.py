import requests
import streamlit as st
import threading
import time

FLASK_API_URL = 'http://127.0.0.1:5000'

def start_flask_app():
    from flask_app import app  # Import your Flask app
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True)
    flask_thread.start()
    time.sleep(5)  # Give Flask some time to start

def main():
    st.title("Healthcare Assistant")

    start_flask_app()  # Start the Flask app in a separate thread

    persona_data = st.text_area("Enter Persona Data:")
    query = st.text_input("Enter your query:")

    if st.button("Submit"):
        try:
            persona_response = requests.post(f'{FLASK_API_URL}/api/persona', json={'persona_data': persona_data})
            persona_response.raise_for_status()
            persona = persona_response.json().get('persona')

            query_response = requests.post(f'{FLASK_API_URL}/api/query', json={'query': query})
            query_response.raise_for_status()
            context = query_response.json().get('context')

            recommendation_response = requests.post(f'{FLASK_API_URL}/api/recommendation', json={'context': context})
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

if __name__ == "__main__":
    main()
