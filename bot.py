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

TOKEN = "MTU0MjY1MDY0MjI1NzE1NDE1OQ.GDNe66.-WTaZjCUcpax1LFuPEBdHwvUR9Wz8J7VO9x5BE"

LOG_CHANNEL_ID = 1542647789685710848      
TICKET_CHANNEL_ID = 1542650866987835484   
STOCK_CHANNEL_ID = 1542650898432524378    
AUTHORIZED_USERS = [1296895463097897015] 

PLATFORMS = ['Salla', 'Zid', 'Telegram', 'Eldorado.gg', 'G2G.com']
MY_WALLETS = {"USDT (TRC20)": 0.0, "BTC": 0.0, "LTC": 0.0, "Bank Account (SAR)": 0.0}

CRYPTO_RATES = {"USDT (TRC20)": 1.0, "BTC": 64000.0, "LTC": 85.0}

PRICES = {
    "ChatGPT Plus": {"Account": {"1 Month": 10.0, "1 Year": 90.0}, "Activation Link": {"1 Month": 12.0, "1 Year": 110.0}, "Gift Card": {"1 Month": 15.0, "1 Year": 150.0}},
    "Claude Pro": {"Account": {"1 Month": 18.0, "1 Year": 160.0}, "Activation Link": {"1 Month": 22.0, "1 Year": 200.0}, "Gift Card": {"1 Month": 25.0, "1 Year": 240.0}}
}

INVENTORY_FILE = 'master_inventory.json'
SALES_FILE = 'master_sales.json'
PENDING_APPROVAL_FILE = 'pending_approval.json'
PENDING_EVENTS_FILE = 'pending_events.json'
PAYOUTS_FILE = 'pending_payouts.json'
BALANCES_FILE = 'balances.json'
CONFIG_FILE = 'bot_config.json'

def init_db():
    if not os.path.exists(INVENTORY_FILE):
        inv = {}
        for prod, types in PRICES.items():
            inv[prod] = {}
            for t, durations in types.items():
                inv[prod][t] = {}
                for dur in durations:
                    if t == "Account":
                        inv[prod][t][dur] = [{"id": f"ACC-{random.randint(1000,9999)}", "created_at": datetime.now().isoformat()} for _ in range(80)]
                    else:
                        inv[prod][t][dur] = 80
        with open(INVENTORY_FILE, 'w') as f: json.dump(inv, f, indent=4)
        
    if not os.path.exists(BALANCES_FILE):
        with open(BALANCES_FILE, 'w') as f: json.dump(MY_WALLETS, f, indent=4)

    for file in [SALES_FILE, PENDING_APPROVAL_FILE, PENDING_EVENTS_FILE, PAYOUTS_FILE, CONFIG_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f: json.dump({} if file == CONFIG_FILE else [], f)

init_db()

def load_data(file):
    with open(file, 'r') as f: return json.load(f)

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

def is_authorized(user_id): return user_id in AUTHORIZED_USERS

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

# --- واجهات التسليم وإظهار البيانات ---

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
    def __init__(self, order_id, prod, duration):
        self.order_id = order_id
        self.prod = prod
        self.duration = duration
        
        inv = load_data(INVENTORY_FILE)
        accounts = inv.get(prod, {}).get("Account", {}).get(duration, [])
        options = []
        
        total_days = 30 if duration == "1 Month" else 365
        now = datetime.now()
        
        for acc in accounts[:25]:
            created = datetime.fromisoformat(acc["created_at"])
            rem = max(1, total_days - (now - created).days)
            options.append(discord.SelectOption(label=f"ID: {acc['id']}", description=f"{rem} Days Remaining", value=acc['id']))
            
        if not options:
            options.append(discord.SelectOption(label="Out of Stock", value="empty"))
            
        super().__init__(placeholder="Select an account to deliver...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "empty": return await interaction.response.send_message("❌ Stock is empty.", ephemeral=True)
        
        pending = load_data(PENDING_APPROVAL_FILE)
        order = next((o for o in pending if o["oid"] == self.order_id), None)
        if not order: return await interaction.response.send_message("❌ Order not found.", ephemeral=True)
        
        inv = load_data(INVENTORY_FILE)
        accounts = inv[self.prod]["Account"][self.duration]
        selected_acc = next((a for a in accounts if a["id"] == self.values[0]), None)
        
        if selected_acc:
            accounts.remove(selected_acc)
            save_data(INVENTORY_FILE, inv)
            pwd = ''.join(random.choices(string.ascii_letters, k=8)) + "!9"
            acc_details = f"{selected_acc['id']}:{pwd}"
            
            sales = load_data(SALES_FILE)
            order["status"] = "DELIVERED"
            order["item_data"] = f"{order['full_contact']} -> {acc_details}"
            order["delivered_at"] = datetime.now().isoformat()
            sales.append(order)
            save_data(SALES_FILE, sales)
            
            pending = [o for o in pending if o["oid"] != self.order_id]
            save_data(PENDING_APPROVAL_FILE, pending)
            
            await interaction.response.send_message(f"✅ **Account {selected_acc['id']} Delivered!**", ephemeral=True)
            self.view.stop_view()
            await interaction.message.edit(content="✅ Order fulfilled.", view=None, embed=interaction.message.embeds[0])

class AccountSelectView(View):
    def __init__(self, order_id, prod, duration):
        super().__init__(timeout=None)
        self.add_item(AccountSelectDropdown(order_id, prod, duration))
        
    def stop_view(self):
        for child in self.children: child.disabled = True

class ManualDeliveryView(View):
    def __init__(self, order_id, prod, duration):
        super().__init__(timeout=None)
        self.order_id = order_id
        self.prod = prod
        self.duration = duration

    @discord.ui.button(label="📦 Choose Account & Deliver", style=discord.ButtonStyle.primary)
    async def deliver_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        view = AccountSelectView(self.order_id, self.prod, self.duration)
        await interaction.response.send_message("Select which account to give to the client:", view=view, ephemeral=True)
        button.disabled = True
        await interaction.message.edit(view=self)

# --- نظام إدارة المخزون المتقدم ---
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
                    if t == "Account":
                        inv[p][t][dur].extend([{"id": f"ACC-{random.randint(1000,9999)}", "created_at": datetime.now().isoformat()} for _ in range(amt)])
                    else: inv[p][t][dur] += amt
        save_data(INVENTORY_FILE, inv)
        await interaction.response.send_message(f"✅ Stock added successfully.", ephemeral=True)

class StockSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=p, value=p) for p in load_data(INVENTORY_FILE).keys()]
        super().__init__(placeholder="Select product to restock...", min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RestockModal(prod_name=self.values[0]))

class AdvancedStockView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StockSelect())
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

    @discord.ui.button(label="⚙️ Manage Stock", style=discord.ButtonStyle.green)
    async def stock_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        await interaction.response.send_message("Select a product to restock:", view=AdvancedStockView(), ephemeral=True)

# --- نظام الشكاوى (Disputes & Refunds) ---
class DisputeActionView(View):
    def __init__(self, order_id, remaining_days, prod, duration, issue_type):
        super().__init__(timeout=None)
        self.order_id = order_id
        self.remaining_days = remaining_days
        self.prod = prod
        self.duration = duration
        self.issue_type = issue_type

    @discord.ui.button(label="🔄 Replace from Stock", style=discord.ButtonStyle.green)
    async def replace_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        if "Account" not in self.issue_type:
            await interaction.response.send_message(f"✅ Sent new Link/Key.", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Replacement sent! Valid for roughly **{self.remaining_days} days**.", ephemeral=True)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="💸 Refund", style=discord.ButtonStyle.blurple)
    async def refund_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        sales = load_data(SALES_FILE)
        order = next((s for s in sales if s["oid"] == self.order_id), None)
        if not order or order.get("status") == "REFUNDED": return await interaction.response.send_message("❌ Invalid or already refunded.", ephemeral=True)
        
        dest = order["wallet_dest"]
        amt = order["actual_received"]
        
        if order.get("payout_cleared"):
            bals = load_data(BALANCES_FILE)
            if dest in bals: bals[dest] -= amt
            save_data(BALANCES_FILE, bals)
            msg = f"✅ Refunded! Deducted `{amt}` from `{dest}`."
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

# --- الأوامر الرئيسية ---
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
    embed.add_field(name="`!order [ID]`", value="Full unmasked details + payment status.", inline=False)
    embed.add_field(name="`!wallets`", value="Check current funds in Bank & Crypto.", inline=False)
    embed.add_field(name="`!forcepay [ID]`", value="Manually clear a stuck payment.", inline=False)
    embed.add_field(name="`!check [Product]`", value="Check specific inventory stock.", inline=False)
    embed.add_field(name="`!setpayout [Room ID]`", value="Set the room for payment arrival alerts.", inline=False)
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
    embed.add_field(name=f"👤 Client ({order['contact_type']})", value=f"`{order['full_contact']}`", inline=True)
    embed.add_field(name="🛒 Item", value=f"{order['prod']} ({order['type']}) - {order['duration']}", inline=False)
    
    embed.add_field(name="💰 Exact Paid Amount", value=f"`{order['exact_paid']}`", inline=True)
    payout_status = "✅ Arrived in Wallet" if order.get("payout_cleared") else "⚠️ Unconfirmed / Pending"
    embed.add_field(name="💸 Payment Route", value=f"{order['method']} \n{payout_status}", inline=False)
    
    embed.add_field(name="📌 Status", value=f"`{order['status']}`", inline=True)
    
    if order['status'] == 'DELIVERED':
        del_time = datetime.fromisoformat(order['delivered_at'])
        days_active = (datetime.now() - del_time).days
        embed.add_field(name="⏱️ Days Active", value=f"`{days_active} Days`", inline=True)
        embed.add_field(name="🔑 Unmasked Data", value=f"```\n{order['item_data']}\n```", inline=False)
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

@bot.command(name="check")
async def check_stock_item(ctx, *, product_name: str):
    if not is_authorized(ctx.author.id): return
    inv = load_data(INVENTORY_FILE)
    found = next((p for p in inv.keys() if p.lower() == product_name.lower()), None)
    if not found: return await ctx.send("❌ Product not found.")
    embed = discord.Embed(title=f"📦 Stock Check: {found}", color=0x3498db)
    for ptype, durations in inv[found].items():
        for dur, qty in durations.items():
            count = len(qty) if isinstance(qty, list) else qty
            embed.add_field(name=f"🔘 {ptype} ({dur})", value=f"`{count}` units", inline=True)
    await ctx.send(embed=embed)

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

# --- العمليات التلقائية (Tasks) ---
@tasks.loop(minutes=2)
async def update_bot_status():
    sales = load_data(SALES_FILE)
    valid_orders = len([s for s in sales if s.get("status") != "REFUNDED"])
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"I love M | Serving {valid_orders} Clients"))

@tasks.loop(minutes=10)
async def background_sales():
    if random.random() < 0.70: return 
    log_chan = bot.get_channel(LOG_CHANNEL_ID)
    if not log_chan: return
    
    platform = random.choice(PLATFORMS)
    prod = random.choice(list(PRICES.keys()))
    ptype = random.choice(["Account", "Activation Link", "Gift Card"])
    duration = random.choice(["1 Month", "1 Year"])
    price_usd = PRICES[prod][ptype][duration]
    
    inv = load_data(INVENTORY_FILE)
    remaining = len(inv[prod][ptype][duration]) if ptype == "Account" else inv[prod][ptype][duration]
    
    if remaining <= 0:
        msg = f"<@{AUTHORIZED_USERS[0]}> 🚨 **OUT OF STOCK!** {prod} ({ptype} - {duration}) is empty!"
        await log_chan.send(msg); return
    elif remaining == 10:
        await log_chan.send(f"<@{AUTHORIZED_USERS[0]}> ⚠️ **Low Stock Alert:** Only 10 left for {prod} ({ptype} - {duration})!")
        
    promo_str = "None"
    if random.random() < 0.20:
        price_usd = round(price_usd * 0.90, 2); promo_str = random.choice(["SALE10", "WELCOME10"])
        
    oid = generate_order_id(platform)
    full_contact, masked_contact, contact_type = generate_contact_info()

    method = random.choices(["Credit Card", "Bank Transfer", "Crypto"], weights=[40, 30, 30])[0]
    payout_delay = 0
    payout_dest = ""
    exact_paid = ""
    actual_received = 0.0
    
    if method in ["Credit Card", "Bank Transfer"]:
        currency = random.choice(["SAR", "AED", "USD"])
        if currency == "SAR": paid_amt = price_usd * 3.75; symbol = "SAR"
        elif currency == "AED": paid_amt = price_usd * 3.67; symbol = "AED"
        else: paid_amt = price_usd; symbol = "$"
        exact_paid = f"{paid_amt:.2f} {symbol}"
        
        actual_received = price_usd * 3.75 
        payout_dest = "Bank Account (SAR)"
        payout_delay = 12 * 60 if method == "Credit Card" else 4 * 60
    else:
        coin = random.choice(["USDT (TRC20)", "BTC", "LTC"])
        crypto_amt = price_usd / CRYPTO_RATES[coin]
        exact_paid = f"{crypto_amt:.5f} {coin} (~${price_usd})"
        actual_received = crypto_amt
        payout_dest = coin
        method = f"Crypto ({coin})"
        payout_delay = 5

    fee = round(actual_received * 0.029, 2) if "Credit" in method else 0
    is_stuck = random.random() < 0.15 
    
    order_data = {
        "oid": oid, "platform": platform, "prod": prod, "type": ptype, 
        "duration": duration, "price": price_usd, "fee": fee, "method": method,
        "exact_paid": exact_paid, "actual_received": actual_received, "wallet_dest": payout_dest,
        "full_contact": full_contact, "masked_contact": masked_contact, "contact_type": contact_type,
        "promo": promo_str, "payout_cleared": False, "created_at": datetime.now().isoformat()
    }
    
    if not is_stuck:
        payouts = load_data(PAYOUTS_FILE)
        payouts.append({"oid": oid, "amount": actual_received - fee, "dest": payout_dest, "trigger_at": (datetime.now() + timedelta(minutes=payout_delay)).isoformat()})
        save_data(PAYOUTS_FILE, payouts)
    
    embed = discord.Embed(title="🛒 New Order Received!", color=0x00FF00 if ptype != "Account" else 0xf1c40f)
    embed.add_field(name="🌐 Platform", value=platform, inline=True)
    embed.add_field(name="🏷️ Order ID", value=oid, inline=True)
    embed.add_field(name="📦 Product", value=f"**{prod}**\n{ptype} ({duration})", inline=False)
    embed.add_field(name="💳 Paid Amount", value=f"`{exact_paid}`", inline=True)
    embed.add_field(name=f"👤 Client ({contact_type})", value=f"`{masked_contact}`", inline=True)

    if ptype == "Account":
        order_data["status"] = "PENDING_APPROVAL"
        pending = load_data(PENDING_APPROVAL_FILE)
        pending.append(order_data)
        save_data(PENDING_APPROVAL_FILE, pending)
        embed.add_field(name="📌 Action Required", value="Awaiting your approval to assign an account.", inline=False)
        await log_chan.send(embed=embed, view=ManualDeliveryView(oid, prod, duration))
    else:
        inv[prod][ptype][duration] -= 1
        save_data(INVENTORY_FILE, inv)
        
        order_data["status"] = "DELIVERED"
        order_data["delivered_at"] = datetime.now().isoformat()
        secret_data = f"https://activate.com/{oid}" if ptype == "Activation Link" else f"GIFT-{random.randint(1000,9999)}"
        order_data["item_data"] = secret_data
        
        sales = load_data(SALES_FILE)
        sales.append(order_data)
        save_data(SALES_FILE, sales)
        
        embed.set_footer(text="Auto-Delivered instantly to client.")
        await log_chan.send(embed=embed, view=RevealDataView(oid))

    if random.random() < 0.40:
        events = load_data(PENDING_EVENTS_FILE)
        events.append({"oid": oid, "type": "Dispute", "trigger_at": (datetime.now() + timedelta(minutes=random.randint(60, 180))).isoformat()})
        save_data(PENDING_EVENTS_FILE, events)

@tasks.loop(minutes=2)
async def process_payouts():
    payouts, sales, pending = load_data(PAYOUTS_FILE), load_data(SALES_FILE), load_data(PENDING_APPROVAL_FILE)
    bals = load_data(BALANCES_FILE)
    config = load_data(CONFIG_FILE)
    payout_chan_id = config.get("payout_channel")
    payout_chan = bot.get_channel(payout_chan_id) if payout_chan_id else None
    remaining = []
    
    now = datetime.now()
    for p in payouts:
        if now >= datetime.fromisoformat(p["trigger_at"]):
            for lst in [sales, pending]:
                for o in lst:
                    if o["oid"] == p["oid"]: o["payout_cleared"] = True
            
            if p["dest"] in bals: 
                bals[p["dest"]] += p["amount"]
                
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
                del_time = datetime.fromisoformat(order["delivered_at"])
                days_used = (now - del_time).days
                total_days = 30 if order["duration"] == "1 Month" else 365
                rem_days = max(1, total_days - days_used)
                
                issue_type = "Account stopped working" if order["type"] == "Account" else "Link/Key Invalid"
                embed = discord.Embed(title="🚨 Client Dispute", color=0xe74c3c)
                embed.add_field(name="🏷️ Order", value=order["oid"], inline=True)
                embed.add_field(name="⏱️ Age", value=f"{days_used} Days Used", inline=True)
                embed.add_field(name="⚠️ Issue", value=issue_type, inline=False)
                await ticket_chan.send(embed=embed, view=DisputeActionView(order["oid"], rem_days, order["prod"], order["duration"], order["type"]))
        else:
            remaining.append(e)
    save_data(PENDING_EVENTS_FILE, remaining)

@bot.event
async def on_ready():
    print(f"AFK Cafe Bot Ready as {bot.user.name}")
    if not background_sales.is_running(): background_sales.start()
    if not process_payouts.is_running(): process_payouts.start()
    if not process_delayed_events.is_running(): process_delayed_events.start()
    if not update_bot_status.is_running(): update_bot_status.start()

app = Flask(__name__)
@app.route('/')
def home(): return "Online"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run).start()

bot.run(TOKEN)
