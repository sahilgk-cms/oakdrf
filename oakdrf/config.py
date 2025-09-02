import os
from dotenv import load_dotenv

load_dotenv()


GOOGLE_API_KEY_1 = os.getenv("GOOGLE_API_KEY_1")
GOOGLE_API_KEY_2 = os.getenv("GOOGLE_API_KEY_2")
GOOGLE_API_KEYS = [GOOGLE_API_KEY_1, GOOGLE_API_KEY_2]
GEMINI_MODEL_NAME = "models/gemini-2.0-flash"

LOGS_DIRECTORY = os.path.join(os.getcwd(), "logs")

#print(GOOGLE_API_KEYS)

current_file_path = os.getcwd()

PHASE1_JSON_FILE_PATH = os.path.join(current_file_path, "data", "phase1.json")
PHASE2_JSON_FILE_PATH = os.path.join(current_file_path, "data", "phase2.json")
PHASE2_WITH_SDD_JSON_FILE_PATH = os.path.join(current_file_path, "data", "phase2_with_sdd.json")
ALL_PHASES_JSON_FILE_PATH = os.path.join(current_file_path, "data", "all_phases.json")
GAF_JSON_FILE_PATH = os.path.join(current_file_path, "data", "gaf.json")
PROGRESS_REPORT_PARTNERS_PATH = os.path.join(current_file_path, "data", "progress_report_partners.json")
OUTCOME_JOURNALS_PATH = os.path.join(current_file_path, "data", "outcome_journals.json")

CASE_STORY_PROMPT_TEMPLATE = (
    "You are a development impact writer. Based on the context below, generate a NEW case story. "
    "Use a compelling, human-centered tone. Structure it with:\n"
    '''
    1. Title (Should capture the transformation)

    2. Context (2-3 lines)
    Geographic + thematic background
    Why this story matters

    3. The Problem
    What issue was being faced?
    Who was most affected?

    4. The Intervention
    What did the partner do?
    Who was involved (community, gov, other actors)?
    Mention any tools, processes (like participatory planning, legal training, MIS systems, etc.)

    5. Voices from the Ground (Optional)
    A quote or story from a beneficiary or frontline worker (Only if there is a quote in the provided context. If not, skip this.)

    6. Outcomes / Change Observed
    Tangible results — behavioural change, system-level changes, impact numbers if any

    7. What’s Next / Sustainability
    Is the change embedded?
    What are the next steps or replication ideas?
    '''

    "DO NOT copy any part of the example used earlier. Only use facts and ideas from the context.\n\n"
    "----------- CONTEXT -----------\n"
    "{context_str}\n"
    "----------- END CONTEXT -----------\n\n"
    "Start your case story below:"
)

CASE_STORY_ACROSS_ALL_ACTORS_TEMPLATE = (
    "You are a development impact writer. "
    "Using only the information provided in the context below, craft a comprehensive case story that captures key outcomes, changes, and impact across all social actors. "
    "Do not include any assumptions or fabricated details."
     "----------- CONTEXT -----------\n"
    "{context_str}\n"
    "----------- END CONTEXT -----------\n\n"
)

OUTCOME_JOURNALS_DICT = {
    "Phase 1 Journal": "phase1_journal",
    "Phase 2 Journal": "phase2_journal"
}

OUTCOME_JOURNALS_DOCUMENT_TYPE = "Outcome Journals"
PROGRESS_DOCUMENT_TYPE = "Progress Report Partners"

PROGRESS_REPORT_PARTNERS_DICT = {
    "Association for India's Development": "PR_Association_for_Indias_Development_StrenCommuForesGoverIn_202310310804.pdf",
    "Dignity Alliance International": "PR_A_Dignity_Alliance_International_SuppoTheMigraResilColla_202310310826.pdf",
    "Sign of Hope": "PR_A_Sign_of_Hope_StrenTribaVoiceInSunda_202311011310.pdf",
    "Development Research Communication and Services Centre": "PR_A_Development_Research_Communication_and_Services_Centre_FacilStratPlannAndColla_202310310824.pdf",
    "SEWA Bharat": "PR_SEWA_Bharat_AssisWomenWorkeInTheUnorg_202311011309.pdf",
    "Pratham Education Foundation": "PR_A_Pratham_Education_Foundation_VocatTrainForRuralYouth_202311011325.pdf",
    "National Centre for Advocacy Studies, Pune": "PR_A_National_Centre_for_Advocacy_Studies_Pune_AmpliCommuVoice_202310310923.pdf",
    "Baikunthapur Tarun Sangha": "PR_A_Baikunthapur_Tarun_Sangha_AmpliCommuVoiceInPatha_202310310807.pdf",
    "Terre des hommes Lausanne": "PR_Terre_des_hommes_Lausanne_AddreTraffThrouEffecReint_202311011315.pdf",
    "MUKTI": "PR_A_MUKTI_AmpliCommuVoiceInPatha_202310310917.pdf",
    "Rupantaran Foundation": "PR_A_Rupantaran_Foundation_AmpliCommuVoice_202311011304.pdf",
    "IPAS": "PR_A_IPAS_EnhanAgenImprSRH_202310310857.pdf",
    "New Alipore Praajak Development Society": "PR_A_New_Alipore_Praajak_Development_Society_AmpliCommuVoiceInPatha_202310310929.pdf",
    "Family Planning Association of India": "PR_A_Family_Planning_Association_of_India_ExpanSexuaReproHealtRight_202310310834.pdf",
    "Indraprastha Srijan Welfare Society": "PR_A_Indraprastha_Srijan_Welfare_Society_AmpliCommuVoice_202310310853.pdf",
    "Swaniti Initiative": "PR_A_Swaniti_Initiative_EnsurAccesToSocioAndLabou_202311011313.pdf",
    "Sanhita": "PR_A_Sanhita_PreveAndRedreOfSexuaHaras_202311011307.pdf",
    "Nazdeek": "PR_A_Nazdeek__Inc_EnsurAccesToSocioAndLabou_202310310927.pdf",
    "One Year Progress Report": "One Year Progress Report - UPDATED VERSION_23.1.24.docx"
}

MAIN_DOCUMENT_CHOICES = [
        ("Outcome Journals", "Outcome Journals"),
        ("Progress Report Partners", "Progress Report Partners"),
    ]