# bot.py (aiogram v3 compatible)

import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties  # ✅ NEW
from config import BOT_TOKEN, ADMIN_IDS, PAYMENT_NUMBERS
import db
import utils

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ✅ /start
@router.message(Command("start"))
async def register_user(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        db.create_user(message.from_user.id, message.from_user.full_name)
        await message.answer("✅ Registration complete! You got 200 bonus coins 🎉")
    else:
        await message.answer("You are already registered ✅")

# 👤 /profile
@router.message(Command("profile"))
async def profile(message: Message):
    user = db.get_user(message.from_user.id)
    if user:
        await message.answer(
            f"👤 Name: {user[2]}\n💰 Balance: {user[3]} coins\n💸 Earnings: {user[4]} coins"
        )
    else:
        await message.answer("Please use /start to register first.")

# 📝 /post_task
@router.message(Command("post_task"))
async def post_task(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Please register first with /start")
        return

    await message.answer("Send task in this format:\n\nTitle | Description | Proof Required | Total Workers")

@router.message(lambda msg: "|" in msg.text and msg.text.count("|") == 3)
async def task_input(msg: Message):
    parts = msg.text.split("|")
    title, desc, proof, slots = [p.strip() for p in parts]
    try:
        slots = int(slots)
        cost = slots * 20

        if utils.user_balance(msg.from_user.id) < cost:
            await msg.answer(f"❌ Not enough coins. You need {cost} coins.")
            return

        db.post_task(title, desc, proof, slots, msg.from_user.id)
        db.update_balance(msg.from_user.id, -cost)
        await msg.answer(f"✅ Task '{title}' posted! {cost} coins deducted.")
    except:
        await msg.answer("❌ Invalid format. Use: Title | Description | Proof | Total Workers")

# 📋 /tasks
@router.message(Command("tasks"))
async def view_tasks(message: Message):
    tasks = db.get_active_tasks()
    if not tasks:
        await message.answer("No tasks available right now.")
        return

    msg = "📋 Available Tasks:\n"
    for task in tasks:
        msg += f"\n🆔 {task[0]}\n📌 {task[1]}\n📄 {task[2]}\n🧾 Proof: {task[3]}\n👥 Slots: {task[4]}\n"

    await message.answer(msg)

# 📤 /submit
@router.message(Command("submit"))
async def submit(message: Message):
    await message.answer("Submit proof in this format:\n\nTaskID | Your proof link/text")

@router.message(lambda m: "|" in m.text and m.text.count("|") == 1)
async def handle_submission(m: Message):
    try:
        task_id, proof = [x.strip() for x in m.text.split("|")]
        db.submit_task(m.from_user.id, int(task_id), proof)
        await m.answer("✅ Submission received. Pending admin review.")
    except:
        await m.answer("❌ Error submitting. Use: TaskID | Proof")

# 💰 /recharge
@router.message(Command("recharge"))
async def recharge(message: Message):
    await message.answer(f"Send recharge like this:\n\nAmount | Method (bkash/nagad) | TrxID\n\nSend to {PAYMENT_NUMBERS['bkash']}")

@router.message(lambda m: "|" in m.text and m.text.count("|") == 2)
async def handle_recharge(m: Message):
    try:
        amt, method, trx = [x.strip() for x in m.text.split("|")]
        db.add_recharge(m.from_user.id, int(amt), method.lower(), trx)
        await m.answer("✅ Recharge request submitted. Admin will verify soon.")
    except:
        await m.answer("❌ Format error. Use: Amount | Method | TrxID")

@router.message(Command("recharge_requests"))
async def recharge_requests(message: Message):
    if not utils.is_admin(message.from_user.id):
        await message.answer("Unauthorized.")
        return

    requests = db.get_pending_recharges()  # Ei function apnar db.py te implement korte hobe
    if not requests:
        await message.answer("No pending recharge requests.")
        return

    text = "📝 Pending Recharge Requests:\n"
    for req in requests:
        req_id, user_name, amount, method, trx_id = req
        text += f"\nID: {req_id}\nUser: {user_name}\nAmount: {amount}\nMethod: {method}\nTrxID: {trx_id}\n"

    await message.answer(text)



# 🔐 /admin_panel
@router.message(Command("admin_panel"))
async def admin_panel(message: Message):
    if not utils.is_admin(message.from_user.id):
        await message.answer("Unauthorized.")
        return

    users = db.count_users()
    tasks = db.count_tasks()
    pending = db.count_pending_submissions()

    await message.answer(f"📊 Admin Panel\n👥 Users: {users}\n📝 Tasks: {tasks}\n⏳ Pending Submissions: {pending}")

# ✅ /pending
@router.message(Command("pending"))
async def pending_subs(message: Message):
    if not utils.is_admin(message.from_user.id):
        return

    subs = db.get_pending_submissions()
    if not subs:
        await message.answer("✅ No pending submissions.")
        return

    for sub in subs:
        sid, name, task, proof = sub
        btns = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{sid}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{sid}")
            ]
        ])
        await message.answer(
            f"📨 Submission ID: {sid}\n👤 User: {name}\n📝 Task: {task}\n🔗 Proof: {proof}",
            reply_markup=btns
        )

# ☑️ Callback handler
@router.callback_query()
async def approve_or_reject(callback: CallbackQuery):
    if not callback.data or ":" not in callback.data:
        return

    action, sid = callback.data.split(":")
    sid = int(sid)
    user_id = db.get_user_id_from_submission(sid)

    if action == "approve":
        db.set_submission_status(sid, "approved")
        db.add_earning(user_id, 20)
        db.update_balance(user_id, 20)
        await callback.message.edit_text("✅ Approved!")
    else:
        db.set_submission_status(sid, "rejected")
        await callback.message.edit_text("❌ Rejected.")

    await callback.answer()

# 🟢 Launch bot
async def main():
    db.init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
