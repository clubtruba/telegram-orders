import asyncio
import re
from uuid import UUID

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.services.drafts import DraftError, DraftService, OpenDraftCommand
from app.services.users import UserService

router = Router()
dispatcher = Dispatcher()
dispatcher.include_router(router)
URL_RE = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)
SIZES = ("XS", "S", "M", "L", "XL")


def size_keyboard(draft_id: UUID) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=size, callback_data=f"draft:size:{draft_id}:{size}")
               for size in SIZES]
    buttons.append(InlineKeyboardButton(text="Без размера", callback_data=f"draft:size:{draft_id}:-"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:3], buttons[3:]])


def confirm_keyboard(draft_id: UUID) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Добавить заказ", callback_data=f"draft:confirm:{draft_id}")]])


async def identity(event: Message | CallbackQuery):
    user = event.from_user
    if user is None:
        raise RuntimeError("Telegram user is unavailable")
    async with SessionFactory() as session, session.begin():
        app_user, customer = await UserService(session).register_customer(
            user.id, user.first_name, user.last_name, user.username)
        return app_user.id, customer.id


@router.message(CommandStart())
async def start(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    await identity(message)
    await message.answer("Добро пожаловать. Чтобы сделать заказ, отправьте мне ссылку на товар.")


@router.message(F.text)
async def receive_url(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    match = URL_RE.search(message.text or "")
    if match is None:
        await message.answer("Пришлите ссылку на товар, начинающуюся с https://")
        return
    app_user_id, _ = await identity(message)
    async with SessionFactory() as session, session.begin():
        draft = await DraftService(session).open(OpenDraftCommand(
            app_user_id, message.chat.id, message.message_id, match.group(0)))
        draft_id = draft.id
    await message.answer("Какой размер вам нужен?", reply_markup=size_keyboard(draft_id))


@router.callback_query(F.data.startswith("draft:size:"))
async def choose_size(callback: CallbackQuery):
    if callback.message is None or callback.message.chat.type != ChatType.PRIVATE:
        await callback.answer()
        return
    _, _, raw_id, raw_size = (callback.data or "").split(":", 3)
    app_user_id, _ = await identity(callback)
    async with SessionFactory() as session, session.begin():
        await DraftService(session).set_size(
            UUID(raw_id), app_user_id, None if raw_size == "-" else raw_size)
    await callback.message.edit_text(
        f"Размер: {raw_size if raw_size != '-' else 'без размера'}. Добавить заказ?",
        reply_markup=confirm_keyboard(UUID(raw_id)))
    await callback.answer()


@router.callback_query(F.data.startswith("draft:confirm:"))
async def confirm(callback: CallbackQuery):
    if callback.message is None or callback.message.chat.type != ChatType.PRIVATE:
        await callback.answer()
        return
    raw_id = (callback.data or "").rsplit(":", 1)[-1]
    app_user_id, customer_id = await identity(callback)
    try:
        async with SessionFactory() as session, session.begin():
            item = await DraftService(session).confirm(UUID(raw_id), app_user_id, customer_id)
            item_id = item.id
    except DraftError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.message.edit_text(f"✅ Заказ {item_id} добавлен. Статус: ожидает покупки.")
    await callback.answer()


async def main():
    token = get_settings().telegram_bot_token
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required to run the bot profile")
    await dispatcher.start_polling(Bot(token=token))


if __name__ == "__main__":
    asyncio.run(main())
