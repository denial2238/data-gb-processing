import requests
import streamlit as st
import subprocess
import time

def start_flask_app():
    process = subprocess.Popen(['python', 'flask_app.py'])
    time.sleep(2)
    return process

FLASK_API_URL = 'https://data-gb-processing-dfbj772djxhxjzv5knkrft.streamlit.app'

def main():
    st.title("Healthcare Assistant")
    flask_process = start_flask_app()

    persona_data = st.text_area("Enter Persona Data:")
    query = st.text_input("Enter your query:")

    if st.button("Submit"):
        try:
            persona_response = requests.post(f'{FLASK_API_URL}/persona', json={'persona_data': persona_data}, timeout=10)
            persona_response.raise_for_status()
            persona = persona_response.json().get('persona')

            query_response = requests.post(f'{FLASK_API_URL}/query', json={'query': query}, timeout=10)
            query_response.raise_for_status()
            context = query_response.json().get('context')

            recommendation_response = requests.post(f'{FLASK_API_URL}/recommendation', json={'context': context}, timeout=10)
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

    if st.button("Stop Flask App"):
        flask_process.terminate()

if __name__ == "__main__":
    main()
