from notifications.signals import notify
from django.contrib.auth import get_user_model
from .models import (
    ChatSession, ChatSessionMember, ChatSessionMessage, deserialize_user
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions


# Create your views here.

class ChatSessionView(APIView):
    """Manage Chat Sessions."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """Create A New Session."""
        user = request.user

        chat_session = ChatSession.objects.create(owner=user)

        return Response({
            'status': 'SUCCESS',
            'uri': chat_session.uri,
            'message': "New Chat Session Created"
        })

    def patch(self, request, *args, **kwargs):
        """Add A User to a Chat Session"""
        """Also does'nt Create Multiple instances of the same User Joining and Leaving the Session"""
        User = get_user_model()

        uri = kwargs['uri']
        username = request.data['username']
        user = User.objects.get(username=username)

        chat_session = ChatSession.objects.get(uri=uri)
        owner = chat_session.owner

        if owner != user:
            """Only Allow Non-Owners To Join The Room"""
            chat_session.members.get_or_create(
                user=user, chat_session=chat_session
            )

        owner = deserialize_user(owner)
        members = [
            deserialize_user(chat_session.user)
            for chat_session in chat_session.members.all()
        ]
        members.insert(0, owner)  # Makes the Owner the First Member

        return Response({
            'status': 'SUCCESS',
            'members': members,
            'message': '%s Joined The Chat' % user.username,
            'user': deserialize_user(user)
        })


class ChatSessionMessageView(APIView):
    """Create/Get Chat Session Messages."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Returns All Messages in a Chat Session."""
        uri = kwargs['uri']

        chat_session = ChatSession.objects.get(uri=uri)
        messages = [chat_session_message.to_json()
                    for chat_session_message in chat_session.messages.all()
                    ]

        return Response({
            'id': chat_session.id,
            'uri': chat_session.uri,
            'messages': messages
        })

    def post(self, request, *args, **kwargs):
        """Create a New Message in a Chat Session."""

        uri = kwargs['uri']
        message = request.data['message']

        user = request.user
        chat_session = ChatSession.objects.get(uri=uri)

        chat_session_message = ChatSessionMessage.objects.create(
            user=user, chat_session=chat_session, message=message
        )

        notif_args = {
            'source': user,
            'source_display_name': user.get_full_name(),
            'category': 'chat', 'action': 'Sent',
            'obj': chat_session_message.id,
            'short_description': 'You a new message', 'silent': True,
            'extra_data': {'uri': chat_session.uri}
        }
        notify.send(
            sender=self.__class__, **notif_args, channels=['websocket']
        )
        return Response({
            'status': 'SUCCESS',
            'uri': chat_session.uri,
            'message': message,
            'user': deserialize_user(user)
        })
