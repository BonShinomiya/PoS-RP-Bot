import disnake
import asyncio
import os
import stat
import re
import json
import aiofiles
import weakref
from contextlib import asynccontextmanager

# Используем слабую структуру данных вместо обычного словаря dict
character_locks = weakref.WeakValueDictionary()
# Обычный словарь для удержания активных локов, пока они выполняются
_active_locks_holder = {}

# Глобальный реестр замков для предотвращения Race Condition

@asynccontextmanager
async def get_char_lock(user_id):
    try:
        key = int(user_id)
    except (ValueError, TypeError):
        key = str(user_id)

    # Инициализация блокировки и счетчика ссылок
    if key not in _active_locks_holder:
        _active_locks_holder[key] = [asyncio.Lock(), 0]
        
    lock_data = _active_locks_holder[key]
    lock_data[1] += 1
    lock = lock_data[0]
    
    try:
        async with lock:
            yield lock
    finally:
        # Сброс счетчика ссылок и освобождение памяти
        lock_data[1] -= 1
        if lock_data[1] <= 0:
            _active_locks_holder.pop(key, None)
    
def remove_readonly(func, path, onerror):
    # Снимаем защиту от записи
    os.chmod(path, stat.S_IWRITE)
    # Пытаемся выполнить операцию (удаление) снова
    func(path)

async def gms_char_autocomplete(inter: disnake.ApplicationCommandInteraction, string: str):
    """Универсальный автокомплит персонажей для ГМских команд"""
    player = inter.filled_options.get("target") or inter.filled_options.get("player")
    u_id = None

    if hasattr(player, "id"):
        u_id = str(player.id)
    elif isinstance(player, str) and player.isdigit():
        u_id = player
    
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

def sanitize_name(name: str):
    name = name.strip()
    
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:50]

def is_valid_tech_id(text):
    # Проверяем, соответствует ли вся строка шаблону от начала до конца
    return bool(re.fullmatch(r'[a-z0-9_]+', text))

def create_embed_bs (title, description=None, image_url=None):
    embed = disnake.Embed(title=title, description=description, color=disnake.Color.red())
    if image_url:
        embed.set_image(url=image_url)
    embed.set_footer(text="© By Bon Shinomiya")
    return embed

def get_interaction_id(inter):
    if isinstance(inter, disnake.ApplicationCommandInteraction):
        return f"app_cmd_{inter.id}"
    elif isinstance(inter, disnake.MessageInteraction):
        return f"{inter.id}_{inter.message.id if inter.message else 'no_message'}"
    else:
        return f"unknown_{inter.id}"
    
async def get_user_info(bot: disnake.Client, user_id: int):
    user = bot.get_user(user_id) or await bot.fetch_user(user_id)
    
    return {
        "player_name": user.name,
        "player_avatar": user.display_avatar.url
    }

async def get_stat_names_map() -> dict:
    names = await load_skill_names()
    groups = await load_skill_group_names()
    
    names.update(groups)
    
    base_params = {
        "heal_points": "ПЗ",
        "mental_points": "МЗ",
        "radiation_points": "РЗ",
        "carry_weight": "Переносимый вес",
        "movement_speed": "Движение",
        "psi_resist": "МС"
    }
    names.update(base_params)
    base_params_modifiers = {
        "heal_modificator": "Модификатор ПЗ",
        "mental_modificator": "Модификатор МЗ",
        "radiation_modificator": "Модификатор РЗ",
        "weight_modificator": "Модификатор переносимого веса",
        "speed_modificator": "Модификатор движения",
        "psi_resist_modificator": "Модификатор МС"
    }
    names.update(base_params_modifiers)    
    return names

async def load_skill_group_names() -> dict:
    blank_chars_path = "chars_data/blank_chars.json"
    stats_file = blank_chars_path
    try:
        async with aiofiles.open(stats_file, "r", encoding="utf-8") as f:
            char_stats = json.loads(await f.read())
        return {group["skill_group"][0]: group["skill_group"][1] for group in char_stats if isinstance(group.get("skill_group"), list) and len(group["skill_group"]) >= 2}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading skill_group_names from {stats_file}: {str(e)}")
        return {}

async def load_skills_by_group(selected_group: str) -> dict:
    blank_chars_path = "chars_data/blank_chars.json"
    try:
        async with aiofiles.open(blank_chars_path, "r", encoding="utf-8") as f:
            char_stats = json.loads(await f.read())
        
        for group_data in char_stats:
            group_info = group_data.get("skill_group")
            
            if isinstance(group_info, list) and group_info[0] == selected_group:
                skills = {}
                for key, value in group_data.items():
                    if key != "skill_group" and isinstance(value, list) and len(value) >= 2:
                        skills[key] = value[0]
                return skills
                
        return {} # Если группу не нашли
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading skills for group {selected_group}: {e}")
        return {}
    
async def load_skill_names() -> dict:
    blank_chars_path = "chars_data/blank_chars.json"
    try:
        async with aiofiles.open(blank_chars_path, "r", encoding="utf-8") as f:
            char_stats = json.loads(await f.read())
        
        skill_names = {}
        # Пропускаем первый словарь (там char_name и прочая мета)
        for group in char_stats[1:]: 
            for key, value in group.items():
                if key != "skill_group" and isinstance(value, list) and len(value) >= 3:
                    skill_names[key] = value[0] 
        return skill_names
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading skill_names: {str(e)}")
        return {}

def has_role(inter: disnake.MessageInteraction, role_id: int) -> bool:
    if hasattr(inter.author, "get_role"):
        return inter.author.get_role(role_id) is not None
    return False

def calculate_skill_level(total_fp: int) -> int:
    level = 0
    while True:
        next_level = level + 1
        if 1 <= next_level <= 3:
            cost = 1
        elif 4 <= next_level <= 6:
            cost = 2
        elif 7 <= next_level <= 10:
            cost = 3
        else:
            break
            
        if total_fp >= cost:
            total_fp -= cost
            level = next_level
        else:
            break
    return level


    
