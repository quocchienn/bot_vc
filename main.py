# main.py – PHIÊN BẢN HOÀN HẢO NHẤT 2025 – CHẠY MƯỢT TRÊN RENDER
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest, TimedOut
import re
import json
import asyncio
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Thiếu BOT_TOKEN!")

DB_FILE = "/tmp/vouchers.json"

# 50+ kênh public HOT 2025
PUBLIC_CHANNELS = [
    "hoisanvoucher", "nghiensandeal", "groupsanxuvamagiamgia", "sansaleshopee_lazada",
    "nss247", "xomsansale", "bloggiamgia", "magiamgiatiktok", "nghienshopeelazada",
    "dealhotvn", "tiktokvoucherhot", "shopeedeal24h", "voucher100k", "freeshiptiktok",
    "hotvouchervn", "sansaledeal", "shopeevoucher24h", "voucherfreeshipshopee",
    "tiktokshopvoucher24h", "dealhot24h", "voucher100k_up", "huntersvoucher",
    "freeship24h", "affiliateshopeevn", "shopeevoucherhn", "tiktokshop0d",
    "vouchertiktokshopfree", "tiktokhoanxu", "hotdealshopee2025"
]

def load_vouchers():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_vouchers(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

vouchers = load_vouchers()
CODE_PATTERN = re.compile(r'\b[A-Z0-9]{10,20}\b|\b\d{15,20}\b|shp\.ee/[a-zA-Z0-9]+|vt\.tiktok\.com/[A-Za-z0-9]+', re.I)

# Tự động join kênh
async def auto_join_channels(bot):
    print("Đang tự động join 50+ kênh public...")
    for ch in PUBLIC_CHANNELS:
        try:
            await bot.join_chat(f"@{ch}")
            print(f"Joined @{ch}")
            await asyncio.sleep(2)
        except Exception as e:
            if "already" not in str(e).lower():
                print(f"Skip @{ch}: {e}")
        await asyncio.sleep(1)
    print("JOIN XONG!")

# Scanner siêu ổn định
async def scanner_loop(app):
    while True:
        try:
            updates = await app.bot.get_updates(
                offset=getattr(app.bot, "last_update_id", 0) + 1,
                timeout=15,
                allowed_updates=["message", "channel_post"]
            )
            for update in updates:
                msg = update.message or update.channel_post
                if not msg or not msg.text:
                    continue
                text = msg.text.lower()
                if not any(kw in text for kw in ["50k","100k","freeship","hoàn xu","extra","toàn sàn","0đ"]):
                    continue

                codes = CODE_PATTERN.findall(msg.text)
                source = getattr(msg.chat, "username", "") or getattr(msg.chat, "title", "Unknown")
                new_v = {
                    "code": " | ".join(codes) if codes else "Xem tin",
                    "text": msg.text[:400],
                    "source": f"@{source}" if source != "Unknown" else source,
                    "time": datetime.now().strftime("%H:%M %d/%m")
                }
                if not any(v["text"] == new_v["text"] for v in vouchers[:50]):
                    vouchers.insert(0, new_v)
                    vouchers = vouchers[:500]
                    save_vouchers(vouchers)
                    logger.info(f"NEW VOUCHER từ @{source}")

            if updates:
                app.bot.last_update_id = updates[-1].update_id

        except TimedOut:
            pass
        except Exception as e:
            if "Conflict" in str(e):
                logger.warning("Conflict cũ – đã được clear cache, bỏ qua")
            else:
                logger.error(f"Lỗi scanner: {e}")
        await asyncio.sleep(60)

# Lệnh
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("HOT", callback_data="hot")],
        [InlineKeyboardButton("≥50k", callback_data="50k"), InlineKeyboardButton("≥100k", callback_data="100k")],
        [InlineKeyboardButton("Freeship", callback_data="freeship")],
        [InlineKeyboardButton("TikTok", callback_data="tiktok"), InlineKeyboardButton("Shopee", callback_data="shopee")],
    ]
    await update.message.reply_text(
        "VOUCHER HUNTER 2025\n\n"
        "Tự quét 50+ kênh 24/7 – Không cần làm gì!\n"
        "Nhấn nút lấy mã ngon ngay!\n\n"
        "Cập nhật mỗi phút",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    results = []
    title = ""

    if data == "hot": results = vouchers[:10]; title = "10 VOUCHER HOT"
    elif data == "50k": results = [v for v in vouchers if re.search(r'50+k|60+k|70+k|80+k|90+k|100+k', v["text"], re.I)][:12]; title = "≥50K"
    elif data == "100k": results = [v for v in vouchers if re.search(r'100+k|150+k|200+k', v["text"], re.I)][:12]; title = "≥100K"
    elif data == "freeship": results = [v for v in vouchers if "freeship" in v["text"].lower()][:12]; title = "FREESHIP"
    elif data == "tiktok": results = [v for v in vouchers if "tiktok" in v["text"].lower()][:12]; title = "TIKTOK"
    elif data == "shopee": results = [v for v in vouchers if "shopee" in v["text"].lower() or "shp.ee" in v["code"]][:12]; title = "SHOPEE"

    if not results:
        await query.edit_message_text("Đang quét... chờ 5-10 phút sẽ có mã ngon nhé!")
        return

    msg = f"{title} ({len(results)} mã)\n\n"
    for i, v in enumerate(results, 1):
        msg += f"{i}. {v['time']} • {v['source']}\n"
        msg += f"➤ `{v['code']}`\n{v['text'][:200]}{'...' if len(v['text'])>200 else ''}\n\n"
    await query.edit_message_text(msg, parse_mode="Markdown")

# Khởi động
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Tự join kênh + bật scanner
    await auto_join_channels(app.bot)
    asyncio.create_task(scanner_loop(app))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    logger.info("BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG – CHẠY 24/7!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True, timeout=20)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
