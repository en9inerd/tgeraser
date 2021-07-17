"""
Eraser class
"""
import asyncio
import platform
import sys
from getpass import getpass
from time import sleep
from typing import Any, List, Set, Union

from telethon import TelegramClient, hints
from telethon.errors import SessionPasswordNeededError
from telethon.network import ConnectionTcpAbridged
from telethon.tl.functions.channels import DeleteMessagesRequest
from telethon.tl.functions.messages import (
    DeleteMessagesRequest as DeleteMessagesRequestFromUser,
)
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import Channel, InputMessagesFilterEmpty, InputUserSelf, User
from telethon.utils import get_display_name

from .__version__ import VERSION
from .exceptions import TgEraserException
from .utils import cast_to_int, chunks, print_header, sprint

_ = Any, List, Set, Union

loop = asyncio.get_event_loop()


async def async_input(prompt: str) -> str:
    """
    Python's ``input()`` is blocking, which means the event loop we set
    above can't be running while we're blocking there. This method will
    let the loop run while we wait for input.
    """
    print(prompt, end="", flush=True)
    return (await loop.run_in_executor(None, sys.stdin.readline)).rstrip()


class Eraser(TelegramClient):  # type: ignore
    """
    Subclass of TelegramClient class
    """

    def __init__(self: TelegramClient, **kwargs: Any) -> None:
        super().__init__(
            session=kwargs["session_name"],
            api_id=kwargs["api_id"],
            api_hash=kwargs["api_hash"],
            connection=ConnectionTcpAbridged,
            device_model=platform.uname().system,
            system_version=platform.uname().release,
            app_version=VERSION,
        )

        self.__limit = kwargs["limit"]  # Limit to retrieve the top dialogs
        self.__peers = kwargs["peers"].split(",") if kwargs["peers"] else []
        self.__dialogs = kwargs["dialogs"]
        self.__channels = kwargs["channels"]
        self.__entities: List[hints.Entity] = []
        self.__display_name = ""
        self.__messages_to_delete: Set[int] = set()

        # Check connection to the server
        print("Connecting to Telegram servers...")
        try:
            loop.run_until_complete(self.connect())
        except ConnectionError:
            print("Initial connection failed. Retrying...")
            loop.run_until_complete(self.connect())

        # Check authorization
        if not loop.run_until_complete(self.is_user_authorized()):
            print("First run. Sending code request...")
            if kwargs.get("user_phone", None):
                user_phone = kwargs["user_phone"]
            else:
                user_phone = input("Enter your phone: ")
            loop.run_until_complete(self.sign_in(user_phone))

            self_user = None
            while self_user is None:
                code = input("Enter the code you just received: ")
                try:
                    self_user = loop.run_until_complete(self.sign_in(code=code))

                # Two-step verification may be enabled
                except SessionPasswordNeededError:
                    password = getpass(
                        "Two step verification is enabled. "
                        "Please enter your password: "
                    )

                    self_user = loop.run_until_complete(self.sign_in(password=password))

    async def run(self) -> None:
        """
        Runs deletion of messages from peer
        """
        if self.__peers:
            for peer in self.__peers:
                if peer.isdigit():
                    peer = cast_to_int(peer, f"peer: {peer}")
                try:
                    self.__entities.append(await self.get_entity(peer))
                except ValueError:
                    raise TgEraserException(
                        f"Specified entity '{peer}' can't be found."
                    )
        else:
            await self.__get_entity()
        for entity in self.__entities:
            self.__display_name = get_display_name(entity)
            self.__messages_to_delete.update(
                msg.id for msg in await self.__get_messages(entity)
            )
            await self.__delete_messages_from_peer(entity)
            self.__messages_to_delete.clear()
        self.__entities.clear()

    async def __get_entity(self) -> None:
        """
        Returns chosen peer
        """
        entities = [d.entity for d in await self.get_dialogs(limit=self.__limit)]

        entities = [
            entity
            for entity in entities
            if isinstance(entity, User if self.__dialogs else Channel)
        ]
        if not self.__dialogs and not self.__channels:
            entities = [entity for entity in entities if entity.megagroup]

        if not entities:
            raise TgEraserException("You aren't joined to any chat.")

        print_header("Dialogs")
        for i, entity in enumerate(entities, start=1):
            sprint(f"{i}. {get_display_name(entity)}\t | {entity.id}")

        num = cast_to_int(await async_input("\nChoose peer: "), "peer")
        self.__entities = [entities[int(num) - 1]]
        self.__display_name = get_display_name(self.__entities[0])
        print(self.__display_name)
        print("Chosen: " + self.__display_name)

    async def __delete_messages_from_peer(self, entity: hints.Entity) -> None:
        """
        Method deletes messages
        """
        messages_to_delete = list(self.__messages_to_delete)
        print_header(
            f"Delete {len(messages_to_delete)} of my messages in chat {self.__display_name}"
        )
        for chunk_data in chunks(
            messages_to_delete, 100
        ):  # Because we can delete only 100 messages per request (Telegram API restrictions)
            if self.__dialogs:
                result = await self(
                    DeleteMessagesRequestFromUser(chunk_data, revoke=True)
                )
            else:
                result = await self(DeleteMessagesRequest(entity, chunk_data))
            if result.pts_count:
                print(f"Number of deleted messages: {result.pts_count}")
            sleep(1)
        print_header("Erasing is finished.")

    async def __get_messages(
        self,
        entity: hints.Entity,
        limit: int = 100,
        offset_id: int = 0,
        max_id: int = 0,
        min_id: int = 0,
    ) -> List[Any]:
        print_header(f"Getting messages from {self.__display_name}...")
        add_offset = 0
        messages: List[Any] = []

        while True:
            result = await self(
                SearchRequest(
                    peer=entity,
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
                    f"Received: {len(result.messages)} messages. Offset: {add_offset}."
                )
                messages.extend(result.messages)
                add_offset += len(result.messages)
                sleep(1)
            else:
                print("It's finished because it met end of chat.")
                return messages
