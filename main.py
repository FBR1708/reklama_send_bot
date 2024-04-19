import asyncio
import json
import logging
import sys

from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, \
    InputMediaVideo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from buttons import keyboard
from db import Base, engine, Session, Advertisement
from forms import Form
from middleware import AlbumMiddleware

TOKEN = "6869504270:AAHoR2rdl49oP38E9Ql24kVqhN7RQDyFquo"

dp = Dispatcher()
bot = Bot(TOKEN)
Base.metadata.create_all(engine)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Salom admin xizmatni tanlang.", reply_markup=keyboard)


@dp.message(F.text == 'Reklama yaratish')
async def command_top(message: Message, state: FSMContext):
    await state.set_state(Form.title)
    await message.answer(text='Reklamangiz nomini kiriting', reply_markup=ReplyKeyboardRemove())


@dp.message(Form.title)
async def name(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Form.body)
    await message.answer(text='Reklamangiz asosiy qismini kiriting')


@dp.message(Form.body)
async def body(message: Message, state: FSMContext):
    await state.update_data(body=message.text)
    await state.set_state(Form.file)
    await message.answer(text='Reklamangiz rasmi yoki video kiriting')


@dp.message(Form.file, F.media_group_id)
async def handle_message(message: Message, state: FSMContext, albums):
    db = Session()
    data = await state.get_data()
    title = data.get('title', '')
    body_ = data.get('body', '')
    media_dict = {}
    media_list = []
    advertisement = f'{title}\n\n{body_}'
    for item in albums[message.media_group_id]:
        if item.photo:
            media_list.append(InputMediaPhoto(media=item.photo[-1].file_id))
            media_dict[item.photo[-1].file_id] = "photo"
        elif item.video:
            media_list.append(InputMediaVideo(media=item.video.file_id))
            media_dict[item.video.file_id] = "video"
    media_list[0].caption = advertisement
    media_json = json.dumps(media_dict)
    info = Advertisement(title=title, body=body_, file_id=media_json)
    db.add(info)
    db.commit()
    db.close()
    await state.clear()
    await message.answer_media_group(media_list)
    await message.answer('Xizmatni tanlang :', reply_markup=keyboard)


@dp.message(Form.file)
async def handle_message(message: Message, state: FSMContext):
    db = Session()
    data = await state.get_data()
    title = data.get('title', '')
    body_ = data.get('body', '')
    media_dict = {}
    advertisement = f'{title}\n\n{body_}'
    if message.photo:
        media_dict[message.photo[-1].file_id] = "photo"
    elif message.video:
        media_dict[message.video.file_id] = "video"
    media_json = json.dumps(media_dict)
    info = Advertisement(title=title, body=body_, file_id=media_json)
    db.add(info)
    db.commit()
    db.close()
    await state.clear()
    if message.photo:
        await message.answer_photo(photo=message.photo[-1].file_id, caption=advertisement, reply_markup=keyboard)
    elif message.video:
        await message.answer_video(video=message.video.file_id, caption=advertisement, reply_markup=keyboard)
    else:
        await message.answer("Xatolik Rasm yoki Video kiriting")


@dp.message(F.text == 'Reklama o\'chirish')
async def inline_button_food(message: Message):
    db = Session()
    try:
        main_menu = db.query(Advertisement.id, Advertisement.title).all()
        if main_menu:
            in_but = InlineKeyboardBuilder()
            for menu in main_menu:
                in_but.add(InlineKeyboardButton(text=f'{menu.title}', callback_data=f'delete_{menu.id}'))
            in_but.add(InlineKeyboardButton(text='🔙Ortga', callback_data='ortga'))
            in_but.adjust(2)
            await message.answer(text='Barcha reklamalar', reply_markup=in_but.as_markup(resize_keyboard=True))

        else:
            await message.answer("Reklama mavjud emas")

    finally:
        db.close()


@dp.callback_query(F.data == 'ortga')
async def handle_message_handler(callback_query: CallbackQuery):
    await bot.delete_message(chat_id=callback_query.message.chat.id,
                             message_id=callback_query.message.message_id)


@dp.callback_query(F.data.startswith('delete_'))
async def handle_message_handler(callback_query: CallbackQuery):
    action, data_id = callback_query.data.split('_')
    db = Session()
    try:
        data_id = int(data_id)
        delete_advertisement = db.query(Advertisement).filter(Advertisement.id == data_id).first()
        if delete_advertisement:
            db.delete(delete_advertisement)
            db.commit()
            await callback_query.message.answer(text='Reklama o\'chirildi', reply_markup=keyboard)
            await bot.delete_message(chat_id=callback_query.message.chat.id,
                                     message_id=callback_query.message.message_id)
        else:
            await callback_query.message.answer(text="Bunday reklama emas")
    except ValueError:
        await callback_query.message.answer(text=f'Invalid data_id: {data_id}')
    finally:
        db.close()


@dp.message(F.text == 'Reklamani guruhlarga jo\'natish')
async def send_advertisement(message: Message):
    db = Session()
    all_advertisements = db.query(Advertisement).all()
    group_chat_id = [-1002101580581]
    for adv in all_advertisements:
        file = adv.file_id
        title = adv.title
        body_ = adv.body
        advertisement = f'{title}\n\n{body_}'
        file = json.loads(file)
        media_group = []
        for file_id, type_ in file.items():
            if type_ == 'photo':
                media_group.append(InputMediaPhoto(media=file_id))
            elif type_ == 'video':
                media_group.append(InputMediaVideo(media=file_id))
        media_group[0].caption = advertisement
        for chat_id in group_chat_id:
            await bot.send_media_group(chat_id=chat_id, media=media_group)

    await message.answer('Reklama jo\'natildi', reply_markup=keyboard)


@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


# @aiocron.crontab('* * * * *')
# async def scheduled_tak():
#     db = Session()
#     all_advertisements = db.query(Advertisement).all()
#     group_chat_id = [-1002101580581]
#     for adv in all_advertisements:
#         file = adv.file_id
#         title = adv.title
#         body_ = adv.body
#         advertisement = f'{title}\n\n{body_}'
#         file = json.loads(file)
#         media_group = []
#         for file_id, type_ in file.items():
#             if type_ == 'photo':
#                 media_group.append(InputMediaPhoto(media=file_id, caption=advertisement))
#             elif type_ == 'video':
#                 media_group.append(InputMediaVideo(media=file_id))
#
#         for chat_id in group_chat_id:
#             await bot.send_media_group(chat_id=chat_id, media=media_group)

async def main() -> None:
    bot_ = Bot(TOKEN)
    dp.message.middleware(AlbumMiddleware())
    await dp.start_polling(bot_)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
