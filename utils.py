import disnake
import asyncio
import os
import stat
import re
import json
import aiofiles

# Глобальный реестр замков для предотвращения Race Condition
character_locks = {}

def get_char_lock(user_id) -> asyncio.Lock:
    """
    Возвращает или создает asyncio.Lock для конкретного ключа.
    Принимает как int (user_id), так и str (путь к файлу/папке).
    """
    # Если пришло число или строка-число, приводим к инту. 
    # Если пришел путь (строка с буквами) — оставляем строкой в качестве ключа.
    try:
        key = int(user_id)
    except (ValueError, TypeError):
        key = str(user_id)

    if key not in character_locks:
        character_locks[key] = asyncio.Lock()
    return character_locks[key]

def get_interaction_id(inter):
    """Генерирует уникальный interaction_id в зависимости от типа взаимодействия."""
    if isinstance(inter, disnake.ApplicationCommandInteraction):
        return f"app_cmd_{inter.id}"
    elif isinstance(inter, disnake.MessageInteraction):
        return f"{inter.id}_{inter.message.id if inter.message else 'no_message'}"
    else:
        return f"unknown_{inter.id}"
    
def remove_readonly(func, path, onerror):
    """
    Современная функция для снятия атрибута 'Только чтение'.
    Параметр 'err' — это сам объект ошибки (например, PermissionError).
    """
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
    # 1. Убираем пробелы по краям
    name = name.strip()
    
    # 2. Удаляем спецсимволы, запрещенные в Windows
    # \ / : * ? " < > |
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    
    # 3. Ограничиваем длину (опционально, но полезно для вьюх)
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
    # Пытаемся взять из кеша, если нет — тянем из сети
    user = bot.get_user(user_id) or await bot.fetch_user(user_id)
    
    return {
        "player_name": user.name,
        "player_avatar": user.display_avatar.url
    }

async def get_stat_names_map() -> dict:
    # Используем ваши существующие функции
    names = await load_skill_names() # Загружает "skill_stealth": "Скрытность" и т.д.
    groups = await load_skill_group_names() # Загружает "body": "Телосложение" и т.д.
    
    # Объединяем их
    names.update(groups)
    
    # Добавляем базовые параметры из первого блока (т.к. в списках там нет имен)
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
        
        # Ищем блок, где skill_group[0] совпадает с нашим выбором
        for group_data in char_stats:
            group_info = group_data.get("skill_group")
            
            # Проверяем, та ли это группа (например, "craft")
            if isinstance(group_info, list) and group_info[0] == selected_group:
                # Группа найдена! Теперь собираем все навыки из этого же словаря
                skills = {}
                for key, value in group_data.items():
                    # Пропускаем сам ключ "skill_group"
                    if key != "skill_group" and isinstance(value, list) and len(value) >= 2:
                        # key = "blacksmithing", value[1] = "Кузнечное дело"
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
                # Проверяем, что это навык: не "skill_group", это список и в нем минимум 3 элемента
                # (Название, ОП, Мод)
                if key != "skill_group" and isinstance(value, list) and len(value) >= 3:
                    # В вашей новой структуре:
                    # value[0] - "Ближний бой" (Название)
                    # value[1] - ОП
                    # value[2] - Модификатор
                    skill_names[key] = value[0] 
        return skill_names
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading skill_names: {str(e)}")
        return {}

def has_role(inter: disnake.MessageInteraction, role_id: int) -> bool:
    # Проверяем, что взаимодействие произошло на сервере, а не в ЛС
    if hasattr(inter.author, "get_role"):
        return inter.author.get_role(role_id) is not None
    return False

def is_valid_tech_id(text):
    return bool(re.fullmatch(r'[a-z0-9_]+', text))

def calculate_skill_level(total_fp: int) -> int:
    level = 0
    # Мы просто вычитаем цену каждого следующего уровня, пока ОП хватает
    while True:
        next_level = level + 1
        if 1 <= next_level <= 3:
            cost = 1
        elif 4 <= next_level <= 6:
            cost = 2
        elif 7 <= next_level <= 10:
            cost = 3
        else:
            break # Максимальный уровень или иная логика
            
        if total_fp >= cost:
            total_fp -= cost
            level = next_level
        else:
            break
    return level


    
