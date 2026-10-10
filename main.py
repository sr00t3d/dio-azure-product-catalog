import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
import json
from dotenv import load_dotenv
load_dotenv()

blobConnectionString = os.getenv("BLOB_CONNECTION_STRING")
blobContainerName = os.getenv("BLOB_CONTAINER_NAME")
blobAccountName = os.getenv("BLOB_ACCOUNT_NAME")

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

st.title("Cadastro de Produtos")

# Formulário de cadastro de produtos
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png", "webp"])

# Salvar imagem no BLOB

def upload_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    container_client = blob_service_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + os.path.splitext(file.name)[1]
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(), overwrite=True)
    return f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"

def insert_product(product_name, product_price, product_description, product_image):
    try:
        if not product_image:
            st.warning("Por favor, selecione uma imagem para o produto.")
            return False

        image_url = upload_blob(product_image)
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        query = "INSERT INTO Produtos (nome, preco, descricao, imagem_url) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (product_name, float(product_price), product_description, image_url))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto: {e}")
        return False

if st.button("Salvar Produto"):
    if product_name and product_image:
        if insert_product(product_name, product_price, product_description, product_image):
            st.success("Produto salvo com sucesso!")
    else:
        st.warning("Preencha ao menos o nome e selecione uma imagem.")

st.header("Produtos Cadastrados")

if st.button("Listar Produtos"):
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor(as_dict=True)
        cursor.execute("SELECT id, nome, preco, descricao, imagem_url FROM Produtos")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if rows:
            for item in rows:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if item.get("imagem_url"):
                        st.image(item["imagem_url"], width=120)
                with col2:
                    st.subheader(item["nome"])
                    st.write(f"**Preço:** R$ {item['preco']:.2f}")
                    st.write(f"**Descrição:** {item['descricao']}")
                st.divider()
        else:
            st.info("Nenhum produto cadastrado ainda.")
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")