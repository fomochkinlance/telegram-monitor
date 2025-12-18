import asyncio
import re
from telethon import TelegramClient, events
import gspread
from datetime import datetime

api_id = 30037513          
api_hash = '08fd0f2ba28b607c819abc85a9b6aad8'   
chat_id =-1001844956237   

SPREADSHEET_ID = "1NrjCoI6UWdN2Zfa5x3poT2_a8t7WqdTnyC0ca-iF5v0"
SHEET_REG = "Реєстрації"                       # для Lost registration
SHEET_SIGN = "Очікування підпису"              # для pre_approved_accepted

gc = gspread.service_account(filename='credentials.json')
sh = gc.open_by_key(SPREADSHEET_ID)

client = TelegramClient('session', api_id, api_hash)

# Оновлена функція — чистить дату і повертає MM/DD/YYYY без крапки/коми
client = TelegramClient('session', api_id, api_hash)

# Повертає дату у форматі MM/DD/YYYY (для запису і логування)
def get_full_date(raw_date=None):
    if raw_date:
        try:
            clean_date = re.search(r'(\d{4}-\d{2}-\d{2})', raw_date)
            if clean_date:
                yyyymmdd = clean_date.group(1)
                parsed = datetime.strptime(yyyymmdd, '%Y-%m-%d')
                return parsed.strftime('%m/%d/%Y')
        except:
            pass
    # Якщо не вдалося — поточна дата
    return datetime.now().strftime('%m/%d/%Y')

# Запис у таблицю
def append_to_sheet(sheet_name, full_date_str, phone):
    if not phone or not phone.isdigit():
        return

    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=sheet_name, rows=1000, cols=10)
        worksheet.append_row(["Дата зупинки", "Ігнорувати", "Телефон"])

    row = [full_date_str, "", phone]
    worksheet.append_row(row)
    print(f"Записано в '{sheet_name}': {phone} | Повна дата: {full_date_str}")

@client.on(events.NewMessage(chats=chat_id))
async def handler(event):
    text = event.message.message or ""
    if not text:
        return

    text_lower = text.lower()

    if "[ok]" in text[:20]:
        return

    if "metrics:" not in text_lower:
        return

    if "lost registration" in text_lower:
        target_sheet = SHEET_REG
    elif "pre_approved_accepted" in text_lower:
        target_sheet = SHEET_SIGN
    else:
        return

    lines = text.splitlines()
    in_metrics = False
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.lower().startswith("metrics:"):
            in_metrics = True
            continue
        if not in_metrics or not line_stripped:
            continue

        if "fake_" in line_stripped:
            continue

        # Формат з Дата:
        match_complex = re.search(r'○\s*\+(\d{10,15}).*Дата:([^,;]+)', line)
        if match_complex:
            phone = match_complex.group(1)
            raw_date = match_complex.group(2).strip()
            full_date = get_full_date(raw_date)
            append_to_sheet(target_sheet, full_date, phone)
            continue

        # Простий формат
        if re.match(r'^\+?\d{10,15}:\s*[\d.]+$', line_stripped):
            phone_raw = re.search(r'\+?(\d{10,15})', line_stripped)
            if phone_raw:
                phone = phone_raw.group(1)
                full_date = get_full_date()  # поточна
                append_to_sheet(target_sheet, full_date, phone)

async def main():
    await client.start()
    print("Скрипт запущено! Моніторинг: ")
    await client.run_until_disconnected()

asyncio.run(main())