import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import random
import json
import os
from datetime import datetime
import string
from flask import Flask
from threading import Thread

# ضع التوكن الجديد هنا بعد عمل Reset Token
TOKEN = "MTU0MjY1MDY0MjI1NzE1NDE1OQ.GDNe66.-WTaZjCUcpax1LFuPEBdHwvUR9Wz8J7VO9x5BE"

# --- Channel IDs ---
LOG_CHANNEL_ID = 1542647789685710848      
TICKET_CHANNEL_ID = 1542650866987835484   
STOCK_CHANNEL_ID = 1542650898432524378    

# 🚨 ضع الـ ID الخاص بحسابك في ديسكورد هنا بدلاً من هذا الرقم لكي لا يتحكم أحد غيرك في البوت
AUTHORIZED_USERS = [1296895463097897015]

PLATFORMS = ['Salla', 'Zid', 'Telegram', 'Eldorado.gg', 'G2G.com', 'Mtjr-OW', 'Mada-R', 'Linkin.sa']
CURRENCIES = {'USD': 1.0, 'SAR': 3.75, 'AED': 3.67}

# قائمة الأسعار الجديدة (مفصلة لكل نوع)
FIXED_PRICES = {
    "ChatGPT Plus": {"Account": 9.0, "Activation Link": 12.0, "Gift Card": 15.0},
    "ChatGPT Pro": {"Account": 45.0, "Activation Link": 48.0, "Gift Card": 55.0},
    "ChatGPT Business": {"Account": 80.0, "Activation Link": 82.0, "Gift Card": 85.0},
    "Claude Pro": {"Account": 20.0, "Activation Link": 23.0, "Gift Card": 25.0},
    "Claude Max": {"Account": 140.0, "Activation Link": 142.0, "Gift Card": 145.0},
    "Gemini Pro 18-Month": {"Account": 5.0, "Activation Link": 7.5},
    "Midjourney Basic": {"Account": 4.5, "Activation Link": 5.0, "Gift Card": 6.0},
    "Midjourney Standard": {"Account": 8.0, "Activation Link": 10.0, "Gift Card": 12.0},
    "Midjourney Pro": {"Account": 20.0, "Activation Link": 22.0, "Gift Card": 25.0},
    "Canva Pro Yearly": {"Account": 10.0, "Activation Link": 12.0, "Gift Card": 15.0},
    "ElevenLabs Pro": {"Account": 80.0, "Activation Link": 85.0, "Gift Card": 90.0}
    # يمكنك إضافة بقية المنتجات هنا بنفس النمط...
}

INVENTORY_FILE = 'master_inventory.json'
SALES_FILE = 'master_sales.json'

def init_db():
    if not os.path.exists(INVENTORY_FILE):
        inv = {}
        for prod, types in FIXED_PRICES.items():
            inv[prod] = {t: 1500 for t in types} 
        with open(INVENTORY_FILE, 'w') as f: json.dump(inv, f, indent=4)
        
    if not os.path.exists(SALES_FILE):
        with open(SALES_FILE, 'w') as f: json.dump([], f)

init_db()

def load_data(file):
    with open(file, 'r') as f: return json.load(f)

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS

def generate_item_data(prod_name, prod_type):
    domains = ['@gmail.com', '@outlook.com', '@hotmail.com', '@yahoo.com']
    uname = ''.join(random.choices(string.ascii_lowercase, k=7)) + str(random.randint(1995, 2026))
    email = uname + random.choice(domains)
    masked = uname[:3] + "****" + email[email.find('@'):]
    
    if "Account" in prod_type:
        pwd = ''.join(random.choices(string.ascii_letters, k=8)).capitalize() + str(random.randint(100, 999)) + "!"
        return masked, f"{email}:{pwd}"
    elif "Link" in prod_type:
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        base = prod_name.split()[0].lower().replace('.', '')
        return masked, f"https://{base}.com/activate?key={token}"
    elif "Gift Card" in prod_type:
        pfx = prod_name.split()[0][:4].upper()
        return masked, f"{pfx}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
    return masked, "N/A"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- أزرار التعامل مع شكاوى العملاء ---
class TicketActionView(View):
    def __init__(self, order_id, client_email):
        super().__init__(timeout=None)
        self.order_id = order_id
        self.client_email = client_email

    @discord.ui.button(label="✅ Send Replace", style=discord.ButtonStyle.green)
    async def replace_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        await interaction.response.send_message(f"✅ **Replacement sent** successfully for Order `{self.order_id}`.", ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="❌ Reject / Dispute", style=discord.ButtonStyle.red)
    async def dispute_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
        await interaction.response.send_message(f"❌ **Disputed / Rejected** for Order `{self.order_id}`. Marked as Fake.", ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

# --- لوحة التحكم التفاعلية ---
class StorePanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📊 View Stats", style=discord.ButtonStyle.blurple, custom_id="btn_stats")
    async def stats_button(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return await interaction.response.send_message("❌ Access Denied", ephemeral=True)
        sales = load_data(SALES_FILE)
        total_rev = sum(s.get("price", 0) for s in sales)
        total_fees = sum(s.get("fee", 0) for s in sales)
        net_profit = total_rev - total_fees
        await interaction.response.send_message(f"📊 **Store Statistics:**\n- Total Orders: `{len(sales)}`\n- Gross Revenue: `${total_rev:.2f}`\n- Net Profit (After Fees): `${net_profit:.2f}`", ephemeral=True)

    @discord.ui.button(label="📦 View Stock", style=discord.ButtonStyle.green, custom_id="btn_stock")
    async def stock_button(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return await interaction.response.send_message("❌ Access Denied", ephemeral=True)
        inv = load_data(INVENTORY_FILE)
        desc = "\n".join([f"**{p} ({t})**: `{val}` units" for p, t_dict in inv.items() for t, val in t_dict.items()])
        if len(desc) > 1900: desc = desc[:1900] + "\n... (Truncated)"
        await interaction.response.send_message(f"📦 **Current Inventory (Max 1500):**\n{desc}", ephemeral=True)

    @discord.ui.button(label="🔄 Quick Restock All (+500)", style=discord.ButtonStyle.gray, custom_id="btn_restock")
    async def restock_button(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return await interaction.response.send_message("❌ Access Denied", ephemeral=True)
        inv = load_data(INVENTORY_FILE)
        for p in inv:
            for t in inv[p]:
                inv[p][t] += 500
        save_data(INVENTORY_FILE, inv)
        await interaction.response.send_message("✅ Successfully added `+500` units to **ALL products** in inventory!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user.name}")
    # الحالة المخصصة للسيرفر
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="AFK Cafe | Serving Clients"))
    if not background_sales.is_running():
        background_sales.start()

@bot.command(name="panel")
async def panel_cmd(ctx):
    if not is_authorized(ctx.author.id): return
    embed = discord.Embed(
        title="⚙️ Store Management Dashboard", 
        description="Use the interactive buttons below to manage your store instantly:", 
        color=0x00FF00
    )
    embed.set_footer(text="Zayn C. © 2026 | Encrypted Connection")
    await ctx.send(embed=embed, view=StorePanelView())

@bot.command(name="setprice")
async def set_price(ctx, product: str, p_type: str, new_price: float):
    if not is_authorized(ctx.author.id): return
    if product in FIXED_PRICES and p_type in FIXED_PRICES[product]:
        FIXED_PRICES[product][p_type] = new_price
        await ctx.send(f"✅ Price for **{product} ({p_type})** updated to `${new_price}`.")
    else:
        await ctx.send("❌ Product or Type not found. Example: `!setprice \"ChatGPT Plus\" Account 10.5`")

# --- محاكاة مبيعات لايف ---
@tasks.loop(minutes=4)
async def background_sales():
    log_chan = bot.get_channel(LOG_CHANNEL_ID)
    ticket_chan = bot.get_channel(TICKET_CHANNEL_ID)
    if not log_chan: return
    
    inv = load_data(INVENTORY_FILE)
    choices, weights = [], []
    for p, t_dict in inv.items():
        for t, qty in t_dict.items():
            if qty > 0:
                choices.append((p, t, FIXED_PRICES[p][t]))
                weights.append(1000 / (FIXED_PRICES[p][t] + 5))
                
    if not choices: return
    prod, ptype, base_price_usd = random.choices(choices, weights=weights, k=1)[0]
    
    # 1. طلبات الجملة
    is_bulk = random.random() < 0.05
    qty = random.randint(10, 50) if is_bulk else 1
    if inv[prod][ptype] < qty: qty = inv[prod][ptype]
    if qty == 0: return

    inv[prod][ptype] -= qty
    stock_left = inv[prod][ptype]
    save_data(INVENTORY_FILE, inv)
    
    total_price_usd = base_price_usd * qty
    psar = round(total_price_usd * CURRENCIES['SAR'], 2)
    plat = random.choice(PLATFORMS)
    oid = f"ORD-{random.randint(10000, 99999)}"
    masked_email, item_data = generate_item_data(prod, ptype)

    # 2. بوابات الدفع
    pay_methods = ["Credit Card", "Crypto", "Bank Transfer"]
    method = random.choices(pay_methods, weights=[50, 30, 20])[0]
    
    fee = 0
    pay_details = ""
    if method == "Credit Card":
        fee = round((total_price_usd * 0.029) + 0.30, 2)
        pay_details = f"💳 Visa ending in **{random.randint(1000, 9999)}** (Fee: ${fee})"
    elif method == "Crypto":
        coin = random.choice(["USDT (TRC20)", "BTC", "LTC"])
        pay_details = f"🪙 {coin} | TXID: `0x{''.join(random.choices(string.ascii_letters + string.digits, k=12))}`"
    elif method == "Bank Transfer":
        pay_details = f"🏦 IBAN: `SA{''.join(random.choices(string.digits, k=22))}`"
    
    sales = load_data(SALES_FILE)
    sales.append({
        "oid": oid, 
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prod": prod, 
        "type": ptype, 
        "qty": qty,
        "price": total_price_usd, 
        "fee": fee,
        "method": method,
        "email": masked_email
    })
    save_data(SALES_FILE, sales)
    
    # إرسال إشعار المبيعة
    embed_color = 0xFFD700 if is_bulk else 0x00FF00
    title = "🚨 📦 MASSIVE BULK ORDER!" if is_bulk else "💰 New Store Sale!"
    
    embed = discord.Embed(title=title, color=embed_color, timestamp=datetime.utcnow())
    embed.add_field(name="🛒 Product", value=f"{qty}x {prod} ({ptype})", inline=True)
    embed.add_field(name="🌐 Platform", value=plat, inline=True)
    embed.add_field(name="🏷️ Order ID", value=oid, inline=True)
    embed.add_field(name="💵 Revenue", value=f"${total_price_usd:.2f} / {psar} SAR", inline=True)
    embed.add_field(name="🏦 Payment", value=pay_details, inline=True)
    embed.add_field(name="📦 Stock Left", value=str(stock_left), inline=True)
    embed.add_field(name="📧 Client", value=masked_email, inline=True)
    embed.add_field(name="🔑 Data", value=f"||{item_data}||", inline=False)
    
    if is_bulk:
        await log_chan.send(content=f"<@{AUTHORIZED_USERS[0]}> 🚨 Stock alert! Big purchase just happened.", embed=embed)
    else:
        await log_chan.send(embed=embed)

    # 3. محاكاة المشاكل
    if not is_bulk and ticket_chan and random.random() > 0.6: 
        issues = ["Password is incorrect / Not working", "Activation Link expired / Invalid", "Crypto payment not confirmed", "Fake Account Details"]
        issue_reason = random.choice(issues)
        
        t_embed = discord.Embed(title="🚨 New Client Report / Dispute!", color=0xFF0000, timestamp=datetime.utcnow())
        t_embed.add_field(name="🏷️ Order ID", value=oid, inline=True)
        t_embed.add_field(name="🛒 Product", value=f"{prod} ({ptype})", inline=True)
        t_embed.add_field(name="📧 Client Email", value=masked_email, inline=True)
        t_embed.add_field(name="⚠️ Problem Details", value=issue_reason, inline=False)
        t_embed.set_footer(text="Choose an action below:")
        
        await ticket_chan.send(embed=t_embed, view=TicketActionView(oid, masked_email))

# --- Flask Web Server (لكي يعمل 24/7 على Render) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Online 24/7!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

bot.run(TOKEN)
