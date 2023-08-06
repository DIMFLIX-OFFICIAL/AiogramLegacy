import aiomysql
import jsonpickle as jsonpickle
from asyncio import AbstractEventLoop
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from typing import Dict, Optional, Any


class PoolManager:
    __slots__ = ("_db_auth_data", "_tables_is_created", "pool", "cursor")

    def __init__(self, **kwargs) -> None:
        self._db_auth_data = kwargs
        self._tables_is_created = False

    async def __aenter__(self) -> aiomysql.Cursor:
        self.pool: aiomysql.Connection = await aiomysql.connect(**self._db_auth_data, autocommit=True)
        self.cursor: aiomysql.Cursor = self.pool.cursor()

        if not self._tables_is_created:
            await self.cursor.execute("""CREATE TABLE IF NOT EXISTS "aiogram_state"(
                                    "key" TEXT NOT NULL PRIMARY KEY,
                                    "state" TEXT NOT NULL)""")
            await self.cursor.execute("""CREATE TABLE IF NOT EXISTS "aiogram_data"(
                                    "key" TEXT NOT NULL PRIMARY KEY,
                                    "data" TEXT)""")
            self._tables_is_created = True

        return self.cursor

    async def __aexit__(self, *args):
        await self.cursor.close()
        await self.pool.close()


class MySQLStorage(BaseStorage):
    __slots__ = ("host", "port", "username", "password", "db", "loop")

    def __init__(
            self, username: str, password: str, database: str,
            host: str = "localhost", port: int = 5432,
            loop: AbstractEventLoop = None
    ) -> None:
        self.__auth_data = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database
        }

        if loop is not None:
            self.__auth_data.update({"loop": loop})

        self.__db = PoolManager(**self.__auth_data)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        async with self.__db as db:
            await db.execute("INSERT INTO \"AiogramLegacyStates\" VALUES(%s, %s)", (key, state))

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with self.__db as db:
            await db.execute("SELECT \"state\" FROM \"AiogramLegacyStates\" WHERE key=%s", (key,))
            response = await db.fetchone()
            return response[0]

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        async with self.__db as db:
            await db.execute("INSERT INTO \"AiogramLegacyData\" VALUES(%s, %s)", (key, jsonpickle.dumps(data)))

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        async with self.__db as db:
            await db.execute("SELECT \"data\" FROM \"AiogramLegacyData\" WHERE key=%s", (key,))
            response = await db.fetchone()
            return jsonpickle.loads(response[0])

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self.__db as db:
            await db.execute("UPDATE \"AiogramLegacyData\" SET data=%s WHERE key=%s", (jsonpickle.dumps(data), key))
            response = await self.get_data(key)

        return response

    async def close(self) -> None:
        pass
