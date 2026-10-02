import os
import ast
import operator as op
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN=os.getenv("DISCORD_TOKEN")
OWNER_ID=1311295859325145159
LTC_ADDRESS="ltc1qgtam35vt6cu7qpaha5r9g6m5c9lua0kzqngzqd"
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing.")

intents = discord.Intents.default()
intents.dm_messages = True
intents.message_content = True
client = discord.Client(intents=intents)
tree=app_commands.CommandTree(
    client,
    allowed_contexts=app_commands.AppCommandContext(guild=True,dm_channel=True,private_channel=True),
    allowed_installs=app_commands.AppInstallationType(guild=True,user=True),
)

def owner_only():
    async def check(interaction):
        return interaction.user.id==OWNER_ID
    return app_commands.check(check)

OPS={ast.Add:op.add,ast.Sub:op.sub,ast.Mult:op.mul,ast.Div:op.truediv,ast.FloorDiv:op.floordiv,ast.Mod:op.mod,ast.Pow:op.pow,ast.USub:op.neg,ast.UAdd:op.pos}
def safe_calc(expression):
    if len(expression)>100: raise ValueError("Expression is too long.")
    parsed=ast.parse(expression,mode="eval")
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:
            a,b=ev(n.left),ev(n.right)
            if isinstance(n.op,ast.Pow) and abs(b)>100: raise ValueError("Exponent is too large.")
            return OPS[type(n.op)](a,b)
        if isinstance(n,ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.operand))
        raise ValueError("Only basic arithmetic is allowed.")
    r=ev(parsed)
    return int(r) if isinstance(r,float) and r.is_integer() else r

@client.event
async def on_ready():
    await tree.sync()  # Global sync, no guild argument
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Commands synced globally.")

@tree.command(name="calculate",description="Calculate a basic arithmetic expression.")
@owner_only()
@app_commands.describe(expression="Example: 1+1")
async def calculate_cmd(interaction,expression:str):
    try: await interaction.response.send_message(f"**Result:** `{safe_calc(expression)}`")
    except ZeroDivisionError: await interaction.response.send_message("❌ You cannot divide by zero.")
    except Exception as e: await interaction.response.send_message(f"❌ Invalid calculation: {e}")

@tree.command(name="upi",description="Send the UPI QR image.")
@owner_only()
async def upi(interaction):
    await interaction.response.send_message(file=discord.File(os.path.join(os.path.dirname(__file__),"upi.jpg"),filename="upi.jpg"))

@tree.command(name="ltc",description="Show the Litecoin address.")
@owner_only()
async def ltc(interaction):
    await interaction.response.send_message(f"**LTC Address:**\n`{LTC_ADDRESS}`")

@tree.error
async def command_error(interaction,error):
    msg="❌ You don't have permission to use this command." if isinstance(error,app_commands.CheckFailure) else "❌ Something went wrong."
    if not interaction.response.is_done(): await interaction.response.send_message(msg,ephemeral=True)

client.run(DISCORD_TOKEN)
