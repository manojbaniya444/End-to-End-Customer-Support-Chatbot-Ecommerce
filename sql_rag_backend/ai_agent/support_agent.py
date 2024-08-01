import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from operator import itemgetter
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
import re

load_dotenv()

def extract_query(text):
    # Define the regular expression to find the SQL query part
    pattern = r'SQLQuery:\s*(.*)'
    match = re.search(pattern, text)
    
    if match:
        return match.group(1)
    else:
        return None

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["PINECONE_API_KEY"] = os.environ["PINECONE_API_KEY"]


MODEL_NAME = "llama3-8b-8192"
EMBEDDING_MODEL = "D:\\Major Project\\Mid Term Project\\sql_rag_backend\\sentence-transformers-local\\all-MiniLM-L6-v2"
DB_PATH = "products.db"
INDEX_NAME = "storeagent"

embedding = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)
llm = ChatGroq(
    model=MODEL_NAME,
)

db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
write_query = create_sql_query_chain(llm, db)
extract_sql_query = RunnableLambda(lambda x: extract_query(x))
query_getter = write_query | extract_sql_query
execute_query = QuerySQLDataBaseTool(db=db)

answer_prompt = PromptTemplate.from_template(
    """
    "You are customer service agent for an e-commerce store located in Nepal.The store sell electronics and gadgets and you are chatting with a customer who need help.
    Given the following user question, corresponding  SQL query, and the result of the query, respond to the user with the suitable answer to the question without adding anything up in a short and concise manner as possible.
    
    If the SQL Result is empty, dont try to make up answer, just negate the user question.
    
    Question: <question>{question}</question>
    SQL Query: <query>{query}</query>
    SQL Result: <result>{result}</result>
    Answer:
    """
)

chat_system_prompt = (
    "You are customer service agent for an e-commerce store."
    "The store sell electronics and gadgets and you are chatting with a customer who need help."
    "Use the retrieved information or chat history to answer the customer's question."
    "If the retrieved information is not useful or the chat history is not relevant, you can ignore it and just answer the question."
    "but remember you only answer about the store and questions related to it and nothing else."
    "If asked anything else just say that you are just customer service agent and you can only answer about the store."
    "\n\n"
    "{context}"
)

answer_chain = answer_prompt | llm | StrOutputParser()

sql_chain = (
    RunnablePassthrough.assign(query=query_getter).assign(result=itemgetter("query") | execute_query)
    | answer_chain
)

vectorstore = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=embedding
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k":2
    }
)

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", chat_system_prompt),
        ("human", "{input}"),
    ]
)

chat_chain = create_stuff_documents_chain(
    llm,
    chat_prompt
)

rag_chain = create_retrieval_chain(
    retriever, # retrieve documents
    chat_chain # get the retrieved documents and pass it to LLM to answer the question
)

classifier_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a customer service agent who is expert in classifying the customer questions in ecommerce store."),
        ("human", "Classify the question: {question} as one of the following:\n1. 'product_inquiry': If the customer is asking about specific product price, product details or product stock only.\n2. 'general_information': If the customer is asking about the store information, store location, store policies or anything that is general information only about the store.\n3. 'greeting': If the user says hello, hi, initiates a conversation or asks about you. \n4. 'others': If the question does not fall in any of the above categories and is likely out of topic for a customer support service of ecommerce store.")
    ]
)

classification_chain = classifier_template | llm | StrOutputParser()

general_chain = PromptTemplate.from_template(
    """
    Respond to the user that you dont answer that question as you are a customer service agent and you can only answer about the store.
    """
) | llm | StrOutputParser()

greeting_chain = PromptTemplate.from_template(
    """
    You are customer service AI agent for an e-commerce store name 'All Electronics' which sells electronics and gadgets.You are AI agent so you dont have a name. Customer has greeted you with {question}. Respond to the customer with a greeting message in a short and concise response.
    """
) | llm | StrOutputParser()

def route(info):
    print(info)
    if "general_information" in info["topic"].lower():
        question = info["question"]
        return RunnableLambda(lambda x: {"input": question}) | rag_chain | RunnableLambda(lambda x: x["answer"])
    elif "product_inquiry" in info["topic"].lower():
        return sql_chain
    elif "greeting" in info["topic"].lower():
        return greeting_chain
    else:
        return general_chain
    
sql_rag_chain = {
    "topic": classification_chain,
    "question": lambda x: x["question"]
} | RunnableLambda(route)



def getResponseFromAgent(question: str):
    response = sql_rag_chain.invoke({"question": question})
    return response