import disnake
import asyncio
import os
import json
import shutil
import stat
import subprocess
from datetime import datetime
from email.policy import default
from operator import truediv
from random import randint
from tabnanny import check
from typing import Optional
from zipapp import create_archive

from disnake import MessageInteraction, Member
from disnake.ext import commands
from disnake.ui import channel_select
from configs import *
from charlists import *

intents = disnake.Intents.default()
checker_list = open('check_data.txt', 'a')
votuum_gm_list = open('data.txt', 'a')
intents.members = True
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="%", intents=intents)

bot.active_creations = {} # {user_id: message_id}

def remove_readonly(func, path, _):
    try:
        # Пытаемся выставить права 0777 (читать/писать/выполнять всем)
        os.chmod(path, 0o777)
        func(path)
    except Exception as e:
        print(f"Критическая ошибка прав при удалении {path}: {e}")

@bot.event
async def on_raw_message_delete(payload):
    target_user_id = None
    
    # 1. Ищем, какому пользователю принадлежит удаленное сообщение
    # Проходим по всем активным сессиям
    for user_id, data in bot.active_creations.items():
        if data.get("msg_id") == payload.message_id:
            target_user_id = user_id
            break
            
    # 2. Если нашли совпадение — проводим зачистку
    if target_user_id:
        # Извлекаем данные и удаляем запись из реестра
        session_data = bot.active_creations.pop(target_user_id)
        
        path = session_data.get("folder_path")
        
        if path and os.path.exists(path):
            try:
                # Используем нашу "умную" зачистку на случай WinError 5
                shutil.rmtree(path, onerror=remove_readonly)
                print(f"Сообщение сессии {payload.message_id} удалено. Папка {path} очищена.")
            except Exception as e:
                print(f"Ошибка при удалении папки после удаления сообщения: {e}")

def create_embed (title, description, image_url=None):
    embed = disnake.Embed(title=title, description=description, color=disnake.Color.light_gray())
    if image_url:
        embed.set_image(url=image_url)
    return embed

class LocationSelectSwamps(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Затон", value="Затон!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        

        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_swamps_role = disnake.utils.get(inter.guild.roles, name="Болота")
            await inter.user.remove_roles(location_swamps_role)

            if self.values[0] == "Затон!":
                location_zaton_role = disnake.utils.get(inter.guild.roles, name="Затон")
                await inter.user.add_roles(location_zaton_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_zaton)

                elif irradiation >= 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                                                      view=None, embed=embed_zaton)

                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_zaton)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", ephemeral=True)

class DropDownSwamps(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectSwamps(user_id))

class LocationSelectZaton(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Болота", value="Болота!"),
            disnake.SelectOption(label="— НИИЧАЗ", value="НИИЧАЗ!"),
            disnake.SelectOption(label="— Дикий Остров", value="Дикий Остров!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        

        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_zaton_role = disnake.utils.get(inter.guild.roles, name="Затон")
            await inter.user.remove_roles(location_zaton_role)

            if self.values[0] == "Болота!":
                location_swamps_role = disnake.utils.get(inter.guild.roles, name="Болота")
                await inter.user.add_roles(location_swamps_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_swamps)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_swamps)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_swamps)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_swamps)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_swamps)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_swamps)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                                                      view=None, embed=embed_swamps)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_swamps)

            elif self.values[0] == "НИИЧАЗ!":
                location_sircaa_role = disnake.utils.get(inter.guild.roles, name="НИИЧАЗ")
                await inter.user.add_roles(location_sircaa_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.", 
                        view=None, embed=embed_sircaa)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.", 
                        view=None, embed=embed_sircaa)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_sircaa)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}", embed=embed_sircaa)

            elif self.values[0] == "Дикий Остров!":
                location_wild_island_role = disnake.utils.get(inter.guild.roles, name="Дикий Остров")
                await inter.user.add_roles(location_wild_island_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.", 
                        view=None, embed=embed_wild_island)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.", 
                        view=None, embed=embed_wild_island)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_wild_island)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}", 
                                                      view=None, embed=embed_wild_island)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownZaton(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectZaton(user_id))

class LocationSelectSIRCAA(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Затон", value="Затон!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_sircaa_role = disnake.utils.get(inter.guild.roles, name="НИИЧАЗ")
            await inter.user.remove_roles(location_sircaa_role)

            if self.values[0] == "Затон!":
                location_zaton_role = disnake.utils.get(inter.guild.roles, name="Затон")
                await inter.user.add_roles(location_zaton_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_zaton)

                elif irradiation >= 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                                                      view=None, embed=embed_zaton)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_zaton)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownSIRCAA(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectSIRCAA(user_id))

class LocationSelectWildIsland(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Кордон", value="Кордон!"),
            disnake.SelectOption(label="— Свалка", value="Свалка!"),
            disnake.SelectOption(label="— Затон", value="Затон!"),
            disnake.SelectOption(label="— Малая Зона", value="Малая Зона!"),
            disnake.SelectOption(label="— Цементный завод", value="Цементный завод!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_wild_island = disnake.utils.get(inter.guild.roles, name="Дикий Остров")
            await inter.user.remove_roles(location_wild_island)

            if self.values[0] == "Кордон!":
                location_kordon_role = disnake.utils.get(inter.guild.roles, name="Кордон")
                await inter.user.add_roles(location_kordon_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.", 
                        view=None, embed=embed_kordon)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.", 
                        view=None, embed=embed_kordon)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_kordon)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}", 
                                                      view=None, embed=embed_kordon)

            elif self.values[0] == "Свалка!":
                location_garbage_role = disnake.utils.get(inter.guild.roles, name="Свалка")
                await inter.user.add_roles(location_garbage_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_garbage)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                                                      view=None, embed=embed_garbage)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_garbage)

            elif self.values[0] == "Затон!":
                location_zaton_role = disnake.utils.get(inter.guild.roles, name="Затон")
                await inter.user.add_roles(location_zaton_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_zaton)

                elif irradiation >= 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_zaton)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_zaton)

            elif self.values[0] == "Малая Зона!":
                location_lesser_zone_role = disnake.utils.get(inter.guild.roles, name="Малая Зона")
                await inter.user.add_roles(location_lesser_zone_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_lesser_zone)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_lesser_zone)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_lesser_zone)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_lesser_zone)

            elif self.values[0] == "Цементный завод!":
                location_cement_factory = disnake.utils.get(inter.guild.roles, name="Цементный завод")
                await inter.user.add_roles(location_cement_factory)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_cement_factory)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_cement_factory)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_cement_factory)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_cement_factory)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownWildIsland(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectWildIsland(user_id))

class LocationSelectKordon(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Дикий Остров", value="Дикий Остров!"),
            disnake.SelectOption(label="— Малая Зона", value="Малая Зона!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_kordon_role = disnake.utils.get(inter.guild.roles, name="Кордон")
            await inter.user.remove_roles(location_kordon_role)

            if self.values[0] == "Дикий Остров!":
                location_wild_island_role = disnake.utils.get(inter.guild.roles, name="Дикий Остров")
                await inter.user.add_roles(location_wild_island_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_wild_island)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_wild_island)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_wild_island)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_wild_island)

            elif self.values[0] == "Малая Зона!":
                location_lesser_zone_role = disnake.utils.get(inter.guild.roles, name="Малая Зона")
                await inter.user.add_roles(location_lesser_zone_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_lesser_zone)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_lesser_zone)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_lesser_zone)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_lesser_zone)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownKordon(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectKordon(user_id))

class LocationSelectCementFactory(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Градирни", value="Градирни!"),
            disnake.SelectOption(label="— Дикий Остров", value="Дикий Остров!"),
            disnake.SelectOption(label="— Свалка", value="Свалка!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_cement_factory_role = disnake.utils.get(inter.guild.roles, name="Цементный завод")
            await inter.user.remove_roles(location_cement_factory_role)

            if self.values[0] == "Градирни!":
                location_cooling_towers_role = disnake.utils.get(inter.guild.roles, name="Градирни")
                await inter.user.add_roles(location_cooling_towers_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_cooling_towers)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_cooling_towers)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_cooling_towers)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_cooling_towers)

            elif self.values[0] == "Дикий Остров!":
                location_wild_island_role = disnake.utils.get(inter.guild.roles, name="Дикий Остров")
                await inter.user.add_roles(location_wild_island_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.", 
                        view=None, embed=embed_wild_island)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.", 
                        view=None, embed=embed_wild_island)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_wild_island)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}", 
                                                      view=None, embed=embed_wild_island)

            elif self.values[0] == "Свалка!":
                location_garbage_role = disnake.utils.get(inter.guild.roles, name="Свалка")
                await inter.user.add_roles(location_garbage_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_garbage)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_garbage)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_garbage)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownCementFactory(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectCementFactory(user_id))

class LocationSelectCoolingTowers(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Цементный завод", value="Цементный завод!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_cooling_towers_role = disnake.utils.get(inter.guild.roles, name="Градирни")
            await inter.user.remove_roles(location_cooling_towers_role)

            if self.values[0] == "Цементный завод!":
                location_cement_factory_role = disnake.utils.get(inter.guild.roles, name="Цементный завод")
                await inter.user.add_roles(location_cement_factory_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.", 
                                                      view=None, embed=embed_cement_factory)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.", 
                                                      view=None, embed=embed_cement_factory)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.", 
                                                      view=None, embed=embed_cement_factory)

                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}", 
                                                      view=None, embed=embed_cement_factory)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownCoolingTowers(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectCoolingTowers(user_id))

class LocationSelectLesserZone(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Кордон", value="Кордон!"),
            disnake.SelectOption(label="— Свалка", value="Свалка!"),
            disnake.SelectOption(label="— Дикий Остров", value="Дикий Остров!"),
            disnake.SelectOption(label="— Горелый Лес", value="Горелый Лес!"),
            disnake.SelectOption(label="— Химзавод", value="Химзавод!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_lesser_zone_role = disnake.utils.get(inter.guild.roles, name="Малая Зона")
            await inter.user.remove_roles(location_lesser_zone_role)

            if self.values[0] == "Кордон!":
                location_kordon_role = disnake.utils.get(inter.guild.roles, name="Кордон")
                await inter.user.add_roles(location_kordon_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.", 
                                                      view=None, embed=embed_kordon)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.", 
                                                      view=None, embed=embed_kordon)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.", 
                                                      view=None, embed=embed_kordon)

                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}", 
                                                      view=None,embed=embed_kordon)

            elif self.values[0] == "Свалка!":
                location_garbage_role = disnake.utils.get(inter.guild.roles, name="Свалка")
                await inter.user.add_roles(location_garbage_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_garbage)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_garbage)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_garbage)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_garbage)
                    
            elif self.values[0] == "Дикий Остров!":
                location_wild_island_role = disnake.utils.get(inter.guild.roles, name="Дикий Остров")
                await inter.user.add_roles(location_wild_island_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_wild_island)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_wild_island)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_wild_island)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_wild_island)

            elif self.values[0] == "Горелый Лес!":
                location_burned_forest_role = disnake.utils.get(inter.guild.roles, name="Горелый Лес")
                await inter.user.add_roles(location_burned_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_burned_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_burned_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_burned_forest)

                elif irradiation > 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_burned_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_burned_forest)

            elif self.values[0] == "Химзавод!":
                location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
                await inter.user.add_roles(location_chemical_plant_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_chemical_plant)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_chemical_plant)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_chemical_plant)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_chemical_plant)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownLesserZone(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectLesserZone(user_id))

class LocationSelectGarbage(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Дикий Остров", value="Дикий Остров!"),
            disnake.SelectOption(label="— Цементный завод", value="Цементный завод!"),
            disnake.SelectOption(label="— Малая Зона", value="Малая Зона!"),
            disnake.SelectOption(label="— Химзавод", value="Химзавод!"),
            disnake.SelectOption(label="— Росток", value="Росток!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_garbage_role = disnake.utils.get(inter.guild.roles, name="Свалка")
            await inter.user.remove_roles(location_garbage_role)

            if self.values[0] == "Дикий Остров!":
                location_wild_island_role = disnake.utils.get(inter.guild.roles, name="Дикий Остров")
                await inter.user.add_roles(location_wild_island_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_wild_island)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_wild_island)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_wild_island)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_wild_island)

            elif self.values[0] == "Цементный завод!":
                location_cement_factory_role = disnake.utils.get(inter.guild.roles, name="Цементный завод")
                await inter.user.add_roles(location_cement_factory_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.", 
                                                      view=None, embed=embed_cement_factory)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.", 
                                                      view=None, embed=embed_cement_factory)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.", 
                                                      view=None, embed=embed_cement_factory)

                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}", 
                                                      view=None, embed=embed_cement_factory)


            elif self.values[0] == "Малая Зона!":
                location_lesser_zone_role = disnake.utils.get(inter.guild.roles, name="Малая Зона")
                await inter.user.add_roles(location_lesser_zone_role)
                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_lesser_zone)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_lesser_zone)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_lesser_zone)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_lesser_zone)

            elif self.values[0] == "Химзавод!":
                location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
                await inter.user.add_roles(location_chemical_plant_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_chemical_plant)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_chemical_plant)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_chemical_plant)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_chemical_plant)

            elif self.values[0] == "Росток!":
                location_rostok_role = disnake.utils.get(inter.guild.roles, name="Росток")
                await inter.user.add_roles(location_rostok_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_rostok)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_rostok)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_rostok)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_rostok)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownGarbage(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectGarbage(user_id))

class LocationSelectBurnedForest(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Малая Зона", value="Малая Зона!"),
            disnake.SelectOption(label="— Химзавод", value="Химзавод!"),
            disnake.SelectOption(label="— Дуга", value="Дуга!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_burned_forest_role = disnake.utils.get(inter.guild.roles, name="Горелый Лес")
            await inter.user.remove_roles(location_burned_forest_role)

            if self.values[0] == "Малая Зона!":
                location_lesser_zone_role = disnake.utils.get(inter.guild.roles, name="Малая Зона")
                await inter.user.add_roles(location_lesser_zone_role)
                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_lesser_zone)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_lesser_zone)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_lesser_zone)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_lesser_zone)

            elif self.values[0] == "Химзавод!":
                location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
                await inter.user.add_roles(location_chemical_plant_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_chemical_plant)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_chemical_plant)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_chemical_plant)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_chemical_plant)

            elif self.values[0] == "Дуга!":
                location_duga_role = disnake.utils.get(inter.guild.roles, name="Дуга")
                await inter.user.add_roles(location_duga_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_duga)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_duga)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_duga)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_duga)

class DropDownBurnedForest(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectBurnedForest(user_id))

class LocationSelectChemicalPlant(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Свалка", value="Свалка!"),
            disnake.SelectOption(label="— Малая Зона", value="Малая Зона!"),
            disnake.SelectOption(label="— Горелый Лес", value="Горелый Лес!"),
            disnake.SelectOption(label="— Дуга", value="Дуга!"),
            disnake.SelectOption(label="— Малахит", value="Малахит!"),
            disnake.SelectOption(label="— Янтарь", value="Янтарь!"),
            disnake.SelectOption(label="— Росток", value="Росток!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
            await inter.user.remove_roles(location_chemical_plant_role)

            if self.values[0] == "Свалка!":
                location_garbage_role = disnake.utils.get(inter.guild.roles, name="Свалка")
                await inter.user.add_roles(location_garbage_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_zaton)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_zaton)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_garbage)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                                                      view=None, embed=embed_garbage)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_garbage)

            elif self.values[0] == "Малая Зона!":
                location_lesser_zone_role = disnake.utils.get(inter.guild.roles, name="Малая Зона")
                await inter.user.add_roles(location_lesser_zone_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_lesser_zone)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_lesser_zone)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_lesser_zone)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_lesser_zone)

            elif self.values[0] == "Горелый Лес!":
                location_burned_forest_role = disnake.utils.get(inter.guild.roles, name="Горелый Лес")
                await inter.user.add_roles(location_burned_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            embed=embed_burned_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_burned_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_burned_forest)

                elif irradiation >= 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_burned_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_burned_forest)

            elif self.values[0] == "Дуга!":
                location_duga_role = disnake.utils.get(inter.guild.roles, name="Дуга")
                await inter.user.add_roles(location_duga_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_duga)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_duga)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_duga)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_duga)

            elif self.values[0] == "Малахит!":
                location_malachit_role = disnake.utils.get(inter.guild.roles, name="Малахит")
                await inter.user.add_roles(location_malachit_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_malachit)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_malachit)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_malachit)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_malachit)

            elif self.values[0] == "Янтарь!":
                location_yantar_role = disnake.utils.get(inter.guild.roles, name="Янтарь")
                await inter.user.add_roles(location_yantar_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_yantar)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_yantar)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_yantar)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_yantar)

            elif self.values[0] == "Росток!":
                location_rostok_role = disnake.utils.get(inter.guild.roles, name="Росток")
                await inter.user.add_roles(location_rostok_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_rostok)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_rostok)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_rostok)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_rostok)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownChemicalPlant(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectChemicalPlant(user_id))

class LocationSelectDuga(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Горелый Лес", value="Горелый Лес!"),
            disnake.SelectOption(label="— Химзавод", value="Химзавод!"),
            disnake.SelectOption(label="— Малахит", value="Малахит!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_duga_role = disnake.utils.get(inter.guild.roles, name="Дуга")
            await inter.user.remove_roles(location_duga_role)

            if self.values[0] == "Горелый Лес!":
                location_burned_forest_role = disnake.utils.get(inter.guild.roles, name="Горелый Лес")
                await inter.user.add_roles(location_burned_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_burned_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_burned_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_burned_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_burned_forest)

                elif irradiation >= 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_burned_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_burned_forest)

            elif self.values[0] == "Химзавод!":
                location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
                await inter.user.add_roles(location_chemical_plant_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_chemical_plant)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_chemical_plant)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_chemical_plant)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_chemical_plant)

            elif self.values[0] == "Малахит!":
                location_malachit_role = disnake.utils.get(inter.guild.roles, name="Малахит")
                await inter.user.add_roles(location_malachit_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_malachit)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_malachit)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_malachit)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_malachit)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownDuga(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectDuga(user_id))

class LocationSelectMalachit(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Дуга", value="Дуга!"),
            disnake.SelectOption(label="— Мертвый Город", value="Мертвый Город!"),
            disnake.SelectOption(label="— Химзавод", value="Химзавод!"),
            disnake.SelectOption(label="— Янтарь", value="Янтарь!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_malachit_role = disnake.utils.get(inter.guild.roles, name="Малахит")
            await inter.user.remove_roles(location_malachit_role)

            if self.values[0] == "Дуга!":
                location_duga_role = disnake.utils.get(inter.guild.roles, name="Дуга")
                await inter.user.add_roles(location_duga_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_duga)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_duga)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_duga)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_duga)

            elif self.values[0] == "Мертвый Город!":
                location_dead_city_role = disnake.utils.get(inter.guild.roles, name="Мертвый Город")
                await inter.user.add_roles(location_dead_city_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_dead_city)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_dead_city)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_dead_city)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_dead_city)

            elif self.values[0] == "Химзавод!":
                location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
                await inter.user.add_roles(location_chemical_plant_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_chemical_plant)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_chemical_plant)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_chemical_plant)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_chemical_plant)

            elif self.values[0] == "Янтарь!":
                location_yantar_role = disnake.utils.get(inter.guild.roles, name="Янтарь")
                await inter.user.add_roles(location_yantar_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_yantar)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_yantar)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_yantar)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_yantar)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownMalachit(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectMalachit(user_id))

class LocationSelectDeadCity(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Янтарь", value="Янтарь!"),
            disnake.SelectOption(label="— Малахит", value="Малахит!"),
            disnake.SelectOption(label="— Рыжий Лес", value="Рыжий Лес!"),
            disnake.SelectOption(label="— Лиманск", value="Лиманск!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_dead_city_role = disnake.utils.get(inter.guild.roles, name="Мертвый Город")
            await inter.user.remove_roles(location_dead_city_role)

            if self.values[0] == "Янтарь!":
                location_yantar_role = disnake.utils.get(inter.guild.roles, name="Янтарь")
                await inter.user.add_roles(location_yantar_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_yantar)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_yantar)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_yantar)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_yantar)

            elif self.values[0] == "Малахит!":
                location_malachit_role = disnake.utils.get(inter.guild.roles, name="Малахит")
                await inter.user.add_roles(location_malachit_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_malachit)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_malachit)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_malachit)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_malachit)

            elif self.values[0] == "Рыжий Лес!":
                location_red_forest_role = disnake.utils.get(inter.guild.roles, name="Рыжий Лес")
                await inter.user.add_roles(location_red_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_red_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_red_forest)

            elif self.values[0] == "Лиманск!":
                location_limansk_role = disnake.utils.get(inter.guild.roles, name="Лиманск")
                await inter.user.add_roles(location_limansk_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_limansk)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_limansk)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownDeadCity(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectDeadCity(user_id))

class LocationSelectLimansk(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Мертвый Город", value="Мертвый Город!"),
            disnake.SelectOption(label="— Рыжий Лес", value="Рыжий Лес!"),
            disnake.SelectOption(label="— Янов", value="Янов!"),
            disnake.SelectOption(label="— Юпитер", value="Юпитер!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_limansk_role = disnake.utils.get(inter.guild.roles, name="Лиманск")
            await inter.user.remove_roles(location_limansk_role)

            if self.values[0] == "Мертвый Город!":
                location_dead_city_role = disnake.utils.get(inter.guild.roles, name="Мертвый Город")
                await inter.user.add_roles(location_dead_city_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_dead_city)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_dead_city)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_dead_city)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_dead_city)

            elif self.values[0] == "Рыжий Лес!":
                location_red_forest_role = disnake.utils.get(inter.guild.roles, name="Рыжий Лес")
                await inter.user.add_roles(location_red_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_red_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_red_forest)

            elif self.values[0] == "Янов!":
                location_yanov_role = disnake.utils.get(inter.guild.roles, name="Янов")
                await inter.user.add_roles(location_yanov_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_yanov)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_yanov)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_yanov)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_yanov)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_yanov)

            elif self.values[0] == "Юпитер!":
                location_jupiter_role = disnake.utils.get(inter.guild.roles, name="Юпитер")
                await inter.user.add_roles(location_jupiter_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_red_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_red_forest)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownLimansk(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectLimansk(user_id))

class LocationSelectRostok(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Свалка", value="Свалка!"),
            disnake.SelectOption(label="— Химзавод", value="Химзавод!"),
            disnake.SelectOption(label="— Янтарь", value="Янтарь!"),
            disnake.SelectOption(label="— Рыжий Лес", value="Рыжий Лес!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_rostok_role = disnake.utils.get(inter.guild.roles, name="Росток")
            await inter.user.remove_roles(location_rostok_role)

            if self.values[0] == "Свалка!":
                location_garbage_role = disnake.utils.get(inter.guild.roles, name="Свалка")
                await inter.user.add_roles(location_garbage_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_garbage)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_garbage)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_garbage)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_garbage)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_garbage)

            elif self.values[0] == "Химзавод!":
                location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
                await inter.user.add_roles(location_chemical_plant_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_chemical_plant)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_chemical_plant)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_chemical_plant)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_chemical_plant)

            elif self.values[0] == "Янтарь!":
                location_yantar_role = disnake.utils.get(inter.guild.roles, name="Янтарь")
                await inter.user.add_roles(location_yantar_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_yantar)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_yantar)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_yantar)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_yantar)

            elif self.values[0] == "Рыжий Лес!":
                location_red_forest_role = disnake.utils.get(inter.guild.roles, name="Рыжий Лес")
                await inter.user.add_roles(location_red_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_red_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_red_forest)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownRostok(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectRostok(user_id))

class LocationSelectYantar(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Росток", value="Росток!"),
            disnake.SelectOption(label="— Мертвый Город", value="Мертвый Город!"),
            disnake.SelectOption(label="— Химзавод", value="Химзавод!"),
            disnake.SelectOption(label="— Малахит", value="Малахит!"),
            disnake.SelectOption(label="— Рыжий Лес", value="Рыжий Лес!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_yantar_role = disnake.utils.get(inter.guild.roles, name="Янтарь")
            await inter.user.remove_roles(location_yantar_role)

            if self.values[0] == "Росток!":
                location_rostok_role = disnake.utils.get(inter.guild.roles, name="Росток")
                await inter.user.add_roles(location_rostok_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_rostok)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_rostok)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_rostok)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_rostok)

            elif self.values[0] == "Мертвый Город!":
                location_dead_city_role = disnake.utils.get(inter.guild.roles, name="Мертвый Город")
                await inter.user.add_roles(location_dead_city_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_dead_city)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_dead_city)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_dead_city)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_dead_city)

            elif self.values[0] == "Химзавод!":
                location_chemical_plant_role = disnake.utils.get(inter.guild.roles, name="Химзавод")
                await inter.user.add_roles(location_chemical_plant_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_chemical_plant)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_chemical_plant)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_chemical_plant)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_chemical_plant)

            elif self.values[0] == "Малахит!":
                location_malachit_role = disnake.utils.get(inter.guild.roles, name="Малахит")
                await inter.user.add_roles(location_malachit_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_malachit)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_malachit)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_malachit)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_malachit)

            elif self.values[0] == "Рыжий Лес!":
                location_red_forest_role = disnake.utils.get(inter.guild.roles, name="Рыжий Лес")
                await inter.user.add_roles(location_red_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_red_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_red_forest)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownYantar(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectYantar(user_id))

class LocationSelectRedForest(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Росток", value="Росток!"),
            disnake.SelectOption(label="— Мертвый Город", value="Мертвый Город!"),
            disnake.SelectOption(label="— Лиманск", value="Лиманск!"),
            disnake.SelectOption(label="— Янтарь", value="Янтарь!"),
            disnake.SelectOption(label="— Янов", value="Янов!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_red_forest_role = disnake.utils.get(inter.guild.roles, name="Рыжий Лес")
            await inter.user.remove_roles(location_red_forest_role)

            if self.values[0] == "Росток!":
                location_rostok_role = disnake.utils.get(inter.guild.roles, name="Росток")
                await inter.user.add_roles(location_rostok_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_rostok)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_rostok)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_rostok)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_rostok)

            if self.values[0] == "Мертвый Город!":
                location_dead_city_role = disnake.utils.get(inter.guild.roles, name="Мертвый Город")
                await inter.user.add_roles(location_dead_city_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_dead_city)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_dead_city)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_dead_city)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_dead_city)

            elif self.values[0] == "Лиманск!":
                location_limansk_role = disnake.utils.get(inter.guild.roles, name="Лиманск")
                await inter.user.add_roles(location_limansk_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_limansk)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_limansk)

            elif self.values[0] == "Янтарь!":
                location_yantar_role = disnake.utils.get(inter.guild.roles, name="Янтарь")
                await inter.user.add_roles(location_yantar_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                        view=None, embed=embed_yantar)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует жажду.",
                        view=None, embed=embed_yantar)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                        view=None, embed=embed_yantar)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                        view=None, embed=embed_yantar)

            elif self.values[0] == "Янов!":
                location_yanov_role = disnake.utils.get(inter.guild.roles, name="Янов")
                await inter.user.add_roles(location_yanov_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_yanov)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_yanov)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_yanov)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_yanov)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_yanov)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownRedForest(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectRedForest(user_id))

class LocationSelectYanov(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Рыжий Лес", value="Рыжий Лес!"),
            disnake.SelectOption(label="— Лиманск", value="Лиманск!"),
            disnake.SelectOption(label="— Юпитер", value="Юпитер!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_red_forest_role = disnake.utils.get(inter.guild.roles, name="Рыжий Лес")
            await inter.user.remove_roles(location_red_forest_role)

            if self.values[0] == "Рыжий Лес!":
                location_red_forest_role = disnake.utils.get(inter.guild.roles, name="Рыжий Лес")
                await inter.user.add_roles(location_red_forest_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_red_forest)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_red_forest)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_red_forest)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_red_forest)

            elif self.values[0] == "Лиманск!":
                location_limansk_role = disnake.utils.get(inter.guild.roles, name="Лиманск")
                await inter.user.add_roles(location_limansk_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_limansk)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_limansk)

            elif self.values[0] == "Юпитер!":
                location_jupiter_role = disnake.utils.get(inter.guild.roles, name="Юпитер")
                await inter.user.add_roles(location_jupiter_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_jupiter)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_jupiter)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_jupiter)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_jupiter)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_jupiter)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownYanov(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectYanov(user_id))

class LocationSelectJupiter(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Янов", value="Янов!"),
            disnake.SelectOption(label="— Лиманск", value="Лиманск!"),
            disnake.SelectOption(label="— Припять", value="Припять!"),
            disnake.SelectOption(label="— Генераторы", value="Генераторы!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_jupiter_role = disnake.utils.get(inter.guild.roles, name="Юпитер")
            await inter.user.remove_roles(location_jupiter_role)

            if self.values[0] == "Янов!":
                location_yanov_role = disnake.utils.get(inter.guild.roles, name="Янов")
                await inter.user.add_roles(location_yanov_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_yanov)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_yanov)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_yanov)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_yanov)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_yanov)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_yanov)

            elif self.values[0] == "Лиманск!":
                location_limansk_role = disnake.utils.get(inter.guild.roles, name="Лиманск")
                await inter.user.add_roles(location_limansk_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_limansk)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_limansk)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_limansk)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_limansk)

            elif self.values[0] == "Припять!":
                location_pripyat_role = disnake.utils.get(inter.guild.roles, name="Припять")
                await inter.user.add_roles(location_pripyat_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_pripyat)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_pripyat)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_pripyat)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_pripyat)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_pripyat)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_pripyat)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_pripyat)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_pripyat)

            elif self.values[0] == "Генераторы!":
                location_generators_role = disnake.utils.get(inter.guild.roles, name="Генераторы")
                await inter.user.add_roles(location_generators_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_generators)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_generators)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_generators)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_generators)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_generators)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_generators)

                elif irradiation >= 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_generators)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_generators)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownJupiter(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectJupiter(user_id))

class LocationSelectGenerators(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Юпитер", value="Юпитер!"),
            disnake.SelectOption(label="— Припять", value="Припять!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_generators_role = disnake.utils.get(inter.guild.roles, name="Генераторы")
            await inter.user.remove_roles(location_generators_role)

            if self.values[0] == "Юпитер!":
                location_jupiter_role = disnake.utils.get(inter.guild.roles, name="Юпитер")
                await inter.user.add_roles(location_jupiter_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_jupiter)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_jupiter)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_jupiter)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_jupiter)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_jupiter)

            elif self.values[0] == "Припять!":
                location_pripyat_role = disnake.utils.get(inter.guild.roles, name="Припять")
                await inter.user.add_roles(location_pripyat_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_pripyat)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_pripyat)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_pripyat)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_pripyat)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_pripyat)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_pripyat)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_pripyat)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_pripyat)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownGenerators(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectGenerators(user_id))

class LocationSelectPripyat(disnake.ui.StringSelect):
    def __init__(self, user_id: int):
        self.user_id = user_id
        options = [
            disnake.SelectOption(label="— Юпитер", value="Юпитер!"),
            disnake.SelectOption(label="— Генераторы", value="Генераторы!")]

        super().__init__(
            placeholder="На какую локацию вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        hunger = random.randint(1, 100)
        hunger_role = disnake.utils.get(inter.guild.roles, name="Голод")

        thirst = random.randint(1, 100)
        thirst_role = disnake.utils.get(inter.guild.roles, name="Жажда")

        irradiation = random.randint(1, 100)
        irradiation_role = disnake.utils.get(inter.guild.roles, name="Облучение")

        tiredness_role = disnake.utils.get(inter.guild.roles, name="Усталость")

        if inter.author.id == self.user_id:
            location_pripyat_role = disnake.utils.get(inter.guild.roles, name="Припять")
            await inter.user.remove_roles(location_pripyat_role)

            if self.values[0] == "Юпитер!":
                location_jupiter_role = disnake.utils.get(inter.guild.roles, name="Юпитер")
                await inter.user.add_roles(location_jupiter_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_jupiter)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            embed=embed_jupiter)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 50:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_jupiter)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_jupiter)

                elif irradiation >= 50:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_jupiter)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_jupiter)

            elif self.values[0] == "Генераторы!":
                location_generators_role = disnake.utils.get(inter.guild.roles, name="Генераторы")
                await inter.user.add_roles(location_generators_role)

                if hunger >= 50 and thirst <= 50:
                    await inter.user.add_roles(hunger_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод.",
                            view=None, embed=embed_generators)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_generators)

                elif hunger <= 50 and thirst >= 50:
                    await inter.user.add_roles(thirst_role)
                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует жажду.",
                            view=None, embed=embed_generators)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод.",
                            view=None, embed=embed_generators)

                elif hunger >= 50 and thirst >= 50:
                    await inter.user.add_roles(hunger_role)
                    await inter.user.add_roles(thirst_role)
                    await inter.user.add_roles(tiredness_role)

                    if irradiation >= 30:
                        await inter.user.add_roles(irradiation_role)
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации и чувствует голод, жажду и усталость.",
                            view=None, embed=embed_generators)
                    else:
                        await inter.edit_original_message(
                            f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж чувствует голод, жажду и усталость.",
                            view=None, embed=embed_generators)

                elif irradiation >= 30:
                    await inter.user.add_roles(irradiation_role)
                    await inter.edit_original_message(
                        f"{inter.user.mention} Вы перешли на локацию {self.values[0]} Ваш персонаж облучился дозой радиации.",
                        view=None, embed=embed_generators)
                else:
                    await inter.edit_original_message(f"{inter.user.mention} Вы перешли на локацию {self.values[0]}",
                                                      view=None, embed=embed_generators)
        else:
            await inter.edit_original_message("Вы не можете пользоваться данной функцией!", view=None, ephemeral=True)

class DropDownPripyat(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(LocationSelectPripyat(user_id))

locations_roles = []

class LocationSelect2Locations(disnake.ui.StringSelect):
    def __init__(self):
        options = [
            disnake.SelectOption(label=f"— {locations_roles[0]}", value=f"{locations_roles[0]}"),
            disnake.SelectOption(label=f"— {locations_roles[1]}", value=f"{locations_roles[1]}")]

        super().__init__(
            placeholder="Из какой локации вы хотите перейти?",
            min_values=1,
            max_values=1,
            options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        if self.values[0] == f"{locations_roles[0]}":
            location_role = disnake.utils.get(inter.guild.roles, name=f"{locations_roles[1]}")
            await inter.user.remove_roles(location_role)
            await show_locations(inter)
            await inter.user.add_roles(location_role)

        elif self.values[0] == f"{locations_roles[1]}":
            location_role = disnake.utils.get(inter.guild.roles, name=f"{locations_roles[0]}")
            await inter.user.remove_roles(location_role)
            await show_locations(inter)
            await inter.user.add_roles(location_role)

class DropDownSelect2Locations(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(LocationSelect2Locations())

@bot.slash_command(name="pos_move", description="Перейти на другую локацию.")
async def pos_move (inter: disnake.ApplicationCommandInteraction):
    locations_roles.clear()
    if disnake.utils.get(inter.author.roles, name="Болота"):  # 1
        locations_roles.append("Болота")

    if disnake.utils.get(inter.author.roles, name="Затон"):  # 2
        locations_roles.append("Затон")

    if disnake.utils.get(inter.author.roles, name="Дикий Остров"):  # 3
        locations_roles.append("Дикий Остров")

    if disnake.utils.get(inter.author.roles, name="НИИЧАЗ"):  # 4
        locations_roles.append("НИИЧАЗ")

    if disnake.utils.get(inter.author.roles, name="Кордон"):  # 5
        locations_roles.append("Кордон")

    if disnake.utils.get(inter.author.roles, name="Цементный завод"):  # 6
        locations_roles.append("Цементный завод")

    if disnake.utils.get(inter.author.roles, name="Градирни"):  # 7
        locations_roles.append("Градирни")

    if disnake.utils.get(inter.author.roles, name="Малая Зона"):  # 8
        locations_roles.append("Малая Зона")

    if disnake.utils.get(inter.author.roles, name="Свалка"):  # 9
        locations_roles.append("Свалка")

    if disnake.utils.get(inter.author.roles, name="Горелый Лес"):  # 10
        locations_roles.append("Горелый Лес")

    if disnake.utils.get(inter.author.roles, name="Химзавод"):  # 11
        locations_roles.append("Химзавод")

    if disnake.utils.get(inter.author.roles, name="Дуга"):  # 12
        locations_roles.append("Дуга")

    if disnake.utils.get(inter.author.roles, name="Малахит"):  # 13
        locations_roles.append("Малахит")

    if disnake.utils.get(inter.author.roles, name="Мертвый Город"):  # 14
        locations_roles.append("Мертвый Город")

    if disnake.utils.get(inter.author.roles, name="Лиманск"):  # 15
        locations_roles.append("Лиманск")

    if disnake.utils.get(inter.author.roles, name="Росток"):  # 16
        locations_roles.append("Росток")

    if disnake.utils.get(inter.author.roles, name="Янтарь"):  # 17
        locations_roles.append("Янтарь")

    if disnake.utils.get(inter.author.roles, name="Рыжий Лес"):  # 18
        locations_roles.append("Рыжий Лес")

    if disnake.utils.get(inter.author.roles, name="Янов"):  # 19
        locations_roles.append("Янов")

    if disnake.utils.get(inter.author.roles, name="Юпитер"):  # 20
        locations_roles.append("Юпитер")

    if disnake.utils.get(inter.author.roles, name="Генераторы"):  # 21
        locations_roles.append("Генераторы")

    if disnake.utils.get(inter.author.roles, name="Припять"):  # 22
        locations_roles.append("Припять")

    locations_number = len(locations_roles)
    if locations_number >= 2:
        view = DropDownSelect2Locations()
        await inter.response.send_message("Вы имеете две роли локаций при себе. Пожалуйста, выберите одну с помощью кнопки ниже.", view=view, ephemeral=True)
    else:
        locations_roles.clear()
        await show_locations(inter)

async def show_locations(inter):
    locations_roles.clear()
    if disnake.utils.get(inter.author.roles, name="Болота"): # 1
        view = DropDownSwamps(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_swamps, view=view)

    elif disnake.utils.get(inter.author.roles, name="Затон"): # 2
        view = DropDownZaton(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_zaton, view=view)

    elif disnake.utils.get(inter.author.roles, name="Дикий Остров"): # 3
        view = DropDownWildIsland(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_wild_island, view=view)

    elif disnake.utils.get(inter.author.roles, name="НИИЧАЗ"): # 4
        view = DropDownSIRCAA(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_sircaa, view=view)

    elif disnake.utils.get(inter.author.roles, name="Кордон"): # 5
        view = DropDownKordon(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_kordon, view=view)

    elif disnake.utils.get(inter.author.roles, name="Цементный завод"): # 6
        view = DropDownCementFactory(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_cement_factory, view=view)

    elif disnake.utils.get(inter.author.roles, name="Градирни"): # 7
        view = DropDownCoolingTowers(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_cooling_towers, view=view)

    elif disnake.utils.get(inter.author.roles, name="Малая Зона"): # 8
        view = DropDownLesserZone(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_lesser_zone, view=view)

    elif disnake.utils.get(inter.author.roles, name="Свалка"): # 9
        view = DropDownGarbage(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_garbage, view=view)

    elif disnake.utils.get(inter.author.roles, name="Горелый Лес"): # 10
        view = DropDownBurnedForest(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_burned_forest, view=view)

    elif disnake.utils.get(inter.author.roles, name="Химзавод"): # 11
        view = DropDownChemicalPlant(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_chemical_plant, view=view)

    elif disnake.utils.get(inter.author.roles, name="Дуга"): # 12
        view = DropDownDuga(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_duga, view=view)

    elif disnake.utils.get(inter.author.roles, name="Малахит"): # 13
        view = DropDownMalachit(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_malachit, view=view)

    elif disnake.utils.get(inter.author.roles, name="Мертвый Город"): # 14
        view = DropDownDeadCity(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_dead_city, view=view)

    elif disnake.utils.get(inter.author.roles, name="Лиманск"): # 15
        view = DropDownLimansk(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_limansk, view=view)

    elif disnake.utils.get(inter.author.roles, name="Росток"): # 16
        view = DropDownRostok(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_rostok, view=view)

    elif disnake.utils.get(inter.author.roles, name="Янтарь"): # 17
        view = DropDownYantar(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_yantar, view=view)

    elif disnake.utils.get(inter.author.roles, name="Рыжий Лес"): # 18
        view = DropDownRedForest(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_red_forest, view=view)

    elif disnake.utils.get(inter.author.roles, name="Янов"): # 19
        view = DropDownYanov(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_yanov, view=view)

    elif disnake.utils.get(inter.author.roles, name="Юпитер"): # 20
        view = DropDownJupiter(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_jupiter, view=view)

    elif disnake.utils.get(inter.author.roles, name="Генераторы"): # 21
        view = DropDownGenerators(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_generators, view=view)

    elif disnake.utils.get(inter.author.roles, name="Припять"): # 22
        view = DropDownPripyat(user_id=inter.author.id)
        await inter.response.send_message(embed=embed_pripyat, view=view)

    else:
        warning = create_embed("Ошибка!", "У вас отсутствуют роли локации.")
        await inter.send(embed=warning, ephemeral=True)

@bot.slash_command(name="pos_get_locations", description="Получить список локаций с доступными на них переходами.")
async def pos_get_locations(inter):
    await inter.response.send_message(locations)

@bot.slash_command(name="pos_start_votuum", description="Начать вотуум.")
async def votuum(inter: disnake.ApplicationCommandInteraction, gm_name: str):
    if disnake.utils.get(inter.author.roles, name="Главный Мастер Забав"):
        print('command completed')
    elif disnake.utils.get(inter.author.roles, name="Высшая Администрация"):
        print('command completed')
    else:
        await inter.send("У вас нет прав.")
        return

    # Создаём кнопки с уникальными custom_id, включающими имя GM
    agree_vote = disnake.ui.Button(label="За", custom_id=f"agree_vote:{gm_name}", style=disnake.ButtonStyle.green, emoji="✅")
    opposite_vote = disnake.ui.Button(label="Против", style=disnake.ButtonStyle.red, custom_id=f"opposite_vote:{gm_name}", emoji="❎")

    # Отправляем сообщение с кнопками
    await inter.channel.send(gm_name, components=[agree_vote, opposite_vote])
    return gm_name

# @bot.event
# async def on_button_click(inter: disnake.MessageInteraction):
#    channel_id = 1305584809036484618
#    channel = bot.get_channel(channel_id)
#    custom_id = inter.component.custom_id
#    action, gm_name = custom_id.split(":")
#    user_vote_string = f"{inter.user.name} {gm_name}"
#
#    # Проверяем, голосовал ли уже пользователь за данного ГМа
#    with open('data.txt', 'r', encoding='utf-8') as votuum_gm_list:
#        votes = votuum_gm_list.readlines()
#        if any(user_vote_string in vote for vote in votes):
#            await inter.response.send_message("Вы уже проголосовали!", ephemeral=True)
#            return
#
#    # Записываем голос пользователя
#    if action == 'agree_vote':
#        with open('data.txt', 'a', encoding='utf-8') as file:
#            file.write(f"{user_vote_string} agree\n")
#    elif action == 'opposite_vote':
#        with open('data.txt', 'a', encoding='utf-8') as file:
#            file.write(f"{user_vote_string} opposite,   \n")
#
#    # Подсчитываем количество голосов "agree" и "opposite" за каждый gm_name
#    agree_count = 0
#    opposite_count = 0
#    with open('data.txt', 'r', encoding='utf-8') as votuum_gm_list:
#        votes = votuum_gm_list.readlines()
#        for vote in votes:
#            if gm_name in vote:
#                if "agree" in vote:
#                    agree_count += 1
#                elif "opposite" in vote:
#                    opposite_count += 1
#
#    # Деактивируем все кнопки после голосования
#    for row in inter.message.components:
#        for button in row.children:
#            button.disabled = True
#
#    # Редактируем сообщение и отправляем подтверждение пользователю
#    try:
#        await inter.response.edit_message(components=inter.message.components)
#        await inter.followup.send(
#            f"Вы успешно проголосовали!",
#            ephemeral=True),
#        embed = disnake.Embed(
#            title=f"Счет за {gm_name}",
#            description=f"**За** {gm_name}: {agree_count}. \n **Против** {gm_name}: {opposite_count}",
#            color=disnake.Color.blurple()
#        )
#        await channel.send(embed=embed)
#    except Exception as e:
#        await inter.response.send_message(
#             f"Вы успешно проголосовали!",
#            ephemeral=True),
#        embed = disnake.Embed(
#            title=f"Счет за {gm_name}",
#            description=f"**За**: {agree_count}. \n **Против**: {opposite_count}",
#            color=disnake.Color.blurple()
#        )
#        await channel.send(embed=embed)
#        print(f"Error: {e}")

# channel_id = 664454828671369246

@bot.slash_command(name="guide", description="Краткий справочник: частые вопросы и основные механики ролевой игры.")
async def guide (inter: disnake.ApplicationCommandInteraction):
    class QuestionChoice(disnake.ui.StringSelect):
        def __init__(self, user_id: int):
            self.user_id = user_id
            options = [
                disnake.SelectOption(label="— Что из себя представляет ваш сервер?", value="1"),
                disnake.SelectOption(label="— Что содержит в себе мир ЧЗО на PoS? (краткий лор)", value="2"),
                disnake.SelectOption(label="— Какие основные изменения есть в группировках?", value="3"),
                disnake.SelectOption(label="— Как начать ролеплей?", value="4"),
                disnake.SelectOption(label="— Если у меня есть вопросы или проблема, к кому можно обратиться?", value="5"),
                disnake.SelectOption(label="— Что такое чар-лист, что с ним связано и как его делать?", value="6"),
                disnake.SelectOption(label="— Что делать, если мой ведущий/сорол задерживает отпись?", value="7"),
                disnake.SelectOption(label="— Какие механики есть на сервере и что я в принципе могу делать?", value="8"),
            ]

            super().__init__(
                placeholder="Какой вопрос тебя интересует?",
                min_values=1,
                max_values=1,
                options=options,
            )

        async def callback(self, inter: disnake.MessageInteraction):
            if inter.author.id != self.user_id:
                await inter.response.send_message("Ошибка! Вы не можете пользоваться данной функцией.", ephemeral=True)
                return
            
            if self.values[0] == "1":
                embed = disnake.Embed(
                    title="Вопрос: Что из себя представляет ваш сервер?",
                    description="**Path of S.T.A.L.K.E.R. [RolePlay]** — один из крупных текстовых ролеплей серверов в Discord, который содержит в себе как традиционные текстовые (литературные), так и настольные механики, позволяющие создавать захватывающую историю вашего персонажа.\n\nНаш сервер существует с 2019 года и за это время было немало потрясений - но мы всё ещё продолжаем дарить разноплановый отыгрыш, если вам интересен мир Чернобыльской Зоны Отчуждения: от спокойного изучения мира, таящего в себе опасностей до кровопролитных сражений.",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "2":
                embed = disnake.Embed(
                    title="Вопрос: Что содержит в себе мир ЧЗО на PoS? (краткий лор)",
                    description="- В данный момент, в Зоне 2021 год - вселенная Сталкер 2.\n- Присутствуют все оригинальные группировки, но нельзя играть за МСОП и Учёных.\n- Стрелок мёртв, а Шрам и Скиф ни разу не появлялись - игроки сами имеют право становиться главными персонажами, если кишка не тонка.\n- Помимо локаций С2, есть также Лиманск и Мёртвый Город.\n- На Ростке существует «Рюмочная» - место, где можно выпить, созданное игроком.",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "3":
                embed = disnake.Embed(
                    title="Вопрос: Какие основные изменения есть в группировках?",
                    description="- У «Искры» нет цели задушить «Варту» - это лишь осколок от «Чистого Неба», который воспротивился Лебедеву, Суслову и Каланче (все трое мертвы).\n- «Долг» занял Лиманск вместе с «Нейтралами» и Мертвый Город отдельно.\n- Наёмники работают отдельно, никакого Синдиката нет.\n- Лидер «Свободы» - Лицар (собственный НПС).",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "4":
                embed = disnake.Embed(
                    title="Вопрос: Как начать ролеплей?",
                    description="- Написать анкету в канал - ⁠[Регистрация квент](https://discord.com/channels/659346867250790421/659379106667823135)\n[Примечание: если вы впервые играете на сервере, то старт перманентно с «Новичка»]\n- Дождаться принятия квенты/исправить недочеты, указанные Анкетологом. Можете с ним обсудить всё в спокойной обстановке;\n- Получить стартовые роли и деньги на закуп (свой инвентарь здесь не прописывается, а покупается отдельно за игровую валюту);\n- Написать свой чарник в канале - [Чар-лист](https://discord.com/channels/659346867250790421/1256924175591936021) и дождаться проверки ГМом.\n- Написать в канал #ищу-игрока-куратора и начать свой путь в мире Path of S.T.A.L.K.E.R.",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "5":
                embed = disnake.Embed(
                    title="Вопрос: Если у меня есть вопросы или проблема, к кому можно обратиться?",
                    description="- Если у вас имеется вопрос в ролевой сфере: например, касательно механик или правил, то вы можете смело обращаться к Кураторам или Гейм-Мастерам - они спокойно ответят. Если ответа не последовало спустя некоторое время или вопрос оказался особенный, то обращайтесь за помощью к Высшей Администрации.\n- Если у вас имеется вопрос касательно правил или в чате возникла конфликтная ситуация, то для её разрешения нужно звать Хелперов или Модерацию - наши доблестные стражи порядка во всём разберутся.\n- Если у вас имеются вопросы по поводу анкеты, то обращайтесь к Анкетологам.",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "6":
                embed = disnake.Embed(
                    title="Вопрос: Что такое чар-лист, что с ним связано и как его делать?",
                    description="- Чар-лист (ака чарник) — краткий свод информации о вашем персонаже, представленный в виде характеристик, перков и дебаффов, содержащий также и репутацию.\n- Характеристика - врожденный показатель персонажа, отражающий разные элементы. По сути, это категория навыков. Пример: Ремесло - насколько у вас золотые или кривые руки, Эмпатия - умение общаться и чувствовать людей.\n- Навыки - более узкая специальность в рамках какой-то характеристики, которая прокачивается исключительно за счёт перков или уменьшается за счёт дебаффов. Пример: Эмпатия, Красноречие - умение расположить к себе людей.\n- Перки - это целое направление, разносторонне влияющие на ваши способности (навыки) и которые четко отражают суть того или иного умения. Пример: «Армейская подготовка» - влияет на все навыки «Реакции», так как персонаж имеет представление об оружии, но о каких-то видах лучше, за счёт чего, пользуется ими более умело, чем остальными видами оружия.\n\n- На Характеристики выдается 35 ОУ, с условием, что Характеристика не может быть меньше 2 и не может быть больше 8.\n- Каждому персонажу стартово дается 6 ОУ для выбора перков. В дальнейшем, перки получают за мастерство, с расчетом 50 мастерство = 1 ОУ.\n- Если вам на старте не хватает ОУ для распределения, вы можете взять дебаффы. Дебаффы - это отражение негативных черт персонажа или его недостатков, недугов, отклонений. Именно на старте они могут дать дополнительные ОУ, благодаря чему, вы можете взять ещё перков. Но если вы получите дебаффы во время своего ролевого процесса, то те не будут давать ОУ.",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "7":
                embed = disnake.Embed(
                    title="Вопрос: Что делать, если мой ведущий/сорол задерживает отпись?",
                    description="Курьёзные ситуации встречаются у всех, такое бывает - можно понять. Но всё-таки, долгая задержка способна потушить ваш интерес к игре - поэтому на нашем сервере эту проблему можно решить.\n- Вашему ведущему дается 24 часа на написание ответного поста. Если за это время тот не смог отписать, то у вас есть право написать заявку в [Задержки постов](https://discord.com/channels/659346867250790421/721039678924521512), где остальной ГМ-состав или ГГМ решат эту проблему, согласно правилу [4.3.2]\n-Если вы играете не один, а с соигроком и тот отсутствует уже длительное время, то при необходимости, за него может отписать ваш ведущий либо вы сами, согласно правилам заморозки персонажа [2.4.1], [2.4.2] и [2.4.2.1]",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "8":
                embed = disnake.Embed(
                    title="Вопрос: Какие механики есть на сервере и что я в принципе могу делать?",
                    description="- На Path of S.T.A.L.K.E.R. имеется неплохое разнообразие различных механик, что за один присест их не разобрать. Для того, чтобы информация по каждой механике была подана четко, лаконично и раздельно - описания и суть механик будут в отдельных вкладках со спец.пометкой - [Механики]. Пользуйтесь!\n\n- Также, непосредственно в форуме [Механики ролевой секции](https://discord.com/channels/659346867250790421/1254105259975114806) имеются разделы с пометкой [Прокачка]. Если вам интересна дайсовая система, то в них содержится вся информация касательного этого.",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

    class MechanicChoice(disnake.ui.StringSelect):
        def __init__(self, user_id: int):
            self.user_id = user_id
            options = [
                disnake.SelectOption(label="— Тиры: артефакты, локации, оружие, снаряжение", value="1"),
                disnake.SelectOption(label="— Перки и дебаффы", value="2"),
                disnake.SelectOption(label="— Синтез артефактов", value="3"),
                disnake.SelectOption(label="— Развитие группировки [ВПИ]", value="4"),
                disnake.SelectOption(label="— Крафт и ремонт", value="5"),
                disnake.SelectOption(label="— Поиск артефактов", value="6"),
                disnake.SelectOption(label="— Репутация", value="7"),
                disnake.SelectOption(label="— Проводники", value="8"),
            ]

            super().__init__(
                placeholder="Какая механика тебя интересует?",
                min_values=1,
                max_values=1,
                options=options,
            )

        async def callback(self, inter: disnake.MessageInteraction):
            if inter.author.id != self.user_id:
                await inter.response.send_message("Ошибка! Вы не можете пользоваться данной функцией.", ephemeral=True)
                return
            
            if self.values[0] == "1":
                embed = disnake.Embed(
                    title="[Механики] - Тиры: артефакты, локации, оружие, снаряжение",
                    description="Что такое тир? Тир - это деление разного рода вещей на три категории - чем больше, тем оно лучше (или опаснее, в плане локаций). Таким образом, торговец на локации первого тира не сможет вам продать оружие или снаряжение второго/третьего тира. Узнать более подробно про тиры можно тут - [Тиры и как они используются](https://discord.com/channels/659346867250790421/1255480483299459084)",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "2":
                embed = disnake.Embed(
                    title="[Механики] - Перки и дебаффы",
                    description="Если вы уже читали раздел «Что такое чар-лист, что с ним связано и как его делать?», то должны уже иметь четкое представление о базовых элементах персонажа. Если же не прочитали, то бегом туда - там всё самое необходимое!\n\nВ этом же разделе будут помещены нюансы, связанные с перками и дебаффами (Список -> [Перки и дебаффы](https://discord.com/channels/659346867250790421/1255782834166304821)), которые не с первого раза понятны.\n- Базовые перки Реакции, Телосложения и Интеллекта (искл. «Внимательный», «Любитель чтения») берутся исключительно на старте и подвязаны конкретно к анкете.\n- Базовый перк Телосложения по ходу ролевого отыгрыша может измениться, но на это нужны определенные усилия.\n- Навыки складываются. Условно, если вы взяли два (или более) перка, которые влияют на один навык - то он будет увеличен/уменьшен на то значение, которое получается в результате сложения. Пример: «Новый Опыт» (ЗЗ: +2) и «Путешественник» (ЗЗ: +2). В обоих перках есть «Знание Зоны (33)», в результате сложения [2+2] получаем значение навыка [4].\n- ОУ за дебаффы выдаются исключительно на старте, когда вы их берете для своего персонажа. Получаемое ОУ прописывается возле дебаффа.\n- Также, количество ОУ за ПТСР зависит от степени развития, которую вы выберете.",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "3":
                embed = disnake.Embed(
                    title="[Механики] - Синтез артефактов",
                    description="Скажем, вы сталкер - и используете артефакты не только в качестве предмета торговли, но и активно применяете их свойства. И бац, идея! А что если можно сделать так, чтобы было два или даже три в одном? \n\nПримерно такую механику и представляет из себя синтез. Она осуществляется с помощью специального прибора, который есть у учёных (но тот может быть и на базах группировки, если по механике ВПИ у группировки прокачано «Знание Зоны» до 4 ур.). Для совершения синтеза, всего-то нужно минимум два артефакта и деньги. Синтез может быть удачным, а можно уйти как в минус, так и в ноль.\n\nЕсли вам интересны подробности, то вся нужная информация имеется здесь [Механика синтеза артефактов](https://discord.com/channels/659346867250790421/1259195192066441278)",
                    color=disnake.Colour.light_gray()
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1304523512882659388/1361368938642014349/539b34da745486ff.png?ex=67fe811f&is=67fd2f9f&hm=a7daa4d3478ca467e84e70c84012b6741c714942ca27e8a9cef4c760b35f55a7&")

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "4":
                embed = disnake.Embed(
                    title="[Механики] - Развитие группировки [ВПИ]",
                    description="ВПИ существует и на нашем сервере, так как у каждой группировки имеются свои интересы и вы, как игроки, можете их представлять. Здесь это - инструмент в руках игроков, которые своими персонажами могут улучшать группировку в разных направлениях: как в военной мощи, так и в дипломатии.\n\nВПИ влияет на:\n- Товары, которые группировка может представить. От обычных медикаментов до снаряжения. Неприятно иметь всё посредственно, правда? Тогда флаг вам в руки, если желаете изменить ситуацию.\n- Качество обслуживания у техника и медика.\n- Численность группировки\n- Военную силу группировки.\n- Дипломатию с остальными;\n- Осведомленность о Зоне и её свойствах;\n- Возможности строительства укреплений или даже сооружений;\n- Качество снаряжения.\n\nУ каждого параметра группировки есть свой уровень - максимальный потолок каждого это пятый. Прокачивается он в основном за счёт определенных вложений: как деньги, так и инструменты/медикаменты, но в этот список могут входить и ролевые ситуации (дипломатия, численность).\n\nС более подробной информацией можете ознакомиться в: [Развитие группировок [ВПИ]](https://discord.com/channels/659346867250790421/1255044676080242801)",
                    color=disnake.Colour.light_gray()
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1304523512882659388/1361369006946259126/1da60fc08a628a24.png?ex=67fe8130&is=67fd2fb0&hm=5c3aa3a11411fc0422fcd2ac1f3efe8b22704f2b71d2a8d1dc4c0f27a51cb3cc&")

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "5":
                embed = disnake.Embed(
                    title="[Механики] - Крафт и ремонт",
                    description="Крафт - механика, позволяющая из сподручных деталей при помощи группы навыков Ремесла воссоздавать разные вещи: инструменты, медицинские препараты, модификации для оружия и снаряжения, боеприпасы, а также нечто специфическое (если вы готовы на это). \n\nРемонт - механика, позволяющая приводить вещи в изначальное состояние или близкое к этому. Это относится к оружию, снаряжению, а также, к некоторой технике - детекторы и прочее.\n\nДля реализации крафта и ремонта необходимы компоненты. Их вы можете получить при следующих действиях:\n- Разборка брони/оружия на компоненты.\n- Посредством диггерства.\n- В найденных тайниках.\n- При бартере (за деньги нельзя) с техником.\n\nБолее подробная информация есть в [Крафт и ремонт](https://discord.com/channels/659346867250790421/1255544297722220666)",
                    color=disnake.Colour.light_gray()
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1304523512882659388/1361369037657084076/77d5c0d210df9e10.png?ex=67fe8137&is=67fd2fb7&hm=424e06b8cff5b6c9a57ab9fb52fcf3c054d55a4ffe0911643697dc240a078740&")

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "6":
                embed = disnake.Embed(
                    title="[Механики] - Поиск артефактов",
                    description="Одним из самых популярных видов промысла среди сталкеров является поиск артефактов, но насколько он полезен, настолько же и опасен. Артефакты являются материальным сгустком аномальной энергии и в них же и хранятся, в зависимости от природы аномалии. Хотя, некоторые являются настолько уникальными, что обычным способом их не найти.\n\nНо если мы говорим про обычные? Всё просто - нужен подходящий детектор. Каждый детектор подразделяется на тир, как и сами артефакты: чем лучше детектор - тем лучше (может быть) артефакт, который вы выловите. Артефакты в аномалиях не вечны, но снова появляются в аномалиях после каждого выброса. \n\nПодробнее о процессе поиска артефактов в [Поиск артефактов](https://discord.com/channels/659346867250790421/1256914896369483796)",
                    color=disnake.Colour.light_gray()
                )

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "7":
                embed = disnake.Embed(
                    title="[Механики] - Репутация",
                    description="Чернобыльская Зона Отчуждения не так огромна и именно по этой причине, слухи по ней разносятся достаточно быстро. Ваш персонаж по мере своего ролевого процесса может как обрастать новыми связями, так и приобретать новых врагов. В этом разделе кратко изложено, на что влияет репутация и что влияет на репутацию.\n- Прежде всего, очки репутации зависят от вашей группировки. Если вы вольный сталкер, то вся репутация равна нулю и дальнейшее будет зависеть лишь от действий, совершаемым на вашем пути. Если же нет, то таблица с отношениями группировок находится в канале #дипломатия-группировок (открыто для зарегистрированных игроков).\n- Если вы помогаете кому-то - это обязательно зачтется. Если же наоборот, грабите или даже устраиваете целые налёты, то это мало кому понравится. Также, репутация может изменяться в зависимости от (не) выполненных заданий.\n- Репутация влияет на возможность получения фракционной брони, скидки у торговца и техника группировки, а также на возможную помощь при ситуациях, возникших на близлежащих территориях группировки.\n- Также, существует репутация среди торговцев. Достаточно ответственно выполнять их поручения и вы в плюсе, ведь помимо скидок у каждого торговца есть свои особенности.\nГлавное, помните, что репутация легко теряется, но заслужить её трудно. Более подробная информация о репутации находится здесь: [Репутация](https://discord.com/channels/659346867250790421/1255026358019690526)",
                    color=disnake.Colour.light_gray()
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1304523512882659388/1361369191218675812/07700178bd003468.png?ex=67fe815c&is=67fd2fdc&hm=625682b8d2519cb68a0af16dca912da82039957b4e8ebb949e010cf607aca104&")

                await inter.response.edit_message(embed=embed)

            elif self.values[0] == "8":
                embed = disnake.Embed(
                    title="[Механики] - Проводники",
                    description="Всё достаточно просто и лаконично. Если вы не готовы идти пешком через различные трудности, то к вашей услуге есть проводники. Эти ребята за достойную оплату способны вас безопасно провести практически в любую точку Зоны. И им может быть как обычный НПС, так и игрок со своей колоритной историей!",
                    color=disnake.Colour.light_gray()
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1304523512882659388/1361369131408163046/f1c7e40260ed02c3.png?ex=67fe814d&is=67fd2fcd&hm=b5817892438b969e90e1e5187366d6ad08330009399a4b184fbb78c85fcd07fc&")

                await inter.response.edit_message(embed=embed)

    class DropDownsView(disnake.ui.View):
        def __init__(self, user_id: int):
            super().__init__()

            self.add_item(QuestionChoice(user_id))
            self.add_item(MechanicChoice(user_id))

    embed = disnake.Embed(
            title="Гайд: Часто задаваемые вопросы, механики ролевой игры",
            description="Доброго времени суток! С помощью данной команды, ты призвал мудрость древних - гайд, который тебе пригодится как при первом заходе на сервер, так и при дальнейшем отыгрыше на «Path of S.T.A.L.K.E.R.»! Здесь есть как и самые распространенные вопросы, так и специфичные. Просматривай, и если вдруг возникнут вопросы - обращайся к ГМам!",
            color=disnake.Colour.light_gray()
        )
    embed.set_footer(text="Выберите интересующий Вас вопрос или механику в выпадающих списках ниже, чтобы получить информацию",
                         icon_url=inter.user.avatar)
    
    view = DropDownsView(inter.user.id)
    await inter.response.send_message(embed=embed, view=view)

@bot.event
async def on_member_join(member): 
    channel = bot.get_channel(664454828671369246)

    if channel:
        embed = disnake.Embed(
            title="Приветственное сообщение!",
            description="Здравствуй, сталкер! Желаешь заглянуть к нам на огонёк? В таком случае, проходи, не задерживайся, вот сюда: [**Нажми на меня!**](https://discord.com/channels/659346867250790421/1499439307885379614)",
            color=disnake.Colour.light_gray()
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1304523512882659388/1359458928999661689/stalker.png?ex=67f78e4a&is=67f63cca&hm=b60610189e3e26f9dd567a753b2c0b79182a11e7c912f6eba103a6bba8d09c64&")
#        embed.set_footer(text="Используйте команду «/guide» для получения подробной информации",
#                         icon_url=member.avatar)

        await channel.send(f"{member.mention}", embed=embed)
        
def log_balance_change(user_id, operation, amount, chuser, old_balance, new_balance):
    log_path = f"user_profiles/{user_id}/balance_log.json"
    log_data = []
    
    # Чтение текущего лога, если он существует
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                log_data = json.load(f)
                # Убедимся, что log_data является списком
                if not isinstance(log_data, list):
                    log_data = []
        except json.JSONDecodeError:
            log_data = []
    else:
        log_data = []
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=6)


    
    # Добавление новой записи
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "operation": operation,
        "amount": amount,
        "who": chuser.name,
        "old_balance": old_balance,
        "new_balance": new_balance
    }
    log_data.append(log_entry)
    
    # Ограничение до 10 последних записей
    log_data = log_data[-10:]
    
    # Сохранение лога
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=6)


@bot.slash_command(name="pos_money", description="Проверить баланс ПоС-монет.")
async def pos_money (inter: disnake.ApplicationCommandInteraction, username: Optional[str] = None):
    # Поиск пользователя по имени на сервере
    if username is None:
        user_id = str(inter.author.id)
    else:
        member = None
        for m in inter.guild.members:
            if m.name.lower() == username.lower():  # Игнорируем регистр
                member = m
                break 
        if not member:
            await inter.response.send_message(f"Пользователь с именем {username} не найден на сервере.")
            return
        user_id = str(member.id)
    
    folder_path = f"user_profiles/{user_id}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    if not os.path.exists(f"{folder_path}/user_posmoney.json"):    
        with open(f"{folder_path}/user_posmoney.json", "w") as f:
            json.dump({"posmoney": "0"}, f)
    with open(f"{folder_path}/user_posmoney.json", "r") as f:
        stats = json.load(f)
    posmoney = stats.get("posmoney")
    user = await bot.fetch_user(int(user_id))
    emoji_name = "Y_rub"
    emoji = None
    for e in inter.guild.emojis:
        if e.name.lower() == emoji_name.lower():
            emoji = e
            break
    embed_posmoney = disnake.Embed(
        title="Кошелёк",
        description=(f"{emoji} ПоС-монеты: {posmoney}"),
        color=disnake.Color.red())
    embed_posmoney.set_author(name=user, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed_posmoney.set_footer(text=f"© By Bon Shinomiya.")
    await inter.response.send_message(embed=embed_posmoney)

@bot.slash_command(name="pos_money_update", description="Изменить количество ПоС-монет у пользователя.")
async def pos_money_update(
    inter: disnake.ApplicationCommandInteraction, 
    operation: str,
    amount: int,
    username: str
    ):

    if operation == "add" or operation == "subtract":
        member = None
        for m in inter.guild.members:
            if m.name.lower() == username.lower():  # Игнорируем регистр
                member = m
                break  
        if not member:
            await inter.response.send_message(f"Пользователь с именем {username} не найден на сервере.")
            return
        user_id = str(member.id)
        character_path = f"user_profiles/{user_id}/user_posmoney.json"

        if not os.path.exists(f"user_profiles/{user_id}"):
            os.makedirs(f"user_profiles/{user_id}")
        if not os.path.exists(character_path):
            with open(character_path, "w") as f:
                json.dump({"posmoney": "0"}, f)
    else:
        await inter.response.send_message(f"Некорректная операция. add - добавить, subtract - отнять.")
        return

    # Чтение текущих данных
    with open(character_path, "r") as f:
        stats = json.load(f)
        
    # Получение текущего значения posmoney
    current_posmoney = int(stats.get("posmoney", "0"))
        
    # Обновление значения в зависимости от операции
    if operation == "add":
        if amount > -1:
            stats["posmoney"] = str(current_posmoney + amount)
        else:
            await inter.response.send_message("Указано отрицательное значение.")
    elif operation == "subtract":
        if amount > -1:
            new_value = current_posmoney - amount
            if new_value < 0:
                stats["posmoney"] = 0
            else:
                stats["posmoney"] = str(new_value)
        else:
            await inter.response.send_message("Указано отрицательное значение.")
    # Сохранение обновлённых данных
    with open(character_path, "w") as f:
        json.dump(stats, f, indent=4)
    with open(character_path, "r") as f:
        stats = json.load(f)
    posmoney = stats.get("posmoney")
    user = await bot.fetch_user(int(user_id))
    emoji_name = "Y_rub"
    emoji = None
    for e in inter.guild.emojis:
        if e.name.lower() == emoji_name.lower():
            emoji = e
            break
    embed_posmoney = disnake.Embed(
        title="Кошелёк",
        description=(f"Значение обновлено. Текущее количество ПоС-монет: {emoji} {posmoney}"),
        color=disnake.Color.red())
    embed_posmoney.set_author(name=user, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed_posmoney.set_footer(text=f"© By Bon Shinomiya.")
    await inter.response.send_message(embed=embed_posmoney)
    user_id2 = user_id
    user_id = str(inter.author.id)
    whuser = await bot.fetch_user(int(user_id))
    embed_posmoney_log = disnake.Embed(
        title=(f"Обновлён счёт пользователя {username} (ID: {user_id})."),
        description=(f"Старое значение: {current_posmoney}\n"
        f"Новое значение: {posmoney}"),
        color=disnake.Color.red())
    embed_posmoney_log.set_author(name=user, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed_posmoney_log.set_footer(text=f"© By Bon Shinomiya.")
    channel_id = 1376882314281488405
    channel = bot.get_channel(channel_id)
    await channel.send(embed=embed_posmoney_log)
    log_balance_change(user_id2, operation, amount, whuser, current_posmoney, posmoney)

@bot.slash_command(name="pos_money_log", description="Показывает лог последних изменений баланса ПоС-монет пользователя.")
async def pos_show_balance_log(inter: disnake.ApplicationCommandInteraction, username: str):
    try:
        # Поиск пользователя по имени
        member = None
        for m in inter.guild.members:
            if m.name.lower() == username.lower():
                member = m
                break
        if not member:
            await inter.response.send_message(f"Пользователь с именем {username} не найден на сервере.")
            return
        
        user_id = str(member.id)
        username = member.name
        log_path = f"user_profiles/{user_id}/balance_log.json"
        
        # Проверка существования файла лога
        folder_path = f"user_profiles/{user_id}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if not os.path.exists(log_path):
            log_data = []
            with open(log_path, "w") as f:
                json.dump([], f, indent=6)
        
        
        # Чтение лога
        with open(log_path, "r") as f:
            log_data = json.load(f)
        
        # Создание embed
        embed = disnake.Embed(
            title=f"Лог изменений баланса ПоС-монет для {username}.",
            description=f"ID: {user_id}",
            color=disnake.Color.red()
        )

        
        # Добавление записей лога в embed
        if log_data:
            for entry in log_data:
                embed.add_field(
                    name=entry["timestamp"],
                    value=f"Операция: {entry['operation']} \nСумма: {entry['amount']} \nСтарый баланс: {entry['old_balance']} \nНовый баланс: {entry['new_balance']} \nКто изменил: {entry['who']}\n",
                    inline=False
                )
        else:
            embed.add_field(name="Нет записей", value="Лог пуст.", inline=False)
        
        embed.set_footer(text=f"© By Bon Shinomiya.")
        
        await inter.response.send_message(embed=embed)
    
    except json.JSONDecodeError:
        await inter.response.send_message("Ошибка чтения файла balance_log.json.")
    except Exception as e:
        await inter.response.send_message(f"Произошла ошибка: {str(e)}")


    user_id = str(player.id)
    player_folder = f"posrp_bot/user_profiles/{user_id}" 

    if not os.path.exists(player_folder):
        await inter.response.send_message(
            f"У пользователя {player.display_name} еще нет созданных персонажей.", 
            ephemeral=True
        )
        return
    view = CharacterEditView(user_id=user_id, folder_path=player_folder)
    embed = disnake.Embed(
        title=f"Персонажи пользователя {player.display_name}",
        description="Выберите персонажа игрока для редакции",
        color=disnake.Color.red()
    )
    await inter.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.slash_command(name="pos_ucms", description="Меню единой системы управления персонажами")
async def pos_ucms(inter: disnake.ApplicationCommandInteraction, username: disnake.Member = None):
    await inter.response.defer()
    inter_user_id=str(inter.author.id)
    interaction_id = get_interaction_id(inter)
    print(f"pos_ucms called by user {inter.author.id}, username={username}, interaction_id={interaction_id}, interaction_type={type(inter).__name__}")
    try:
        if username is None:
            user_id = inter_user_id
            user = inter.author
            username = user.name
        else:
            user_id = str(username.id)
            username = username.name
        folder_path = f"user_profiles/{user_id}"
        valid_characters = []
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        else:
            for char_dir in os.listdir(folder_path):
                char_path = os.path.join(folder_path, char_dir)
                if not os.path.isdir(char_path):
                    continue
                    
                # Проверяем маркер завершения
                is_complete = os.path.exists(os.path.join(char_path, "complete_create"))
                
                # Проверяем, идет ли создание ПРЯМО СЕЙЧАС
                # (Ищем user_id в значениях вашего реестра сессий)
                is_active_session = any(
                    data.get("user_id") == user_id 
                    for data in bot.active_creations.values()
                )

                if not is_complete and not is_active_session:
                    # Вызов в коде:
                    try:
                        shutil.rmtree(char_path, onerror=remove_readonly)
                    except Exception as e:
                        print(f"Даже с правами доступа не удалось удалить {char_path}: {e}")
                elif is_complete:
                    # Папка корректна
                    valid_characters.append(char_dir)
                # Если is_active_session == True, мы не трогаем папку, 
                # даже если маркера нет — пользователь еще заполняет анкету.
        character_folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        print(f"Found {len(character_folders)} characters for user {user_id}: {character_folders}, interaction_id={interaction_id}")
        if len(valid_characters) == 0:
            if user_id == str(inter.author.id):
                if inter.author.id in bot.active_creations:
                    return await inter.send("У вас уже запущен процесс!", ephemeral=True)
                bot.active_creations[inter.author.id] = {"msg_id": None, "folder_path": None}
                view = CharacterCreationView(user_id, inter.bot)
                embed = disnake.Embed(
                    title="Нет персонажей",
                    description="Нажмите кнопку ниже, чтобы создать нового персонажа.",
                    color=disnake.Color.red()
                )
                embed.set_footer(text="© By Bon Shinomiya")
                await inter.send(embed=embed, view=view)
                message = await inter.original_response()
                view_store[message.id] = view
                print(f"Stored CharacterCreationView for message_id={message.id}, interaction_id={interaction_id}")
            else:
                await inter.send(f"У данного пользователя ({username}, ID: {user_id}) нет персонажей.")
            return
        else:
            view = CharacterSelectView(user_id=user_id, folder_path=folder_path, inter_user_id=inter_user_id)
            embed = disnake.Embed(
                title="Выберите персонажа",
                description="Выберите персонажа для просмотра его характеристик.",
                color=disnake.Color.red()
            )
            embed.set_footer(text="© By Bon Shinomiya")
            await inter.send(embed=embed, view=view)
            message = await inter.original_response()
            view_store[message.id] = view
            print(f"Stored CharacterSelectView for multiple characters, message_id={message.id}, interaction_id={interaction_id}")
    except Exception as e:
        print(f"Error in pos_ucms: {str(e)}, interaction_id={interaction_id}")
        await inter.send(f"Произошла ошибка: {str(e)}")

@bot.slash_command(name="pos_char_edit", description="Редактировать чарлист игрока")
async def check_char(inter: disnake.ApplicationCommandInteraction, player: disnake.Member):
    user_id = str(player.id)
    player_folder = f"user_profiles/{user_id}" 

    if not os.path.exists(player_folder):
        await inter.send(
            f"У пользователя {player.display_name} еще нет созданных персонажей.", 
            ephemeral=True
        )
        return
    view = CharacterEditView(user_id=user_id, folder_path=player_folder)
    embed = disnake.Embed(
        title=f"Персонажи пользователя {player.display_name}",
        description="Выберите персонажа игрока для редакции",
        color=disnake.Color.red()
    )
    await inter.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.slash_command(name="pos_char_utems", description="Выдать или отнять черту или эффект")
async def nkvd(inter: disnake.ApplicationCommandInteraction, 
    player: disnake.Member,
    char: str,
    entity_type: str = commands.Param(
        choices=["Черта", "Эффект"], 
        description="Тип сущности"
    ),
    operation: str = commands.Param( 
        choices=["Добавить", "Удалить"],
        description="Что сделать с выбранной сущностью?"
    ),
    type: str = commands.Param(
        choices=["Положительный тип", "Отрицательный тип"],
        description="Укажите тип влияния сущности"
    ),
    target: str = commands.Param( 
        description="Начните вводить название"
    ),
    ):

    user_id = str(player.id)
    character_path = f"user_profiles/{user_id}/{char}"
    char_stats_path = f"{character_path}/char_stats.json"
    
    file_path = "chars_data/traits_lib.json" if entity_type == "Черта" else "chars_data/effects_lib.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            library = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        library = {}
    
    if entity_type == "Черта":
        if type == "Положительный тип":
            tech_type = "positive_traits"
        else:
            tech_type = "negative_traits"
    else:
        if type == "Положительный тип":
            tech_type = "buffs"
        else:
            tech_type = "debuffs"

    tech_name = [target]
    user_name = format_traits_list(tech_name, library)
    
    with open(char_stats_path, "r", encoding="utf-8") as f:
        skills_data = json.load(f)
    
    selected_impact = "positive" if type == "Положительный тип" else "negative"
    
    trait_data = library.get(target)
    
    if trait_data and trait_data.get("type") != selected_impact:
        await inter.response.send_message(
            embed=create_embed_bs(
                "Ошибка выбора", 
                f"{entity_type} `{target}` является {trait_data.get('type')}, а вы выбрали категорию {selected_impact}."
            ), 
            ephemeral=True
        )
        return
    
    print(f"DEBUG: Пытаюсь записать в {tech_type} значение {target}")
    print(f"DEBUG: Содержимое этого списка перед записью: {skills_data[0][tech_type]}")
    
    if operation == "Добавить":
        skills_data[0][tech_type].append(target)
        embed = create_embed_bs("Операция выполнена", f"{entity_type} {user_name} успешно присвоен(а) игроку {player}.")
        await inter.response.send_message(embed=embed)
    else:
        skills_data[0][tech_type].remove(target)
        embed = create_embed_bs("Операция выполнена", f"{entity_type} {user_name} успешно снят(а) у игрока {player}.")
        await inter.response.send_message(embed=embed)
    
    with open(f"{char_stats_path}", "w", encoding="utf-8") as f:
        json.dump(skills_data, f, ensure_ascii=False, indent=4)

@nkvd.autocomplete("char")
async def nkvd_autocomp1(inter: disnake.ApplicationCommandInteraction, string: str):
    player = inter.filled_options.get("player")
    u_id = None

    # Если Discord прислал готовый объект
    if hasattr(player, "id"):
        u_id = str(player.id)
    # Если Discord прислал ID в виде строки (твой случай!)
    elif isinstance(player, str) and player.isdigit():
        u_id = player
    
    # Если ничего из этого не подошло — значит, игрок ещё не выбран
    if not u_id:
        return []

    folder_path = f"user_profiles/{u_id}"

    if not os.path.exists(folder_path):
        return []

    try:
        character_folders = [
            f for f in os.listdir(folder_path) 
            if os.path.isdir(os.path.join(folder_path, f))
        ]
        return [c for c in character_folders if string.lower() in c.lower()][:25]
    except Exception:
        return []

@nkvd.autocomplete("target")
async def nkvd_autocomp2(inter: disnake.ApplicationCommandInteraction, string: str):
    # Получаем значение уже выбранного типа сущности
    entity_type = inter.filled_options.get("entity_type")
    
    operation = inter.filled_options.get("operation")

    player = inter.filled_options.get("player")
    user_id = None

    # Если Discord прислал готовый объект
    if hasattr(player, "id"):
        user_id = str(player.id)
    # Если Discord прислал ID в виде строки (твой случай!)
    elif isinstance(player, str) and player.isdigit():
        user_id = player
    
    # Если ничего из этого не подошло — значит, игрок ещё не выбран
    if not user_id:
        return []
    
    char = inter.filled_options.get("char")

    type = inter.filled_options.get("type")
    selected_impact = "positive" if type == "Положительный тип" else "negative"

    character_path = f"user_profiles/{user_id}/{char}"
    char_stats_path = f"{character_path}/char_stats.json"
    file_path = "chars_data/traits_lib.json" if entity_type == "Черта" else "chars_data/effects_lib.json"
    
    if operation == "Добавить":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                library = json.load(f)
        except:
            return []
        
        choices = []
        for tech_id, data in library.items():
            name = data.get("name", tech_id)
            trait_impact = data.get("type")
            if trait_impact == selected_impact:
                if string.lower() in name.lower() or string.lower() in tech_id.lower():
                    choices.append(disnake.OptionChoice(name=name, value=tech_id))
        
        return choices[:25]
    else:
        try:
            with open(char_stats_path, "r", encoding="utf-8") as f:
                library = json.load(f)
            with open(file_path, "r", encoding="utf-8") as f:
                full_library = json.load(f)
        except:
            return []
        
        choices = []
        if entity_type == "Черта":
            tech_names = library[0].get("positive_traits" if type == "Положительный тип" else "negative_traits", [])
        else:
            tech_names = library[0].get("buffs" if type == "Положительный тип" else "debuffs", [])
        for tid in tech_names:
            # 1. Пытаемся найти данные об этой черте в большой библиотеке
            trait_info = full_library.get(tid)
            
            # 2. Определяем отображаемое имя (name)
            if trait_info:
                display_name = trait_info.get("name", tid)
            else:
                # Если черта удалена из библиотеки, но осталась у игрока
                display_name = f"[Удалено] {tid}"
            
            # 3. Фильтруем по вводу ГМа (string)
            # Проверяем вхождение строки и в красивое имя, и в технический ID
            if string.lower() in display_name.lower() or string.lower() in tid.lower():
                choices.append(
                    disnake.OptionChoice(name=display_name, value=tid)
                )
        
        return choices[:25]

@bot.slash_command(name="pos_entity_check", description="Посмотреть данные черты/эффекта")
async def pos_entity_check(inter: disnake.ApplicationCommandInteraction,
    entity_type: str = commands.Param(
        choices=["Черта", "Эффект"], 
        description="Тип сущности"
    ),
    target: str = commands.Param( 
        description="Начните вводить название для редактирования"
    )
):

    # Определяем путь к файлу в зависимости от типа
    file_path = "chars_data/traits_lib.json" if entity_type == "Черта" else "chars_data/effects_lib.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            library = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        library = {}

    data = library.get(target)
    embed = create_entity_data_embed(data)
    await inter.response.send_message(embed=embed, ephemeral=True)
    
@pos_entity_check.autocomplete("target")
async def pos_entity_check_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    # Получаем значение уже выбранного типа сущности
    entity_type = inter.filled_options.get("entity_type")
    
    file_path = "chars_data/traits_lib.json" if entity_type == "Черта" else "chars_data/effects_lib.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            library = json.load(f)
    except:
        return []
    
    choices = []
    for tech_id, data in library.items():
        name = data.get("name", tech_id)
        if string.lower() in name.lower() or string.lower() in tech_id.lower():
            choices.append(disnake.OptionChoice(name=name, value=tech_id))
    
    return choices[:25]

@bot.slash_command(name="pos_entity_enc", description="Посмотреть энциклопедию сущностей")
async def pos_entity_check(inter: disnake.ApplicationCommandInteraction,
    entity_type: str = commands.Param(
        choices=["Черта", "Эффект"], 
        description="Тип сущности"
    ),
    type: str = commands.Param(
        choices=["Положительный тип", "Отрицательный тип"],
        description="Укажите тип влияния сущности"
    )
    ):
    
    file_path = "chars_data/traits_lib.json" if entity_type == "Черта" else "chars_data/effects_lib.json"
    questions_lib_path = "chars_data/questions_lib.json"
    with open(questions_lib_path, "r", encoding="utf-8") as f:
        questions_lib = json.load(f)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            library = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        library = {}   
    
    trait_type = "positive" if type == "Положительный тип" else "negative"
    current_page = 1
    render_type = "view"
    view = TraitsEffectEnc(trait_type, current_page, render_type, questions_lib, library)
    page_items, max_pages, total_count = get_filtered_page(library, trait_type, current_page, render_type)
    embed = create_library_embed(page_items, questions_lib, current_page, max_pages, total_count)
    await inter.send(embed=embed, view=view, ephemeral=True)

@bot.slash_command(name="pos_utems", description="Меню единой системы управления чертами и эффектами")
async def pos_utems(inter: disnake.ApplicationCommandInteraction,
    entity_type: str = commands.Param(
        choices=["Черта", "Эффект"], 
        description="Тип создаваемой или редактируемой сущности"
    ),
    target: str = commands.Param(
        default=None, 
        description="Начните вводить название для редактирования"
    ),
    operation: str = commands.Param(
        default="Редактировать", 
        choices=["Редактировать", "Удалить"],
        description="Что сделать с выбранной сущностью?"
    )
):

    # Определяем путь к файлу в зависимости от типа
    file_path = "chars_data/traits_lib.json" if entity_type == "Черта" else "chars_data/effects_lib.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            library = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        library = {}

    view = UnitedTraitsEffectManagmentSystem()
    view.edit_path = file_path
    view.global_mode = 1 if entity_type == "Черта" else 2

    # РЕЖИМ 1: Создание новой сущности
    if target is None:
        return await view.main_editor_window(inter)

    # Проверка существования
    if target not in library:
        return await inter.response.send_message(f"Ошибка: {entity_type} `{target}` не найдена.", ephemeral=True)

    # РЕЖИМ 2: Удаление
    if operation == "Удалить":
        del library[target]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(library, f, indent=4, ensure_ascii=False)
        return await inter.response.send_message(f"✅ {entity_type} `{target}` удалена.")

    # РЕЖИМ 3: Редактирование
    data = library[target]
    
    # Заполняем View данными
    if view.global_mode == 1:
        view.tech_name = target
        view.old_tech_name = target
        view.user_name = data.get("name", target)
        view.cost = data.get("cost", 0)
        view.desc = data.get("description", "")
        view.text_mod = data.get("text_modifier", "")
        view.ucms_mod = data.get("modifiers", [])
        view.ucms_req = data.get("requirements", {})
        view.bio_req = data.get("biografy_requirements", {})
        view.text_req = data.get("text_requirements", "")
        type = data.get("type", "Положительная")
        if type == "positive":
            type = "Положительная"
        else:
            type = "Отрицательная"
        view.type = type
        unique = data.get("unique")
        if unique == "no":
            unique = "Нет"
        else:
            unique = "Да"
        view.unique = unique
    else:
        view.tech_name = target
        view.old_tech_name = target
        view.user_name = data.get("name", target)
        view.desc = data.get("description", "")
        view.text_mod = data.get("text_modifier", "")
        view.ucms_mod = data.get("modifiers", [])
        type = data.get("type", "Положительнsq")
        if type == "positive":
            type = "Положительный"
        else:
            type = "Отрицательный"
        view.type = type

    await view.main_editor_window(inter)

@pos_utems.autocomplete("target")
async def utems_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    # Получаем значение уже выбранного типа сущности
    entity_type = inter.filled_options.get("entity_type")
    
    file_path = "chars_data/traits_lib.json" if entity_type == "Черта" else "chars_data/effects_lib.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            library = json.load(f)
    except:
        return []
    
    choices = []
    for tech_id, data in library.items():
        name = data.get("name", tech_id)
        if string.lower() in name.lower() or string.lower() in tech_id.lower():
            choices.append(disnake.OptionChoice(name=name, value=tech_id))
    
    return choices[:25]

@bot.event
async def on_ready():
    print(f"Запущен как {bot.user}!")

bot.run ("MTMwMjM0NDg4MzQ3Mzc0ODA1OQ.GQPKQH._9Yh1C0jG-Ur22ZZ8hMaYtG5baM_VJaSGD7QfE")