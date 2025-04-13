from aiogram import Bot, Dispatcher, types, F
from config_ready import config
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, CallbackQuery
import asyncio

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    builder = InlineKeyboardBuilder()

    builder.add(
        types.InlineKeyboardButton(
            text="постройки",
            callback_data="button1"
        )),
    
    builder.add(
        types.InlineKeyboardButton(
            text="соцсети",
            callback_data="button2"
    )),

    builder.add(
        types.InlineKeyboardButton(
            text="Ники игроков",
            callback_data="button3" 
        )
    )
    await message.answer("Тыкай",reply_markup=builder.as_markup())

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