import requests
import streamlit as st
import logging

FLASK_API_URL = 'http://127.0.0.1:5000'

def main():
    logging.basicConfig(level=logging.INFO)
    st.title("Healthcare Assistant")

    persona_data = st.text_area("Enter Persona Data:")
    query = st.text_input("Enter your query:")

    if st.button("Submit"):
        try:
            logging.info("Submitting persona data and query.")
            persona_response = requests.post(f'{FLASK_API_URL}/api/persona', json={'persona_data': persona_data}, timeout=10)
            persona_response.raise_for_status()
            logging.info(f"Raw response from /api/persona: {persona_response.text}")
            persona = persona_response.json().get('persona')

            query_response = requests.post(f'{FLASK_API_URL}/api/query', json={'query': query}, timeout=10)
            query_response.raise_for_status()
            logging.info(f"Raw response from /api/query: {query_response.text}")
            context = query_response.json().get('context')

            recommendation_response = requests.post(f'{FLASK_API_URL}/api/recommendation', json={'context': context}, timeout=10)
            recommendation_response.raise_for_status()
            logging.info(f"Raw response from /api/recommendation: {recommendation_response.text}")
            recommended_category = recommendation_response.json().get('recommended_category')
            product_recommendation = recommendation_response.json().get('product_recommendation')

            st.subheader("Response to User:")
            st.write(persona)

            st.subheader("Recommended Category:")
            st.write(recommended_category)

            st.subheader("Recommended Product:")
            st.write(product_recommendation)

            logging.info("Successfully retrieved persona, category, and product recommendation.")

        except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with Flask app: {e}")
            logging.error(f"RequestException: {e}")

if __name__ == "__main__":
    main()
