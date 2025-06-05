from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.MWAPI import get_person_info

router = Router()


class UserInput(StatesGroup):
    name = State()
    current_person = State()  # Для хранения данных о текущей личности


async def download_photo(file_id: str, file_path: str, bot: Bot):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, file_path)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Добро пожаловать в бот-энциклопедию!',
                         reply_markup=kb.main)


@router.message(Command('help'))
@router.message(F.text.lower() == 'помощь')
async def cmd_help(message: Message):
    await message.answer('Список команд:\n'
                         '/help - список команд\n'
                         '/find - поиск личности\n'
                         '/cancel - отмена')


@router.message(UserInput.name, F.text.lower() == 'отмена')
@router.message(UserInput.name, Command('cancel'))
async def cancel_search(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('❌ Поиск отменен', reply_markup=kb.main)


@router.message(Command('find'))
@router.message(F.text.lower() == 'поиск')
async def request_name(message: Message, state: FSMContext):
    await state.set_state(UserInput.name)
    await message.answer('📑 Введите имя для поиска:', reply_markup=kb.cancel)


async def send_person_info(message: Message, info: dict):
    """Функция для отправки основной информации о личности"""

    birth_date = info.get('birth_date')
    death_date = info.get('death_date')
    occupations = ', '.join(info.get('occupations', []))
    countries = ', '.join(info.get('countries', []))
    description = info.get('description', '')
    summary = info.get('summary', '')
    image_url = info.get('image_url')

    info_message = f'<b>🪪 {info.get("full_name", "Неизвестно")}</b>\n\n'

    if birth_date or death_date:
        info_message += f'📅 <b>Годы жизни:</b> {birth_date} - {death_date}\n'
    if occupations:
        info_message += f'💼 <b>Род деятельности:</b> {occupations}\n'
    if countries:
        info_message += f'🌍 <b>Страны:</b> {countries}\n'
    if description:
        info_message += f'\n📃 {description}\n'
    """if summary:
        info_message += f'\nℹ️ {summary[:500]}...'"""

    if image_url:
        await message.answer_photo(photo=image_url, caption=info_message,
                                   reply_markup=kb.more_info, parse_mode="HTML")
    else:
        await message.answer(info_message, reply_markup=kb.more_info, parse_mode="HTML")


@router.message(UserInput.name)
async def search_by_name(message: Message, state: FSMContext):
    name = message.text
    await message.answer(f'🔍 Ищу информацию о "{name}"...')

    info = get_person_info(name)

    if "error" in info:
        await message.answer(info["error"], reply_markup=kb.main)
        await state.clear()
        return

    await state.update_data(current_person=info)
    await send_person_info(message, info)
    await state.set_state(UserInput.current_person)


@router.callback_query(F.data == 'demographic data')
async def demographic_data(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    person = data.get('current_person', {})

    message_text = "<b>📊 Демографические данные:</b>\n\n"

    if person.get('gender'):
        message_text += f"👤 <b>Пол:</b> {', '.join(person['gender'])}\n"
    if person.get('birth_date'):
        message_text += f"🎂 <b>Дата рождения:</b> {person['birth_date']}\n"
    if person.get('birth_place'):
        message_text += f"🏠 <b>Место рождения:</b> {', '.join(person['birth_place'])}\n"
    if person.get('death_date'):
        message_text += f"⚰️ <b>Дата смерти:</b> {person['death_date']}\n"
    if person.get('death_place'):
        message_text += f"🕯️ <b>Место смерти:</b> {', '.join(person['death_place'])}\n"
    if person.get('ethnic_group'):
        message_text += f"🌐 <b>Этническая принадлежность:</b> {', '.join(person['ethnic_group'])}\n"
    if person.get('religion'):
        message_text += f"🙏 <b>Религия:</b> {', '.join(person['religion'])}\n"
    if person.get('children'):
        message_text += f"👨‍👩‍👧‍👦 <b>Дети:</b> {', '.join(person['children'])}\n"

    await callback.message.answer(message_text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == 'geographical information')
async def geographical_info(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    person = data.get('current_person', {})

    message_text = "<b>🌍 Географическая информация:</b>\n\n"

    if person.get('countries'):
        message_text += f"🏳️ <b>Гражданство:</b> {', '.join(person['countries'])}\n"
    if person.get('birth_place'):
        message_text += f"📍 <b>Место рождения:</b> {', '.join(person['birth_place'])}\n"
    if person.get('death_place'):
        message_text += f"⚰️ <b>Место смерти:</b> {', '.join(person['death_place'])}\n"
    if person.get('languages'):
        message_text += f"🗣️ <b>Языки:</b> {', '.join(person['languages'])}\n"

    await callback.message.answer(message_text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == 'professional activity')
async def professional_activity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    person = data.get('current_person', {})

    message_text = "<b>💼 Профессиональная деятельность:</b>\n\n"

    if person.get('occupations'):
        message_text += f"👔 <b>Род деятельности:</b> {', '.join(person['occupations'])}\n"
    if person.get('educations'):
        message_text += f"🎓 <b>Образование:</b> {', '.join(person['educations'])}\n"
    if person.get('positions'):
        message_text += f"🏛️ <b>Должности:</b> {', '.join(person['positions'])}\n"
    if person.get('awards'):
        message_text += f"🏆 <b>Награды:</b> {', '.join(person['awards'])}\n"
    if person.get('notable_works'):
        message_text += f"📚 <b>Известные работы:</b> {', '.join(person['notable_works'])}\n"

    await callback.message.answer(message_text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == 'political-organizational affiliation')
async def political_org_affiliation(callback: CallbackQuery,
                                    state: FSMContext):
    data = await state.get_data()
    person = data.get('current_person', {})

    message_text = "<b>🏛️ Политическая/организационная принадлежность:</b>\n\n"

    if person.get('parties'):
        message_text += f"🎗️ <b>Политические партии:</b> {', '.join(person['parties'])}\n"
    if person.get('official_websites'):
        websites = person['official_websites']
        if isinstance(websites, list):
            message_text += f"🌐 <b>Официальные сайты:</b> {', '.join(websites)}\n"
        else:
            message_text += f"🌐 <b>Официальный сайт:</b> {websites}\n"

    await callback.message.answer(message_text, parse_mode="HTML")
    await callback.answer()