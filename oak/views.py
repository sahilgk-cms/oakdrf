from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from oak.case_story_generation import generate_case_story
from oak.files_processing import load_dict_from_json
from oak.serializers import ChatRequestSerializer, ChatMessageSerializer, CaseStoryRequestSerializer, CaseStoryChatRequestSerializer, CaseStoryChatMessageSerializer
from oak.models import ChatSession, ChatMessage, CaseStory, CaseStoryChatMessage, CaseStoryChatSession
from oak.chat import qa_chat_with_prompt
from oakdrf.logging_config import get_logger
import json
import uuid
from oakdrf.config import ALL_PHASES_JSON_FILE_PATH, PHASE1_JSON_FILE_PATH, PHASE2_WITH_SDD_JSON_FILE_PATH, \
    PROGRESS_REPORT_PARTNERS_PATH, GAF_JSON_FILE_PATH, OUTCOME_JOURNALS_PATH, PROGRESS_REPORT_PARTNERS_DICT, OUTCOME_JOURNALS_DICT

logger = get_logger(__name__)

# Create your views here.
class ChatbotAPIView(APIView):
    """API View for chat"""
    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data = request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            query = serializer.validated_data['query']
            session_id = serializer.validated_data.get('session_id')

            if not session_id:
                session_id = str(uuid.uuid4())

            if text == "all phases":
                text = json.load(open(ALL_PHASES_JSON_FILE_PATH, "r", encoding = "utf-8"))
            elif text == "phase 1":
                text = json.load(open(PHASE1_JSON_FILE_PATH, "r", encoding = "utf-8"))
            elif text == "phase 2":
                text = json.load(open(PHASE2_WITH_SDD_JSON_FILE_PATH, "r", encoding = "utf-8"))
            elif text == "progress report partners":
                text = json.load(open(PROGRESS_REPORT_PARTNERS_PATH, "r", encoding = "utf-8"))
            elif text == "grant application form":
                text = json.load(open(GAF_JSON_FILE_PATH, "r", encoding = "utf-8"))

            session, _ = ChatSession.objects.get_or_create(id = session_id)

            chat_history = list(session.chatmessages.all()
                                .order_by("timestamp")
                                .values("role", "message"))

            try:
                response = qa_chat_with_prompt(text = text,
                                           query = query,
                                           chat_history = chat_history)
                full_response = f"Answer: {response["answer"]}\nSource: {response['source']}"

                ChatMessage.objects.create(session=session,
                                           role="user",
                                           message=query)

                ChatMessage.objects.create(session = session,
                                           role = "assistant",
                                           message = full_response)

                chat_history = ChatMessageSerializer(session.chatmessages.all(), many=True).data

                return Response({ "session_id": str(session.id),
                                  "query":query,
                                  "response": full_response,
                                 "chat_history": chat_history},
                                status = status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Chatbot API error: {str(e)}")
                return Response({"error": str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)



class CaseStoryView(APIView):
    """API View to generate or retrieve case story"""
    def post(self, request, *args, **kwargs):
        serializer = CaseStoryRequestSerializer(data = request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        main_document = validated_data["main_document"]


        if main_document == "Outcome Journals":
            journal = validated_data['journal']
            partner = validated_data['partner']
            social_actor_name = validated_data['social_actor_name']


            #check the database
            case_story_obj = CaseStory.objects.filter(
                main_document = main_document,
                journal = journal,
                partner = partner,
                social_actor_name = social_actor_name
            )
            if case_story_obj:
                return Response({
                    "main_document": main_document,
                    "journal": journal,
                    "partner": partner,
                    "social_actor_name": social_actor_name,
                    "case_story": case_story_obj.case_story,
                    "from_cache": True
                },
                    status=status.HTTP_200_OK)

            #else generate
            json_data = load_dict_from_json(OUTCOME_JOURNALS_PATH)
            journal_data = json_data[OUTCOME_JOURNALS_DICT[journal]]
            partner_data = journal_data[partner]

            if social_actor_name != "All":
                text, index = None, None

                for i in range(0, len(partner_data)):
                    if partner_data[i]["(Social actor - individual, groups, institutions, networks, community, organisation)"] == social_actor_name:
                        index = i
                        break

                text = partner_data[index]

            else:
                text = partner_data
                social_actor_name = "All"

            try:
                case_story = generate_case_story(text = text, social_actor_name = social_actor_name)

                case_story_obj = CaseStory.objects.create(
                    main_document = main_document,
                    journal = journal,
                    partner = partner,
                    social_actor_name = social_actor_name,
                    case_story = case_story
                )

                return Response({
                                "main_document": main_document,
                                "journal": journal,
                                "partner": partner,
                                "social_actor_name": social_actor_name,
                                "case_story": case_story_obj.case_story,
                                "from_cache": False
                },
                status = status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Chatbot API error: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif main_document == "Progress Report Partners":
            pdf_name = validated_data["pdf_name"]

            #check the database
            case_story_obj = CaseStory.objects.filter(
                main_document=main_document,
                pdf_name=pdf_name
            ).first()

            if case_story_obj:
                return Response({
                    "main_document": main_document,
                    "pdf_name": pdf_name,
                    "case_story": case_story_obj.case_story,
                    "from_cache": True
                }, status = status.HTTP_200_OK)

            #else generate
            json_data = load_dict_from_json(PROGRESS_REPORT_PARTNERS_PATH)

            pdf = PROGRESS_REPORT_PARTNERS_DICT[pdf_name]
            text = json_data[pdf]

            try:
                case_story = generate_case_story(text=text)
                case_story_obj = CaseStory.objects.create(
                    main_document = main_document,
                    pdf_name = pdf_name,
                    case_story = case_story
                )

                return Response({
                    "main_document": main_document,
                    "pdf_name": pdf_name,
                    "case_story": case_story_obj.case_story,
                    "from_cache": False
                }, status = status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Chatbot API error: {str(e)}")
                return Response({"error": str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


class CaseStoryChatView(APIView):
    """API view to chat with case story"""
    def post(self, request, *args, **kwargs):
        serializer = CaseStoryChatRequestSerializer(data = request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        session_id = validated_data.get("session_id", None)
        case_story_id = validated_data.get("case_story_id", None)
        query = validated_data["query"]

        if session_id:
            try:
                session = CaseStoryChatSession.objects.get(id = session_id)
            except CaseStoryChatSession.DoesNotExist:
                return Response({"error": "Invalid session id"}, status = status.HTTP_404_NOT_FOUND)
        else:
            if not case_story_id:
                return Response(
                    {"error": "case_story_id is required when starting a new session"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                case_story = CaseStory.objects.get(id = case_story_id)
            except CaseStory.DoesNotExist:
                return Response({"error": "Invalid case story id"}, status = status.HTTP_404_NOT_FOUND)

            session = CaseStoryChatSession.objects.create(
                id = uuid.uuid4(),
                case_story = case_story
            )
            session_id = str(session.id)

        chat_history = list(session.case_story_chatmessages.all()
                                .order_by("timestamp")
                                .values("role", "message"))

        case_story_text = session.case_story.case_story

        response = qa_chat_with_prompt(text = case_story_text,
                                        query = query,
                                        chat_history = chat_history)
        full_response = f"Answer: {response["answer"]}\nSource: {response['source']}"


        CaseStoryChatMessage.objects.create(session=session,
                                   role="user",
                                   message=query)

        CaseStoryChatMessage.objects.create(session=session,
                                   role="assistant",
                                   message=full_response)

        chat_history = CaseStoryChatMessageSerializer(session.case_story_chatmessages.all(), many=True).data

        return Response({
            "session_id": session_id,
            "query": query,
            "response": full_response,
            "chat_history": chat_history
        }, status=status.HTTP_200_OK)




