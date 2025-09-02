from typing import List
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage
from llama_index.llms.gemini import Gemini
from pydantic import BaseModel
from typing import List
import os
import llama_index
import nest_asyncio
from oakdrf.config import GOOGLE_API_KEYS, GEMINI_MODEL_NAME
import re
import json
from dotenv import load_dotenv
import time
from requests.exceptions import HTTPError, ConnectionError, Timeout
from oakdrf.logging_config import get_logger


load_dotenv()
nest_asyncio.apply()

logger = get_logger(__name__)



def switch_google_api_key(current_index: int, first_attempt:bool = False) -> int:
   """
    Switch to the next API key in the list.
    Args:
        current_index (int): The index of the current API key.
        first_attempt (bool): default is False
    Returns:
        int: The new API key index.
    Raises:
        ValueError: If all API keys have been exhausted.
    """
   # move to the next index 
   # will be reset to 0 once reached the end
   new_index = (current_index + 1)%len(GOOGLE_API_KEYS)
   
   if new_index == 0:
      
      # stopping condition for recursion
      if first_attempt: 
        raise ValueError("All API keys are exhausted")
      
      # go into recursive loop....
      # retries when the new index = 0 but this time first attempt = True
      # this means its a retry
      return switch_google_api_key(new_index, first_attempt = True)
   
   logger.warning(f"API key {GOOGLE_API_KEYS[current_index]} rate limit exceeded. Switching to {GOOGLE_API_KEYS[new_index]}")
   return new_index
   


class QAResponse(BaseModel):
   answer: str
   source: str


def convert_query_into_chat_message(text: str, 
                                    query: str,
                                    chat_history: List[dict] = None) -> List[llama_index.core.base.llms.types.ChatMessage]:
   '''
   This function converts the input text & query into chat message template
   Args:
   Input context text & query
   Returns:
   Chat Message template 
   '''
   messages = []

   if chat_history:
        for chat in chat_history:
            role = chat.get("role")
            message = chat.get("message")
            if role in ["user", "assistant"] and message:
                messages.append(ChatMessage(role=role, content=message))

   template = (
      "The following text consists of some context, a question, and some instructions. "
      "Use the context to answer the question and follow the instructions while doing so."
      "\n\n----------- Start of Context ----------\n"
      f"{text}\n"
      "\n----------- End of Context -----------\n"

       "\n\n----------- Start of Previous Conversation ----------\n"
    "You will also be provided with the history of previous messages between the user and the assistant. "
    "Use this history to maintain coherence, avoid repetition, and build upon prior discussion where relevant.\n"
    "Note: If the current query depends on something mentioned earlier, be sure to incorporate it.\n"
    "----------- End of Previous Conversation -----------\n"


      "When answering, please provide relevant supporting details and cite the specific part of the context where the answer is derived from."
   "Try to rephrase or summarize the relevant supporting details in your answer instead of using the exact same wording as present in the context."
   "Make sure your answer responds to the query being asked and does not contain irrelevant information or spelling mistakes."
   "Your answer should be concise and to the point while including all necessary details."
   "Try not to use too many bullet points with short sentences, only use them when necessary. You can use bullet points to list out important points or key details."
   "Your entire answer should not be longer than 500 words."
      "Please provide your response in **JSON format** with the following fields:\n"
      "```json\n"
      "{\n"
      '  "answer": "<Your concise answer here>",\n'
      '  "source": "<Plain text reference to where the answer is found>"\n'
      "}\n"
      "```\n"
      "If the answer is not found in the provided context, return:\n"
      "```json\n"
      '{ "answer": "Answer not found from the given context provided.", "source": "" }\n'
      "```\n"
      "\n----------- End of Instructions -----------\n"
   )
   messages.insert(0, ChatMessage(role="system", content=template))
   messages.append(ChatMessage(role="user", content=query))
   return messages


def clean_json_output(result_text: str) -> dict:
   '''
    This function converts the raw result from LLM into json
    Args:
      result text 
    Returns:
      dictionary
   '''
   try:
        # Remove triple backticks and optional 'json' after them
        cleaned = re.sub(r"```(?:json)?\n?", "", result_text)
        cleaned = cleaned.strip().strip("`")  # Just in case

        return json.loads(cleaned)

   except json.JSONDecodeError as e:
        logger.error(f"Failed to decode json: {e}")
        logger.info(f"Raw response: {result_text}")
        return None
      

def format_response(response: dict) -> dict:
   '''
    This function formats the answer and source response into string values
    Args:
      response  dictionary
    Returns:
      formatted dictionary
   '''
   formatted_response = {}
  
  # format answer into string
   if isinstance(response["answer"], dict):
      formatted_response["answer"] = "\n".join([f"{k}: {v}" for k, v in response["answer"].items()])
   elif isinstance(response["answer"], list):
      formatted_response["answer"] = "\n".join(response["answer"])
   else:
      formatted_response["answer"] = str(response["answer"])

  # format source into string
   if isinstance(response["source"], dict):
      formatted_response["source"] = "\n".join([f"{k}: {v}" for k, v in response["source"].items()])
   elif isinstance(response["source"], list):
      formatted_response["source"] = "\n".join(response["source"])
   else:
      formatted_response["source"] = str(response["source"])

   return formatted_response


def qa_chat_with_prompt(text: str, 
                        query: str,
                        chat_history: List[dict]) -> dict:
  '''
  This function returns a dictionary containing answer & source
  Args:
    Input context text & query
  Returns:
    Dictionary containing query, answer, source
  '''
  messages = convert_query_into_chat_message(text = text, 
                                           query = query,
                                           chat_history = chat_history)
  current_index = 0

  while True: 
     try:
        api_key = GOOGLE_API_KEYS[current_index]
        llm = Gemini(model = GEMINI_MODEL_NAME, api_key = api_key)
        resp = llm.chat(messages)  #llama_index.core.base.llms.types.ChatResponse

        if not resp.message.blocks or not resp.message.blocks[0].text.strip():
           logger.error("Empty response received from Gemini")
           return {"query": query, "answer": "ERROR: Empty response received from Gemini", "source": None}

        result_text = resp.message.blocks[0].text
        json_response = clean_json_output(result_text)
        formatted_response = format_response(json_response)
        parsed_response = QAResponse(**formatted_response)

        d = {}
        d["query"] = query
        d["answer"] = parsed_response.answer
        d["source"] = parsed_response.source
        return d
     
     except HTTPError as e:
        if e.response.status_code == 429:
            try:
              current_index = switch_google_api_key(current_index)
              time.sleep(2)
            except ValueError:
               raise ValueError("All API keys are exhausted or invalid")
            
        elif e.response.status_code in [501, 502, 503, 504]:
           logger.error(f"Server error {e.response.status_code}: {e.response.text}")
           raise e
           
        
        elif e.response.status_code in [401, 401, 403, 404]:
           logger.error(f"Client error {e.response.status_code}: {e.response.text}")
           raise e
           
        else:
           raise e 
        
     except (ConnectionError, Timeout) as e:
        logger.error(f"Network error: {str(e)}")
        raise e
     
     except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise e


def stream_data(response):
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.02)