from rest_framework import serializers
from .models import ChatMessage, CaseStoryChatMessage
from oakdrf.config import MAIN_DOCUMENT_CHOICES, OUTCOME_JOURNALS_DICT

class ChatRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    query = serializers.CharField()
    session_id = serializers.CharField(required = False, allow_blank = True)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["role", "message", "timestamp"]


class CaseStoryRequestSerializer(serializers.Serializer):
    main_document = serializers.ChoiceField(choices = MAIN_DOCUMENT_CHOICES)
    journal = serializers.CharField(required = False, allow_null = True, allow_blank = True)
    partner = serializers.CharField(required = False, allow_null = True, allow_blank = True)
    social_actor_name = serializers.CharField(required = False, allow_null = True, allow_blank = True)
    pdf_name = serializers.CharField(required = False, allow_null = True, allow_blank = True)

    def validate(self, data):
        main_document = data["main_document"]

        if main_document == "Outcome Journals":
            journal = data.get("journal")
            if not journal:
                raise serializers.ValidationError({"journal": f"This field is required when main_document is {main_document} "})

            if journal not in OUTCOME_JOURNALS_DICT.keys():
                raise serializers.ValidationError({"journal": f"Invalid journal. Must be one of {list(OUTCOME_JOURNALS_DICT.keys())}"})

            if not data.get("partner"):
                raise serializers.ValidationError({"partner": f"This field is required when main_document is {main_document} "})

            if not data.get("social_actor_name"):
                raise serializers.ValidationError({"social actor name": f"This field is required when main_document is {main_document} "})

        elif main_document == "Progress Report Partners":
            if not data.get("pdf_name"):
                raise serializers.ValidationError({"pdf_name": f"This field is required when main_document is {main_document} "})

        return data


class CaseStoryChatRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required = False)
    case_story_id = serializers.IntegerField(required = False)
    query = serializers.CharField(required = True, allow_blank = False)

class CaseStoryChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStoryChatMessage
        fields = ["role", "message", "timestamp"]
