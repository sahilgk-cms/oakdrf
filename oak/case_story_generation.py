from llama_index.core import PromptTemplate
from llama_index.llms.gemini import Gemini
from llama_index.core.base.llms.types import ChatMessage
from requests.exceptions import HTTPError, ConnectionError, Timeout
from time import time
from typing import List, Union
#from markdown_pdf import MarkdownPdf, Section
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oak.chat import switch_google_api_key
from oak.files_processing import load_dict_from_json
from oakdrf.config import GOOGLE_API_KEYS, GEMINI_MODEL_NAME, OUTCOME_JOURNALS_PATH, PROGRESS_REPORT_PARTNERS_PATH, CASE_STORY_PROMPT_TEMPLATE, CASE_STORY_ACROSS_ALL_ACTORS_TEMPLATE, OUTCOME_JOURNALS_DOCUMENT_TYPE, PROGRESS_DOCUMENT_TYPE
#from handlers.MongoDBHandler import MongoDBHandler
from oakdrf.logging_config import get_logger



# logger = get_logger(__name__)
# mongodb_handler = MongoDBHandler(CASE_STORY_COLLECTION)
#
#
# def check_case_story_exists(document_type: str,
#                             journal_name: str = None,
#                             partner_name: str = None,
#                             social_actor_name: str = None,
#                             pdf_name: str = None):
#     if document_type == OUTCOME_JOURNALS_DOCUMENT_TYPE:
#         query = {
#             "document_type" : document_type,
#             "journal_name": journal_name,
#             "partner_name": partner_name,
#             "social_actor_name": social_actor_name
#         }
#     else:
#         query = {
#             "document_type" : document_type,
#             "pdf_name": pdf_name
#         }
#
#     results = mongodb_handler.read_data(query)
#     if results:
#         return results[0]
#     return None
#
#
# def store_case_story(
#         case_story: str,
#         document_type: str,
#         journal_name: str = None,
#         partner_name: str = None,
#         social_actor_name: str = None,
#         pdf_name: str = None,
#         overwrite: bool = False
#     ):
#     if document_type == OUTCOME_JOURNALS_DOCUMENT_TYPE:
#         data = {
#             'document_type': document_type,
#             'journal_name': journal_name,
#             'partner_name': partner_name,
#             'social_actor_name': social_actor_name,
#             'case_story': case_story
#         }
#         query = {'document_type': document_type, 'journal_name': journal_name, 'partner_name': partner_name}
#     else:
#         data = {
#             'document_type': document_type,
#             'pdf_name': pdf_name,
#             'case_story': case_story
#         }
#         query = {'document_type': document_type, 'pdf_name': pdf_name}
#
#     if overwrite:
#         mongodb_handler.insert_data(data)
#         logger.info(f"Inserted case story for {journal_name} and {partner_name} or {pdf_name}")
#         return
#
#     existing_case_story = check_case_story_exists(query)
#     if not existing_case_story:
#         mongodb_handler.insert_data(data)


def convert_query_to_prompt(text: str, social_actor_name: str) -> str:
    '''
    Converts input text into a prompt that can be used in the chat template
    Args: 
        Input context text and query
    Returns:
        Prompt Template
    '''
    if social_actor_name == "All":
        prompt_to_be_used = CASE_STORY_ACROSS_ALL_ACTORS_TEMPLATE
    else:
        prompt_to_be_used = CASE_STORY_PROMPT_TEMPLATE

    prompt = PromptTemplate(prompt_to_be_used)
    prompt_text = prompt.format(context_str=text)

    return prompt_text


def convert_query_into_chat(text: str, social_actor_name: str) -> List[ChatMessage]:
    '''
    This function converts the prompt text into chat message template
    Args:
      Input context text and query
    Returns:
      Chat Message template 
     '''
    prompt_text = convert_query_to_prompt(text, social_actor_name)
    return [ChatMessage(role="user", content=prompt_text)]


def generate_case_story(text: str, social_actor_name: str = None) -> Union[str, None]:
    '''
    This function generates case story
    Args:
      Input text 
    Returns:
      case story 
     '''
    message = convert_query_into_chat(text, social_actor_name)

    current_index = 0
    while True:
        try:
            api_key = GOOGLE_API_KEYS[0]
            llm = Gemini(model = GEMINI_MODEL_NAME, api_key = api_key)
            response = llm.chat(message)
            try:
                return response.message.content.strip()
            except Exception as ex:
                logger.error(f"Error: {ex}")
                return response.text.strip()
            
        except HTTPError as e:
            if e.response.status_code == 429:
                try:
                    current_index = switch_google_api_key(current_index)
                    time.sleep(2)
                except ValueError:
                    raise ValueError("All API keys are exhausted or invalid.")
                
            elif e.response.status_code in [501, 502, 503, 504]:
                logger.error(f"Server error {e.response.status_code}: {e.response.text}")
                return  None
        
            elif e.response.status_code in [401, 401, 403, 404]:
                logger.error(f"Client error {e.response.status_code}: {e.response.text}")
                return  None
            else:
                raise e 
        
        except (ConnectionError, Timeout) as e:
            logger.error(f"Network error: {str(e)}")
            return  None
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return  None

            
# def generate_all_case_stories():
#     outcome_journals = load_dict_from_json(OUTCOME_JOURNALS_PATH)
#     progress_report_partners = load_dict_from_json(PROGRESS_REPORT_PARTNERS_PATH)
#
#     for journal in outcome_journals.keys():
#         for partner in outcome_journals[journal].keys():
#             context = outcome_journals[journal][partner]
#             case_story = generate_case_story(text = context)
#             store_case_story(
#                 case_story = case_story,
#                 document_type = OUTCOME_JOURNALS_DOCUMENT_TYPE,
#                 journal_name = journal,
#                 overwrite = True
#             )
#
#     for pdf in progress_report_partners.keys():
#         context = progress_report_partners[pdf]
#         case_story = generate_case_story(text = context)
#         store_case_story(
#             case_story = case_story,
#             document_type = PROGRESS_DOCUMENT_TYPE,
#             pdf_name = pdf,
#             overwrite = True
#         )


# def get_case_story_pdf(
#         case_story_markdown: str,
#     ) -> MarkdownPdf:
#     '''
#     Export the generated case story to a PDF file that can be downloaded through the web application.
#     Args:
#         case_story_markdown: The generated case story in Markdown format.
#     Returns:
#         None
#     '''
#
#     pdf = MarkdownPdf(toc_level=2, optimize=True)
#     pdf.add_section(Section(case_story_markdown, toc=False))
#
#     return pdf