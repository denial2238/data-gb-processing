from flask import Flask, request, jsonify
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeException
import os
from dotenv import load_dotenv
from xata.client import XataClient
import google.generativeai as genai
import logging

load_dotenv()
PINECONE_API = os.getenv("PINECONE_API")
XATA_DATABASE_URL = os.getenv("XATA_DATABASE_URL")
XATA_API_KEY = os.getenv("XATA_API_KEY")
API_KEY = os.getenv('API_KEY')
genai.configure(api_key=API_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class RetrieAPI:
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API)
        index_name = "gbhack-index"
        existing_indexes = self.pc.list_indexes()
        if index_name not in existing_indexes:
            try:
                self.pc.create_index(
                    name=index_name,
                    dimension=256,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            except PineconeException as e:
                if "already exists" in str(e):
                    logging.info(f"Index '{index_name}' already exists.")
                else:
                    raise
        self.index = self.pc.Index(index_name)

    def query_similar(self, embed_values):
        query_results = self.index.query(
            namespace="gb_vectorstore1",
            vector=embed_values,
            top_k=20,
            include_values=False
        )
        return query_results

retriveAPI = RetrieAPI()
model = genai.GenerativeModel('gemini-pro')
xata = XataClient(db_url=XATA_DATABASE_URL, api_key=XATA_API_KEY)

@app.route('/api/persona', methods=['POST'])
def handle_persona():
    data = request.json
    persona_data = data.get('persona_data')
    prompt = "From the following data, create an imaginary persona in a few sentences. Make sure to include Health state and Activity Level.\n" + persona_data
    response = model.generate_content(prompt)
    return jsonify({'persona': response.text})

@app.route('/api/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query')
    query_embeds = embed_text(query)
    data_results = retriveAPI.query_similar(query_embeds)
    context = build_context(data_results)
    return jsonify({'context': context})

@app.route('/api/recommendation', methods=['POST'])
def handle_recommendation():
    data = request.json
    context = data.get('context')
    categories = get_categories()
    recommended_category = get_category_recommendation(context, categories, model)
    recommended_product_data = fetch_recommended_product(xata, recommended_category)
    product_recommendation = get_product_from_eshop(recommended_product_data, context, model)
    return jsonify({
        'recommended_category': recommended_category,
        'product_recommendation': product_recommendation
    })

def embed_text(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        output_dimensionality=768
    )
    return result["embedding"]

def build_context(results):
    context = ""
    for match in results["matches"]:
        context += f"==========filename: {match['id']}==========\n"
        context += get_text_form_match(match) + "\n"
    return context

def get_chunks(file_path, chunk_size=2000):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        return []
    chunks = [(f"{file_path}-{eid}", text[i:i+chunk_size]) for eid, i in enumerate(range(0, len(text), chunk_size))]
    return chunks

def get_text_form_match(match):
    file_id = match["id"]
    filename = file_id.split("-")[0]
    chunks = get_chunks(filename)
    for chunk in chunks:
        if chunk[0] == file_id:
            return chunk[1]
    return "Nothing"

def get_categories():
    with open("categories.txt", "r") as file:
        lines = file.readlines()
    categories = "\n".join([category.strip() for category in lines[1:]])
    return categories

def get_category_recommendation(context, categories, model):
    prompt = f"""Here are categories. Based on the context, return the one category that best fits the context. 
              Output only the category name. \n
              CONTEXT: \n
              {context} \n
              CATEGORIES: \n
              {categories}"""
    response = model.generate_content(prompt)
    return response.text.strip()

def fetch_recommended_product(xata, recommended_category):
    resp = xata.data().query("products", {
        "columns": ["product_name", "product_url", "desc_text"],
        "filter": {"category": recommended_category},
        "page": {"size": 5}
    })
    logging.info("Xata Response: %s", resp)
    product_data = ""
    if "records" in resp and resp["records"]:
        for record in resp["records"]:
            product_data += f"{record['product_name']}\n{record['product_url']}\n{record['desc_text']}\n-------------\n"
    else:
        return f"No products found in the '{recommended_category}' category. Please check other categories or add more products."
    return product_data

def get_product_from_eshop(recommended_product_data, context, model):
    prompt = f"""You are a product recommendation assistant. Based on the context and product data, 
              recommend a suitable fitness product. \n
              CONTEXT: \n
              {context} \n
              PRODUCT DATA: \n
              {recommended_product_data} \n
              Please provide the product title and product URL."""
    response = model.generate_content(prompt)
    return response.text

if __name__ == '__main__':
    app.run(debug=True)
