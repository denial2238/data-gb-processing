from __future__ import annotations
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
from xata.client import XataClient
from xata.api_response import ApiResponse
from xata.helpers import to_rfc339
import textwrap
import google.generativeai as genai
from IPython.display import display, Markdown

load_dotenv()
PINECONE_API = os.getenv("PINECONE_API")
XATA_DATABASE_URL = os.getenv("XATA_DATABASE_URL")
XATA_API_KEY = os.getenv("XATA_API_KEY")
API_KEY = os.getenv('API_KEY')
genai.configure(api_key=API_KEY)

class RetrieAPI:
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API)
        index_name = "gbhack-index"
        if not self.pc.has_index(index_name):
            self.pc.create_index(
                name=index_name,
                dimension=256,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws', 
                    region='us-east-1'
                ) 
            ) 
        self.index = self.pc.Index(index_name)

    def query_similar(self, embed_values):
        query_results = self.index.query(
            namespace="gb_vectorstore1",
            vector=embed_values,
            top_k=20,
            include_values=False
        )
        return query_results

def embed_text(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/text-embedding-004", 
        content=text, 
        output_dimensionality=768  
    )
    return result["embedding"]

def get_chunks(file_path, chunk_size=2000):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
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

def build_context(results):
    context = ""
    for i in range(len(results["matches"])):
        context += "==========filename:" + results["matches"][i]["id"] + "==========" + "\n"
        context += get_text_form_match(results["matches"][i]) + "\n"
    return context

def create_persona(persona_data, model):
    prompt = "From the following data, create an imaginary persona in a few sentences. Make sure to include Health state and Activity Level.\n"
    prompt += persona_data
    response = model.generate_content(prompt)
    return response.text

def get_categories():
    with open("categories.txt", "r") as file:
        lines = file.readlines()
    categories = "\n ".join([category.strip() for category in lines[1:]])
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
    product_data = ""
    if "records" in resp:  # Check if 'records' exist in response
        for record in resp["records"]:
            product_data += f"{record['product_name']}\n{record['product_url']}\n{record['desc_text']}\n-------------\n"
    else:
        print("No records found in response.")
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



def create_prompt(context, query, persona):
    prompt = f"""You are a healthcare assistant aiming to inform clients with relevant, scientific information. 
              Based on the CONTEXT, QUERY, and PERSONA, advise accordingly. Include the filename for context.\n
              CONTEXT: \n
              {context} \n
              QUERY: \n
              {query} \n
              PERSONA: \n
              {persona}"""
    return prompt

retriveAPI = RetrieAPI()
model = genai.GenerativeModel('gemini-pro')
xata = XataClient(db_url=XATA_DATABASE_URL, api_key=XATA_API_KEY)

persona_data = "1) Type: Foodie, Age: 25, Sex: Žena, Weight: 60, Height: 175, Activity level: 3x týdně posilovna, 2x týdně kardio, Health state: Nízká hladina vitaminu D v krvi."
persona = create_persona(persona_data, model)
query = "Should this person take vitamin D to improve health?"
query_embeds = embed_text(query)
data_results = retriveAPI.query_similar(query_embeds)
context = build_context(data_results)
prompt = create_prompt(context, query, persona)

response_to_user = model.generate_content(prompt)
categories = get_categories()
recommended_category = get_category_recommendation(response_to_user.text, categories, model)
recommended_product_data = fetch_recommended_product(xata, recommended_category)
product_recommendation_for_user = get_product_from_eshop(recommended_product_data, context, model)

print(f"Response_to_user: {response_to_user.text}")
print(f"Recommended Category: {recommended_category}")
print(f"Recommended Product Data: {product_recommendation_for_user}")