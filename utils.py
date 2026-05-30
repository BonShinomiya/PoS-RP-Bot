import disnake
import asyncio
import os
import stat

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