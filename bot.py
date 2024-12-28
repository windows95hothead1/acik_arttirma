import discord
from discord.ext import commands, tasks
from logic import DatabaseManager, hide_img
from config import TOKEN, DATABASE
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

manager = DatabaseManager(DATABASE)
manager.create_tables()

# A command for user registration
@bot.command()
async def start(ctx):
    user_id = ctx.author.id
    if user_id in manager.get_users():
        await ctx.send("You are registered already!")
    else:
        manager.add_user(user_id, ctx.author.name)
        await ctx.send("""Hi! Welcome! You have been successfully registered! You'll be receiving new images every minute, and you'll have a chance to get them! To do this, you need to click on the 'Get!' button! Only the first three users to click the 'Get!' button will get the picture! =)""")

# A scheduled task for sending images
@tasks.loop(minutes=1)
async def send_message():
    for user_id in manager.get_users():
        prize_id, img = manager.get_random_prize()[:2]
        hide_img(img)
        user = await bot.fetch_user(user_id) 
        if user:
            await send_image(user, f'hidden_img/{img}', prize_id)
        manager.mark_prize_used(prize_id)

async def send_image(user, image_path, prize_id):
    with open(image_path, 'rb') as img:
        file = discord.File(img)
        button = discord.ui.Button(label="Get!", custom_id=str(prize_id))
        view = discord.ui.View()
        view.add_item(button)
        await user.send(file=file, view=view)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data['custom_id']
        user_id = interaction.user.id
        img = manager.get_prize_img(custom_id)
        if manager.add_winner(user_id, custom_id):
            with open(f'img/{img}', 'rb') as photo:
                file = discord.File(photo)
                await interaction.response.send_message(file=file, content="Congratulations, you got the image!")
        else:
            await interaction.response.send_message(content="Unfortunately, someone has already claimed this image.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    if not send_message.is_running():
        send_message.start()

bot.run(TOKEN)
