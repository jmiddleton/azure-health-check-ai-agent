# data_layer.py
import chainlit.data as cl_data
from typing import Dict, List, Optional
from chainlit.types import (
    Feedback,
    PaginatedResponse,
    Pagination,
    ThreadDict,
    ThreadFilter,
)
from chainlit.user import PersistedUser, User
from chainlit.element import Element, ElementDict
from chainlit.step import StepDict
import uuid
from datetime import datetime

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

class CustomDataLayer(cl_data.BaseDataLayer):
    def __init__(self):
        super().__init__()
        self.messages: List[Dict[str, str]] = []
        self.users: Dict[str, PersistedUser] = {}
        self.elements: Dict[str, ElementDict] = {}
        self.steps: Dict[str, StepDict] = {}
        self.threads: Dict[str, ThreadDict] = {}
        self.feedback: Dict[str, Feedback] = {}

    # ---------------- User Methods ----------------
    async def get_user(self, identifier: str) -> Optional[PersistedUser]:
        if identifier in self.users:
            return self.users[identifier]
        # Return dummy persisted user if not found
        return PersistedUser(
            id=identifier,
            identifier=identifier,
            createdAt=datetime.now().strftime(ISO_FORMAT),
            metadata={},
        )

    async def create_user(self, user: "User") -> Optional[PersistedUser]:
        persisted = PersistedUser(
            id=user.identifier,
            identifier=user.identifier,
            createdAt=datetime.now().strftime(ISO_FORMAT),
            metadata=getattr(user, "metadata", {}),
        )
        self.users[user.identifier] = persisted
        return persisted

    # ---------------- Message Methods ----------------
    async def save_message(self, user_id: str, message: str, role: str) -> None:
        self.messages.append({"user_id": user_id, "message": message, "role": role})

    async def get_messages(self, user_id: str) -> List[Dict[str, str]]:
        return [m for m in self.messages if m["user_id"] == user_id]

    # ---------------- Feedback Methods ----------------
    async def delete_feedback(self, feedback_id: str) -> bool:
        return self.feedback.pop(feedback_id, None) is not None

    async def upsert_feedback(self, feedback: Feedback) -> str:
        feedback_id = getattr(feedback, "id", str(uuid.uuid4()))
        self.feedback[feedback_id] = feedback
        return feedback_id

    # ---------------- Element Methods ----------------
    async def create_element(self, element: "Element"):
        eid = getattr(element, "id", str(uuid.uuid4()))
        self.elements[eid] = element.dict()
        return eid

    async def get_element(self, thread_id: str, element_id: str) -> Optional["ElementDict"]:
        return self.elements.get(element_id)

    async def delete_element(self, element_id: str, thread_id: Optional[str] = None):
        return self.elements.pop(element_id, None)

    # ---------------- Step Methods ----------------
    async def create_step(self, step_dict: "StepDict"):
        sid = step_dict.get("id", str(uuid.uuid4()))
        step_dict["createdAt"] = datetime.now().strftime(ISO_FORMAT)
        self.steps[sid] = step_dict
        return sid

    async def update_step(self, step_dict: "StepDict"):
        sid = step_dict.get("id")
        if sid in self.steps:
            self.steps[sid] = step_dict

    async def delete_step(self, step_id: str):
        return self.steps.pop(step_id, None)

    # ---------------- Thread Methods ----------------
    async def get_thread_author(self, thread_id: str) -> str:
        thread = self.threads.get(thread_id)
        return thread["user_id"] if thread else ""

    async def delete_thread(self, thread_id: str):
        return self.threads.pop(thread_id, None)

    async def list_threads(self, pagination: "Pagination", filters: "ThreadFilter") -> "PaginatedResponse[ThreadDict]":
        # Return all threads in memory as a paginated response
        threads_list = list(self.threads.values())
        return PaginatedResponse(
            data=threads_list,
            pageInfo={
                "page": 1,
                "size": len(threads_list),
                "total": len(threads_list),
                "hasNextPage": False,
                "startCursor": "",
                "endCursor": ""
            }
        )

    async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
        return self.threads.get(thread_id)

    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        thread = self.threads.get(thread_id)
        if not thread:
            thread = {"id": thread_id}
            self.threads[thread_id] = thread

        if name:
            thread["name"] = name
        if user_id:
            thread["user_id"] = user_id
        if metadata:
            thread["metadata"] = metadata
        if tags:
            thread["tags"] = tags

    # ---------------- Misc Methods ----------------
    async def build_debug_url(self) -> str:
        return "http://debug-url"

    async def close(self) -> None:
        pass
