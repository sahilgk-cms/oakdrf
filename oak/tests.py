from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory
from unittest.mock import patch
from oak.models import ChatSession, ChatMessage, CaseStory, CaseStoryChatMessage, CaseStoryChatSession
from oakdrf.config import OUTCOME_JOURNALS_DICT
import uuid


# Create your tests here.
class ChatbotAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    @patch("oak.views.qa_chat_with_prompt")
    def test_start_new_chat(self, mock_qa):
        """
            Test: starting a new chat session (no session_id provided).
            - We mock qa_chat_with_prompt to avoid calling the real LLM.
            - Expect: API returns 200, creates a session, and saves 2 messages.
        """

        # Mock the return value of qa_chat_with_prompt
        mock_qa.return_value = {"answer": "This is a test answer", "source": "mocked"}

        # Send POST request to our API
        response = self.client.post("/oak/chat/",
                                    {
                                        "text": "phase 1",
                                        "query": "tell me something"
                                    },
                                    format="json")

        # Assertions = checks we expect to be true
        # API worked
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # New session created
        self.assertIn("session_id", response.data)

        # user + assistant saved
        self.assertEqual(ChatMessage.objects.count(), 2)

    @patch("oak.views.qa_chat_with_prompt")
    def test_continue_chat_existing_session(self, mock_qa):
        """
        Test: continue a chat using an existing session_id.
        - First we create a ChatSession manually.
        - Expect: API uses the same session, and saves 2 more messages.
        """

        mock_qa.return_value = {"answer": "Continue", "source": "mocked"}

        # Create a fake session in DB
        session = ChatSession.objects.create(id=str(uuid.uuid4()))

        # Send request with session_id
        response = self.client.post("/oak/chat/", {
            "session_id": str(session.id),
            "text": "phase 1",
            "query": "What next?"
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Works
        self.assertEqual(response.data["session_id"], str(session.id))  # Reused old session
        self.assertEqual(ChatMessage.objects.filter(session=session).count(), 2)  # 2 messages added

    def test_invalid_serializer(self):
        """
        Test: sending invalid data (missing query).
        - Serializer should reject it.
        - Expect: 400 Bad Request with error details.
        """
        response = self.client.post("/oak/chat/",
                                    {
                                        "text": "phase 1"
                                    }, format = "json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("oak.views.qa_chat_with_prompt", side_effect = Exception("mocked failure"))
    def test_qa_chat_with_failure(self, mock_qa):
        """
        Test: simulate qa_chat_with_prompt crashing.
        - We force it to raise an Exception.
        - Expect: API returns 500 Internal Server Error.
        """
        response = self.client.post("/oak/chat/",
                                    {
                                        "text": "phase 1",
                                        "query": "fail please"
                                    }, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)



class CaseStoryViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/oak/casestory/"

    def test_invalid_request_returns(self):
        """Missing required fields → should return 400"""
        response = self.client.post(self.url,
                                    {"main_document": "Outcome Journals"},
                                    format = "json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    @patch("oak.views.generate_case_story")
    @patch("oak.views.load_dict_from_json")
    def test_cache_hit(self, mock_load, mock_generate):
        """If CaseStory already exists → should return cached result"""


        journal = list(OUTCOME_JOURNALS_DICT.keys())[0]

        obj = CaseStory.objects.create(
            main_document = "Outcome Journals",
            journal = journal,
            partner = "Partner X",
            social_actor_name = "Social actor X",
            case_story = "Cached story"
        )

        payload = {
            "main_document": obj.main_document,
            "journal": obj.journal,
            "partner": obj.partner,
            "social_actor_name": obj.social_actor_name
        }

        response = self.client.post(self.url, payload, format = "json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["from_cache"])
        self.assertEqual(response.data["case_story"], "Cached story")

    @patch("oak.views.generate_case_story")
    @patch("oak.views.load_dict_from_json")
    def test_cache_miss(self, mock_load, mock_generate):
        """If no CaseStory exists → should generate and save"""
        journal = list(OUTCOME_JOURNALS_DICT.keys())[0]
        payload = {
            "main_document": "Outcome Journals",
            "journal": journal,
            "partner": "Pratham",
            "social_actor_name": "Youth from Tea Gardens",
        }

        mock_generate.return_value = "Generated story"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["from_cache"])
        self.assertEqual(CaseStory.objects.count(), 1)

    @patch("oak.views.generate_case_story", side_effect=Exception("Mocked failure"))
    @patch("oak.views.load_dict_from_json")
    def test_generation_failure_returns_500(self, mock_load, mock_generate):
        """If generate_case_story raises an exception → should return 500"""
        journal = list(OUTCOME_JOURNALS_DICT.keys())[0]

        # Provide a dummy JSON structure that matches what the view expects
        mock_load.return_value = {
            OUTCOME_JOURNALS_DICT[journal]: {
                "Partner X": [
                    {"(Social actor - individual, groups, institutions, networks, community, organisation)": "Actor 1"}
                ]
            }
        }

        payload = {
            "main_document": "Outcome Journals",
            "journal": journal,
            "partner": "Partner X",
            "social_actor_name": "Actor 1",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)


class CaseStoryChatViewTests(TestCase):
    def setUp(self):

        # Create a CaseStory instance
        self.case_story = CaseStory.objects.create(
            main_document="Outcome Journals",
            journal="Journal A",
            partner="Partner X",
            social_actor_name="Actor 1",
            case_story="This is a case story text."
        )

        # Create a session instance
        self.session = CaseStoryChatSession.objects.create(
            id = uuid.uuid4(),
            case_story = self.case_story
        )

        self.url = "/oak/casestorychat/"

    @patch("oak.views.qa_chat_with_prompt")
    def test_chat_with_existing_session(self, mock_qa):
        """Test chatting using an existing session"""

        # Mock the response of qa_chat_with_prompt
        mock_qa.return_value = {
            "answer": "This is a mocked answer.",
            "source": "mocked source"
        }

        payload = {
            "session_id": str(self.session.id),
            "query": "What is the case story about?"
        }

        response = self.client.post(self.url, payload, format = "json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("session_id", response.data)
        self.assertIn("query", response.data)
        self.assertIn("response", response.data)
        self.assertIn("chat_history", response.data)

        # Validate that the mocked response is used
        self.assertIn("This is a mocked answer.", response.data["response"])
        self.assertIn("mocked source", response.data["response"])

        # Check that messages were created
        chat_messages = CaseStoryChatMessage.objects.filter(session = self.session)
        self.assertEqual(chat_messages.count(), 2)
        roles = {msg.role for msg in chat_messages}
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)

    @patch("oak.views.qa_chat_with_prompt")
    def test_chat_with_new_session_with_case_story_id(self, mock_qa):
        """If no session_id but valid case_story_id → should create new session"""

        mock_qa.return_value = {
            "answer": "generated answer",
            "source": "generated source"
        }

        payload = {
            "case_story_id": self.case_story.id,
            "query": "explain this query"
        }

        response = self.client.post(self.url, payload, format = "json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("session_id", response.data)
        self.assertTrue(CaseStoryChatSession.objects.filter(case_story = self.case_story).exists())

    def test_invalid_session_id(self):
        """If session_id is invalid → should return 404"""
        payload = {
            "session_id": str(uuid.uuid4()),  # random ID, doesn't exist
            "query": "What's the story?"
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Invalid session id")

    def test_invalid_case_story_id(self):
        """If case_story_id is invalid → should return 404"""
        payload = {
            "case_story_id": 99999,  # assuming this ID doesn't exist
            "query": "Explain this case story."
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Invalid case story id")






# Create your tests here.
