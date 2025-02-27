from dotenv import load_dotenv
import os
import json
import requests
from typing import Final
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, filters, ConversationHandler, MessageHandler, \
    CallbackQueryHandler


load_dotenv()
Token: Final = os.getenv("TOKEN")
Bot_username: Final = os.getenv("BOT_USERNAME")

base_url = 'https://node-js-test-six.vercel.app'
TITLE, DESCRIPTION = range(2)

headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}


def getAllTasks():
    url = base_url + '/getAll'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/tasks", "/createTask"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, True)
    await update.message.reply_text("Choose command: ", reply_markup=reply_markup)


async def mark_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    id = query.data.split("_")[1]
    status = False if query.data.split("_")[2].lower() == 'true' else True

    body = {
        "_id": id,
        "status": status,
    }
    json_body = json.dumps(body)
    response = requests.put(base_url + '/updateTask', json_body, headers=headers)
    if response.status_code == 200:
        await context.bot.send_message(
            update.callback_query.message.chat_id,
            "Task updated successfully! Fetching updated list...",
        )
        await get_all_tasks(update.callback_query, context)
    else:
        await context.bot.send_message(
            update.callback_query.message.chat_id,
            'Task update failed.'
        )


async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.message.message_id)
    for i in range(update.message.message_id, 0, -1):
       try:
           await context.bot.deleteMessage(update.message.chat_id, i)
       except:
           break
    return


async def get_all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Fetching tasks list...')
    tasks = getAllTasks()
    await clear_chat(update, context)
    if tasks:
        message = "Here are all the tasks:\n\n"
        keyboard = []

        for index, item in enumerate(tasks):
            mark_status = "Completed" if item["status"] != True else "Not Completed"
            status_icon = "Not completed ❎" if item["status"] != True else "Completed ✅"
            message += f"{index + 1}. <b>{item['title']}</b>\n<em>{item['description']}\nStatus: {status_icon}</em>\n\n"

            keyboard.append([InlineKeyboardButton(f"{index + 1}. Mark {mark_status}",
                                                  callback_data=f"mark_{item['_id']}_{item['status']}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, "HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text("No tasks found.")


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    body = {
        "title": context.user_data["title"],
        "description": context.user_data["description"],
    }
    body_json = json.dumps(body)
    response = requests.post(base_url + '/addTask', body_json, headers=headers)
    if response.status_code == 200:
        await update.message.reply_text("Task added successfully.")
        await get_all_tasks(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Something went wrong.")
        return ConversationHandler.END


async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Enter description of task:")
    return DESCRIPTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Task creation canceled.")
    return ConversationHandler.END


async def create_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter title of task:")
    return TITLE


def main():
    app = Application.builder().token(Token).build()
    app.add_handler(CallbackQueryHandler(mark_task, pattern=r"^mark_[a-f0-9]{24}_(True|False)$"))
    conv_handler = ConversationHandler(
        [CommandHandler("start", start_command), CommandHandler("tasks", get_all_tasks),
         CommandHandler("createTask", create_task)],
        {
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
        },
        [CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
