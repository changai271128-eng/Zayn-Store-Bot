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

    for file in [SALES_FILE, PENDING_APPROVAL_FILE, PENDING_EVENTS_FILE, PAYOUTS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f: json.dump([], f)

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

def get_account_from_stock(prod, duration, required_days=None):
    inv = load_data(INVENTORY_FILE)
    accounts = inv.get(prod, {}).get("Account", {}).get(duration, [])
    if not accounts: return None, inv
    
    total_days = 30 if duration == "1 Month" else 365
    now = datetime.now()
    
    selected_acc = None
    if required_days:
        best_match, min_diff = None, 999
        for acc in accounts:
            created = datetime.fromisoformat(acc["created_at"])
            rem_days = max(1, total_days - (now - created).days)
            diff = abs(rem_days - required_days)
            if diff < min_diff:
                min_diff = diff; best_match = acc
        selected_acc = best_match
    else:
        selected_acc = accounts[0]
        
    if selected_acc:
        accounts.remove(selected_acc)
        save_data(INVENTORY_FILE, inv)
        rem_days = max(1, total_days - (now - datetime.fromisoformat(selected_acc["created_at"])).days)
        pwd = ''.join(random.choices(string.ascii_letters, k=8)) + "!9"
        return f"{selected_acc['id']}:{pwd} (Remaining: {rem_days} Days)", inv
    return None, inv

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- نظام التعبئة المتقدم (Modals & Selects) ---
class RestockModal(Modal):
    def __init__(self, prod_name=None):
        title = f"Restock {prod_name}" if prod_name else "Global Restock (All Items)"
        super().__init__(title=title[:45])
        self.prod_name = prod_name
        self.amount_input = TextInput(label="Amount to Add", style=discord.TextStyle.short, placeholder="e.g. 50", required=True)
        self.add_item(self.amount_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try: amt = int(self.amount_input.value)
        except: return await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)
        
        inv = load_data(INVENTORY_FILE)
        if self.prod_name:
            for t in inv[self.prod_name]:
                for dur in inv[self.prod_name][t]:
                    if t == "Account":
                        inv[self.prod_name][t][dur].extend([{"id": f"ACC-{random.randint(1000,9999)}", "created_at": datetime.now().isoformat()} for _ in range(amt)])
                    else:
                        inv[self.prod_name][t][dur] += amt
            msg = f"✅ Added `{amt}` fresh units to all variations of **{self.prod_name}**."
        else:
            for p in inv:
                for t in inv[p]:
                    for dur in inv[p][t]:
                        if t == "Account":
                            inv[p][t][dur].extend([{"id": f"ACC-{random.randint(1000,9999)}", "created_at": datetime.now().isoformat()} for _ in range(amt)])
                        else:
                            inv[p][t][dur] += amt
            msg = f"✅ Global Restock: Added `{amt}` fresh units to **EVERYTHING**."
            
        save_data(INVENTORY_FILE, inv)
        await interaction.response.send_message(msg, ephemeral=True)

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
    
    @discord.ui.button(label="🌐 Global Restock (Custom Amount)", style=discord.ButtonStyle.blurple, row=1)
    async def global_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RestockModal(prod_name=None))

# --- بقية الواجهات والأوامر ---
class ManualDeliveryView(View):
    def __init__(self, order_id):
        super().__init__(timeout=None)
        self.order_id = order_id

    @discord.ui.button(label="📦 Select Account from Stock", style=discord.ButtonStyle.primary)
    async def deliver_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        pending = load_data(PENDING_APPROVAL_FILE)
        order = next((o for o in pending if o["oid"] == self.order_id), None)
        if not order: return await interaction.response.send_message("❌ Order not found.", ephemeral=True)
        
        acc_details, _ = get_account_from_stock(order["prod"], order["duration"])
        if not acc_details: return await interaction.response.send_message("❌ No accounts in stock!", ephemeral=True)
        
        sales = load_data(SALES_FILE)
        order["status"] = "DELIVERED"
        order["item_data"] = f"{order['full_email']} -> {acc_details}"
        order["delivered_at"] = datetime.now().isoformat()
        sales.append(order)
        save_data(SALES_FILE, sales)
        
        pending = [o for o in pending if o["oid"] != self.order_id]
        save_data(PENDING_APPROVAL_FILE, pending)
        
        button.disabled = True; button.label = "✅ Delivered"
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"✅ **Account Delivered!**\nData: `{order['item_data']}`", ephemeral=True)

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
            await interaction.response.send_message(f"✅ Sent new Link/Key for {self.prod}", ephemeral=True)
        else:
            acc_details, _ = get_account_from_stock(self.prod, self.duration, self.remaining_days)
            if not acc_details: return await interaction.response.send_message("❌ No suitable accounts left in stock.", ephemeral=True)
            await interaction.response.send_message(f"✅ Replacement sent! Valid for roughly **{self.remaining_days} days**.\nData: `{acc_details}`", ephemeral=True)
            
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="💸 Refund", style=discord.ButtonStyle.blurple)
    async def refund_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        
        sales = load_data(SALES_FILE)
        order = next((s for s in sales if s["oid"] == self.order_id), None)
        if not order: return await interaction.response.send_message("❌ Order not found.", ephemeral=True)
        if order.get("status") == "REFUNDED": return await interaction.response.send_message("⚠️ Already refunded.", ephemeral=True)
        
        amount = order["price"] - order.get("fee", 0)
        dest = "Bank Account (SAR)" if "Credit" in order["method"] or "Bank" in order["method"] else order["method"].replace("Crypto (", "").replace(")", "")
        deducted_amt = amount * 3.75 if "Bank" in dest else amount
        
        if order.get("payout_cleared"):
            bals = load_data(BALANCES_FILE)
            if dest in bals: bals[dest] -= deducted_amt
            save_data(BALANCES_FILE, bals)
            msg = f"✅ Refund issued! Deducted `{deducted_amt:.2f}` from `{dest}`."
        else:
            payouts = [p for p in load_data(PAYOUTS_FILE) if p["oid"] != self.order_id]
            save_data(PAYOUTS_FILE, payouts)
            msg = f"✅ Refund issued! Payment was still pending, cancelled arrival to `{dest}`."
            
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

class StorePanelView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="📊 View Stats", style=discord.ButtonStyle.blurple)
    async def stats_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        sales = load_data(SALES_FILE)
        valid = [s for s in sales if s.get("status") != "REFUNDED"]
        rev = sum(s.get("price", 0) for s in valid)
        net = rev - sum(s.get("fee", 0) for s in valid)
        await interaction.response.send_message(f"📊 **Live Stats:**\n- Valid Orders: `{len(valid)}`\n- Refunds: `{len(sales)-len(valid)}`\n- Gross: `${rev:.2f}`\n- Net: `${net:.2f}`", ephemeral=True)

    @discord.ui.button(label="⚙️ Manage Stock (Advanced)", style=discord.ButtonStyle.green)
    async def stock_btn(self, interaction: discord.Interaction, button: Button):
        if not is_authorized(interaction.user.id): return
        await interaction.response.send_message("Select a product to restock or use Global:", view=AdvancedStockView(), ephemeral=True)

@bot.command(name="panel")
async def panel_cmd(ctx):
    if not is_authorized(ctx.author.id): return
    embed = discord.Embed(title="⚙️ Store Dashboard", color=0x00FF00)
    await ctx.send(embed=embed, view=StorePanelView())

@bot.command(name="wallets")
async def check_wallets(ctx):
    if not is_authorized(ctx.author.id): return
    bals = load_data(BALANCES_FILE)
    embed = discord.Embed(title="💼 AFK Cafe Finances", color=0xf1c40f)
    embed.add_field(name="🏦 Bank Account", value=f"`{bals['Bank Account (SAR)']:.2f} SAR`", inline=False)
    embed.add_field(name="🪙 USDT", value=f"`${bals['USDT (TRC20)']:.2f}`", inline=True)
    embed.add_field(name="🪙 BTC", value=f"`${bals['BTC']:.2f}`", inline=True)
    embed.add_field(name="🪙 LTC", value=f"`${bals['LTC']:.2f}`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="forcepay")
async def force_pay(ctx, order_id: str):
    if not is_authorized(ctx.author.id): return
    sales, pending = load_data(SALES_FILE), load_data(PENDING_APPROVAL_FILE)
    order = next((s for s in sales + pending if s["oid"] == order_id), None)
    if not order: return await ctx.send("❌ Order not found.")
    
    if order.get("payout_cleared"): return await ctx.send("⚠️ Payment was already cleared for this order.")
    
    order["payout_cleared"] = True
    save_data(SALES_FILE, sales); save_data(PENDING_APPROVAL_FILE, pending)
    
    dest = "Bank Account (SAR)" if "Credit" in order["method"] or "Bank" in order["method"] else order["method"].replace("Crypto (", "").replace(")", "")
    amount = order["price"] - order.get("fee", 0)
    if "Bank" in dest: amount *= 3.75 
    
    bals = load_data(BALANCES_FILE)
    if dest in bals: bals[dest] += amount
    save_data(BALANCES_FILE, bals)
    
    await ctx.send(f"✅ **Forced Payment!** Added `{amount:.2f}` to `{dest}` wallet.")

@bot.command(name="system")
async def system_menu(ctx):
    if not is_authorized(ctx.author.id): return
    embed = discord.Embed(title="⚙️ AFK Cafe | System Menu", color=0x2b2d31)
    embed.add_field(name="`!order [ID]`", value="Full unmasked details + payment status.", inline=False)
    embed.add_field(name="`!wallets`", value="Check current funds in Bank & Crypto.", inline=False)
    embed.add_field(name="`!forcepay [ID]`", value="Manually clear a stuck payment.", inline=False)
    embed.add_field(name="`!check [Product]`", value="Check specific inventory stock.", inline=False)
    embed.add_field(name="`!stock_chats`", value="View active delivered accounts & aging.", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="order")
async def check_order(ctx, order_id: str):
    if not is_authorized(ctx.author.id): return
    sales, pending = load_data(SALES_FILE), load_data(PENDING_APPROVAL_FILE)
    order = next((s for s in sales + pending if s["oid"] == order_id), None)
    if not order: return await ctx.send(f"❌ Order `{order_id}` not found.")
    
    embed = discord.Embed(title=f"🧾 Order: {order['oid']} ({order['platform']})", color=0x3498db)
    embed.add_field(name="📧 Client", value=f"`{order['full_email']}`", inline=True)
    embed.add_field(name="🛒 Item", value=f"{order['prod']} ({order['type']}) - {order['duration']}", inline=False)
    embed.add_field(name="💰 Paid", value=f"${order['price']} (Promo: {order.get('promo', 'None')})", inline=True)
    
    payout_status = "✅ Arrived in Wallet" if order.get("payout_cleared") else "⚠️ Unconfirmed / Pending"
    embed.add_field(name="💸 Payment Status", value=f"{order['method']} - {payout_status}", inline=False)
    embed.add_field(name="📌 Status", value=f"`{order['status']}`", inline=True)
    
    if order['status'] == 'DELIVERED':
        del_time = datetime.fromisoformat(order['delivered_at'])
        days_active = (datetime.now() - del_time).days
        embed.add_field(name="⏱️ Days Active", value=f"`{days_active} Days`", inline=True)
        embed.add_field(name="🔑 Data", value=f"```\n{order['item_data']}\n```", inline=False)
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
        embed.add_field(name=f"Order {acc['oid']} - {acc['prod']}", value=f"👤 Client: `{acc['masked_email']}`\n⏳ Active: `{days} Days`", inline=False)
    await ctx.send(embed=embed)

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

# --- المهام الخلفية المحدثة ---
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
    price = PRICES[prod][ptype][duration]
    
    # التحقق من توفر المخزون قبل أي شيء وإرسال التنبيهات
    inv = load_data(INVENTORY_FILE)
    remaining = len(inv[prod][ptype][duration]) if ptype == "Account" else inv[prod][ptype][duration]
    
    if remaining <= 0:
        msg = f"<@{AUTHORIZED_USERS[0]}> 🚨🚨 **OUT OF STOCK!** {prod} ({ptype} - {duration}) is empty! Restock NOW!"
        await log_chan.send(msg); await log_chan.send(msg); await log_chan.send(msg)
        return
    elif remaining == 10:
        await log_chan.send(f"<@{AUTHORIZED_USERS[0]}> ⚠️ **Low Stock Alert:** Only 10 left for {prod} ({ptype} - {duration})!")
        
    promo_str = "None"
    if random.random() < 0.20:
        price = round(price * 0.90, 2); promo_str = random.choice(["SALE10", "WELCOME10"])
        
    oid = generate_order_id(platform)
    names = ['ahmed', 'mohamed', 'james', 'omar', 'khaled']
    full_email = f"{random.choice(names)}.{random.choice(names)}{random.randint(10,99)}@gmail.com"
    masked_email = f"{full_email[:3]}***@gmail.com"

    method = random.choices(["Credit Card", "Crypto", "Bank Transfer"], weights=[50, 30, 20])[0]
    fee, payout_delay, payout_dest = 0, 0, ""
    
    if method == "Credit Card":
        fee = round((price * 0.029) + 0.30, 2)
        payout_delay, payout_dest = 12 * 60, "Bank Account (SAR)"
    elif method == "Crypto":
        coin = random.choice(["USDT (TRC20)", "BTC", "LTC"])
        payout_delay, payout_dest, method = 5, coin, f"Crypto ({coin})"
    elif method == "Bank Transfer":
        payout_delay, payout_dest = 4 * 60, "Bank Account (SAR)"

    is_stuck = random.random() < 0.15 
    
    order_data = {
        "oid": oid, "platform": platform, "prod": prod, "type": ptype, 
        "duration": duration, "price": price, "fee": fee, "method": method,
        "full_email": full_email, "masked_email": masked_email, "promo": promo_str,
        "payout_cleared": False, "created_at": datetime.now().isoformat()
    }
    
    if not is_stuck:
        payouts = load_data(PAYOUTS_FILE)
        payouts.append({"oid": oid, "amount": price - fee, "method": method, "dest": payout_dest, "trigger_at": (datetime.now() + timedelta(minutes=payout_delay)).isoformat()})
        save_data(PAYOUTS_FILE, payouts)
    
    if ptype == "Account":
        order_data["status"] = "PENDING_APPROVAL"
        pending = load_data(PENDING_APPROVAL_FILE)
        pending.append(order_data)
        save_data(PENDING_APPROVAL_FILE, pending)
        embed = discord.Embed(title="⏳ New Account Order", color=0xf1c40f)
        embed.add_field(name="🏷️ ID", value=oid, inline=True)
        embed.add_field(name="🛒 Item", value=f"{prod} ({duration})", inline=True)
        await log_chan.send(embed=embed, view=ManualDeliveryView(oid))
    else:
        inv[prod][ptype][duration] -= 1
        save_data(INVENTORY_FILE, inv)
        
        order_data["status"] = "DELIVERED"
        order_data["delivered_at"] = datetime.now().isoformat()
        order_data["item_data"] = f"https://activate.com/{oid}" if ptype == "Activation Link" else f"GIFT-{random.randint(1000,9999)}"
        sales = load_data(SALES_FILE)
        sales.append(order_data)
        save_data(SALES_FILE, sales)
        
        embed = discord.Embed(title="⚡ Auto-Delivered Order", color=0x2ecc71)
        embed.add_field(name="🏷️ ID", value=oid, inline=True)
        embed.add_field(name="🛒 Item", value=f"{prod} ({ptype})", inline=True)
        await log_chan.send(embed=embed)

    if random.random() < 0.40:
        events = load_data(PENDING_EVENTS_FILE)
        events.append({"oid": oid, "type": "Dispute", "trigger_at": (datetime.now() + timedelta(minutes=random.randint(60, 180))).isoformat()})
        save_data(PENDING_EVENTS_FILE, events)

@tasks.loop(minutes=2)
async def process_payouts():
    payouts, sales, pending = load_data(PAYOUTS_FILE), load_data(SALES_FILE), load_data(PENDING_APPROVAL_FILE)
    bals = load_data(BALANCES_FILE)
    remaining = []
    
    now = datetime.now()
    for p in payouts:
        if now >= datetime.fromisoformat(p["trigger_at"]):
            for lst in [sales, pending]:
                for o in lst:
                    if o["oid"] == p["oid"]: o["payout_cleared"] = True
            
            amt = p["amount"] * 3.75 if "Bank" in p["dest"] else p["amount"]
            if p["dest"] in bals: bals[p["dest"]] += amt
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
