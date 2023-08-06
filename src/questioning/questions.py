import asyncio
import inspect
from dataclasses import dataclass
from typing import List, Union, Callable, Any

from aiogram import Dispatcher, Bot, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply


@dataclass()
class Question:
    question_text: str
    question_type: ContentType
    validation_func: Callable[[str], bool] = None


@dataclass
class ResponseData:
    questions: List[Question]
    answers: dict


class SurveyState(StatesGroup):
    waiting_for_answer = State()


class Survey:
    def __init__(
            self,
            dispatcher: Dispatcher,
            bot: Bot,
            questions: List[Question],

            reply_markup_for_back_button: Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply,
                None
            ],

            finish_func: Callable[[types.Message, ResponseData], Any]
    ) -> None:
        self._dp = dispatcher
        self._bot = bot
        self._questions = questions
        self._reply_markup_for_back_button = reply_markup_for_back_button
        self._finish_func = finish_func
        self._dp.message.register(self.process_answer, SurveyState.waiting_for_answer)

    async def start(self, message: types.Message, state: FSMContext):
        await state.set_state(SurveyState.waiting_for_answer)
        await state.set_data({'current_question': 0, 'answers': {}})
        await self.send_question(message, state)

    async def send_question(self, message: types.Message, state: FSMContext, text: str = None):
        data = await state.get_data()

        if text is None:
            text = self._questions[data['current_question']].question_text

        try:
            if "last_msg" not in data:
                new_msg = await self._bot.send_message(message.chat.id, text, self._reply_markup_for_back_button)
            else:
                new_msg = await self._bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=data["last_msg"].message_id,
                    text=text,
                    reply_markup=self._reply_markup_for_back_button
                )

            await state.update_data({'last_msg': new_msg})
        except:
            pass
        await self._bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    async def process_answer(self, message: types.Message, state: FSMContext):
        data = await state.get_data()
        question = self._questions[data['current_question']]

        if (message.content_type != question.question_type) or \
                (question.validation_func and not question.validation_func(message.text)):
            await self.send_question(
                message, state,
                'Wrong data format. Please, try again.\n\n' + question.question_text
            )
            return

        data['answers'][data['current_question']] = message.text
        data['current_question'] += 1

        if data['current_question'] < len(self._questions):
            await self.send_question(message, state)
            await state.set_data(data)
        else:
            await state.clear()
            if inspect.iscoroutinefunction(self._finish_func):
                await self._finish_func(
                    message,
                    ResponseData(
                        questions=self._questions,
                        answers=data
                    )
                )
            elif callable(self._finish_func):
                self._finish_func(
                    message,
                    ResponseData(
                        questions=self._questions,
                        answers=data
                    )
                )
