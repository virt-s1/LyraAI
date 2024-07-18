# ref: https://www.gradio.app/guides/creating-a-custom-chatbot-with-blocks
# ref: https://github.com/chroma-core/chroma/blob/main/examples/chat_with_your_documents/main.py

from openai import OpenAI
import time
import gradio as gr

import os
from typing import List
from openai.types.chat import ChatCompletionMessageParam
import openai
import chromadb
import logging
import sys

from misc import param_init, save_data_csv

params = param_init()

MODEL_SERVICE_URL = params['model'].get('model_service_url')
MODEL_NAME = params['model'].get('model_name')
API_KEY = params['model'].get('model_name')
ai_client = OpenAI(
    base_url = MODEL_SERVICE_URL,
    api_key=API_KEY,
)

persist_directory = params['chromadb'].get('persist_directory')
collection_name = params['chromadb'].get('collection_name')
db_client = chromadb.PersistentClient(path=persist_directory)

# Get the collection.
collection = db_client.get_collection(name=collection_name)

CHAT_HISTORY_CSV = 'chat_history.csv'
CHAT_HISTORY_CSV_HEADER = ['Question','Response','Time']

CHAT_VOTED_CSV = 'chat_voted_history.csv'
CHAT_VOTED_CSV_HEADER = ['Voted','Response','Time']

# we record up/down voted reponse to csv for now, the feedback might help us build more accuracy reponse in future
def vote_for_response(data: gr.LikeData):
    data = [{'Voted':data.liked and 'Up' or 'Down', 'Response': data.value["value"], 'Time':time.ctime()}]
    save_data_csv(csv_file=CHAT_VOTED_CSV, headers=CHAT_VOTED_CSV_HEADER, data=data)

def build_prompt(query: str, context: List[str]) -> List[ChatCompletionMessageParam]:
    """
    Builds a prompt for the LLM. #

    This function builds a prompt for the LLM. It takes the original query,
    and the returned context, and asks the model to answer the question based only
    on what's in the context, not what's in its weights.

    More information: https://platform.openai.com/docs/guides/chat/introduction

    Args:
    query (str): The original query.
    context (List[str]): The context of the query, returned by embedding search.

    Returns:
    A prompt for the LLM (List[ChatCompletionMessageParam]).
    """

    system: ChatCompletionMessageParam = {
        "role": "system",
        "content": "I am going to ask you a question, which I would like you to answer"
        "based only on the provided context, and not any other information."
        "If there is not enough information in the context to answer the question,"
        'say "I am not sure", then try to make a guess.'
        "Break your answer up into nicely readable paragraphs.",
    }
    #print("context:{}".format(context))
    user: ChatCompletionMessageParam = {
        "role": "user",
        "content": f"The question is {query}. Here is all the context you have:"
        f'{context}',
        #f'{(" ").join(context)}',
    }

    #print("system:{}, user:{}".format(system, user))
    return [system, user]

def chat_with_local_query(query: str, context: List[str]) -> str:
    
    """
    Queries the OpenAI API to get a response to the question.

    Args:
    query (str): The original query.
    context (List[str]): The context of the query, returned by embedding search.

    Returns:
    A response to the question.
    """
    
    results = collection.query(
            query_texts=[query], n_results=params['chromadb'].get('n_results'), include=["documents", "metadatas"]
        )

    sources = "\n".join(
        [
            f"{result['filename']}: line {result['line_number']}"
            for result in results["metadatas"][0]  # type: ignore
        ]
    )

    #print("query:{} sources:{}".format(query,sources))
    try:
        response =  ai_client.chat.completions.create(
            model=MODEL_NAME,
            #messages=build_prompt(query, results['documents'][0]),
            messages=build_prompt(query, results['documents']),
            stream = True
            #parallel_tool_calls=False
        )
    except Exception as err:
        tmp_msg = "Error found, try again later! Details:{}".format(err)
        print(tmp_msg)
        yield tmp_msg
        
    tmp_msg = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            #print(chunk.choices[0].delta.content, end='')
            tmp_msg += chunk.choices[0].delta.content
            yield tmp_msg
    data = [{'Question': query, 'Response': tmp_msg, 'Time':time.ctime()}]
    save_data_csv(csv_file=CHAT_HISTORY_CSV, headers=CHAT_HISTORY_CSV_HEADER, data=data)

def chat_without_local_data(message, history):
    formatted_history = []
    print(history)
    for user, assistant in history:
        formatted_history.append({"role": "user", "content": user })
        #formatted_history.append({"role": "assistant", "content":assistant})
    formatted_history.append({"role": "user", "content": message})
    print(formatted_history)

    chat_completion = ai_client.chat.completions.create(
    messages = formatted_history,
    model = MODEL_NAME,
    stream=True,
)
    tmp_msg = ""
    for chunk in chat_completion:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end='')
            tmp_msg += chunk.choices[0].delta.content
            yield tmp_msg

chatbot = gr.Chatbot(placeholder="<strong>Welcome to {}!</strong><br>Ask Me Now".format(params['front_end'].get('title')), likeable=True)

with gr.Blocks() as main_page:
    chatbot.like(vote_for_response,None,None)
    gr.ChatInterface(chat_with_local_query,
    chatbot = chatbot,
    title=params['front_end'].get('title'),
    description=params['front_end'].get('description'),
    fill_height=False).queue()
    with gr.Accordion("About this service!", open=False):
        instruct = """
        **source_repo:** {}  
        **model_service_provider:** {}  
        **model_service_url**: {}  
        **model_name**: {}  
        **contacts**: {}  
        """.format(params['general'].get('source_repo'),params['model'].get('model_service_provider'),MODEL_SERVICE_URL, MODEL_NAME,
        params['general'].get('contacts'))
        gr.Markdown(instruct)

if __name__ == "__main__":
    main_page.launch(server_name='0.0.0.0',width=80,height=80,inline=True)