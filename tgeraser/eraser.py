# coding=utf-8
"""
Eraser class
"""
from time import sleep
from typing import Any, List, Set, Union

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import DeleteMessagesRequest
from telethon.tl.functions.messages import (
    DeleteMessagesRequest as DeleteMessagesRequestFromUser,
)
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import Channel, InputMessagesFilterEmpty, InputUserSelf, User

from .utils import chunks, print_header, check_num
from .exceptions import TgEraserException

_ = Any, List, Set, Union


class Eraser(TelegramClient):  # type: ignore
    """
    Subclass of TelegramClient class
    """

    def __init__(self: TelegramClient, **kwargs: Union[str, bool, None]) -> None:
        super().__init__(kwargs["session_name"], kwargs["api_id"], kwargs["api_hash"])

        self.__limit = kwargs["limit"]
        self.__peer = kwargs["peer"]
        self.__dialogs = kwargs["dialogs"]
        self.__entity = None
        self.__messages_to_delete: Set[int] = set()

        # Check connection to the server
        print("Connecting to Telegram servers...")
        self.connect()
        if not self.is_connected():
            print("Could not connect to Telegram servers.")
            return

        # Check authorization
        if not self.is_user_authorized():
            print("First run. Sending code request...")
            self.send_code_request(kwargs["user_phone"])

            self_user = None
            while self_user is None:
                code = input("Enter the code you just received: ")
                try:
                    self_user = self.sign_in(kwargs["user_phone"], code)

                # Two-step verification may be enabled
                except SessionPasswordNeededError:
                    pw = input(
                        "Two step verification is enabled. Please enter your password: "
                    )
                    self_user = self.sign_in(password=pw)

        limit = input("Enter number of chats to show them (empty for all): ")
        # To show specified number of chats
        if limit:
            self.__limit = int(limit)
        else:
            self.__limit = None

    def run(self) -> bool:
        """
        Runs deletion of messages from peer
        """
        if self.__peer:
            try:
                self.__entity = self.get_entity(self.__peer)
            except ValueError:
                raise TgEraserException("Specified entity can't be found.")
        else:
            self.__get_entity()
        self.__messages_to_delete.update(msg.id for msg in self.__get_messages())
        return self.__delete_messages_from_peer()

    def __get_entity(self) -> None:
        """
        Returns chosen peer
        """
        entities = [d.entity for d in self.get_dialogs(limit=self.__limit)]
        s = ""

        entities = [
            entity
            for entity in entities
            if isinstance(entity, User if self.__dialogs else Channel)
        ]
        if not self.__dialogs:
            entities = [entity for entity in entities if entity.megagroup]

        for i, entity in enumerate(entities):
            name = entity.first_name if self.__dialogs else entity.title
            s += "{0}. {1}\t | {2}\n".format(i, name, entity.id)

        print(s)
        num = input("Choose peer: ")
        check_num("peer", num)
        self.__entity = entities[int(num)]
        print(
            "Chosen: " + self.__entity.first_name
            if self.__dialogs
            else self.__entity.title
        )

    def __delete_messages_from_peer(self) -> bool:
        """
        Message eraser method
        """
        messages_to_delete = list(self.__messages_to_delete)
        print_header(
            "Delete {0} of my messages in chat {1}".format(
                len(messages_to_delete),
                self.__entity.first_name if self.__dialogs else self.__entity.title,
            )
        )
        for chunk_data in chunks(
            messages_to_delete, 100
        ):  # Because we can delete only 100 messages per request (Telegram API restrictions)
            if self.__dialogs:
                r = self(DeleteMessagesRequestFromUser(chunk_data, revoke=True))
            else:
                r = self(DeleteMessagesRequest(self.__entity, chunk_data))
            if r.pts_count:
                print("Number of deleted messages: {0}".format(r.pts_count))
            sleep(1)
        return True

    def __get_messages(
        self, limit: int = 100, offset_id: int = 0, max_id: int = 0, min_id: int = 0
    ) -> List[Any]:
        print_header("Getting messages...")
        add_offset = 0
        messages: List[Any] = []

        while True:
            sleep(1)
            result = self(
                SearchRequest(
                    peer=self.__entity,
                    q="",
                    filter=InputMessagesFilterEmpty(),
                    min_date=None,
                    max_date=None,
                    offset_id=offset_id,
                    add_offset=add_offset,
                    limit=limit,
                    max_id=max_id,
                    min_id=min_id,
                    from_id=InputUserSelf(),
                    hash=0,
                )
            )

            if result.messages:
                print(
                    "Received: {0} messages. Offset: {1}.".format(
                        len(result.messages), add_offset
                    )
                )
                messages.extend(result.messages)
                add_offset += len(result.messages)
            else:
                print_header("It's finished because it met end of chat.")
                return messages
