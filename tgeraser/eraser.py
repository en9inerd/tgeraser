"""
Eraser class
"""

import datetime
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
        self.__limit = kwargs["limit"]
        self.__peers = kwargs["peers"].split(",") if kwargs["peers"] else []
        self.__wipe_everything = kwargs["wipe_everything"]
        self.__entity_type = kwargs["entity_type"]
        self.__older_than = kwargs["older_than"]
        self.__entities: List[hints.Entity] = []

    async def init(self) -> None:
        """
        Initializes the client
        """
        await self._connect_to_server()
        await self._authorize_user()

    async def _connect_to_server(self) -> None:
        """
        Connects to the Telegram server
        """
        print("Connecting to Telegram servers...")
        try:
            await self.connect()
        except ConnectionError:
            print("Initial connection failed. Retrying...")
            await self.connect()

    async def _authorize_user(self) -> None:
        """
        Authorizes the user
        """
        if not await self.is_user_authorized():
            print("First run. Sending code request...")
            user_phone = await async_input("Enter your phone: ")
            await self.sign_in(user_phone)

            self_user = None
            while self_user is None:
                code = await async_input("Enter the code you just received: ")
                try:
                    self_user = await self.sign_in(code=code)
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
        await self._determine_entities()
        await self._delete_messages_from_entities()
        self.__entities.clear()

    async def _determine_entities(self) -> None:
        """
        Determines entities to delete messages from
        """
        if self.__peers:
            await self._get_entities_by_peers()
        elif self.__wipe_everything:
            self.__entities = await self._filter_entities()
        else:
            await self._get_user_selected_entity()

    async def _get_entities_by_peers(self) -> None:
        """
        Returns entities by peers
        """
        for peer in self.__peers:
            if peer.isdigit():
                peer = cast_to_int(peer, f"peer: {peer}")
            try:
                self.__entities.append(await self.get_entity(peer))
            except ValueError as err:
                raise TgEraserException(
                    f"Specified entity '{peer}' can't be found."
                ) from err

    async def _delete_messages_from_entities(self) -> None:
        """
        Deletes messages from entities
        """
        offset_date = None
        if self.__older_than is not None:
            offset_date = datetime.datetime.now() - datetime.timedelta(
                seconds=self.__older_than
            )

        for entity in self.__entities:
            if isinstance(entity, User):
                print_header(
                    f"Deleting messages from conversation with user {get_display_name(entity)}..."
                )

                await self.delete_dialog(entity.id, revoke=True)

                print(
                    f"\nDeleted all messages from conversation with user {get_display_name(entity)}.\n"
                )
                continue

            display_name = get_display_name(entity)
            print_header(f"Getting messages from '{display_name}'...")
            messages_to_delete = [
                msg.id
                for msg in await self.get_messages(
                    entity,
                    from_user=InputUserSelf(),
                    limit=None,
                    wait_time=None,
                    offset_date=offset_date,
                )
            ]
            print(f"\nFound {len(messages_to_delete)} messages to delete.")
            await self._delete_messages(entity, messages_to_delete, display_name)

    async def _delete_messages(
        self, entity: hints.Entity, messages_to_delete: List[int], display_name: str
    ) -> None:
        """
        Deletes messages
        """
        print_header(f"Deleting messages from '{display_name}'...")
        result = await self.delete_messages(entity, messages_to_delete, revoke=True)
        number_of_deleted_msgs = sum([result[i].pts_count for i in range(len(result))])
        print(
            f"\nDeleted {number_of_deleted_msgs} messages of {len(messages_to_delete)} in '{display_name}' entity."
        )

        if number_of_deleted_msgs < len(messages_to_delete):
            print(
                f"Remaining {len(messages_to_delete) - number_of_deleted_msgs} messages can't be deleted without admin rights because they are service messages."
            )

        print("\n")

    async def _filter_entities(self) -> List[hints.EntityLike]:
        """
        Returns requested filtered entities
        """
        entities = [d.entity for d in await self.get_dialogs(limit=self.__limit)]
        entity_filters = {
            "any": lambda e: True,
            "user": lambda e: isinstance(e, User) and not e.is_self,
            "chat": lambda e: isinstance(e, Chat)
            or (isinstance(e, Channel) and (e.megagroup or e.gigagroup)),
            "channel": lambda e: isinstance(e, Channel) and not e.megagroup,
        }
        if self.__entity_type not in entity_filters:
            raise TgEraserException(
                f"Error: wrong entity type: '{self.__entity_type}'. Use 'any', 'user', 'chat' or 'channel'."
            )
        return [
            entity for entity in entities if entity_filters[self.__entity_type](entity)
        ]

    async def _get_user_selected_entity(self) -> None:
        """
        Returns chosen peer
        """
        entities = await self._filter_entities()

        if not entities:
            raise TgEraserException("You aren't joined to any chat.")

        print_header("List of entities")
        for i, entity in enumerate(entities, start=1):
            sprint(f"{i}. {get_display_name(entity)}\t | {entity.id}")

        num = cast_to_int(await async_input("\nChoose peer: "), "peer")
        self.__entities = [entities[num - 1]]
        print("Chosen: " + get_display_name(self.__entities[0]))
