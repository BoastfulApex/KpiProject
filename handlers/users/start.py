from aiogram.types import ReplyKeyboardRemove, Message, CallbackQuery
from loader import dp, bot
from keyboards.inline.menu_button import *
from keyboards.inline.main_inline import *
from utils.db_api.database import *
from data import config
from aiogram.filters import Command, StateFilter, CommandObject, CommandStart
from aiogram import F, Router


router = Router()


dp.include_router(router)


channel_id = config.CHANNEL_ID


@router.message(CommandStart(), StateFilter(None))
async def handler(message: Message, command: CommandStart):
    user = message.from_user
    telegram_user = await get_telegram_user(user.id)
    if not telegram_user:
        await add_telegram_user(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or ""
        )

    check = await is_user_employee(message.from_user.id)
    check_admin = await is_user_admin(message.from_user.id)
    if check_admin:
        await message.answer(
            "👋 Assalomu alaykum, Hurmatli Administrator!\n\n"
            "Siz botning administratorisiz. Sizga quyidagi imkoniyatlar mavjud:\n"
            "- Xodimlarni boshqarish\n"
            "- Kirish va chiqishlarni tekshirish\n"
            "- Bot sozlamalarini o'zgartirish\n"
        )
        keyboard = await admin_menu_keyboard()
        await message.answer("Iltimos, kerakli bo'limni tanlang:", reply_markup=keyboard)
    elif check:
        keyboard = await go_web_app()
        await message.answer("Tugmani bosing", reply_markup=keyboard)
    else:
        await message.answer(
            "⚠️ Siz xodim emassiz!\n\n"
            "Botdan foydalanish uchun xodim bo‘lishingiz kerak.\n"
        )

        # 2. Inline tugma bilan administratorga murojaat qilishni taklif qilamiz
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📨 Administratorga xabar yuborish", callback_data="notify_admin")]
        ])
        await message.answer("Administratorga xabar yubormoqchimisiz?", reply_markup=keyboard)
        

@router.callback_query(lambda c: c.data == "notify_admin")
async def notify_admin_callback(callback_query: CallbackQuery):
    user = callback_query.from_user
    admins = await get_all_admin_ids()

    for admin_id in admins:
        keyboard = get_user_approval_keyboard(user.id)

        await callback_query.bot.send_message(
            chat_id=admin_id,
            text=(
                f"🚨 Yangi foydalanuvchi botga kirishga harakat qildi:\n\n"
                f"👤 Ismi: {user.full_name}\n"
                f"🆔 Telegram ID: {user.id}\n"
                f"📩 U administratorga murojaat yuborishni tanladi."
            ),
            reply_markup=keyboard
        )

    await callback_query.message.answer("✅ Administratorga xabaringiz yuborildi.")
    await callback_query.answer()
    await callback_query.message.delete()