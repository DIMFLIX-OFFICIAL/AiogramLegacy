import asyncpg
import jsonpickle as jsonpickle
from asyncio import AbstractEventLoop
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from typing import Dict, Optional, Any


class PoolManager:
    __slots__ = ("_db_auth_data", "_tables_is_created", "pool")

    def __init__(self, **kwargs) -> None:
        self._db_auth_data = kwargs
        self._tables_is_created = False

    async def __aenter__(self) -> asyncpg.Pool:
        self.pool = await asyncpg.create_pool(**self._db_auth_data, autocommit=True)

        if not self._tables_is_created:
            await self.pool.execute("""CREATE TABLE IF NOT EXISTS "aiogram_state"(
                                    "key" TEXT NOT NULL PRIMARY KEY,
                                    "state" TEXT NOT NULL)""")
            await self.pool.execute("""CREATE TABLE IF NOT EXISTS "aiogram_data"(
                                    "key" TEXT NOT NULL PRIMARY KEY,
                                    "data" TEXT)""")
            self._tables_is_created = True

        return self.pool

    async def __aexit__(self, *args):
        await self.pool.close()


class PGStorage(BaseStorage):
    __slots__ = ("host", "port", "username", "password", "database", "dsn", "loop")

    def __init__(
            self, username: str, password: str, database: str,
            host: str = "localhost", port: int = 5432, dsn: str = None,
            loop: AbstractEventLoop = None
    ) -> None:
        self.__auth_data = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database
        }

        if dsn is not None:
            self.__auth_data.clear()
            self.__auth_data.update({"dsn": dsn})

        if loop is not None:
            self.__auth_data.update({"loop": loop})

        self.__db = PoolManager(**self.__auth_data)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        async with self.__db as db:
            await db.execute("INSERT INTO \"AiogramLegacyStates\" VALUES($1, $2)", key, state)

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with self.__db as db:
            response = await db.fetchval("SELECT \"state\" FROM \"AiogramLegacyStates\" WHERE key=$1", key)
            return response

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        async with self.__db as db:
            await db.execute("INSERT INTO \"AiogramLegacyData\" VALUES($1, $2)", key, jsonpickle.dumps(data))

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        async with self.__db as db:
            response = await db.fetchval("SELECT \"data\" FROM \"AiogramLegacyData\" WHERE key=$1", key)
            return jsonpickle.loads(response)

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self.__db as db:
            response = await db.fetchval(
                "UPDATE \"AiogramLegacyData\" SET data=$1 WHERE key=$2 RETURNING data",
                jsonpickle.dumps(data), key
            )

        return response

    async def close(self) -> None:
        pass
