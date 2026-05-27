import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8889645517:AAF75wOFCoD7HFrU54sAg-l8nI5YftZJatw"
ADMIN_ID = 6057290342

bot = Bot(token=TOKEN)
dp = Dispatcher()

CHANNELS_FILE = "channels.json"

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

async def check_subscriptions(user_id: int) -> list:
    channels = load_channels()
    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(ch)
        except:
            not_subscribed.append(ch)
    return not_subscribed

# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    channels = load_channels()
    if not channels:
        await message.answer("👋 Добро пожаловать! Доступ открыт.")
        return

    not_subscribed = await check_subscriptions(message.from_user.id)

    if not not_subscribed:
        await message.answer("✅ Добро пожаловать! Доступ открыт.")
        return

    buttons = []
    for ch in not_subscribed:
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['name']}", url=ch["url"])])
    buttons.append([InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "🔒 Доступ ограничен\n\nЧтобы пользоваться ботом, подпишись на наши каналы снизу\n\nПосле подписки нажми кнопку «✅ Проверить подписку».",
        reply_markup=kb
    )

# Проверка подписки
@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    not_subscribed = await check_subscriptions(callback.from_user.id)

    if not not_subscribed:
        await callback.message.edit_text("✅ Добро пожаловать! Доступ открыт.")
    else:
        buttons = []
        for ch in not_subscribed:
            buttons.append([InlineKeyboardButton(text=f"📢 {ch['name']}", url=ch["url"])])
        buttons.append([InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.answer("❌ Ты ещё не подписался на все каналы!", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=kb)

# Админ панель
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа.")
        return

    channels = load_channels()
    text = "👑 Админ панель\n\n"
    if channels:
        text += "📋 Каналы для обязательной подписки:\n"
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch['name']} ({ch['id']})\n"
    else:
        text += "Каналов пока нет.\n"

    text += "\nКоманды:\n"
    text += "/add_channel @username Название — добавить канал\n"
    text += "/remove_channel @username — удалить канал\n"
    text += "/list_channels — список каналов"

    await message.answer(text)

# Добавить канал: /add_channel @username Название
@dp.message(Command("add_channel"))
async def add_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа.")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /add_channel @username Название\nПример: /add_channel @mychannel Мой канал")
        return

    username = args[1]
    name = args[2]

    if not username.startswith("@"):
        await message.answer("Username должен начинаться с @")
        return

    try:
        chat = await bot.get_chat(username)
        channels = load_channels()

        for ch in channels:
            if ch["id"] == chat.id:
                await message.answer(f"Канал {name} уже добавлен!")
                return

        invite_link = f"https://t.me/{username[1:]}"
        channels.append({"id": chat.id, "name": name, "url": invite_link})
        save_channels(channels)
        await message.answer(f"✅ Канал «{name}» успешно добавлен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: не могу найти канал {username}\nУбедись что бот добавлен в канал как администратор!")

# Удалить канал
@dp.message(Command("remove_channel"))
async def remove_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /remove_channel @username")
        return

    username = args[1]

    try:
        chat = await bot.get_chat(username)
        channels = load_channels()
        new_channels = [ch for ch in channels if ch["id"] != chat.id]

        if len(new_channels) == len(channels):
            await message.answer(f"Канал {username} не найден в списке.")
        else:
            save_channels(new_channels)
            await message.answer(f"✅ Канал {username} удалён!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# Список каналов
@dp.message(Command("list_channels"))
async def list_channels(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа.")
        return

    channels = load_channels()
    if not channels:
        await message.answer("Каналов пока нет. Добавь через /add_channel")
        return

    text = "📋 Каналы для обязательной подписки:\n\n"
    for i, ch in enumerate(channels, 1):
        text += f"{i}. {ch['name']}\n   ID: {ch['id']}\n   Ссылка: {ch['url']}\n\n"

    await message.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
