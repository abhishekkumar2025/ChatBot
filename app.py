import PyPDF2
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
import chainlit as cl
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

#loading environment variables
load_dotenv()

#function to initialise conv chain with GROQ LM
groq_api_key=os.environ['GROQ_API_KEY']

#init GROQ chat with the api , model name and settings
llm_groq=ChatGroq(
    groq_api_key=groq_api_key, model_name="llama3-70b-8192", temperature=0.3
)

@cl.on_chat_start
async def on_chat_start():
    files=None #variable to store files is initialised here
    
    
    #waiting for user to upload PDFS
    while files is None:
        files=await cl.AskFileMessage(
            content="Upload 1 or more PDF files to begin RAG(Retrieval Augmented Generation) Chat Feature!",
            accept=["application/pdf"],
            max_size_mb=500,
            max_files=10,
            timeout=100, #a timeout for user resp
        ).send()
    #adding spinner gif while processing   
    loading_msg=await cl.Message(content="Processing Files.....", elements=[cl.Image(name="spinner",display="inline",path="spinner.gif")]).send()
    #processing each uploaded PDF
    texts=[]
    metadatas=[]
    for file in files:
        print(file) #for debugging purpose
        
        #read PDF file
        pdf=PyPDF2.PdfReader(file.path)
        pdf_text=" "
        for page in pdf.pages:
            pdf_text+=page.extract_text()
            
        #splitting text into chunks
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=50)
        file_texts=text_splitter.split_text(pdf_text)
        texts.extend(file_texts)
        
        #create metadata for each chunk
        file_metadatas=[{"source": f"{i}-{file.name}"} for i in range(len(file_texts))]
        metadatas.extend(file_metadatas)
        
    #create a Chroma Vector Store
    embeddings=OllamaEmbeddings(model="nomic-embed-text")
    docsearch=await cl.make_async(Chroma.from_texts)(
        texts,embeddings,metadatas=metadatas
    )
    
    #init message history for Conv
    message_history=ChatMessageHistory()
    
    #Memory for Conversational Context
    memory=ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )
    
    #Create a chain that uses the chroma vector store
    chain=ConversationalRetrievalChain.from_llm(
        llm=llm_groq,
        chain_type="stuff",
        retriever=docsearch.as_retriever(),
        memory=memory,
        return_source_documents=True,
    )
    
    #sending an image with no of files uploaded
    #replacing spinner gif
    await cl.Message(
        content=f"Processing of {len(files)} files successfully completed. You can now utilize the RAG ChatBot.",
        elements=[]
    ).send()
        # Clear out any previous elements
    
    
    elements=[
        cl.Image(name="image",display="inline",path="myImg.jpg")
    ]
    
    #inform user that processing ended. Chat Now
    msg=cl.Message(content="RAG LLM", elements=elements)
    await msg.send()
    
    #store this chain in users session
    cl.user_session.set("chain",chain)
    
    

@cl.on_message
async def main(message:cl.Message):
    #Retrieve the chain from user session
    chain=cl.user_session.get("chain")
    #async callback/parallel callbacks
    cb=cl.AsyncLangchainCallbackHandler()
    
    #call the chain with users message content
    res=await chain.ainvoke(message.content,callbacks=[cb])
    answer=res["answer"]
    source_documents=res["source_documents"]
    
    text_elements=[] #to store text elements
    
    #process source docs if available
    if source_documents:
        for source_idx,source_doc in enumerate(source_documents):
            source_name=f"source_{source_idx}"
            #Create the text element referenced in the message
            text_elements.append(
                cl.Text(content=source_doc.page_content,name=source_name)
            )
        
        source_names=[text_el.name for text_el in text_elements]
        
        #adding source references to the answer
        if source_names:
            answer+=f"\nSources:{','.join(source_names)}"
        else:
            answer+="\nNo Source Found"
            
    #return results
    await cl.Message(content=answer,elements=text_elements).send()
    
        
        
        
        

