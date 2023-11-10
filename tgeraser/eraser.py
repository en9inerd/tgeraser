"""
Eraser class
"""

import platform
from getpass import getpass
from typing import Any, List

from telethon import TelegramClient, hints
from telethon.errors import SessionPasswordNeededError
from telethon.network import ConnectionTcpAbridged
from telethon.tl.types import Channel, Chat, InputUserSelf, User
from telethon.utils import get_display_name

from .__version__ import VERSION
from .exceptions import TgEraserException
from .utils import async_input, cast_to_int, print_header, sprint


class Eraser(TelegramClient):  # type: ignore
    """
    Subclass of TelegramClient class
    """

    def __init__(self: TelegramClient, **credentials: Any) -> None:
        super().__init__(
            session=credentials["session_name"],
            api_id=credentials["api_id"],
            api_hash=credentials["api_hash"],
            connection=ConnectionTcpAbridged,
            device_model=platform.uname().system,
            system_version=platform.uname().release,
            app_version=VERSION,
        )

    async def init(self, **kwargs: Any) -> None:
        """
        Initializes the client
        """
        self.__limit = kwargs["limit"]  # Limit to retrieve the top dialogs
        self.__peers = kwargs["peers"].split(",") if kwargs["peers"] else []
        self.__wipe_everything = kwargs["wipe_everything"]
        self.__entity_type = kwargs["entity_type"]
        self.__entities: List[hints.Entity] = []
        self.__display_name = ""

        # Check connection to the server
        print("Connecting to Telegram servers...")
        try:
            await self.connect()
        except ConnectionError:
            print("Initial connection failed. Retrying...")
            await self.connect()

        # Check authorization
        if not await self.is_user_authorized():
            print("First run. Sending code request...")

            user_phone = await async_input("Enter your phone: ")
            await self.sign_in(user_phone)

            self_user = None
            while self_user is None:
                code = await async_input("Enter the code you just received: ")
                try:
                    self_user = await self.sign_in(code=code)

                # Two-step verification may be enabled
                except SessionPasswordNeededError:
                    password = getpass(
                        "Two step verification is enabled. "
                        "Please enter your password: "
                    )

                    self_user = await self.sign_in(password=password)

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
                except ValueError as err:
                    raise TgEraserException(
                        f"Specified entity '{peer}' can't be found."
                    ) from err
        elif self.__wipe_everything:
            self.__entities = await self.__filter_entities()
        else:
            await self.__get_entity()

        for entity in self.__entities:
            self.__display_name = get_display_name(entity)
            print_header(f"Getting messages from '{self.__display_name}'...")
            messages_to_delete = [
                msg.id
                for msg in await self.get_messages(
                    entity, from_user=InputUserSelf(), limit=None, wait_time=None
                )
            ]
            print(f"\nFound {len(messages_to_delete)} messages to delete.")

            print_header(f"Deleting messages from '{self.__display_name}'...")
            result = await self.delete_messages(entity, messages_to_delete, revoke=True)
            number_of_deleted_msgs = sum(
                [result[i].pts_count for i in range(len(result))]
            )
            print(
                f"\nDeleted {number_of_deleted_msgs} messages of {len(messages_to_delete)} in '{self.__display_name}' entity."
            )

            if number_of_deleted_msgs < len(messages_to_delete):
                print(
                    f"Remaining {len(messages_to_delete) - number_of_deleted_msgs} messages can't be deleted without admin rights because they are service messages."
                )

            print("\n")

        self.__entities.clear()

    async def __filter_entities(self) -> List[hints.EntityLike]:
        """
        Returns requested entities
        """
        entities = [d.entity for d in await self.get_dialogs(limit=self.__limit)]

        if self.__entity_type == "any":
            return entities
        elif self.__entity_type == "user":
            return [
                entity
                for entity in entities
                if isinstance(entity, User) and not entity.is_self
            ]
        elif self.__entity_type == "chat":
            return [
                entity
                for entity in entities
                if (
                    isinstance(entity, Chat)
                    or (isinstance(entity, Channel) and entity.megagroup)
                    or (isinstance(entity, Channel) and entity.gigagroup)
                )
            ]
        elif self.__entity_type == "channel":
            return [
                entity
                for entity in entities
                if isinstance(entity, Channel) and not entity.megagroup
            ]
        else:
            raise TgEraserException(
                f"Error: wrong entity type: '{self.__entity_type}'. Use 'any', 'user', 'chat' or 'channel'."
            )

    async def __get_entity(self) -> None:
        """
        Returns chosen peer
        """
        entities = await self.__filter_entities()

        if not entities:
            raise TgEraserException("You aren't joined to any chat.")

        print_header("List of entities")
        for i, entity in enumerate(entities, start=1):
            sprint(f"{i}. {get_display_name(entity)}\t | {entity.id}")

        num = cast_to_int(await async_input("\nChoose peer: "), "peer")
        self.__entities = [entities[num - 1]]
        self.__display_name = get_display_name(self.__entities[0])
        print("Chosen: " + self.__display_name)
