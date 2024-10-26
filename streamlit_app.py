import requests
import streamlit as st

def main():
    st.title("Healthcare Assistant")
    persona_data = st.text_area("Enter Persona Data:")
    query = st.text_input("Enter your query:")

    if st.button("Submit"):
        persona_response = requests.post('http://127.0.0.1:5000/api/persona', json={'persona_data': persona_data})
        persona = persona_response.json().get('persona')

        query_response = requests.post('http://127.0.0.1:5000/api/query', json={'query': query})
        context = query_response.json().get('context')

        recommendation_response = requests.post('http://127.0.0.1:5000/api/recommendation', json={'context': context})
        recommended_category = recommendation_response.json().get('recommended_category')
        product_recommendation = recommendation_response.json().get('product_recommendation')

        st.subheader("Response to User:")
        st.write(persona)

        st.subheader("Recommended Category:")
        st.write(recommended_category)

        st.subheader("Recommended Product:")
        st.write(product_recommendation)

if __name__ == "__main__":
    main()
