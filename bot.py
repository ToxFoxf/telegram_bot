from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from cryptography.fernet import Fernet
import sqlite3
import asyncio
from config_ready import config

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

key = Fernet.generate_key()
cipher = Fernet(key)

conn = sqlite3.connect('clanguard.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS members 
                  (user_id INTEGER PRIMARY KEY, username TEXT, trust_level INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS coords
                  (id INTEGER PRIMARY KEY, name TEXT, coords TEXT, access_level INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS blacklist
                  (nickname TEXT PRIMARY KEY, reason TEXT)''')
conn.commit()

@dp.message(Command("start"))
async def start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="постройки", callback_data="button1"),
        types.InlineKeyboardButton(text="соцсети", callback_data="button2"),
        types.InlineKeyboardButton(text="Ники игроков", callback_data="button3"),
        types.InlineKeyboardButton(text="ClanGuard", callback_data="clanguard_menu")
    )
    await message.answer("Тыкай", reply_markup=builder.as_markup())

@dp.message(Command("ban"))
async def ban_player(message: Message, command: CommandObject):
    try:
        nickname, reason = command.args.split(maxsplit=1)
        cursor.execute("INSERT INTO blacklist VALUES (?, ?)", (nickname, reason))
        conn.commit()
        await message.answer(f"{nickname} добавлен в ЧС")
    except:
        await message.answer("Формат: /ban ник причина")

@dp.message(Command("unban"))
async def unban_player(message: Message, command: CommandObject):
    nickname = command.args
    cursor.execute("DELETE FROM blacklist WHERE nickname=?", (nickname,))
    conn.commit()
    await message.answer(f"{nickname} удалён из ЧС")

@dp.message(Command("blacklist"))
async def show_blacklist(message: Message):
    cursor.execute("SELECT * FROM blacklist")
    rows = cursor.fetchall()
    if not rows:
        await message.answer("ЧС пуст")
        return
    result = "Чёрный список:\n" + "\n".join(f"{row[0]} — {row[1]}" for row in rows)
    await message.answer(result)

@dp.message(Command("add_member"))
async def add_member(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Формат: /add_member @username уровень доступа")
        return

    try:
        username, level = command.args.split()
        level = int(level)
        
        if level not in {1, 2, 3}:
            await message.answer("Уровень доступа должен быть: 1 (новичок), 2 (проверенный), 3 (лидер)")
            return
        
        cursor.execute(
            "INSERT OR REPLACE INTO members (username, trust_level) VALUES (?, ?)",
            (username, level))
        conn.commit()
        
        await message.answer(f"{username} добавлен с уровнем доступа {level}")
    except ValueError:
        await message.answer("Ошибка. Формат: /add_member @username уровень (1-3)")

@dp.message(Command("set_level"))
async def set_level(message: Message, command: CommandObject):
    try:
        username, new_level = command.args.split()
        new_level = int(new_level)
        
        if new_level not in {1, 2, 3}:
            await message.answer("Допустимые уровни: 1, 2, 3")
            return

        cursor.execute(
            "UPDATE members SET trust_level = ? WHERE username = ?",
            (new_level, username))
        conn.commit()
        
        if cursor.rowcount == 0:
            await message.answer(f"{username} не найден в БД")
        else:
            await message.answer(f"{username} теперь имеет уровень {new_level}")
    except:
        await message.answer("Формат: /set_level @username новый уровень")

async def check_access(username: str, required_level: int) -> bool:
    cursor.execute(
        "SELECT trust_level FROM members WHERE username = ?",
        (username,))
    result = cursor.fetchone()
    return result and result[0] >= required_level

@dp.message(Command("get_coords"))
async def get_coords(message: Message):
    username = message.from_user.username
    
    if not await check_access(username, 2):  # Требуется уровень 2+
        await message.answer("Доступ запрещён!")
        return
    
    cursor.execute("SELECT name, coords FROM coords")
    bases = cursor.fetchall()
    response = "Доступные базы:\n" + "\n".join(f"{name}: {cipher.decrypt(coords.encode()).decode()}" for name, coords in bases)
    await message.answer(response)

@dp.message(Command("members"))
async def list_members(message: Message):
    cursor.execute("SELECT username, trust_level FROM members ORDER BY trust_level DESC")
    members = cursor.fetchall()
    
    if not members:
        await message.answer("В базе нет участников")
        return
    
    response = "📜 Список участников:\n" + "\n".join(
        f"{username} — {['Новичок', 'Проверенный', 'Лидер'][level-1]}" 
        for username, level in members
    )
    await message.answer(response)
    
@dp.message(Command("add_coords"))
async def add_coords(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Нужны параметры! Пример: /add_coords Название 100 64 200 2")
        return

@dp.callback_query(F.data == "clanguard_menu")
async def clanguard_menu(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Добавить координаты", callback_data="add_coords_menu"),
        types.InlineKeyboardButton(text="Черный список", callback_data="blacklist_menu")
    )
    await callback.message.edit_text(
        "ClanGuard - Защита клана:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "add_coords_menu")
async def add_coords_menu(callback: CallbackQuery):
    await callback.message.answer(
        "Добавьте координаты в формате:\n"
        "/add_coords НазваниеБазы X Y Z УровеньДоступа\n"
        "Пример: /add_coords MainBase 100 200 300 2"
    )
    await callback.answer()

    
    try:
        name, x, y, z, access_level = command.args.split()
        encrypted = cipher.encrypt(f"{x} {y} {z}".encode())
        cursor.execute(
            "INSERT INTO coords (name, coords, access_level) VALUES (?, ?, ?)",
            (name, encrypted.decode(), int(access_level)),
        conn.commit())
        await message.answer(f" Координаты '{name}' сохранены (требуемый уровень: {access_level})")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("base"))
async def base(message: Message):
    await message.answer_photo(types.FSInputFile("logo.jpg"))

@dp.message(Command("idea"))
async def idea_command(message: Message, command: CommandObject):
    args = command.args
    with open("ideas_for_base.txt", "a+", encoding="utf-8") as file:
        file.write(f'{message.chat.username} | {args}\n')
    await message.answer('Сохранено')

@dp.callback_query(F.data == "button1")
async def button1(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.add(
        types.InlineKeyboardButton(
            text="надо построить",
            callback_data="need_build"
        ),
        types.InlineKeyboardButton(
            text="уже построили",
            callback_data="already_built"
        ),
        types.InlineKeyboardButton(
            text="идея для построек",
            callback_data="idea"
        )
    )
    await callback.message.edit_text(
        "Выберите категорию:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "button2")
async def button2(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.add(
        types.InlineKeyboardButton(
            text="YouTube",
            url="https://www.youtube.com/channel/UCpG0QiByXNvuiFJJYRnMQFQ"
        )
    )
    await callback.message.edit_text(
        "соцсети:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "button3")
async def nickaname(callback: CallbackQuery):
        with open("nickname.txt", "r") as msg:
            otv = msg.read()
        await callback.message.answer(otv)
        await callback.answer()

@dp.callback_query(F.data == "need_build")
async def need_build(callback: CallbackQuery):
    await callback.message.answer("Список объектов для строительства...")
    await callback.answer()

@dp.callback_query(F.data == "already_built")
async def already_built(callback: CallbackQuery):
    await callback.message.answer("Список построенных объектов...")
    await callback.answer()

@dp.callback_query(F.data == "idea")
async def idea_callback(callback: CallbackQuery):
    await callback.message.answer("Напиши в чат идею для построек")     
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())