from typing import List, Tuple
from llama_index.core import  Document
from typing import List
import os
import llama_index
import pandas as pd
import json
from datetime import datetime
#import gspread
# from gspread_dataframe import get_as_dataframe
# from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from collections import Counter, defaultdict
# from pypdf import PdfReader
# from docx import Document
import regex as re
from oakdrf.logging_config import get_logger

logger = get_logger(__name__)

def custom_serializer(obj):
    """
    Serialize non-JSON serializable objects, such as datetime.
    Args:
        obj (any): The object to serialize.
    Returns:
        str: An ISO 8601 formatted string if the object is a datetime instance.
    Raises:
        TypeError: If the object type is not supported for serialization.
    """
    if isinstance(obj, datetime):
      return obj.isoformat()
    raise TypeError(f"Type {type(obj)} is not serializable")


def save_dict_to_json(input_dict: dict, file_path: str):
  '''
  This function saves the dictionary to JSON file
  Args:
    input dictionary, file path
  Returns:
    None
  '''
  with open(file_path, "w") as f:
    json.dump(input_dict, f, default=custom_serializer)

def load_dict_from_json(file_path: str) -> dict:
  '''
  This function loads the dictionary from json file
  Args:
    file path
  Returns:
    dictionary
  '''
  with open(file_path, "r") as f:
    loaded_dict  = json.load(f)
  return loaded_dict


################################################ EXCEL PROCESSING ##################################################################################

# def authenticate_gspread(gdrive_credentials_path: str) -> gspread.client.Client:
#   """Authenticate with Google Sheets using the service account JSON key."""
#   scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#   creds = ServiceAccountCredentials.from_json_keyfile_name(gdrive_credentials_path, scope)
#   client = gspread.authorize(creds)
#   return client
#
#
# def get_all_sheet_names(spreadsheet_id: str,
#                         client: gspread.client.Client) -> List[str]:
#   '''
#   This function returns all sheet names in a given excel file
#   Args:
#     spreadsheet id, client
#   Returns:
#     list containing all sheet names
#   '''
#   spreadsheet = client.open_by_key(spreadsheet_id)
#   return [sheet.title for sheet in spreadsheet.worksheets()]


# def get_single_sheet_from_spreadsheet(spreadsheet_id: str,
#                                       sheet_name: str,
#                                       client: gspread.client.Client):
#   '''
#   This function returns the dataframe from execl file & a given sheet
#   Args:
#     spreadsheet id, sheet name, client
#   Returns:
#     dataframe of that given sheet
#   '''
#   spreadsheet = client.open_by_key(spreadsheet_id)
#   worksheet = spreadsheet.worksheet(sheet_name)
#   df = get_as_dataframe(worksheet, evaluate_formulas=True, header=0)
#   return df.dropna(how="all")  # Drop empty rows


################################################ FOR CHAT PROMPT TEMPLATE ##################################################################################

# def convert_excel_to_dict(spreadsheet_id: str,
#                                      json_file_path: str,
#                                      gdrive_credentials_path: str) -> dict:
#   '''
#   This function converts the entire excel file in a dict.
#   Also checks the current json file & only adds new sheets which aren't present in the current json file
#   Args:
#     spreadsheet id, json file path, gdrive credentials path
#   Returns:
#     dictionary containing keys as sheet names & values as a dictionary of dataframe
#   '''
#   client = authenticate_gspread(gdrive_credentials_path)
#
#   #load the current json file
#   if os.path.exists(json_file_path):
#     try:
#       current_dict = load_dict_from_json(json_file_path)
#       current_sheet_names = current_dict.keys()
#     except Exception:
#       logger.warning("Error reading JSON file. Initilazing as empty")
#       current_dict = {}
#       current_sheet_names = set()
#   else:
#     logger.warning("JSON file does not exist. Extracting all sheets....")
#     current_dict = {}
#     current_sheet_names = set()
#
#
#   #get all sheet names
#   sheet_names = get_all_sheet_names(spreadsheet_id, client)
#
#   #find the new sheets
#   new_sheets = [sheet for sheet in sheet_names if sheet not in current_sheet_names]
#   logger.info(f"New sheets to add: {len(new_sheets)}")
#
#   #iterate through all sheets & convert each sheet into dictionary of records
#   for sheet in new_sheets:
#     logger.info(f"Preprocessing sheet: {sheet}")
#     try:
#       df = get_single_sheet_from_spreadsheet(spreadsheet_id, sheet)
#       dict_ = df.to_dict(orient = "records")
#       current_dict[sheet] = dict_
#     except Exception as e:
#       logger.error(f"Error in sheet: {sheet}. Moving on to the next one.....")
#
#   return current_dict

########################################## OUTCOME JOURNALS PROCESSING ################################
def deduplicate_columns(cols: List[str]) -> List[str]:
    """
    Ensures column names are unique by appending a suffix (e.g., '.1', '.2') to duplicates.
    Arguments:
        cols (list of str): List of column names that may contain duplicates.
    Returns:
        list of str: List of unique column names with suffixes added to duplicates.
    """
    seen = Counter()
    new_cols = []
    for col in cols:
        count = seen[col]
        new_col = f"{col}.{count}" if count > 0 else col
        new_cols.append(new_col)
        seen[col] += 1
    return new_cols


def preprocess_records_from_excel_style(dataframe: pd.DataFrame) -> List[dict]:
    """
    Cleans and preprocesses data extracted from an Excel-style table.
    Steps performed:
        1. Converts the input into a pandas DataFrame if it's a list.
        2. De-duplicates column names.
        3. Identifies and forward-fills the 'Partner' column.
        4. Cleans up cell values, removing whitespace and converting invalid values to None.
    Arguments:
        dataframe (pd.DataFrame or list of dict): Input data to preprocess.
    Returns:
        list of dict: Cleaned list of records where each row is represented as a dictionary.
    """
    if isinstance(dataframe, list):
        dataframe = pd.DataFrame(dataframe)

    # Step 1: De-duplicate column names (e.g., "Partner", "Partner.1", etc.)
    dataframe.columns = deduplicate_columns([col.strip().replace("\n", " ").replace("  ", " ") for col in dataframe.columns])

    # Step 3: Find the correct 'Partner' column
    partner_col = None
    for col in dataframe.columns:
        if col.strip().lower() == "partner":
            partner_col = col
            break
    if partner_col:
        dataframe["Partner"] = dataframe[partner_col].ffill()
    else:
        print("No 'Partner' column found!")

    records = []
    for _, row in dataframe.iterrows():
        record = {}
        for key in dataframe.columns:
            val = row.get(key)
            record[key] = str(val).strip() if pd.notna(val) and str(val).strip().lower() not in ["none", "nan", ""] else None
        records.append(record)

    return  records


def restructure_by_partner(records: list) -> dict:
  """
    Restructures a list of records into a dictionary grouped by the 'Partner' field.
    Arguments:
        records (list of dict): List of records, each containing a 'Partner' key.
    Returns:
        dict: A dictionary where keys are partner names and values are lists of records 
              (excluding the 'Partner' key) associated with each partner.
    """
  partner_dict = defaultdict(list)

  for entry in records:
    partner = entry.get("Partner").strip()
    other_entries = {key:value for key, value in entry.items() if key != "Partner"}
    partner_dict[partner].append(other_entries)

  return partner_dict


############################################### PDF/WORD to JSON ###########################################################
# def convert_pdf_into_json(folder_path: str, section_patterns: dict) -> dict:
#   """
#     Converts all PDF files in a specified folder into structured JSON format
#     by extracting and segmenting text based on section patterns.
#     For each PDF:
#         - All text is extracted from each page and concatenated.
#         - Predefined section patterns are used to locate the start of each section.
#         - Text is split into sections based on the order of matched patterns.
#     Arguments:
#         folder_path (str): Path to the folder containing PDF files.
#         section_patterns (dict): A dictionary where keys are section names and
#                                  values are regex patterns to identify section starts.
#     Returns:
#         dict: A dictionary where each key is a PDF filename and the value is
#               another dictionary mapping section names to their extracted text.
#   """
#   final_dict = {}
#
#   for filename in os.listdir(folder_path):
#     if not filename.endswith(".pdf"):
#       continue
#
#     file_path = os.path.join(folder_path, filename)
#     reader = PdfReader(file_path)
#
#     #join text of all pages
#     full_text = []
#     for i in range(0, len(reader.pages)):
#       text = reader.pages[i].extract_text()
#       full_text.append(text)
#     full_text = "\n".join(full_text)
#
#
#     #find the start index of the section
#     section_matches = {}
#     for section_name, pattern in section_patterns.items():
#       match_ = re.search(pattern, full_text, re.IGNORECASE)
#       if match_:
#         section_matches[section_name] = match_.start()
#
#     sorted_sections = sorted(section_matches.items(), key = lambda x:x[1])
#
#     #split full text as per section
#     sectioned_text = {}
#     for i, (section_name, start_idx) in enumerate(sorted_sections):
#       if i+1 < len(sorted_sections):
#         end_idx =  sorted_sections[i+1][1]
#       else:
#         end_idx = len(full_text)
#       sectioned_text[section_name] = full_text[start_idx:end_idx].strip()
#
#     final_dict[filename] = sectioned_text
#
#   return final_dict
#
#
# def convert_word_into_json(folder_path: str, section_patterns: dict) -> dict:
#   """
#     Converts all WORD files in a specified folder into structured JSON format
#     by extracting and segmenting text based on section patterns.
#     For each WORD:
#         - All text is extracted from each page and concatenated.
#         - Predefined section patterns are used to locate the start of each section.
#         - Text is split into sections based on the order of matched patterns.
#     Arguments:
#         folder_path (str): Path to the folder containing PDF files.
#         section_patterns (dict): A dictionary where keys are section names and
#                                  values are regex patterns to identify section starts.
#     Returns:
#         dict: A dictionary where each key is a PDF filename and the value is
#               another dictionary mapping section names to their extracted text.
#   """
#   final_dict = {}
#
#
#   for filename in os.listdir(folder_path):
#     if filename.endswith(".pdf"):
#       continue
#
#
#     if filename.endswith(".docx"):
#       file_path = os.path.join(folder_path, filename)
#       doc = Document(file_path)
#
#     #join text of all pages
#     full_text = []
#     for i in range(0, len(doc.paragraphs)):
#       text = doc.paragraphs[i].text
#       full_text.append(text)
#     full_text = "\n".join(full_text)
#
#
#     #find the start index of the section
#     section_matches = {}
#     for section_name, pattern in section_patterns.items():
#       match_ = re.search(pattern, full_text, re.IGNORECASE)
#       if match_:
#         section_matches[section_name] = match_.start()
#
#     sorted_sections = sorted(section_matches.items(), key = lambda x:x[1])
#
#     sectioned_text = {}
#     for i, (section_name, start_idx) in enumerate(sorted_sections):
#       if i+1 < len(sorted_sections):
#         end_idx =  sorted_sections[i+1][1]
#       else:
#         end_idx = len(full_text)
#       sectioned_text[section_name] = full_text[start_idx + len(section_name):end_idx].strip()
#
#     final_dict[filename] = sectioned_text
#
#   return final_dict