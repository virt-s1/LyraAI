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

from misc import param_init

params = param_init()

BASE_MODEL_URL = params['model'].get('base_model_url')
MODEL_NAME = params['model'].get('model_name')
API_KEY = params['model'].get('model_name')
ai_client = OpenAI(
    base_url = BASE_MODEL_URL,
    api_key=API_KEY,
)

persist_directory = params['chromadb'].get('persist_directory')
collection_name = params['chromadb'].get('collection_name')
db_client = chromadb.PersistentClient(path=persist_directory)

# Get the collection.
collection = db_client.get_collection(name=collection_name)

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
    response =  ai_client.chat.completions.create(
        model=MODEL_NAME,
        #messages=build_prompt(query, results['documents'][0]),
        messages=build_prompt(query, results['documents']),
        stream = True
    )
    tmp_msg = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end='')
            tmp_msg += chunk.choices[0].delta.content
            yield tmp_msg

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

with gr.Blocks() as main_page:
    gr.ChatInterface(chat_with_local_query,
    title=params['front_end'].get('title'),
    description=params['front_end'].get('description'),
    fill_height=False).queue()
    with gr.Accordion("About this service!", open=False):
        instruct = """
        **service_provider:** {}  
        **base_model_url**: {}  
        **model_name**: {}  
        **Contacts**: yuxisun@redhat.com, yoguo@redhat.com, xiliang@redhat.com
        """.format(params['model'].get('service_provider'),BASE_MODEL_URL, MODEL_NAME)
        gr.Markdown(instruct)
    

if __name__ == "__main__":
    main_page.launch(server_name='0.0.0.0',width=80,height=80,inline=True)