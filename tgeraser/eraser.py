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

from .utils import chunks, print_header

# _ = Any, Dict, Iterable, List, Set, Union


class Eraser(TelegramClient):  # type: ignore
    """
    Subclass of TelegramClient class
    """

    def __init__(
        self: TelegramClient,
        session_user_id: str,
        user_phone: str,
        api_id: str,
        api_hash: str,
        dialogs: bool = False,
    ) -> None:
        super().__init__(session_user_id, api_id, api_hash)

        self.__dialogs = dialogs
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
            self.send_code_request(user_phone)

            self_user = None
            while self_user is None:
                code = input("Enter the code you just received: ")
                try:
                    self_user = self.sign_in(user_phone, code)

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
        peer = self.__choose_peer()
        self.__messages_to_delete.update(msg.id for msg in self.__get_messages(peer))
        return self.__delete_messages_from_peer(peer)

    def __choose_peer(self) -> Union[User, Channel]:
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
            s += "{}. {}\t | {}\n".format(i, name, entity.id)

        print(s)
        num = input("Choose group: ")
        print(
            "Chosen: " + entities[int(num)].first_name
            if self.__dialogs
            else entities[int(num)].title
        )

        return entities[int(num)]

    def __delete_messages_from_peer(self, peer: Union[Channel, User]) -> bool:
        """
        Message eraser method
        """
        messages_to_delete = list(self.__messages_to_delete)
        print_header(
            "Delete {0} of my messages in chat {1}".format(
                len(messages_to_delete),
                peer.first_name if self.__dialogs else peer.title,
            )
        )
        for chunk_data in chunks(
            messages_to_delete, 100
        ):  # Because we can delete only 100 messages per request (Telegram API restrictions)
            if self.__dialogs:
                r = self(DeleteMessagesRequestFromUser(chunk_data, revoke=True))
            else:
                r = self(DeleteMessagesRequest(peer, chunk_data))
            if r.pts_count:
                print("Number of deleted messages: {0}".format(r.pts_count))
            sleep(1)
        return True

    def __get_messages(
        self,
        peer: Union[Channel, User],
        limit: int = 100,
        offset_id: int = 0,
        max_id: int = 0,
        min_id: int = 0,
    ) -> List[Any]:
        print_header("Getting messages...")
        add_offset = 0
        messages: List[Any] = []

        while True:
            sleep(1)
            result = self(
                SearchRequest(
                    peer=peer,
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
