import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import random
import json
import os
from datetime import datetime
import string

# ضع التوكن الجديد هنا بعد عمل Reset Token
TOKEN = "MTU0MjY1MDY0MjI1NzE1NDE1OQ.GDNe66.-WTaZjCUcpax1LFuPEBdHwvUR9Wz8J7VO9x5BE"

# --- Channel IDs ---
LOG_CHANNEL_ID = 1542647789685710848      # روم المبيعات
TICKET_CHANNEL_ID = 1542650866987835484   # روم مشاكل العملاء (Reports & Disputes)
STOCK_CHANNEL_ID = 1542650898432524378    # روم مراقبة المخزون

PLATFORMS = ['Salla', 'Zid', 'Telegram', 'Eldorado.gg', 'G2G.com', 'Mtjr-OW', 'Mada-R', 'Linkin.sa']
CURRENCIES = {'USD': 1.0, 'SAR': 3.75, 'AED': 3.67}

FIXED_PRICES = {
    "ChatGPT Plus": {"Account": 9.0, "Activation Link": 9.0, "Gift Card": 9.0},
    "ChatGPT Pro": {"Account": 45.0, "Activation Link": 45.0, "Gift Card": 45.0},
    "ChatGPT Business": {"Account": 80.0, "Activation Link": 80.0, "Gift Card": 80.0},
    "Claude Pro": {"Account": 20.0, "Activation Link": 20.0, "Gift Card": 20.0},
    "Claude Max": {"Account": 140.0, "Activation Link": 140.0, "Gift Card": 140.0},
    "Gemini Pro 18-Month": {"Account": 5.0, "Activation Link": 5.0},
    "Midjourney Basic": {"Account": 4.5, "Activation Link": 4.5, "Gift Card": 4.5},
    "Midjourney Standard": {"Account": 8.0, "Activation Link": 8.0, "Gift Card": 8.0},
    "Midjourney Pro": {"Account": 20.0, "Activation Link": 20.0, "Gift Card": 20.0},
    "Perplexity Pro Monthly": {"Account": 5.0, "Activation Link": 5.0, "Gift Card": 5.0},
    "Perplexity Pro Yearly": {"Account": 25.0, "Activation Link": 25.0, "Gift Card": 25.0},
    "GitHub Copilot Individual": {"Account": 3.0, "Activation Link": 3.0, "Gift Card": 3.0},
    "GitHub Copilot Business": {"Account": 10.0, "Activation Link": 10.0, "Gift Card": 10.0},
    "Canva Pro Monthly": {"Account": 1.0, "Activation Link": 1.0, "Gift Card": 1.0},
    "Canva Pro Yearly": {"Account": 10.0, "Activation Link": 10.0, "Gift Card": 10.0},
    "Notion AI Monthly": {"Account": 5.0, "Activation Link": 5.0, "Gift Card": 5.0},
    "Notion AI Yearly": {"Account": 20.0, "Activation Link": 20.0, "Gift Card": 20.0},
    "ElevenLabs Creator": {"Account": 20.0, "Activation Link": 20.0, "Gift Card": 20.0},
    "ElevenLabs Pro": {"Account": 80.0, "Activation Link": 80.0, "Gift Card": 80.0},
    "Leonardo AI Apprentice": {"Account": 10.0, "Activation Link": 10.0, "Gift Card": 10.0},
    "Leonardo AI Artisan": {"Account": 15.0, "Activation Link": 15.0, "Gift Card": 15.0},
    "Grammarly Premium Monthly": {"Account": 5.0, "Activation Link": 5.0, "Gift Card": 5.0},
    "Grammarly Premium Yearly": {"Account": 9.0, "Activation Link": 9.0, "Gift Card": 9.0},
    "Jasper AI Creator": {"Account": 9.0, "Activation Link": 9.0, "Gift Card": 9.0},
    "Jasper AI Pro": {"Account": 20.0, "Activation Link": 20.0, "Gift Card": 20.0},
    "Copy.ai Pro": {"Account": 4.0, "Activation Link": 4.0, "Gift Card": 4.0},
    "Copy.ai Team": {"Account": 20.0, "Activation Link": 20.0, "Gift Card": 20.0},
    "Runway ML Standard": {"Account": 8.0, "Activation Link": 8.0, "Gift Card": 8.0},
    "Runway ML Pro": {"Account": 21.0, "Activation Link": 21.0, "Gift Card": 21.0},
    "Synthesia Starter": {"Account": 9.0, "Activation Link": 9.0, "Gift Card": 9.0},
    "Synthesia Creator": {"Account": 20.0, "Activation Link": 20.0, "Gift Card": 20.0},
    "Poe Monthly": {"Account": 2.0, "Activation Link": 2.0, "Gift Card": 2.0},
    "Poe Yearly": {"Account": 8.0, "Activation Link": 8.0, "Gift Card": 8.0},
    "Character.ai c.ai+": {"Account": 4.0, "Activation Link": 4.0, "Gift Card": 4.0},
    "DeepL Pro Starter": {"Account": 12.5, "Activation Link": 12.5, "Gift Card": 12.5},
    "DeepL Pro Advanced": {"Account": 25.5, "Activation Link": 25.5, "Gift Card": 25.5},
    "HuggingFace Pro": {"Account": 15.4, "Activation Link": 15.4, "Gift Card": 15.4},
    "CapCut Pro Monthly": {"Account": 5.0, "Activation Link": 5.0, "Gift Card": 5.0},
    "CapCut Pro Yearly": {"Account": 25.0, "Activation Link": 25.0, "Gift Card": 25.0}
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

# --- أزرار التعامل مع شكاوى العملاء (Replace or Dispute) ---
class TicketActionView(View):
    def __init__(self, order_id, client_email):
        super().__init__(timeout=None)
        self.order_id = order_id
        self.client_email = client_email

    @discord.ui.button(label="✅ Send Replace", style=discord.ButtonStyle.green)
    async def replace_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"✅ **Replacement sent** successfully for Order `{self.order_id}` (Client: `{self.client_email}`).", ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="❌ Reject / Dispute (Fake)", style=discord.ButtonStyle.red)
    async def dispute_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"❌ **Disputed / Rejected** for Order `{self.order_id}`. Marked as Fake.", ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

# --- لوحة التحكم التفاعلية بالأزرار (Dashboard Panel) ---
class StorePanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📊 View Stats", style=discord.ButtonStyle.blurple, custom_id="btn_stats")
    async def stats_button(self, interaction: discord.Interaction, button: Button):
        sales = load_data(SALES_FILE)
        total_rev = sum(s["price"] for s in sales)
        await interaction.response.send_message(f"📊 **Store Statistics:**\n- Total Orders: `{len(sales)}`\n- Total Revenue: `${total_rev:.2f} / {total_rev * 3.75:.2f} SAR`", ephemeral=True)

    @discord.ui.button(label="📦 View Stock", style=discord.ButtonStyle.green, custom_id="btn_stock")
    async def stock_button(self, interaction: discord.Interaction, button: Button):
        inv = load_data(INVENTORY_FILE)
        desc = "\n".join([f"**{p} ({t})**: `{val}` units" for p, t_dict in inv.items() for t, val in t_dict.items()])
        # اختصار النص لو تجاوز الحد المسموح في ديسكورد
        if len(desc) > 1900: desc = desc[:1900] + "\n... (Truncated)"
        await interaction.response.send_message(f"📦 **Current Inventory (Max 1500):**\n{desc}", ephemeral=True)

    @discord.ui.button(label="🔄 Quick Restock All (+500)", style=discord.ButtonStyle.gray, custom_id="btn_restock")
    async def restock_button(self, interaction: discord.Interaction, button: Button):
        inv = load_data(INVENTORY_FILE)
        for p in inv:
            for t in inv[p]:
                inv[p][t] += 500
        save_data(INVENTORY_FILE, inv)
        await interaction.response.send_message("✅ Successfully added `+500` units to **ALL products** in inventory!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user.name} | Zayn C. © 2026")
    if not background_sales.is_running():
        background_sales.start()

# --- أمر إرسال لوحة التحكم التفاعلية ---
@bot.command(name="panel")
async def panel_cmd(ctx):
    embed = discord.Embed(
        title="⚙️ Store Management Dashboard", 
        description="Use the interactive buttons below to manage your store instantly:", 
        color=0x00FF00
    )
    # نرسل اللوحة في روم الستوك أو الروم التي كتب فيها الأمر
    await ctx.send(embed=embed, view=StorePanelView())

# --- محاكاة مبيعات لايف + محاكاة تقارير مشاكل عشوائية ---
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
    prod, ptype, price_usd = random.choices(choices, weights=weights, k=1)[0]
    
    inv[prod][ptype] -= 1
    stock_left = inv[prod][ptype]
    save_data(INVENTORY_FILE, inv)
    
    plat = random.choice(PLATFORMS)
    oid = f"ORD-{random.randint(10000, 99999)}"
    psar = round(price_usd * CURRENCIES['SAR'], 2)
    masked_email, item_data = generate_item_data(prod, ptype)
    
    # حفظ البيع
    sales = load_data(SALES_FILE)
    sales.append({"oid": oid, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "prod": prod, "type": ptype, "price": price_usd, "email": masked_email})
    save_data(SALES_FILE, sales)
    
    # إرسال إشعار المبيعة
    embed = discord.Embed(title="💰 New Store Sale!", color=0x00FF00, timestamp=datetime.utcnow())
    embed.add_field(name="🛒 Product", value=f"{prod} ({ptype})", inline=True)
    embed.add_field(name="🌐 Platform", value=plat, inline=True)
    embed.add_field(name="🏷️ Order ID", value=oid, inline=True)
    embed.add_field(name="💵 Revenue", value=f"${price_usd} / {psar} SAR", inline=True)
    embed.add_field(name="📦 Stock Left", value=str(stock_left), inline=True)
    embed.add_field(name="📧 Client", value=masked_email, inline=True)
    embed.add_field(name="🔑 Data", value=f"||{item_data}||", inline=False)
    await log_chan.send(embed=embed)

    # محاكاة عشوائية لتقرير مشكلة (Report/Issue) من عميل لتجربة النظام
    if ticket_chan and random.random() > 0.6: 
        issues = ["Password is incorrect / Not working", "Activation Link expired / Invalid", "Email doesn't exist", "Fake Account Details"]
        issue_reason = random.choice(issues)
        
        t_embed = discord.Embed(title="🚨 New Client Report / Issue!", color=0xFF0000, timestamp=datetime.utcnow())
        t_embed.add_field(name="🏷️ Order ID", value=oid, inline=True)
        t_embed.add_field(name="🛒 Product", value=f"{prod} ({ptype})", inline=True)
        t_embed.add_field(name="📧 Client Email", value=masked_email, inline=True)
        t_embed.add_field(name="⚠️ Problem Details", value=issue_reason, inline=False)
        t_embed.set_footer(text="Choose an action below:")
        
        await ticket_chan.send(embed=t_embed, view=TicketActionView(oid, masked_email))

bot.run(TOKEN)