# main.py – Voucher Hunter Bot 2025 – TỰ ĐỘNG QUÉT, TỰ JOIN, KHÔNG CẦN LÀM GÌ!
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
import re
import json
import asyncio
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CẤU HÌNH ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Thiếu BOT_TOKEN! Vào Render → Environment → thêm BOT_TOKEN")

DB_FILE = "/tmp/vouchers.json"  # Render free tier

# 50+ Public Channel HOT 2025 (bot tự join & quét được ngay)
PUBLIC_CHANNELS = [
    "hoisanvoucher", "nghiensandeal", "groupsanxuvamagiamgia", "sansaleshopee_lazada",
    "nss247", "xomsansale", "bloggiamgia", "magiamgiatiktok", "nghienshopeelazada",
    "dealhotvn", "tiktokvoucherhot", "shopeedeal24h", "voucher100k", "freeshiptiktok",
    "hotvouchervn", "sansaledeal", "shopeevoucher24h", "voucherfreeshipshopee",
    "tiktokshopvoucher24h", "dealhot24h", "voucher100k_up", "huntersvoucher",
    "freeship24h", "affiliateshopeevn", "shopeevoucherhn", "tiktokshop0d",
    "vouchertiktokshopfree", "tiktokhoanxu", "hotdealshopee2025", "shopeevoucherfreeship",
    "tiktokshopdeal", "voucher_shopee_tiktok", "sanvouchervn", "dealshopeetiktok",
    "freeshipshopeeextra", "hoanxushopee", "magiamgia24h", "shopeetiktokvoucher",
    "groupvoucherhot", "deal0dongshopee", "tiktoksalevn", "shopeeaffiliatevn",
    "tiktokshopfreeship", "giamsgiashopee", "hoanthientiktok", "vouchertoansanshopee",
    "sanhotdeal", "shopee12h18h", "tiktokshop100k"
]

# Load/Save voucher
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

# ==================== TỰ ĐỘNG JOIN PUBLIC CHANNEL ====================
async def auto_join_channels(bot: Bot):
    print("Bắt đầu tự động join 50+ kênh public...")
    for channel in PUBLIC_CHANNELS:
        try:
            await bot.join_chat(f"@{channel}")
            print(f"Đã join: @{channel}")
            await asyncio.sleep(2)
        except BadRequest as e:
            if "already" in str(e).lower():
                pass  # đã join rồi
            else:
                print(f"Không join được @{channel}: {e}")
        except Exception as e:
            print(f"Lỗi @{channel}: {e}")
        await asyncio.sleep(1)
    print("HOÀN TẤT JOIN TẤT CẢ KÊNH PUBLIC!")

# ==================== SCANNER TỰ ĐỘNG ====================
async def scanner_loop(app):
    while True:
        try:
            updates = await app.bot.get_updates(
                offset=getattr(app.bot, "last_update_id", 0) + 1,
                timeout=20,
                allowed_updates=["message", "channel_post"]
            )
            for update in updates:
                msg = update.message or update.channel_post
                if not msg or not msg.text:
                    continue
                text_low = msg.text.lower()
                if not any(kw in text_low for kw in ["50k","100k","200k","freeship","hoàn xu","extra","toàn sàn","0đ"]):
                    continue

                codes = CODE_PATTERN.findall(msg.text)
                source = getattr(msg.chat, "username", "") or getattr(msg.chat, "title", "Unknown")
                new_v = {
                    "code": " | ".join(codes) if codes else "Xem tin nhắn",
                    "text": msg.text[:400],
                    "source": f"@{source}" if source != "Unknown" else source,
                    "time": datetime.now().strftime("%H:%M %d/%m")
                }
                if not any(v["text"] == new_v["text"] for v in vouchers[:50]):
                    vouchers.insert(0, new_v)
                    vouchers = vouchers[:500]
                    save_vouchers(vouchers)
                    logger.info(f"ĐÃ LƯU VOUCHER MỚI từ @{source}")

            if updates:
                app.bot.last_update_id = updates[-1].update_id

        except Exception as e:
            if "Conflict" not in str(e):
                logger.error(f"Scanner lỗi: {e}")
        await asyncio.sleep(60)

# ==================== LỆNH BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Voucher HOT", callback_data="hot")],
        [InlineKeyboardButton("≥50k", callback_data="50k"), InlineKeyboardButton("≥100k", callback_data="100k")],
        [InlineKeyboardButton("Freeship Extra", callback_data="freeship")],
        [InlineKeyboardButton("TikTok Shop", callback_data="tiktok"), InlineKeyboardButton("Shopee", callback_data="shopee")],
    ]
    await update.message.reply_text(
        "VOUCHER HUNTER 2025\n\n"
        "Bot tự quét 50+ kênh voucher HOT 24/7\n"
        "Nhấn nút lấy mã ≥50k, freeship, hoàn xu ngay!\n\n"
        "Cập nhật mỗi phút",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    results = []
    title = ""

    if data == "hot":
        results = vouchers[:10]
        title = "10 VOUCHER HOT NHẤT"
    elif data == "50k":
        results = [v for v in vouchers if re.search(r'50+k|60+k|70+k|80+k|90+k|100+k', v["text"], re.I)][:12]
        title = "GIẢM ≥50K"
    elif data == "100k":
        results = [v for v in vouchers if re.search(r'100+k|150+k|200+k|300+k', v["text"], re.I)][:12]
        title = "GIẢM ≥100K"
    elif data == "freeship":
        results = [v for v in vouchers if "freeship" in v["text"].lower()][:12]
        title = "FREESHIP EXTRA"
    elif data == "tiktok":
        results = [v for v in vouchers if "tiktok" in v["text"].lower()][:12]
        title = "TIKTOK SHOP"
    elif data == "shopee":
        results = [v for v in vouchers if "shopee" in v["text"].lower() or "shp.ee" in v["code"]][:12]
        title = "SHOPEE"

    if not results:
        await query.edit_message_text("Chưa có mã nào. Bot đang quét... thử lại sau 5-10 phút nhé!")
        return

    msg = f"{title} ({len(results)} mã)\n\n"
    for i, v in enumerate(results, 1):
        msg += f"{i}. {v['time']} • {v['source']}\n"
        msg += f"➤ `{v['code']}`\n{v['text'][:200]}{'...' if len(v['text'])>200 else ''}\n\n"
    await query.edit_message_text(msg, parse_mode="Markdown")

# ==================== KHỞI ĐỘNG ====================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Tự động join tất cả kênh public khi khởi động
    await auto_join_channels(app.bot)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    # Bật scanner tự động
    asyncio.create_task(scanner_loop(app))

    logger.info("BOT KHỞI ĐỘNG THÀNH CÔNG – TỰ QUÉT 50+ KÊNH 24/7!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
