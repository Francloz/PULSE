import uuid
from typing import Tuple
from typing import List, Optional

import redis
from pydantic import BaseModel


class SessionState(BaseModel):
    """
    This class represents the session state of the session.
    Attributes:
        user_id (str): user id this session belongs to.
        session_id (str): session id of this session.
    """
    user_id: str
    session_id: str


class Message(BaseModel):
    """
    This class represents the message of the session.
    Attributes:
        author (str): author of the message (either user or llm).
        content (str): content of the message.
    """
    author: str
    content: str


class ChatState(BaseModel):
    """"
    This class represents the chat state of the session.
    Attributes:
        user_id (str): user id this session belongs to.
        session_id (str): session id of the user's session.
        chat_id (str): chat id in this session.
        messages (List[Message]): list of messages this session belongs to.
        outstanding_task (Optional[TaskState]): if there is a task incomplete for this session, its task state.
    """
    user_id: str
    session_id: str
    chat_id: str
    messages: List[Message]
    outstanding_task: Optional['TaskState'] = None


class ChatHandler:
    """
    This class represents the chat handler.
    Attributes:
        redis (redis.StrictRedis): redis client instance.
        flow (Text2SQLFlow): flow that represents the task flow.
        chat_state (ChatState): chat state.
    """

    def __init__(self, redis_client: redis.StrictRedis, user_id: str, session_id: str):
        """
        ChatHandler constructor.
        :param redis_client: redis client instance.
        :param session_id: session id
        """
        self.redis = redis_client
        self.flow = None
        self.chat_state: Optional[ChatState] = None
        self.session_id = session_id
        self.chat_id = None
        self.user_id = user_id

    def create_or_recover_chat(self, chat_id: str) -> ChatState:
        """
        Creates or recovers a chat using the user_id, session_id and chat_id.
        :param chat_id: id of the chat
        :return:
        """
        chat_key = f"{self.user_id}:{self.session_id}:{chat_id}"
        chat_data = self.redis.get(chat_key)
        self.chat_id = chat_id

        if chat_data:
            self.chat_state = ChatState.model_validate_json(chat_data)
        else:
            self.chat_state = ChatState(
                user_id=self.user_id,
                session_id=self.session_id,
                chat_id=chat_id,
                messages=[]
            )
            self.save_chat(chat_id, self.chat_state)

        from multiagent.workflow import Text2SQLFlow
        username = self.redis.get(f"{self.user_id}:user_name")
        initial_inquiry = self.chat_state.outstanding_task.initial_inquiry
        if self.chat_state.outstanding_task:
            new_state = self.chat_state.outstanding_task
            kwargs = new_state.model_dump()
        else:
            kwargs = {}
        self.flow = Text2SQLFlow(username=username, initial_inquiry=initial_inquiry, **kwargs)

        return self.chat_state

    def continue_chat(self, input_text: str) -> str:
        """
        Continues the chat where it left off. If there was no outstanding task, it starts anew.
        :param input_text: initial text input
        :return: response text to the user
        """
        self.chat_state.messages.append(Message(author="user", content=input_text))

        response = self.flow.kickoff()
        self.chat_state.messages.append(Message(author="system", content=response))
        self.chat_state.outstanding_task = self.flow.state
        return response

    def save_chat(self, chat_id: str, state: ChatState):
        """
        Saves the chat state to continue it later.
        :param chat_id: id of the chat.
        :param state: chat state.
        :return: None
        """
        chat_key = f"{self.user_id}:{self.session_id}:{chat_id}"
        self.redis.set(chat_key, state.model_dump_json())

class SessionHandler:
    """
    This class represents the session handler.
    Attributes:
        redis (redis.StrictRedis): redis client instance.
        chat_handler (ChatHandler): chat handler.
        session_state (SessionState): session state.
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.chat_handler = None
        self.session_state: SessionState = None

    def create_or_recover_session(self, user_id: str) -> Tuple[str, SessionState]:
        session_key = f"{user_id}:session_id"
        session_data = self.redis.get(session_key)

        if session_data:
            self.session_state = SessionState.model_validate_json(session_data)
        else:
            session_id = str(uuid.uuid4())
            self.session_state = SessionState(userId=user_id, sessionId=session_id)
            self.redis.set(session_key, self.session_state.model_dump_json())

        self.chat_handler = ChatHandler(self.redis, self.session_state.user_id, self.session_state.session_id)
        return self.session_state.sessionId, self.session_state




