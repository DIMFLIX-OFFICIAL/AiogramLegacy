import aiosqlite
import jsonpickle as jsonpickle
from asyncio import AbstractEventLoop
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from typing import Dict, Optional, Any


class PoolManager:
    __slots__ = ("_db_auth_data", "_tables_is_created", "pool")

    def __init__(self, **kwargs) -> None:
        self._db_auth_data = kwargs
        self._tables_is_created = False

    async def __aenter__(self) -> aiosqlite.Connection:
        self.pool = await aiosqlite.connect(**self._db_auth_data)

        if not self._tables_is_created:
            await self.pool.execute("""CREATE TABLE IF NOT EXISTS \"AiogramLegacyStates\"(
                                    "key" TEXT NOT NULL PRIMARY KEY,
                                    "state" TEXT NOT NULL)""")
            await self.pool.execute("""CREATE TABLE IF NOT EXISTS \"AiogramLegacyData\"(
                                    "key" TEXT NOT NULL PRIMARY KEY,
                                    "data" TEXT)""")
            self._tables_is_created = True

        return self.pool

    async def __aexit__(self, *args):
        await self.pool.commit()
        await self.pool.close()


class SQLiteStorage(BaseStorage):
    __slots__ = ("database", "loop")

    def __init__(self, database_path: str, loop: AbstractEventLoop = None) -> None:
        self.__auth_data = {
            "database": database_path
        }

        if loop is not None:
            self.__auth_data.update({"loop": loop})

        self.__db = PoolManager(**self.__auth_data)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        async with self.__db as db:
            await db.execute("INSERT INTO \"AiogramLegacyStates\" VALUES(?, ?)", (key, state))
            await db.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with self.__db as db:
            async with db.execute("SELECT \"state\" FROM \"AiogramLegacyStates\" WHERE key=?", (key,)) as cur:
                response = await cur.fetchone()

            return response[0]

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        async with self.__db as db:
            await db.execute("INSERT INTO \"AiogramLegacyData\" VALUES(?, ?)", (key, jsonpickle.dumps(data)))
            await db.commit()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        async with self.__db as db:
            async with db.execute("SELECT \"data\" FROM \"AiogramLegacyData\" WHERE key=?", (key,)) as cur:
                response = await cur.fetchone()

            return jsonpickle.loads(response[0])

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self.__db as db:
            await db.execute("UPDATE \"AiogramLegacyData\" SET data=? WHERE key=?", (jsonpickle.dumps(data), key))
            await db.commit()

        response = await self.get_data(key)
        return response

    async def close(self) -> None:
        pass
