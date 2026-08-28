import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
import random
import json
import os
from datetime import datetime, timedelta
import string
from flask import Flask
from threading import Thread
import asyncio

TOKEN = "MTU0MjY1MDY0MjI1NzE1NDE1OQ.GDNe66.-WTaZjCUcpax1LFuPEBdHwvUR9Wz8J7VO9x5BE"

LOG_CHANNEL_ID = 1542647789685710848      
TICKET_CHANNEL_ID = 1542650866987835484   
STOCK_CHANNEL_ID = 1542650898432524378    
AUTHORIZED_USERS = [1296895463097897015] 

PLATFORMS = ['Salla', 'Zid', 'Telegram', 'Eldorado.gg', 'G2G.com']
MY_WALLETS = {"USDT (TRC20)": 0.0, "BTC": 0.0, "LTC": 0.0, "Bank Account (SAR)": 0.0}

CRYPTO_RATES = {"USDT (TRC20)": 1.0, "BTC": 64000.0, "LTC": 85.0}

PRICES = {
    "ChatGPT Plus": {"Account": {"1 Month": 9.0, "1 Year": 90.0}, "Activation Link": {"1 Month": 12.0, "1 Year": 110.0}, "Gift Card": {"1 Month": 15.0, "1 Year": 150.0}},
    "ChatGPT Pro": {"Account": {"1 Month": 45.0, "1 Year": 450.0}, "Activation Link": {"1 Month": 48.0, "1 Year": 480.0}, "Gift Card": {"1 Month": 55.0, "1 Year": 550.0}},
    "ChatGPT Business": {"Account": {"1 Month": 80.0, "1 Year": 800.0}, "Activation Link": {"1 Month": 85.0, "1 Year": 850.0}, "Gift Card": {"1 Month": 90.0, "1 Year": 900.0}},
    "Claude Pro": {"Account": {"1 Month": 20.0, "1 Year": 200.0}, "Activation Link": {"1 Month": 23.0, "1 Year": 230.0}, "Gift Card": {"1 Month": 25.0, "1 Year": 250.0}},
    "Claude Max": {"Account": {"1 Month": 140.0, "1 Year": 1400.0}, "Activation Link": {"1 Month": 145.0, "1 Year": 1450.0}, "Gift Card": {"1 Month": 150.0, "1 Year": 1500.0}},
    "Gemini Pro": {"Account": {"1 Month": 5.0, "1 Year": 50.0}, "Activation Link": {"1 Month": 7.5, "1 Year": 75.0}},
    "Midjourney Basic": {"Account": {"1 Month": 4.5, "1 Year": 45.0}, "Activation Link": {"1 Month": 5.0, "1 Year": 50.0}, "Gift Card": {"1 Month": 6.0, "1 Year": 60.0}},
    "Midjourney Standard": {"Account": {"1 Month": 8.0, "1 Year": 80.0}, "Activation Link": {"1 Month": 10.0, "1 Year": 100.0}, "Gift Card": {"1 Month": 12.0, "1 Year": 120.0}},
    "Midjourney Pro": {"Account": {"1 Month": 20.0, "1 Year": 200.0}, "Activation Link": {"1 Month": 22.0, "1 Year": 220.0}, "Gift Card": {"1 Month": 25.0, "1 Year": 250.0}},
    "Perplexity Pro": {"Account": {"1 Month": 5.0, "1 Year": 25.0}, "Activation Link": {"1 Month": 6.0, "1 Year": 30.0}, "Gift Card": {"1 Month": 7.0, "1 Year": 35.0}},
    "GitHub Copilot Individual": {"Account": {"1 Month": 3.0, "1 Year": 30.0}, "Activation Link": {"1 Month": 4.0, "1 Year": 40.0}, "Gift Card": {"1 Month": 5.0, "1 Year": 50.0}},
    "GitHub Copilot Business": {"Account": {"1 Month": 10.0, "1 Year": 100.0}, "Activation Link": {"1 Month": 12.0, "1 Year": 120.0}, "Gift Card": {"1 Month": 15.0, "1 Year": 150.0}},
    "Canva Pro": {"Account": {"1 Month": 1.0, "1 Year": 10.0}, "Activation Link": {"1 Month": 1.5, "1 Year": 12.0}, "Gift Card": {"1 Month": 2.0, "1 Year": 15.0}},
    "Notion AI": {"Account": {"1 Month": 5.0, "1 Year": 20.0}, "Activation Link": {"1 Month": 6.0, "1 Year": 25.0}, "Gift Card": {"1 Month": 7.0, "1 Year": 30.0}},
    "ElevenLabs Creator": {"Account": {"1 Month": 20.0, "1 Year": 200.0}, "Activation Link": {"1 Month": 22.0, "1 Year": 220.0}, "Gift Card": {"1 Month": 25.0, "1 Year": 250.0}},
    "ElevenLabs Pro": {"Account": {"1 Month": 80.0, "1 Year": 800.0}, "Activation Link": {"1 Month": 85.0, "1 Year": 850.0}, "Gift Card": {"1 Month": 90.0, "1 Year": 900.0}},
    "Leonardo AI Apprentice": {"Account": {"1 Month": 10.0, "1 Year": 100.0}, "Activation Link": {"1 Month": 12.0, "1 Year": 120.0}, "Gift Card": {"1 Month": 15.0, "1 Year": 150.0}},
    "Leonardo AI Artisan": {"Account": {"1 Month": 15.0, "1 Year": 150.0}, "Activation Link": {"1 Month": 18.0, "1 Year": 180.0}, "Gift Card": {"1 Month": 20.0, "1 Year": 200.0}},
    "Grammarly Premium": {"Account": {"1 Month": 5.0, "1 Year": 9.0}, "Activation Link": {"1 Month": 6.0, "1 Year": 12.0}, "Gift Card": {"1 Month": 7.0, "1 Year": 15.0}},
    "Jasper AI Pro": {"Account": {"1 Month": 20.0, "1 Year": 200.0}, "Activation Link": {"1 Month": 22.0, "1 Year": 220.0}, "Gift Card": {"1 Month": 25.0, "1 Year": 250.0}},
    "Copy.ai Pro": {"Account": {"1 Month": 4.0, "1 Year": 40.0}, "Activation Link": {"1 Month": 5.0, "1 Year": 50.0}, "Gift Card": {"1 Month": 6.0, "1 Year": 60.0}},
    "Runway ML Pro": {"Account": {"1 Month": 21.0, "1 Year": 210.0}, "Activation Link": {"1 Month": 23.0, "1 Year": 230.0}, "Gift Card": {"1 Month": 25.0, "1 Year": 250.0}},
    "Synthesia Starter": {"Account": {"1 Month": 9.0, "1 Year": 90.0}, "Activation Link": {"1 Month": 10.0, "1 Year": 100.0}, "Gift Card": {"1 Month": 12.0, "1 Year": 120.0}},
    "Character.ai c.ai+": {"Account": {"1 Month": 4.0, "1 Year": 40.0}, "Activation Link": {"1 Month": 5.0, "1 Year": 50.0}, "Gift Card": {"1 Month": 6.0, "1 Year": 60.0}}
}

INVENTORY_FILE = 'master_inventory.json'
SALES_FILE = 'master_sales.json'
PENDING_APPROVAL_FILE = 'pending_approval.json'
PENDING_EVENTS_FILE = 'pending_events.json'
PAYOUTS_FILE = 'pending_payouts.json'
BALANCES_FILE = 'balances.json'
CONFIG_FILE = 'bot_config.json'
VALORANT_FILE = 'valorant_accounts.json' # ملف حسابات فالورانت العامة

def generate_stock_account():
    names = ['ahmed', 'mohamed', 'khalid', 'zayn', 'james', 'omar', 'david', 'sarah', 'john']
    email = f"{random.choice(names)}{random.randint(1990,2024)}@{random.choice(['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com'])}"
    pwd = f"Password{random.randint(100,999)}!"
    return {"id": email, "pwd": pwd, "created_at": datetime.now().isoformat()}

def generate_secret_data(prod, ptype):
    if ptype == "Activation Link":
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        if "Gemini" in prod: return f"https://one.google.com/redeem/gemini-advanced?token={token}"
        elif "ChatGPT" in prod: return f"https://chatgpt.com/activate?code={token}"
        elif "Claude" in prod: return f"https://claude.ai/claim?gift={token}"
        elif "Canva" in prod: return f"https://canva.com/pro/redeem?code={token}"
        elif "GitHub" in prod: return f"https://github.com/settings/copilot/redeem?key={token}"
        else:
            base = prod.split()[0].lower().replace('.', '')
            return f"https://{base}.com/activate?key={token}"
    elif ptype == "Gift Card":
        pfx = prod.split()[0][:4].upper()
        return f"{pfx}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
    return ""

def init_db():
    if not os.path.exists(INVENTORY_FILE):
        inv = {}
        for prod, types in PRICES.items():
            inv[prod] = {}
            for t, durations in types.items():
                inv[prod][t] = {}
                for dur in durations:
                    if t == "Account":
                        inv[prod][t][dur] = [generate_stock_account() for _ in range(80)]
                    else:
                        inv[prod][t][dur] = [generate_secret_data(prod, t) for _ in range(80)]
        with open(INVENTORY_FILE, 'w') as f: json.dump(inv, f, indent=4)
        
    if not os.path.exists(BALANCES_FILE):
        with open(BALANCES_FILE, 'w') as f: json.dump(MY_WALLETS, f, indent=4)

    for file in [SALES_FILE, PENDING_APPROVAL_FILE, PENDING_EVENTS_FILE, PAYOUTS_FILE, CONFIG_FILE, VALORANT_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f: json.dump({} if file == CONFIG_FILE else [], f)

init_db()

def load_data(file):
    with open(file, 'r') as f: return json.load(f)

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

def is_authorized(user_id): return user_id in AUTHORIZED_USERS

def is_vip(contact, sales):
    for s in sales:
        if s.get("full_contact") == contact: return True
    return False

def generate_order_id(platform):
    num = random.randint(10000, 99999)
    if platform == 'Salla': return f"#SAL-{num}"
    elif platform == 'Zid': return f"#ZID-{num}"
    elif platform == 'Eldorado.gg': return f"ELD-{num}89"
    elif platform == 'G2G.com': return f"G2G-{num}14"
    else: return f"TG-{num}"

def generate_contact_info():
    if random.random() > 0.5:
        names = ['ahmed', 'mohamed', 'khalid', 'zayn', 'james', 'omar', 'david']
        f = random.choice(names)
        full = f"{f}.{random.choice(names)}{random.randint(10,99)}@gmail.com"
        masked = f"{full[:3]}***@gmail.com"
        return full, masked, "Email"
    else:
        prefixes = [('+966', 9, '5'), ('+971', 9, '5'), ('+20', 10, '1'), ('+1', 10, ''), ('+965', 8, '6')]
        code, length, start = random.choice(prefixes)
        num = start + ''.join([str(random.randint(0,9)) for _ in range(length - len(start))])
        full = f"{code}{num}"
        masked = f"{code} {''.join(num[:2])}***{''.join(num[-3:])}"
        return full, masked, "Phone"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- أوامر فالورانت الجديدة ---
@bot.command(name="addval")
async def add_valorant(ctx, name: str, user: str, password: str):
    if not is_authorized(ctx.author.id): return
    accs = load_data(VALORANT_FILE)
    accs.append({"name": name, "user": user, "pass": password})
    save_data(VALORANT_FILE, accs)
    await ctx.send(f"✅ Valorant account `{name}` added successfully!")

@bot.command(name="delval")
async def del_valorant(ctx, name: str):
    if not is_authorized(ctx.author.id): return
    accs = load_data(VALORANT_FILE)
    new_accs = [a for a in accs if a["name"].lower() != name.lower()]
    if len(accs) == len(new_accs):
        return await ctx.send(f"❌ Account `{name}` not found.")
    save_data(VALORANT_FILE, new_accs)
    await ctx.send(f"✅ Valorant account `{name}` deleted.")

@bot.command(name="valorant")
async def show_valorant(ctx):
    accs = load_data(VALORANT_FILE)
    if not accs:
        return await ctx.send("❌ No public Valorant accounts available right now.")
    
    embed = discord.Embed(title="🎮 Public Valorant Accounts", color=0xfa4454)
    for acc in accs:
        embed.add_field(
            name=f"📌 {acc['name']}",
            value=f"**User:** `{acc['user']}`\n**Pass:** `{acc['pass']}`",
            inline=False
        )
    embed.set_footer(text="AFK Cafe | Enjoy Playing!")
    await ctx.send(embed=embed)

# --- نظام تصدير وعرض المخزون الشامل (!stock) ---
class StockExportSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=p, value=p) for p in list(load_data(INVENTORY_FILE).keys())[:25]]
        super().__init__(placeholder="Select product to view/export full stock...", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        inv = load_data(INVENTORY_FILE)
        prod = self.values[0]
        data = inv[prod]
        
        content = f"=== STOCK EXPORT: {prod} ===\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for t in data:
            for dur in data[t]:
                content += f"--- {t} ({dur}) ---\n"
                items = data[t][dur]
                if not items:
                    content += "(Empty Stock)\n"
                else:
                    for item in items:
                        if t == "Account":
                            now = datetime.now()
                            created = datetime.fromisoformat(item["created_at"])
                            total_days = 30 if dur == "1 Month" else 365
                            rem = max(1, total_days - (now - created).days)
                            content += f"Credentials: {item['id']}:{item['pwd']}  [Remaining: {rem} Days]\n"
                        else:
                            content += f"Data: {item}\n"
                content += "\n"
        
        file_path = f"Stock_{prod.replace(' ', '_')}.txt"
        with open(file_path, "w", encoding="utf-8") as f: f.write(content)
            
        await interaction.response.send_message(f"✅ Here is the complete stock database for **{prod}**:", file=discord.File(file_path), ephemeral=True)
        os.remove(file_path)

class StockExportView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StockExportSelect())

@bot.command(name="stock")
async def stock_cmd(ctx):
    if not is_authorized(ctx.author.id): return
    inv = load_data(INVENTORY_FILE)
    desc = ""
    for p in list(inv.keys())[:15]: 
        acc = sum(len(inv[p].get("Account", {}).get(d, [])) for d in inv[p].get("Account", {}))
        lnk = sum(len(inv[p].get("Activation Link", {}).get(d, [])) for d in inv[p].get("Activation Link", {}))
        gc = sum(len(inv[p].get("Gift Card", {}).get(d, [])) for d in inv[p].get("Gift Card", {}))
        desc += f"**{p}:** 👤 {acc} | 🔗 {lnk} | 🎁 {gc}\n"
        
    embed = discord.Embed(title="📦 Master Stock Database", description=f"{desc}\n*Select a product below to export its full list as `.txt`*", color=0x3498db)
    await ctx.send(embed=embed, view=StockExportView())

@bot.command(name="top")
async def top_products(ctx):
    if not is_authorized(ctx.author.id): return
    sales = [s for s in load_data(SALES_FILE) if s.get("status") == "DELIVERED"]
    counts = {}
    for s in sales: counts[s["prod"]] = counts.get(s["prod"], 0) + s.get("qty", 1)
    sorted_prods = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    embed = discord.Embed(title="🏆 Top 5 Best Sellers", color=0xf1c40f)
    for i, (prod, qty) in enumerate(sorted_prods, 1):
        embed.add_field(name=f"#{i} {prod}", value=f"`{qty}` units sold", inline=False)
    await ctx.send(embed=embed)

# --- الواجهات والأوامر (Panel, Delivery, Disputes) ---
class RevealDataView(View):
    def __init__(self, order_id):
        super().__init__(timeout=None)
        self.order_id = order_id
        
    @discord.ui.button(label="🔑 Reveal Data", style=discord.ButtonStyle.secondary)
    async def reveal_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        sales = load_data(SALES_FILE)
        order = next((s for s in sales if s["oid"] == self.order_id), None)
        if not order: return await interaction.response.send_message("❌ Cannot fetch data.", ephemeral=True)
        await interaction.response.send_message(f"🔒 **Delivered Data for {self.order_id}:**\n```\n{order['item_data']}\n```", ephemeral=True)

class AccountSelectDropdown(Select):
    def __init__(self, order_id, prod, duration, qty, is_replace=False):
        self.order_id = order_id; self.prod = prod; self.duration = duration; self.qty = qty; self.is_replace = is_replace
        inv = load_data(INVENTORY_FILE)
        accounts = inv.get(prod, {}).get("Account", {}).get(duration, [])
        options = []
        now = datetime.now()
        total_days = 30 if duration == "1 Month" else 365
        
        for acc in accounts[:25]:
            rem = max(1, total_days - (now - datetime.fromisoformat(acc["created_at"])).days)
            options.append(discord.SelectOption(label=acc['id'], description=f"{rem} Days Remaining", value=acc['id']))
            
        if not options: options.append(discord.SelectOption(label="Out of Stock", value="empty"))
        max_v = min(self.qty, len(options), 25) if options[0].value != "empty" else 1
        super().__init__(placeholder=f"Select {max_v} account(s) from stock...", min_values=max_v, max_values=max_v, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "empty": return await interaction.response.send_message("❌ Stock is empty.", ephemeral=True)
        
        inv = load_data(INVENTORY_FILE)
        accounts = inv[self.prod]["Account"][self.duration]
        selected_details = []
        
        for v in self.values:
            selected_acc = next((a for a in accounts if a["id"] == v), None)
            if selected_acc:
                accounts.remove(selected_acc)
                selected_details.append(f"{selected_acc['id']}:{selected_acc['pwd']}")
                
        save_data(INVENTORY_FILE, inv)
        joined_details = "\n".join(selected_details)
        
        if self.is_replace:
            await interaction.response.send_message(f"✅ **Replacement Sent!**\nData:\n`{joined_details}`", ephemeral=True)
        else:
            pending = load_data(PENDING_APPROVAL_FILE)
            order = next((o for o in pending if o["oid"] == self.order_id), None)
            if order:
                sales = load_data(SALES_FILE)
                order["status"] = "DELIVERED"
                order["item_data"] = f"{order['full_contact']} -> \n{joined_details}"
                order["delivered_at"] = datetime.now().isoformat()
                sales.append(order)
                save_data(SALES_FILE, sales)
                pending = [o for o in pending if o["oid"] != self.order_id]
                save_data(PENDING_APPROVAL_FILE, pending)
                await interaction.response.send_message(f"✅ **Account(s) Delivered!**\n`{joined_details}`", ephemeral=True)
                
        self.view.stop_view()
        try: await interaction.message.edit(content="✅ Order fulfilled.", view=None, embed=interaction.message.embeds[0])
        except: pass

class AccountSelectView(View):
    def __init__(self, order_id, prod, duration, qty, is_replace=False):
        super().__init__(timeout=None)
        self.add_item(AccountSelectDropdown(order_id, prod, duration, qty, is_replace))
    def stop_view(self):
        for child in self.children: child.disabled = True

class ManualDeliveryView(View):
    def __init__(self, order_id, prod, duration, qty):
        super().__init__(timeout=None)
        self.order_id = order_id; self.prod = prod; self.duration = duration; self.qty = qty

    @discord.ui.button(label="📦 Choose Account & Deliver", style=discord.ButtonStyle.primary)
    async def deliver_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        view = AccountSelectView(self.order_id, self.prod, self.duration, self.qty)
        await interaction.response.send_message(f"Select {self.qty} account(s) from your stock:", view=view, ephemeral=True)
        button.disabled = True
        await interaction.message.edit(view=self)

class RestockModal(Modal):
    def __init__(self, prod_name=None):
        title = f"Restock {prod_name}" if prod_name else "Global Restock"
        super().__init__(title=title[:45])
        self.prod_name = prod_name
        self.amount_input = TextInput(label="Amount to Add", style=discord.TextStyle.short, placeholder="50", required=True)
        self.add_item(self.amount_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try: amt = int(self.amount_input.value)
        except: return await interaction.response.send_message("❌ Valid number required.", ephemeral=True)
        
        inv = load_data(INVENTORY_FILE)
        targets = [self.prod_name] if self.prod_name else inv.keys()
        for p in targets:
            for t in inv[p]:
                for dur in inv[p][t]:
                    if t == "Account": inv[p][t][dur].extend([generate_stock_account() for _ in range(amt)])
                    else: inv[p][t][dur].extend([generate_secret_data(p, t) for _ in range(amt)])
        save_data(INVENTORY_FILE, inv)
        await interaction.response.send_message(f"✅ Successfully generated and added `{amt}` units.", ephemeral=True)

class StockRestockSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=p, value=p) for p in list(load_data(INVENTORY_FILE).keys())[:25]]
        super().__init__(placeholder="Select product to add stock...", min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RestockModal(prod_name=self.values[0]))

class AdvancedStockView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StockRestockSelect())
    @discord.ui.button(label="🌐 Global Restock", style=discord.ButtonStyle.blurple, row=1)
    async def global_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RestockModal(prod_name=None))

class StorePanelView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="📊 View Stats", style=discord.ButtonStyle.blurple)
    async def stats_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        sales = load_data(SALES_FILE)
        valid = [s for s in sales if s.get("status") != "REFUNDED"]
        rev = sum(s.get("price", 0) for s in valid)
        net = rev - sum(s.get("fee", 0) for s in valid)
        await interaction.response.send_message(f"📊 **Stats:**\n- Valid Orders: `{len(valid)}`\n- Refunds: `{len(sales)-len(valid)}`\n- Gross: `${rev:.2f}`\n- Net: `${net:.2f}`", ephemeral=True)

    @discord.ui.button(label="⚙️ Manage & Add Stock", style=discord.ButtonStyle.green)
    async def stock_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        await interaction.response.send_message("Select a product to restock:", view=AdvancedStockView(), ephemeral=True)

class DisputeActionView(View):
    def __init__(self, order_id, prod, duration, issue_type):
        super().__init__(timeout=None)
        self.order_id = order_id; self.prod = prod; self.duration = duration; self.issue_type = issue_type

    @discord.ui.button(label="🔄 Manual Replace from Stock", style=discord.ButtonStyle.green)
    async def replace_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        if self.issue_type == "Account":
            view = AccountSelectView(self.order_id, self.prod, self.duration, qty=1, is_replace=True)
            await interaction.response.send_message("Select an account to give as replacement:", view=view, ephemeral=True)
        else:
            inv = load_data(INVENTORY_FILE)
            if len(inv[self.prod][self.issue_type][self.duration]) > 0:
                new_item = inv[self.prod][self.issue_type][self.duration].pop(0)
                save_data(INVENTORY_FILE, inv)
                await interaction.response.send_message(f"✅ Sent new {self.issue_type}.\nData: `{new_item}`", ephemeral=True)
            else: return await interaction.response.send_message("❌ Out of stock.", ephemeral=True)
            
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="💸 Refund", style=discord.ButtonStyle.blurple)
    async def refund_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        sales = load_data(SALES_FILE)
        order = next((s for s in sales if s["oid"] == self.order_id), None)
        if not order or order.get("status") == "REFUNDED": return await interaction.response.send_message("❌ Invalid or already refunded.", ephemeral=True)
        
        dest = order["wallet_dest"]; amt = order["actual_received"]
        if order.get("payout_cleared"):
            bals = load_data(BALANCES_FILE)
            if dest in bals: bals[dest] -= amt
            save_data(BALANCES_FILE, bals)
            msg = f"✅ Refunded! Deducted `{amt:.2f}` from `{dest}`."
        else:
            payouts = [p for p in load_data(PAYOUTS_FILE) if p["oid"] != self.order_id]
            save_data(PAYOUTS_FILE, payouts)
            msg = f"✅ Refunded! Cancelled pending payout to `{dest}`."
            
        order["status"] = "REFUNDED"
        save_data(SALES_FILE, sales)
        await interaction.response.send_message(msg, ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="❌ Reject Dispute", style=discord.ButtonStyle.red)
    async def reject_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        await interaction.response.send_message(f"❌ Dispute Rejected.", ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

@bot.command(name="setpayout")
async def set_payout(ctx, channel_id: int):
    if not is_authorized(ctx.author.id): return
    config = load_data(CONFIG_FILE)
    config["payout_channel"] = channel_id
    save_data(CONFIG_FILE, config)
    await ctx.send(f"✅ Payout notifications will now be sent to <#{channel_id}>.")

@bot.command(name="system")
async def system_menu(ctx):
    if not is_authorized(ctx.author.id): return
    embed = discord.Embed(title="⚙️ AFK Cafe | System", color=0x2b2d31)
    embed.add_field(name="`!panel`", value="Main Dashboard & Restock UI", inline=False)
    embed.add_field(name="`!stock`", value="Export complete stock lists to .txt files.", inline=False)
    embed.add_field(name="`!order [ID]`", value="Full unmasked details + payment status.", inline=False)
    embed.add_field(name="`!wallets`", value="Check current funds in Bank & Crypto.", inline=False)
    embed.add_field(name="`!forcepay [ID]`", value="Manually clear a stuck payment.", inline=False)
    embed.add_field(name="`!stock_chats`", value="View active delivered accounts.", inline=False)
    embed.add_field(name="`!top`", value="View top 5 best-selling products.", inline=False)
    embed.add_field(name="`!addval \"Name\" User Pass`", value="Add a public Valorant account.", inline=False)
    embed.set_footer(text="Zayn C. | Internal System")
    await ctx.send(embed=embed)

@bot.command(name="panel")
async def panel_cmd(ctx):
    if not is_authorized(ctx.author.id): return
    embed = discord.Embed(title="⚙️ Store Dashboard", color=0x00FF00)
    embed.set_footer(text="Zayn C. © 2026")
    await ctx.send(embed=embed, view=StorePanelView())

@bot.command(name="wallets")
async def check_wallets(ctx):
    if not is_authorized(ctx.author.id): return
    bals = load_data(BALANCES_FILE)
    embed = discord.Embed(title="💼 AFK Cafe Finances", color=0xf1c40f)
    embed.add_field(name="🏦 Bank Account (SAR)", value=f"`{bals['Bank Account (SAR)']:.2f} SAR`", inline=False)
    embed.add_field(name="🪙 USDT (TRC20)", value=f"`{bals['USDT (TRC20)']:.2f} USDT`", inline=True)
    embed.add_field(name="🪙 BTC", value=f"`{bals['BTC']:.5f} BTC`", inline=True)
    embed.add_field(name="🪙 LTC", value=f"`{bals['LTC']:.3f} LTC`", inline=True)
    embed.set_footer(text="Zayn C. | Live Sync")
    await ctx.send(embed=embed)

@bot.command(name="order")
async def check_order(ctx, order_id: str):
    if not is_authorized(ctx.author.id): return
    sales, pending = load_data(SALES_FILE), load_data(PENDING_APPROVAL_FILE)
    order = next((s for s in sales + pending if s["oid"] == order_id), None)
    if not order: return await ctx.send(f"❌ Order `{order_id}` not found.")
    
    embed = discord.Embed(title=f"🧾 Order: {order['oid']}", color=0x3498db)
    embed.add_field(name="🌐 Platform", value=order['platform'], inline=True)
    vip_tag = "🌟 VIP Returning Client" if is_vip(order['full_contact'], [s for s in sales if s['oid']!=order_id]) else ""
    embed.add_field(name=f"👤 Client ({order['contact_type']})", value=f"`{order['full_contact']}`\n{vip_tag}", inline=True)
    embed.add_field(name="🛒 Item", value=f"{order.get('qty', 1)}x {order['prod']} ({order['type']}) - {order['duration']}", inline=False)
    
    embed.add_field(name="💰 Exact Paid Amount", value=f"`{order['exact_paid']}`", inline=True)
    payout_status = "✅ Arrived in Wallet" if order.get("payout_cleared") else "⚠️ Unconfirmed / Pending"
    embed.add_field(name="💸 Payment Route", value=f"{order['method']} \n{payout_status}", inline=False)
    embed.add_field(name="📌 Status", value=f"`{order['status']}`", inline=True)
    
    if order['status'] == 'DELIVERED':
        del_time = datetime.fromisoformat(order['delivered_at'])
        days_active = (datetime.now() - del_time).days
        embed.add_field(name="⏱️ Days Active", value=f"`{days_active} Days`", inline=True)
        embed.add_field(name="🔑 Unmasked Data", value=f"```\n{order['item_data'][:1000]}\n```", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="forcepay")
async def force_pay(ctx, order_id: str):
    if not is_authorized(ctx.author.id): return
    sales, pending = load_data(SALES_FILE), load_data(PENDING_APPROVAL_FILE)
    order = next((s for s in sales + pending if s["oid"] == order_id), None)
    if not order: return await ctx.send("❌ Order not found.")
    if order.get("payout_cleared"): return await ctx.send("⚠️ Payment was already cleared.")
    
    order["payout_cleared"] = True
    save_data(SALES_FILE, sales); save_data(PENDING_APPROVAL_FILE, pending)
    
    bals = load_data(BALANCES_FILE)
    dest = order["wallet_dest"]
    amt = order["actual_received"]
    if dest in bals: bals[dest] += amt
    save_data(BALANCES_FILE, bals)
    await ctx.send(f"✅ **Forced Payment!** Added `{amt}` to `{dest}` wallet.")

@bot.command(name="stock_chats")
async def stock_chats(ctx):
    if not is_authorized(ctx.author.id): return
    sales = load_data(SALES_FILE)
    active = [s for s in sales if s['type'] == 'Account' and s['status'] == 'DELIVERED']
    if not active: return await ctx.send("📋 No active accounts.")
    embed = discord.Embed(title="📱 Active Delivered Accounts", color=0x2ecc71)
    for acc in active[-5:]:
        days = (datetime.now() - datetime.fromisoformat(acc['delivered_at'])).days
        embed.add_field(name=f"Order {acc['oid']} - {acc['prod']}", value=f"👤 Client: `{acc['masked_contact']}`\n⏳ Active: `{days} Days`", inline=False)
    await ctx.send(embed=embed)

@tasks.loop(minutes=2)
async def update_bot_status():
    sales = load_data(SALES_FILE)
    valid_orders = len([s for s in sales if s.get("status") != "REFUNDED"])
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"I love M | Serving {valid_orders} Clients"))

@tasks.loop(minutes=1)
async def burst_sales():
    num_orders = random.choices([0, 1, 2, 3, 4], weights=[80, 12, 5, 2, 1])[0]
    if num_orders == 0: return
    
    log_chan = bot.get_channel(LOG_CHANNEL_ID)
    if not log_chan: return
    
    sales_db = load_data(SALES_FILE)
    
    for _ in range(num_orders):
        await asyncio.sleep(random.randint(1, 10))
        platform = random.choice(PLATFORMS)
        prod = random.choice(list(PRICES.keys()))
        ptype_options = list(PRICES[prod].keys())
        ptype = random.choice(ptype_options)
        duration = random.choice(list(PRICES[prod][ptype].keys()))
        unit_price = PRICES[prod][ptype][duration]
        
        is_bulk = random.random() < 0.05
        if is_bulk:
            qty = random.randint(25, 65)
            if ptype == "Account": qty = min(qty, 25)
        else:
            qty = random.choices([1, 2, 3, 4], weights=[75, 15, 7, 3])[0]
            
        inv = load_data(INVENTORY_FILE)
        available = len(inv[prod][ptype][duration])
        qty = min(qty, available)
        if qty <= 0: continue
            
        total_usd = unit_price * qty
        promo_str = "None"
        if random.random() < 0.20:
            total_usd = round(total_usd * 0.90, 2); promo_str = random.choice(["SALE10", "WELCOME10"])
            
        oid = generate_order_id(platform)
        full_contact, masked_contact, contact_type = generate_contact_info()
        vip_tag = "🌟 VIP Returning Client" if is_vip(full_contact, sales_db) else ""

        method = random.choices(["Credit Card", "Bank Transfer", "Crypto"], weights=[40, 30, 30])[0]
        payout_delay, payout_dest, exact_paid, actual_received = 0, "", "", 0.0
        
        if method in ["Credit Card", "Bank Transfer"]:
            currency = random.choice(["SAR", "AED", "USD"])
            if currency == "SAR": paid_amt = total_usd * 3.75; symbol = "SAR"
            elif currency == "AED": paid_amt = total_usd * 3.67; symbol = "AED"
            else: paid_amt = total_usd; symbol = "$"
            exact_paid = f"{paid_amt:.2f} {symbol}"
            actual_received = total_usd * 3.75 
            payout_dest = "Bank Account (SAR)"
            payout_delay = 12 * 60 if method == "Credit Card" else 4 * 60
        else:
            coin = random.choice(["USDT (TRC20)", "BTC", "LTC"])
            crypto_amt = total_usd / CRYPTO_RATES[coin]
            exact_paid = f"{crypto_amt:.5f} {coin} (~${total_usd})"
            actual_received = crypto_amt; payout_dest = coin; method = f"Crypto ({coin})"
            payout_delay = 5

        fee = round(actual_received * 0.029, 2) if "Credit" in method else 0
        
        order_data = {
            "oid": oid, "platform": platform, "prod": prod, "type": ptype, 
            "duration": duration, "qty": qty, "price": total_usd, "fee": fee, "method": method,
            "exact_paid": exact_paid, "actual_received": actual_received, "wallet_dest": payout_dest,
            "full_contact": full_contact, "masked_contact": masked_contact, "contact_type": contact_type,
            "promo": promo_str, "payout_cleared": False, "created_at": datetime.now().isoformat()
        }
        
        if random.random() > 0.15: 
            payouts = load_data(PAYOUTS_FILE)
            payouts.append({"oid": oid, "amount": actual_received - fee, "dest": payout_dest, "trigger_at": (datetime.now() + timedelta(minutes=payout_delay)).isoformat()})
            save_data(PAYOUTS_FILE, payouts)
        
        embed_color = 0xFFD700 if is_bulk else (0x00FF00 if ptype != "Account" else 0xf1c40f)
        embed = discord.Embed(title="📦 MASSIVE BULK ORDER!" if is_bulk else "🛒 New Order Received!", color=embed_color)
        embed.add_field(name="🌐 Platform", value=platform, inline=True)
        embed.add_field(name="🏷️ Order ID", value=oid, inline=True)
        embed.add_field(name="📦 Product", value=f"{qty}x **{prod}**\n{ptype} ({duration})", inline=False)
        embed.add_field(name="💳 Paid Amount", value=f"`{exact_paid}`", inline=True)
        embed.add_field(name=f"👤 Client ({contact_type})", value=f"`{masked_contact}`\n{vip_tag}", inline=True)

        if ptype == "Account":
            order_data["status"] = "PENDING_APPROVAL"
            pending = load_data(PENDING_APPROVAL_FILE)
            pending.append(order_data)
            save_data(PENDING_APPROVAL_FILE, pending)
            embed.add_field(name="📌 Action Required", value=f"Awaiting your approval to assign {qty} account(s).", inline=False)
            await log_chan.send(embed=embed, view=ManualDeliveryView(oid, prod, duration, qty))
        else:
            items = []
            for _ in range(qty): items.append(inv[prod][ptype][duration].pop(0))
            save_data(INVENTORY_FILE, inv)
            
            order_data["status"] = "DELIVERED"
            order_data["delivered_at"] = datetime.now().isoformat()
            order_data["item_data"] = "\n".join(items)
            
            sales_db.append(order_data)
            save_data(SALES_FILE, sales_db)
            
            embed.set_footer(text="Auto-Delivered instantly to client.")
            await log_chan.send(embed=embed, view=RevealDataView(oid))

        if random.random() < 0.40:
            events = load_data(PENDING_EVENTS_FILE)
            events.append({"oid": oid, "type": "Account" if ptype == "Account" else "Link/Key Invalid", "trigger_at": (datetime.now() + timedelta(minutes=random.randint(60, 180))).isoformat()})
            save_data(PENDING_EVENTS_FILE, events)

@tasks.loop(minutes=5)
async def daily_report():
    config = load_data(CONFIG_FILE)
    last_rep_str = config.get("last_report")
    if not last_rep_str: last_rep_str = datetime.now().isoformat()
    last_rep = datetime.fromisoformat(last_rep_str)
    
    if (datetime.now() - last_rep).total_seconds() >= 86400:
        log_chan = bot.get_channel(LOG_CHANNEL_ID)
        if log_chan:
            sales = load_data(SALES_FILE)
            daily_sales = [s for s in sales if (datetime.now() - datetime.fromisoformat(s["created_at"])).total_seconds() <= 86400 and s.get("status") != "REFUNDED"]
            rev = sum(s.get("price", 0) for s in daily_sales)
            embed = discord.Embed(title="📈 Daily Automated Report", color=0x2ecc71)
            embed.add_field(name="Orders Completed", value=f"`{len(daily_sales)}`", inline=True)
            embed.add_field(name="Gross Revenue", value=f"`${rev:.2f}`", inline=True)
            await log_chan.send(embed=embed)
        config["last_report"] = datetime.now().isoformat()
        save_data(CONFIG_FILE, config)

@tasks.loop(minutes=2)
async def process_payouts():
    payouts, sales, pending = load_data(PAYOUTS_FILE), load_data(SALES_FILE), load_data(PENDING_APPROVAL_FILE)
    bals, config = load_data(BALANCES_FILE), load_data(CONFIG_FILE)
    payout_chan_id = config.get("payout_channel")
    payout_chan = bot.get_channel(payout_chan_id) if payout_chan_id else None
    remaining = []
    
    now = datetime.now()
    for p in payouts:
        if now >= datetime.fromisoformat(p["trigger_at"]):
            for lst in [sales, pending]:
                for o in lst:
                    if o["oid"] == p["oid"]: o["payout_cleared"] = True
            
            if p["dest"] in bals: bals[p["dest"]] += p["amount"]
                
            if payout_chan:
                symbol = "" if "Bank" in p["dest"] else "🪙"
                embed = discord.Embed(title="💸 Payment Arrived!", color=0x2ecc71)
                embed.add_field(name="🏷️ Order ID", value=p["oid"], inline=True)
                embed.add_field(name="💰 Amount", value=f"`{p['amount']}`", inline=True)
                embed.add_field(name="🏦 Wallet/Bank", value=f"{symbol} `{p['dest']}`", inline=False)
                await payout_chan.send(embed=embed)
        else:
            remaining.append(p)
            
    save_data(PAYOUTS_FILE, remaining); save_data(SALES_FILE, sales); save_data(PENDING_APPROVAL_FILE, pending); save_data(BALANCES_FILE, bals)

@tasks.loop(minutes=5)
async def process_delayed_events():
    ticket_chan = bot.get_channel(TICKET_CHANNEL_ID)
    if not ticket_chan: return
    
    events, sales = load_data(PENDING_EVENTS_FILE), load_data(SALES_FILE)
    remaining = []
    now = datetime.now()
    for e in events:
        if now >= datetime.fromisoformat(e["trigger_at"]):
            order = next((s for s in sales if s["oid"] == e["oid"]), None)
            if order and order.get("status") == "DELIVERED":
                days_used = (now - datetime.fromisoformat(order["delivered_at"])).days
                rem_days = max(1, (30 if order["duration"] == "1 Month" else 365) - days_used)
                embed = discord.Embed(title="🚨 Client Dispute", color=0xe74c3c)
                embed.add_field(name="🏷️ Order", value=order["oid"], inline=True)
                embed.add_field(name="⚠️ Issue", value="Account stopped working" if order["type"] == "Account" else "Link/Key Invalid", inline=False)
                await ticket_chan.send(embed=embed, view=DisputeActionView(order["oid"], order["prod"], order["duration"], order["type"]))
        else: remaining.append(e)
    save_data(PENDING_EVENTS_FILE, remaining)

@bot.event
async def on_ready():
    print(f"AFK Cafe Bot Ready as {bot.user.name}")
    if not burst_sales.is_running(): burst_sales.start()
    if not process_payouts.is_running(): process_payouts.start()
    if not process_delayed_events.is_running(): process_delayed_events.start()
    if not daily_report.is_running(): daily_report.start()
    if not update_bot_status.is_running(): update_bot_status.start()

app = Flask(__name__)
@app.route('/')
def home(): return "Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run).start()

bot.run(TOKEN)
