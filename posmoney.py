import disnake
from disnake.ext import commands
import json
import os
from datetime import datetime
from typing import Optional

class PosMoneyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_balance_change(self, user_id, operation, amount, chuser, old_balance, new_balance):
        log_path = f"user_profiles/{user_id}/balance_log.json"
        log_data = []
        
        if os.path.exists(log_path):
            try:
                with open(log_path, "r") as f:
                    log_data = json.load(f)
                    if not isinstance(log_data, list):
                        log_data = []
            except json.JSONDecodeError:
                log_data = []
        else:
            log_data = []
            with open(log_path, "w") as f:
                json.dump(log_data, f, indent=6)
        
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "amount": amount,
            "who": chuser.name,
            "old_balance": old_balance,
            "new_balance": new_balance
        }
        log_data.append(log_entry)
        log_data = log_data[-10:]
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=6)

    @commands.slash_command(name="pos_money", description="Проверить баланс ПоС-монет.")
    async def pos_money(self, inter: disnake.ApplicationCommandInteraction, username: disnake.Member):
        user_id= str(username.id)  
        folder_path = f"user_profiles/{user_id}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if not os.path.exists(f"{folder_path}/user_posmoney.json"):    
            with open(f"{folder_path}/user_posmoney.json", "w") as f:
                json.dump({"posmoney": "0"}, f)
        with open(f"{folder_path}/user_posmoney.json", "r") as f:
            stats = json.load(f)
        posmoney = stats.get("posmoney")
        user = await self.bot.fetch_user(int(user_id))
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
        embed_posmoney.set_footer(text="© By Bon Shinomiya.")
        await inter.response.send_message(embed=embed_posmoney)

    @commands.slash_command(name="pos_money_update", description="Изменить количество ПоС-монет у пользователя.")
    async def pos_money_update(self, inter: disnake.ApplicationCommandInteraction,
            username: disnake.Member,
            amount: int,
            operation: str = commands.Param(
                choices=["Добавить", "Отнять"], 
                description="Тип операции."),
        ):
        if operation not in ["Добавить", "Отнять"]:
            await inter.response.send_message(f"Некорректная операция.", ephemeral=True)
            return
            
        # 1. Сразу включаем дефер, так как теперь мы работаем с файлами асинхронно
        await inter.response.defer()
        
        user_id = str(username.id)
        folder_path = f"user_profiles/{user_id}"
        character_path = f"{folder_path}/user_posmoney.json"

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        # Импортируем менеджер замков и aiofiles
        from charlists import get_char_lock
        import aiofiles

        # 2. БЛОКИРОВКА: Встаем в безопасную очередь, чтобы ГМы не повредили файл
        async with get_char_lock(folder_path):
            if not os.path.exists(character_path):
                async with aiofiles.open(character_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps({"posmoney": "0"}, indent=4))

            async with aiofiles.open(character_path, "r", encoding="utf-8") as f:
                stats = json.loads(await f.read())
            
            current_posmoney = int(stats.get("posmoney", "0"))
            
            if operation == "Добавить":
                if amount >= 0:
                    stats["posmoney"] = str(current_posmoney + amount)
                else:
                    return await inter.edit_original_message(content="Указано отрицательное значение.")
            elif operation == "Отнять":
                if amount >= 0:
                    stats["posmoney"] = str(max(0, current_posmoney - amount))
                else:
                    return await inter.edit_original_message(content="Указано отрицательное значение.")

            # Сохраняем кошелек обратно на диск через aiofiles
            async with aiofiles.open(character_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(stats, ensure_ascii=False, indent=4))

        # Читаем данные кошелька для вывода на экран
        posmoney = stats.get("posmoney")
        user = await self.bot.fetch_user(int(user_id))
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
        embed_posmoney.set_footer(text="© By Bon Shinomiya.")
        
        # Так как в начале стоит defer(), отвечаем через edit_original_message
        await inter.edit_original_message(embed=embed_posmoney)
        
        # Формируем эмбед для логов
        user_id2 = user_id
        gm_user = inter.author 
        
        embed_posmoney_log = disnake.Embed(
            title=f"Обновлён счёт пользователя {username} (ID: {user_id2}).",
            description=f"Старое значение: {current_posmoney}\nНовое значение: {posmoney}",
            color=disnake.Color.red()
        )
        
        # Устанавливаем ГМа автором эмбеда логов с его именем и его аватаркой
        gm_avatar_url = gm_user.avatar.url if gm_user.avatar else gm_user.default_avatar.url
        embed_posmoney_log.set_author(name=f"Кто: {gm_user.display_name}", icon_url=gm_avatar_url)
        embed_posmoney_log.set_footer(text="© By Bon Shinomiya.")
        
        # 3. ПОДСТРАХОВКА КАНАЛА ЛОГОВ (Решение твоей ошибки AttributeError)
        channel_id = 1376882314281488405
        channel = self.bot.get_channel(channel_id)
        
        if channel is None:
            try:
                # Если кэш пуст — насильно заставляем бота запросить канал у Discord по сети
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"Критическая ошибка: не удалось получить канал логов {channel_id} из API: {e}")

        if channel:
            try:
                await channel.send(embed=embed_posmoney_log)
            except Exception as e:
                print(f"Не удалось отправить эмбед в канал логов: {e}")
        else:
            print(f"⚠️ Предупреждение: Лог изменений не отправлен в Discord, канал {channel_id} недоступен.")
            
        # Локальный лог пишется всегда
        self.log_balance_change(user_id2, operation, amount, gm_user.display_name, current_posmoney, posmoney)

    @commands.slash_command(name="pos_money_log", description="Показывает лог последних изменений баланса ПоС-монет пользователя.")
    async def pos_show_balance_log(self, inter: disnake.ApplicationCommandInteraction, username: disnake.Member):
        try:
            user_id = str(username.id)
            log_path = f"user_profiles/{user_id}/balance_log.json"
            
            folder_path = f"user_profiles/{user_id}"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            if not os.path.exists(log_path):
                log_data = []
                with open(log_path, "w") as f:
                    json.dump([], f, indent=6)
            
            with open(log_path, "r") as f:
                log_data = json.load(f)
            
            embed = disnake.Embed(
                title=f"Лог изменений баланса ПоС-монет для {username}.",
                description=f"ID: {user_id}",
                color=disnake.Color.red()
            )
            
            if log_data:
                for entry in log_data:
                    embed.add_field(
                        name=entry["timestamp"],
                        value=f"Операция: {entry['operation']} \nСумма: {entry['amount']} \nСтарый баланс: {entry['old_balance']} \nНовый баланс: {entry['new_balance']} \nКто изменил: {entry['who']}\n",
                        inline=False
                    )
            else:
                embed.add_field(name="Нет записей", value="Лог пуст.", inline=False)
            
            embed.set_footer(text="© By Bon Shinomiya.")
            await inter.response.send_message(embed=embed)
        
        except json.JSONDecodeError:
            await inter.response.send_message("Ошибка чтения файла balance_log.json.", ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"Произошла ошибка: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(PosMoneyCog(bot))