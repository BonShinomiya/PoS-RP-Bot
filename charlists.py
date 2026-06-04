import aiofiles
import disnake
import json
import os
import shutil
import re
import copy
import random
from typing import Optional, Dict, List

# Глобальный реестр замков для предотвращения Race Condition

from utils import *

async def modify_skill_fp(skill_id: str, bonus_levels: int, folder_path: str):
    path = f"{folder_path}/char_stats.json"
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        stats = json.loads(await f.read())
    
    found = False
    for group in stats[1:]:
        # Проверяем, не является ли stat_id самой группой (аттрибутом)
        group_info = group.get("skill_group")
        if group_info and group_info[0] == skill_id:
            # Аттрибуты обычно растут линейно или иначе, 
            # но если нужно - можно добавить логику и сюда.
            group_info[2] += bonus_levels 
            found = True
            break
        
        if skill_id in group:
            current_fp = group[skill_id][1]
            # Считаем, сколько ОП добавить для роста УРОВНЯ
            added_fp = calculate_needed_fp(current_fp, bonus_levels)
            group[skill_id][1] += added_fp
            found = True
            break
    
    if found:
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(stats, ensure_ascii=False, indent=4))
    
async def calculate_modificators(skills_data, traits_lib, effects_lib, character_path):
    active_mods = {}
    negative_traits_to_remove = []
    for tid in skills_data[0].get("negative_traits", []):
        if tid in traits_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_trait_mods = traits_lib.get(tid, {}).get("modifiers", [])
            for mod in file_trait_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value
        else:
            negative_traits_to_remove.append(tid)
    
    positive_traits_to_remove = []
    for tid in skills_data[0].get("positive_traits", []):
        if tid in traits_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_trait_mods = traits_lib.get(tid, {}).get("modifiers", [])
            for mod in file_trait_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value
        else:
            positive_traits_to_remove.append(tid)
    
    buffs_to_remove = []
    for tid in skills_data[0].get("buffs", []):
        if tid in effects_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_effect_mods = effects_lib.get(tid, {}).get("modifiers", [])
            for mod in file_effect_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value
        else:
            buffs_to_remove.append(tid)
    
    debuffs_to_remove = []
    for tid in skills_data[0].get("debuffs", []):
        if tid in effects_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_effect_mods = effects_lib.get(tid, {}).get("modifiers", [])
            for mod in file_effect_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value
        else:
            debuffs_to_remove.append(tid)
    
    charlist_edit = False
    if negative_traits_to_remove:
        charlist_edit = True
        for t_id in negative_traits_to_remove:
            skills_data[0]["negative_traits"].remove(t_id)
    if positive_traits_to_remove:
        charlist_edit = True
        for t_id in positive_traits_to_remove:
            skills_data[0]["positive_traits"].remove(t_id)
    if buffs_to_remove:
        charlist_edit = True
        for t_id in buffs_to_remove:
            skills_data[0]["buffs"].remove(t_id)
    if debuffs_to_remove:
        charlist_edit = True
        for t_id in debuffs_to_remove:
            skills_data[0]["debuffs"].remove(t_id)    
    if charlist_edit:
        async with aiofiles.open(f"{character_path}/char_stats.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))

    derived_edit = copy.deepcopy(skills_data)
    
    # 3. Применяем модификаторы к копии данных
    for group_dict in skills_data[0:7]: 
        for key, value_list in group_dict.items():
            # Пропускаем, если это не список (на всякий случай)
            if not isinstance(value_list, list):
                continue
            
                # ОПРЕДЕЛЯЕМ ID: для групп это первый элемент, для остального - ключ
            target_id = value_list[0] if key == "skill_group" else key

            if target_id in active_mods:
                mod = active_mods[target_id]
                    
                # ЛОГИКА ДЛЯ ГРУПП (["id", "Название", значение, модификатор])
                if key == "skill_group":
                    # В char_stats.json это: ["reaction", "Реакция", 6] -> индекс [3]
                    value_list[3] += mod
                    
                # ЛОГИКА ДЛЯ НАВЫКОВ (["Название", ОП, Модификатор])
                elif len(value_list) == 3 and isinstance(value_list[1], int):
                    # В char_stats.json это: ["Пистолеты", 3, 0] -> индекс [2]
                    value_list[2] += mod

                # ЛОГИКА ДЛЯ ПРОИЗВОДНЫХ (["ХП/Вес", Модификатор]) или ([Текущее, Макс])
                elif len(value_list) == 2 and isinstance(value_list[0], int):
                    # Если это ХП [0, 0] или перенос веса, модифицируем бонус (индекс [1])
                    value_list[1] += mod
                    
                elif len(value_list) == 1 and isinstance(value_list[0], int):
                    value_list[0] += mod
    
    skill_persistence = 0
    skill_persistence_modificators = 0

    # 3. Пытаемся найти стойкость
    res_persistence = find_skill(skills_data, "skill_persistence")
    if res_persistence:
        skill_persistence = calculate_skill_level(res_persistence[1])
        skill_persistence_modificators = res_persistence[2]

    body_value = int_value = 0
    body_modificator = int_modificator = 0
    for group in skills_data[1:]:
        group_info = group.get("skill_group")
        if group_info:
            g_id = group_info[0]
            if g_id == "body":
                body_value = int(group_info[2])
                body_modificator = int(group_info[3])
            elif g_id == "intellect":
                int_value = int(group_info[2])
                int_modificator = int(group_info[3])
    body_value += body_modificator
    int_value += int_modificator
    
    source = skills_data[0]
    
    heal_modificator = source.get("heal_points", [0])[1]
    mental_modificator = source.get("mental_points", [0])[1]
    radiation_modificator = source.get("radiation_points", [0])[1]
    
    max_heal = body_value * 5 + 15 + skill_persistence + skill_persistence_modificators + heal_modificator
    max_radiation = body_value * 5 + 15 + radiation_modificator
    max_mental = int_value * 5 + 15 + mental_modificator
    
    charlist_edit = False
    actual_hp = skills_data[0]["heal_points"][0]
    if actual_hp > max_heal:
        charlist_edit = True
        derived_edit[0]["heal_points"][0] = max_heal
        skills_data[0]["heal_points"][0] = max_heal
    actual_mental = skills_data[0]["mental_points"][0]
    if actual_mental > max_mental:
        charlist_edit = True
        derived_edit[0]["mental_points"][0] = max_mental
        skills_data[0]["mental_points"][0] = max_mental
    actual_radiation = skills_data[0]["radiation_points"][0]
    if actual_radiation > max_radiation:
        charlist_edit = True
        derived_edit[0]["radiation_points"][0] = max_radiation
        skills_data[0]["radiation_points"][0] = max_radiation

    if charlist_edit:
        async with aiofiles.open(f"{character_path}/char_stats.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(derived_edit, ensure_ascii=False, indent=4))

    return skills_data

async def calculate_modificators_dice_roll(skills_data, traits_lib, effects_lib):
    active_mods = {}
    for tid in skills_data[0].get("negative_traits", []):
        if tid in traits_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_trait_mods = traits_lib.get(tid, {}).get("modifiers", [])
            for mod in file_trait_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value
    
    for tid in skills_data[0].get("positive_traits", []):
        if tid in traits_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_trait_mods = traits_lib.get(tid, {}).get("modifiers", [])
            for mod in file_trait_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value

    for tid in skills_data[0].get("buffs", []):
        if tid in effects_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_effect_mods = effects_lib.get(tid, {}).get("modifiers", [])
            for mod in file_effect_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value

    for tid in skills_data[0].get("debuffs", []):
        if tid in effects_lib:
            # Берем те же модификаторы из библиотеки для черт из файла
            file_effect_mods = effects_lib.get(tid, {}).get("modifiers", [])
            for mod in file_effect_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value

    # 3. Применяем модификаторы к копии данных
    for group_dict in skills_data[1:7]: 
        for key, value_list in group_dict.items():
            # Пропускаем, если это не список (на всякий случай)
            if not isinstance(value_list, list):
                continue
            
                # ОПРЕДЕЛЯЕМ ID: для групп это первый элемент, для остального - ключ
            target_id = value_list[0] if key == "skill_group" else key

            if target_id in active_mods:
                mod = active_mods[target_id]
                    
                # ЛОГИКА ДЛЯ ГРУПП (["id", "Название", значение, модификатор])
                if key == "skill_group":
                    # В char_stats.json это: ["reaction", "Реакция", 6] -> индекс [3]
                    value_list[3] += mod
                    
                # ЛОГИКА ДЛЯ НАВЫКОВ (["Название", ОП, Модификатор])
                elif len(value_list) == 3 and isinstance(value_list[1], int):
                    # В char_stats.json это: ["Пистолеты", 3, 0] -> индекс [2]
                    value_list[2] += mod

    return skills_data

async def stats_rendering(bot: disnake.Client, user_id: str, character_path: str):
    user_id = int(user_id)
    user_data = await get_user_info(bot, user_id)
    player_name = user_data["player_name"]
    player_avatar = user_data["player_avatar"]
    async with aiofiles.open(f"{character_path}/char_stats.json", "r", encoding="utf-8") as f:
        skills_data = json.loads(await f.read())
    async with aiofiles.open(f"{character_path}/short_story.json", "r", encoding="utf-8") as f:
        short_story = json.loads(await f.read())
    async with aiofiles.open("chars_data/questions_lib.json", "r", encoding="utf-8") as f:
        questions_lib = json.loads(await f.read())
    async with aiofiles.open("chars_data/traits_lib.json", "r", encoding="utf-8") as f:
        traits_lib = json.loads(await f.read())
    async with aiofiles.open("chars_data/effects_lib.json", "r", encoding="utf-8") as f:
        effects_lib = json.loads(await f.read())
    char_name = skills_data[0].get("char_name")
    reputation = skills_data[0].get("reputation")[0]
    money = skills_data[0].get("rubles")

    from inventory import sync_character_weight_and_effects
    await sync_character_weight_and_effects(character_path)

    # Функция для превращения "1" в "Медицина" и т.д.
    def get_choice_label(q_id, user_answer):
        question_data = questions_lib.get(str(q_id))
        if not question_data:
            return "Неизвестно"
        
        # Ищем в списке choices объект с нужным value
        for choice in question_data.get("choices", []):
            if str(choice.get("value")) == str(user_answer):
                return choice.get("label")
        return "Не выбрано"
    
    convertion = await calculate_modificators(skills_data, traits_lib, effects_lib, character_path)
    source = convertion[0]
    
    # Безопасно извлекаем текущие значения (actual)
    actual_heal_points = source.get("heal_points", [0])[0]
    actual_mental_points = source.get("mental_points", [0])[0]
    actual_radiation_points = source.get("radiation_points", [0])[0]
    actual_carry_weight = source.get("carry_weight", [0])[0]

    heal_modificator = source.get("heal_points", [0])[1]
    mental_modificator = source.get("mental_points", [0])[1]
    radiation_modificator = source.get("radiation_points", [0])[1]
    weight_modificator = source.get("carry_weight", [0])[1]
    speed_modificator = source.get("movement_speed", [0])[0]
    psi_resist_modificator = source.get("psi_resist", [0])[0]


    char_age = short_story.get("age", [0])[0]
    special_skills = short_story.get("14", ["Не указано"])[0]
    character_desc = short_story.get("15", ["Не указано"])[0]
    appearance_desc = short_story.get("16", ["Не указано"])[0]

    positive_traits_list = source.get("positive_traits", ["Нет черт"])
    negative_traits_list = source.get("negative_traits", ["Нет черт"])
    buffs_list = source.get("buffs", ["Нет эффектов"])
    debuffs_list = source.get("debuffs", ["Нет эффектов"])
    
    from utems import format_traits_list
    
    negative_traits_string = format_traits_list(negative_traits_list, traits_lib)
    positive_traits_string = format_traits_list(positive_traits_list, traits_lib)
    buffs_string = format_traits_list(buffs_list, effects_lib)
    debuffs_string = format_traits_list(debuffs_list, effects_lib)

    # 1. Сначала инициализируем переменные нулями (безопасный дефолт)
    skill_strength = 0
    skill_strength_modificators = 0
    skill_persistence = 0
    skill_persistence_modificators = 0

    # 2. Пытаемся найти силу
    res_strength = find_skill(convertion, "skill_strength")
    if res_strength:
        # res_strength гарантированно список благодаря твоему return ["Неизвестно", 0, 0]
        skill_strength = calculate_skill_level(res_strength[1])
        skill_strength_modificators = res_strength[2]

    # 3. Пытаемся найти стойкость
    res_persistence = find_skill(convertion, "skill_persistence")
    if res_persistence:
        skill_persistence = calculate_skill_level(res_persistence[1])
        skill_persistence_modificators = res_persistence[2]

    body_value = dex_value = int_value = empathy_value = 0
    body_modificator = dex_modificator = int_modificator = empathy_modificator = 0
    for group in convertion[1:]:
        group_info = group.get("skill_group")
        if group_info:
            g_id = group_info[0]
            if g_id == "body":
                body_value = int(group_info[2])
                body_modificator = int(group_info[3])
            elif g_id == "dexterity":
                dex_value = int(group_info[2])
                dex_modificator = int(group_info[3])
            elif g_id == "intellect":
                int_value = int(group_info[2])
                int_modificator = int(group_info[3])
            elif g_id == "empathy":
                empathy_value = int(group_info[2])
                empathy_modificator = int(group_info[3])
    body_value += body_modificator
    dex_value += dex_modificator
    int_value += int_modificator
    empathy_value += empathy_modificator
    max_heal = body_value * 5 + 15 + skill_persistence + skill_persistence_modificators + heal_modificator
    max_radiation = body_value * 5 + 15 + radiation_modificator
    max_mental = int_value * 5 + 15 + mental_modificator
    max_weight = (body_value + skill_strength + skill_strength_modificators) * 3 + weight_modificator
    max_speed = dex_value + 5 + speed_modificator
    max_psi_resist = int((empathy_value / 2) + psi_resist_modificator)
    main_info = (
        f"**Возраст:** {char_age}\n"
        f"**ПЗ:** {actual_heal_points}/{max_heal} | **МЗ:** {actual_mental_points}/{max_mental}\n"
        f"**РЗ:** {actual_radiation_points}/{max_radiation}\n"
        f"**Движение:** {max_speed} м. | **Вес:** {actual_carry_weight}/{max_weight} кг\n"
        f"**МС:** {max_psi_resist}\n"
        f"**Репутация:** {reputation}\n"
        f"**Баланс:** {money} RU\n"
    )
    embed_chars_main = create_embed_bs (f"Умения персонажа {char_name}", main_info)
    embed_chars_main.set_author(
        name=player_name,
        icon_url=player_avatar
    )
    for group in convertion[1:7]:
            group_id = group.get("skill_group", [None])[0]
            if group_id:
                skill_group_raw = group.get("skill_group", ["unknown", "Неизвестная группа", 0])
                
                # Конвертируем значение самой группы, если оно тоже в ОП
                raw_group_fp = skill_group_raw[2] if isinstance(skill_group_raw, list) else 0
                skill_group_modificator = skill_group_raw[3] if isinstance(skill_group_raw, list) else 0
                skill_group_level = raw_group_fp
                skill_group_name = skill_group_raw[1] if isinstance(skill_group_raw, list) else "Группа"
                
                                                        
                field_name = f"{skill_group_name}: {skill_group_level} + {skill_group_modificator}"
                field_value = []
                
                for key, value in group.items():
                    if key != "skill_group":
                        # display_name оставляем как есть
                        display_name = value[0] if isinstance(value, list) and len(value) > 1 else key
                        
                        # skill_fp_value — это то, что лежит в JSON на 3-м месте (индекс 2)
                        skill_fp_value = value[1] if isinstance(value, list) and len(value) >= 3 else 0
                        skill_modificator = value[2]
                        
                        # КОНВЕРТИРУЕМ ОП в УРОВЕНЬ
                        calculated_level = calculate_skill_level(skill_fp_value)
                        
                        # Формируем строку: Название: Уровень (Сумма ОП)
                        field_value.append(f"*{display_name}*: __{calculated_level}+{skill_modificator}__ ({skill_fp_value} ОП)")
                
                embed_chars_main.add_field(
                    name=field_name,
                    value="\n".join(field_value) if field_value else "Нет навыков",
                    inline=True
                )
    
    embed_chars_main.add_field(
        name="Черты",
        value=f"**Положительные:** {positive_traits_string}\n\n**Отрицательные:** {negative_traits_string}",
        inline=True
    )
    embed_chars_main.add_field(
        name="Эффекты",
        value=f"**Баффы:** {buffs_string}\n\n**Дебаффы:** {debuffs_string}",
        inline=True
    )
    bio_details = []
    for q_idx in range(1, 10):
        answer = short_story.get(str(q_idx), [None])[0]
        if answer is not None:
            q_name = questions_lib.get(str(q_idx), {}).get("question", f"Вопрос {q_idx}")
            label = get_choice_label(q_idx, answer)
            bio_details.append(f"**{q_name}:** {label}")

    if bio_details:
        embed_chars_main.add_field(
            name="Жизненный путь", 
            value="\n".join(bio_details), 
            inline=False
        )
    embed_chars_main.add_field(
        name="Характер", 
        value=character_desc if character_desc else "Не заполнено", 
        inline=False
    )
    embed_chars_main.add_field(
        name="Внешность", 
        value=appearance_desc if appearance_desc else "Не заполнено", 
        inline=False
    )
    embed_chars_main.add_field(
        name="Особые умения", 
        value=special_skills, 
        inline=False
        )
    
    return embed_chars_main
    
async def get_all_stat_names() -> dict:
    blank_chars_path = "chars_data/blank_chars.json"
    
    # 1. Базовые переводы, которые не лежат в списках (статичные)
    names = {
        "heal_points": "Очки здоровья",
        "mental_points": "Ментальное здоровье",
        "radiation_points": "Защита от радиации",
        "carry_weight": "Переносимый вес",
        "movement_speed": "Скорость движения"
    }

    try:
        async with aiofiles.open(blank_chars_path, "r", encoding="utf-8") as f:
            char_stats = json.loads(await f.read())

        for group in char_stats:
            # Добавляем названия ГРУПП (Реакция, Телосложение и т.д.)
            group_info = group.get("skill_group")
            if isinstance(group_info, list) and len(group_info) >= 2:
                names[group_info[0]] = group_info[1]

            # Добавляем названия НАВЫКОВ (Пистолеты, Скрытность и т.д.)
            for key, value in group.items():
                if key != "skill_group" and isinstance(value, list) and len(value) >= 2:
                    # Проверяем, что второй элемент - строка (название)
                    if isinstance(value[0], str):
                        names[key] = value[0]
        
        return names

    except Exception as e:
        print(f"Ошибка при сборке имен: {e}")
        return names # Возвращаем хотя бы базу
    
def get_cost_for_level(level: int) -> int:
    """Возвращает стоимость перехода на указанный уровень."""
    if 1 <= level <= 3: return 1
    if 4 <= level <= 6: return 2
    if 7 <= level <= 10: return 3
    return 999 # Заглушка для лимита

def calculate_needed_fp(current_fp: int, bonus_levels: int) -> int:
    """Считает разницу в ОП при изменении уровня на bonus_levels (в обе стороны)."""
    current_level = calculate_skill_level(current_fp)
    target_level = current_level + bonus_levels
    
    # 1. Ограничение сверху (Макс уровень 10)
    if target_level > 10:
        target_level = 10
        # Пересчитываем bonus_levels, чтобы цикл не шел дальше 10
        bonus_levels = target_level - current_level

    # 2. Ограничение снизу (Мин уровень 0)
    if target_level < 0:
        target_level = 0
        bonus_levels = -current_level

    total_diff = 0

    # Если мы уже на максимуме и пытаемся повысить — сразу 0
    if bonus_levels == 0:
        return 0

    if bonus_levels > 0:
        for l in range(current_level + 1, target_level + 1):
            total_diff += get_cost_for_level(l)
    
    elif bonus_levels < 0:
        for l in range(current_level, target_level, -1):
            total_diff -= get_cost_for_level(l)

    return total_diff

def find_skill(data_list, skill_id):
    # Пропускаем первый элемент (там имя) и ищем в остальных
    for group in data_list[1:]:
        if skill_id in group:
            return group[skill_id]
    return ["Неизвестно", 0, 0] # Дефолт, если не нашли

class OBTConfirmationView(disnake.ui.View):
    """Окно подтверждения готовности к тестированию ОБТ."""
    def __init__(self, parent_view, character_path: str, interactor_id: int):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.character_path = character_path
        self.interactor_id = interactor_id

    @disnake.ui.button(label="Да, я готов", style=disnake.ButtonStyle.red, row=0)
    async def confirm_cb(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id != self.interactor_id: 
            return
        
        await inter.response.defer()

        # Блокируем параллельные операции через замок персонажа
        async with get_char_lock(self.character_path):
            inv_file_path = os.path.join(self.character_path, "char_inventory.json")
            stats_file_path = os.path.join(self.character_path, "char_stats.json")

            # Если у персонажа ещё нет файла инвентаря, создаём структуру асинхронно
            if not os.path.exists(inv_file_path):
                default_inventory = {
                    "equipment": {
                        "weapon_slot": None, "melee_slot": None, "armor_slot": None,
                        "head_slot": None, "mask_slot": None, "detector_anomaly_slot": None,
                        "detector_artefact_slot": None, "eyes_slot": None, "ears_slot": None
                    },
                    "inventory": {"static": {}, "unique": {}}
                }
                try:
                    async with aiofiles.open(inv_file_path, "w", encoding="utf-8") as f:
                        await f.write(json.dumps(default_inventory, ensure_ascii=False, indent=4))
                except Exception as e:
                    return await inter.followup.send(f"Ошибка создания файла инвентаря: {e}", ephemeral=True)

            # Модифицируем файл характеристик персонажа для ОБТ
            if os.path.exists(stats_file_path):
                try:
                    async with aiofiles.open(stats_file_path, "r", encoding="utf-8") as f:
                        stats_data = json.loads(await f.read())

                    # Добавляем новый ключ money в первый мета-словарь списка
                    if isinstance(stats_data, list) and len(stats_data) > 0:
                        stats_data[0]["money"] = 0

                    async with aiofiles.open(stats_file_path, "w", encoding="utf-8") as f:
                        await f.write(json.dumps(stats_data, ensure_ascii=False, indent=4))
                except Exception as e:
                    return await inter.followup.send(f"Ошибка инициализации валюты ОБТ: {e}", ephemeral=True)

            from inventory import PlayerInventoryMenu
            
            inventory_menu = PlayerInventoryMenu(
                parent_view=self.parent_view, 
                folder_path=self.character_path, 
                interactor_id=inter.author.id
            )
            
            # Передаём управление инвентарю
            await inventory_menu.send_inventory_window(inter)

    @disnake.ui.button(label="Отмена", style=disnake.ButtonStyle.red, row=0)
    async def cancel_cb(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id != self.interactor_id: 
            return
        await inter.response.edit_message(content="Вход в инвентарь отменен.", embed=None, view=None)

class BaseWorkshopView(disnake.ui.View):
    def __init__(self, bot, user_id, folder_path):
        super().__init__(timeout=900) # Вызов оригинального disnake View
        self.bot = bot
        self.folder_path = folder_path
        self.user_id = user_id

    async def on_timeout(self):
        # 1. Твоя текущая логика очистки папки
        if self.folder_path and os.path.exists(self.folder_path):
            try:
                shutil.rmtree(self.folder_path, onerror=remove_readonly)
                print(f"Таймаут: Временная папка {self.folder_path} удалена.")
            except Exception as e:
                print(f"Ошибка при удалении папки по таймауту: {e}")
        
        # Убираем пользователя из активных сессий
        target_id = int(self.user_id)
        if self.bot and target_id in self.bot.active_creations:
            self.bot.active_creations.pop(target_id, None)
            print(f"Сессия пользователя {target_id} закрыта по таймауту.")

        # 2. А вот и магия убирания кнопок без всяких inter:
        if self.message:
            try:
                # view=None полностью удаляет панель кнопок под сообщением
                await self.message.edit(
                    content="❌ **Время ожидания истекло.** Начните заново через `/pos_ucms`.", 
                    embed=None, 
                    view=None
                )
            except disnake.HTTPException:
                # На случай, если пользователь сам удалил сообщение до таймаута
                pass
        
        self.stop()

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True

class CharacterSelectView(disnake.ui.View):
    def __init__(self, user_id: str, folder_path: str, inter_user_id):
        super().__init__(timeout=900)
        with open("chars_data/traits_lib.json", "r", encoding="utf-8") as f:
            self.traits_lib = json.load(f)
        with open("chars_data/effects_lib.json", "r", encoding="utf-8") as f:
            self.effects_lib = json.load(f)
        self.user_id = user_id
        self.inter_user_id = inter_user_id
        self.folder_path = folder_path
        self.message = None
        self.selected_derived = None
        self.selected_group = None
        self.selected_skill = None
        self.modifier = 0
        character_folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        options = [
            disnake.SelectOption(label=folder, value=folder)
            for folder in character_folders
        ]
        if options:
            select = disnake.ui.Select(
                placeholder="Выберите персонажа",
                options=options,
                custom_id="character_select",
                min_values=1
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        bruh = str(inter.author.id)
        if not bruh == self.inter_user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True

    async def select_callback(self, inter: disnake.MessageInteraction):
        if inter.response.is_done():
            return
        try:
            self.selected_character = inter.data.values[0]
            self.character_path = f"{self.folder_path}/{self.selected_character}"
            await self.main_view(inter)
        except Exception as e:
            print(f"Ошибка в select_callback: {e}")
            import traceback
            traceback.print_exc()
    
    async def main_view(self, inter: disnake.MessageInteraction):
        self.clear_items()
        embed = await stats_rendering(inter.bot, self.user_id, self.character_path)
        if self.inter_user_id == self.user_id:
            inventory = disnake.ui.Button(label="Инвентарь (в разработке)", custom_id="inventory", style=disnake.ButtonStyle.red, row=0)
            dice_roll_menu = disnake.ui.Button(label="Броски кубиков", custom_id="dice_roll_menu", style=disnake.ButtonStyle.red, row=0)
            derived_edit = disnake.ui.Button(label="Изменить производные", custom_id="derived_edit", style=disnake.ButtonStyle.red, row=0)
            delete_char_btn = disnake.ui.Button(label="Удалить персонажа", style=disnake.ButtonStyle.red, row=1)
            delete_char_btn.callback = self.delete_char_callback
            derived_edit.callback = self.derived_edit_callback
            dice_roll_menu.callback = self.dice_roll_menu_callback
            inventory.callback = self.btn_character_inventory_callback
            self.add_item(delete_char_btn)
            self.add_item(dice_roll_menu)
            self.add_item(derived_edit)
            self.add_item(inventory)
        try:
            # 1. Пробуем отредактировать текущее сообщение (для кнопок и селекторов)
            await inter.response.edit_message(embed=embed, content=None, view=self)
        except disnake.errors.InteractionResponded:
            # 2. Если на интеракцию уже ответили (например, из модального окна)
            await inter.edit_original_response(embed=embed, content=None, view=self)
        except (disnake.errors.InteractionNotEditable, disnake.errors.HTTPException):
            # 3. Если сообщения еще нет (первый запуск команды) или оно недоступно для правки
            # Используем ephemeral=True, так как ты этого хотел изначально
            await inter.response.send_message(embed=embed, view=self)
    
    async def btn_character_inventory_callback(self, inter: disnake.MessageInteraction):
        """
        Точка входа: Проверка ролей ОБТ, проверка статуса ОБТ у персонажа и переход в инвентарь.
        """
        obt_roles = {1330594763312988244, 1497975380022263979, 668385755663695882}
        
        # Проверка наличия у участника хотя бы одной целевой роли
        user_roles = {role.id for role in inter.author.roles} if hasattr(inter.author, "roles") else set()
        if not user_roles.intersection(obt_roles):
            return await inter.response.send_message(
                "Вы не являетесь участником ОБТ. Запишитесь в соответствующей теме!", 
                ephemeral=True
            )

        # Проверяем, подтверждал ли уже игрок участие для ЭТОГО персонажа
        stats_file_path = os.path.join(self.character_path, "char_stats.json")
        needs_confirmation = True
        
        if os.path.exists(stats_file_path):
            try:
                async with aiofiles.open(stats_file_path, "r", encoding="utf-8") as f:
                    stats_data = json.loads(await f.read())
                
                # Если ключ money уже есть, инициализация ОБТ для персонажа пройдена
                if isinstance(stats_data, list) and len(stats_data) > 0 and "money" in stats_data[0]:
                    needs_confirmation = False
            except Exception:
                pass # В случае ошибки чтения пускаем через этап подтверждения для перезаписи

        # Если подтверждение не требуется, сразу открываем инвентарь
        if not needs_confirmation:
            await inter.response.defer()
            from inventory import PlayerInventoryMenu
            inventory_menu = PlayerInventoryMenu(
                parent_view=self, 
                folder_path=self.character_path, 
                interactor_id=inter.author.id
            )
            return await inventory_menu.send_inventory_window(inter)

        # Вывод диалога с подтверждением готовности (если money нет)
        embed = disnake.Embed(
            title="Подтверждение участия в тестировании",
            description="Вы действительно готовы принять участие?",
            color=disnake.Color.red()
        )
        
        confirm_view = OBTConfirmationView(
            parent_view=self,
            character_path=self.character_path,
            interactor_id=inter.author.id
        )
        await inter.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

#    async def btn_character_inventory_callback(self, inter: disnake.MessageInteraction):
#        """
#        Точка входа: Переводит интерфейс из меню персонажа в модуль инвентаря.
#        self.character_path — это путь вида 'user_profiles/ID_игрока/Имя_персонажа'
#        """
#        # Блокируем параллельные операции через замок конкретного персонажа
#        async with get_char_lock(self.character_path):
#            inv_file_path = os.path.join(self.character_path, "char_inventory.json")
#            
#            # Если у персонажа ещё нет файла инвентаря, создаём базовую пустую структуру
#            if not os.path.exists(inv_file_path):
#                default_inventory = {
#                    "equipment": {
#                        "weapon_slot": None,
#                        "melee_slot": None,
#                        "armor_slot": None,
#                        "head_slot": None,
#                        "mask_slot": None,
#                        "detector_anomaly_slot": None,
#                        "detector_artefact_slot": None,
#                        "eyes_slot": None,
#                        "ears_slot": None
#                    },
#                    "inventory": {
#                        "static": {},  # Складываемые вещи (патроны, медицина)
#                        "unique": {}   # Уникальные шмотки (оружие с дурабилити, костюмы)
#                    }
#                }
#                try:
#                    with open(inv_file_path, "w", encoding="utf-8") as f:
#                        json.dump(default_inventory, f, ensure_ascii=False, indent=4)
#                except Exception as e:
#                    return await inter.response.send_message(
#                        f"❌ Критическая ошибка создания файла инвентаря: {e}", 
#                        ephemeral=True
#                    )
#
#            # Создаём экземпляр меню инвентаря, передавая выбранного персонажа
#            
#            from inventory import PlayerInventoryMenu
#            
#            inventory_menu = PlayerInventoryMenu(
#                parent_view=self, 
#                folder_path=self.character_path, # Передаем путь К ПЕРСОНАЖУ, а не к юзеру
#                interactor_id=inter.author.id
#            )
#            
#            # Передаём управление инвентарю — он займет текущее сообщение
#            await inventory_menu.send_inventory_window(inter)

    async def dice_roll_menu_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        groups_dict = await load_skill_group_names()
        options = []
        for tech_name, display_name in groups_dict.items():
            options.append(
                disnake.SelectOption(
                    label=display_name,
                    value=tech_name
                )
            )
        if options:
            self.select = disnake.ui.Select(
                placeholder="Выберите группу навыков",
                options=options,
                custom_id="skill_group_select",
                min_values=1,
                row=1
            )
        self.select.callback = self.sg_select_callback
        self.add_item(self.select)

        self.back_main = disnake.ui.Button(label="Вернуться", custom_id="back_to_main", style=disnake.ButtonStyle.red, row=0) 
        self.back_main.callback = self.main_view
        self.add_item(self.back_main)

        await inter.response.edit_message(view=self)
    
    async def sg_select_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        if hasattr(inter.data, "values") and inter.data.values:
            self.selected_group = inter.data.values[0]
        all_groups = await load_skill_group_names()
        selected_group_display = all_groups.get(self.selected_group, self.selected_group)
        available_skills = await load_skills_by_group(self.selected_group)
        options = [
        disnake.SelectOption(label=display_name, value=tech_name)
        for tech_name, display_name in available_skills.items()
        ]
        if options:
            self.skill_select = disnake.ui.Select(
            placeholder=f"Выберите навык из группы {selected_group_display}",
            options=options,
            custom_id="specific_skill_select",
            row=1
        )
        self.skill_select.callback = self.add_roll_button
        self.add_item(self.skill_select)
        self.back_button = disnake.ui.Button(label="Назад к группам", style=disnake.ButtonStyle.red, row=0)
        self.back_button.callback = self.dice_roll_menu_callback # Возвращаемся в начало метода
        self.add_item(self.back_button)
        self.back_main = disnake.ui.Button(label="Вернуться в меню", custom_id="back_to_main", style=disnake.ButtonStyle.red, row=0) 
        self.back_main.callback = self.main_view
        self.add_item(self.back_main)
        await inter.response.edit_message(view=self)

    async def add_roll_button(self, inter: disnake.MessageInteraction):
        self.clear_items()
        self.selected_skill = inter.data.values[0]
        self.back_button = disnake.ui.Button(label="Назад к навыкам", style=disnake.ButtonStyle.red, row=0)
        self.back_button.callback = self.sg_select_callback # Возвращаемся в начало метода
        self.add_item(self.back_button)
        self.back_main = disnake.ui.Button(label="Вернуться в меню", custom_id="back_to_main", style=disnake.ButtonStyle.red, row=0) 
        self.back_main.callback = self.main_view
        self.add_item(self.back_main)
        self.btn_letsroll = disnake.ui.Button(label="Бросок!", custom_id="letsroll", style=disnake.ButtonStyle.red, row=0) 
        self.btn_letsroll.callback = self.letsroll
        self.add_item(self.btn_letsroll)
        self.add_modifier = disnake.ui.Button(label="Добавить модификатор", style=disnake.ButtonStyle.red, row=0)
        self.add_modifier.callback = self.add_modifier_modal # Возвращаемся в начало метода
        self.add_item(self.add_modifier)
        await inter.response.edit_message(view=self)
    
    async def add_modifier_modal(self, inter: disnake.MessageInteraction):
        prev_view = self
        await inter.response.send_modal(ModifierSendModal(prev_view))

    async def letsroll(self, inter: disnake.MessageInteraction):
        async with aiofiles.open(f"{self.character_path}/char_stats.json", "r", encoding="utf-8") as f:
            skills_data = json.loads(await f.read())
        char_name = skills_data[0]["char_name"]
        convertion = await calculate_modificators_dice_roll(skills_data, self.traits_lib, self.effects_lib)

        skill_group_level = 0
        calculated_level = 0
        skill_modificator = 0
        skill_group_modificator = 0
        skill_group_name = "Неизвестно"
        display_name = "Неизвестно"
        
        for group in convertion[1:7]:
            group_id = group.get("skill_group", [None])[0]
            if group_id == self.selected_group:
                skill_group_raw = group.get("skill_group", ["unknown", "Неизвестная группа", 0])
                
                # Конвертируем значение самой группы, если оно тоже в ОП
                raw_group_fp = skill_group_raw[2] if isinstance(skill_group_raw, list) else 0
                skill_group_modificator = skill_group_raw[3] if isinstance(skill_group_raw, list) else 0
                skill_group_level = raw_group_fp
                skill_group_name = skill_group_raw[1] if isinstance(skill_group_raw, list) else "Группа"
                
            for key, value in group.items():
                # Мы ищем совпадение ключа (ID навыка) с выбранным навыком
                if key == self.selected_skill:
                    # display_name — это первый элемент списка ["Пистолеты", 0, 0]
                    display_name = value[0] if isinstance(value, list) else key
                    
                    # Очки навыка (FP) — второй элемент (индекс 1)
                    skill_fp_value = value[1] if isinstance(value, list) and len(value) >= 2 else 0
                    
                    # Модификатор — третий элемент (индекс 2)
                    skill_modificator = value[2] if isinstance(value, list) and len(value) >= 3 else 0
                    
                    # Конвертируем FP в уровень
                    calculated_level = calculate_skill_level(skill_fp_value)
                    
                    # Нашли — выходим из внутреннего цикла
                    break
        
        base = skill_group_level + calculated_level + skill_modificator + skill_group_modificator
        dice_roll = random.randint(1, 10)
        details_list = [
        f"**Характеристика {skill_group_name}:** {skill_group_level} (база) + {skill_group_modificator} (мод)",
        f"**Навык {display_name}:** {calculated_level} (ур) + {skill_modificator} (мод)"
        ]

        total_dice = dice_roll
        history_str = ""
        
        if dice_roll == 10:
            total, history = self.roll_exploding_dice(10, "up")
            total_dice = dice_roll + total
            history_str = " + " + " + ".join(map(str, history))
            details_list.append(f"**Первый куб:** {dice_roll}\n**Взрывы (вверх):** {history}")
            
        elif dice_roll == 1:
            dice_roll_down = random.randint(1, 10)
            details_list.append(f"**Первый куб:** {dice_roll}\n**Куб провала:** {dice_roll_down}")
            
            if dice_roll_down == 1:
                explosions_total, history = self.roll_exploding_dice(10, "down") 
                # Внимание: теперь history возвращает положительные числа!
                total_dice = -(dice_roll + dice_roll_down + explosions_total)
                history_str = f" - {dice_roll_down} - {' - '.join(map(str, history))}"
                details_list.append(f"**Взрывы (вниз):** {history}")
            else:
                total_dice = -(dice_roll + dice_roll_down)
                history_str = f" - {dice_roll_down}"
        else:
            details_list.append(f"**Значение кубика:** {dice_roll}")

        final_result = base + total_dice + self.modifier
            
            # Формируем строку формулы
        char_part = f"{skill_group_level} + {skill_group_modificator} + {calculated_level} + {skill_modificator}"
            
            # Собираем правую часть (кубики и модификатор ГМа)
        dice_part = f"{dice_roll}{history_str}"
        if self.modifier != 0:
            dice_part += f" + {self.modifier}" if self.modifier > 0 else f" - {abs(self.modifier)}"
            details_list.append(f"**Пользовательский модификатор:** {self.modifier}")

            # Итоговая строка для create_embed_bs
        if total_dice >= 0:
            full_formula = f"{char_part} + {dice_roll} = {final_result}"
        else:
            # Для провалов, где total_dice уже включает в себя dice_roll_down и взрывы (отрицательный)
            full_formula = f"{char_part} - {dice_part} = {final_result}"

        embed = create_embed_bs(
            f"Бросок по навыку \"{display_name}\" ({char_name})", 
            full_formula
        )
        
        self.details_cache = "\n".join(details_list) # Сохраняем строку с деталями в объект View
        
        extra_data = self.details_cache
        
        view = DiceDump(extra_data)
        
        await inter.send(embed=embed, view=view)
    
    def roll_exploding_dice(self, sides, direction):
        rolls = []
        while True:
            roll = random.randint(1, sides)
            rolls.append(roll)
            # Взрыв вверх на макс, взрыв вниз на 1
            if (direction == "up" and roll < sides) or (direction == "down" and roll > 1):
                break
        return sum(rolls), rolls

    async def derived_edit_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        choices = [
            ("ПЗ", "1"), ("МЗ", "2"), ("РЗ", "3"), ("Переносимый вес", "4"), ("Репутация", "5")
        ]
        options = [
            disnake.SelectOption(label=name, value=val) 
            for name, val in choices
        ]
        if options:
            select = disnake.ui.Select(
                placeholder="Выберите производную...",
                options=options,
                custom_id="derived_editor",
                min_values=1,
                row=1
            )
        select.callback = self.derived_editor_select_callback
        self.add_item(select)
        exit_btn = disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.red, row=0)
        exit_btn.callback = self.main_view
        self.add_item(exit_btn)
        await inter.response.edit_message(view=self)

    async def derived_editor_select_callback(self, inter: disnake.MessageInteraction):
        bruh = inter.data.values[0]
        self.selected_derived = int(bruh)
        prev_view = self
        operation_number = 14
        
        from utems import UnitedTraitsEffectManagmentSystemModal
        
        await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
            "Укажите значение", 
            "Оно прибавится к производной", 
            "А отрицательное - вычтется",
            "edit_derived",
            "1",
            "5",
            operation_number,
            prev_view
            )
        )

    async def derived_editor_callback(self, inter: disnake.MessageInteraction, result):
        int_result = int(result)
        async with aiofiles.open(f"{self.character_path}/char_stats.json", "r", encoding="utf-8") as f:
            skills_data = json.loads(await f.read())
        option = self.selected_derived
        async with aiofiles.open("chars_data/traits_lib.json", "r", encoding="utf-8") as f:
            traits_lib = json.loads(await f.read())
        async with aiofiles.open("chars_data/effects_lib.json", "r", encoding="utf-8") as f:
            effects_lib = json.loads(await f.read())
        
        skills_data_for_calc = copy.deepcopy(skills_data)
        convertion = await calculate_modificators(skills_data_for_calc, traits_lib, effects_lib, self.character_path)
        source = convertion[0]
    
        actual_heal_points = source.get("heal_points", [0])[0]
        actual_mental_points = source.get("mental_points", [0])[0]
        actual_radiation_points = source.get("radiation_points", [0])[0]
        actual_carry_weight = source.get("carry_weight", [0])[0]

        heal_modificator = source.get("heal_points", [0])[1]
        mental_modificator = source.get("mental_points", [0])[1]
        radiation_modificator = source.get("radiation_points", [0])[1]
    
        skill_persistence = 0
        skill_persistence_modificators = 0

        # 3. Пытаемся найти стойкость
        res_persistence = find_skill(convertion, "skill_persistence")
        if res_persistence:
            skill_persistence = calculate_skill_level(res_persistence[1])
            skill_persistence_modificators = res_persistence[2]

        body_value = int_value = 0
        body_modificator = int_modificator = 0
        for group in convertion[1:]:
            group_info = group.get("skill_group")
            if group_info:
                g_id = group_info[0]
                if g_id == "body":
                    body_value = int(group_info[2])
                    body_modificator = int(group_info[3])
                elif g_id == "intellect":
                    int_value = int(group_info[2])
                    int_modificator = int(group_info[3])
        body_value += body_modificator
        int_value += int_modificator
        
        max_heal = body_value * 5 + 15 + skill_persistence + skill_persistence_modificators + heal_modificator
        max_radiation = body_value * 5 + 15 + radiation_modificator
        max_mental = int_value * 5 + 15 + mental_modificator
    
        if option == 1:
            if actual_heal_points == max_heal and int_result > 0:
                await self.main_view(inter) 
                return await inter.send(content="Уже достигнут максимум по параметру.", ephemeral=True)
            math = actual_heal_points + int_result
            if math > max_heal:
                int_result = max_heal - actual_heal_points
            option_name = "heal_points"
        elif option == 2:
            if actual_mental_points == max_mental and int_result > 0:
                await self.main_view(inter)
                return await inter.send(content="Уже достигнут максимум по параметру.", ephemeral=True)
            math = actual_mental_points + int_result
            if math > max_mental:
                int_result = max_mental - actual_mental_points
            option_name = "mental_points"
        elif option == 3:
            if actual_radiation_points == max_radiation:
                await self.main_view(inter)
                return await inter.send(content="Уже достигнут максимум по параметру. И это плохо!", ephemeral=True)
            math = actual_radiation_points + int_result
            if math > max_radiation:
                int_result = max_radiation - actual_radiation_points
            option_name = "radiation_points"
        elif option == 4:
            math = actual_carry_weight - int_result
            if math < 1 and int_result < 0:
                await self.main_view(inter)
                return await inter.send(content="Опустить вес ниже нуля нельзя.", ephemeral=True)
            option_name = "carry_weight"
        elif option == 5:
            option_name = "reputation"
        
        skills_data[0][option_name][0] += int_result

        character_stats_path = f"{self.character_path}/char_stats.json"
        async with get_char_lock(self.character_path):
            async with aiofiles.open(character_stats_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))

        await self.main_view(inter)

    async def delete_char_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        confirm_delete_char = disnake.ui.Button(label="Подтвердить", style=disnake.ButtonStyle.red, row=1)
        exit_btn = disnake.ui.Button(label="Отменить", style=disnake.ButtonStyle.red, row=1)
        confirm_delete_char.callback = self.delete_folder_button
        exit_btn.callback = self.main_view
        self.add_item(exit_btn)
        self.add_item(confirm_delete_char)
        await inter.response.edit_message(content="Вы точно уверены, что хотите удалить вашего персонажа?", embed=None, view=self)

    async def delete_folder_button(self, inter: disnake.MessageInteraction):
        if os.path.exists(self.character_path):
            try:
                await inter.response.defer()
                shutil.rmtree(self.character_path, onerror=remove_readonly) # Используем onexc
                self.stop()
                
                try:
                    await inter.edit_original_message(embed=None, view=None, content="**Персонаж удалён.**")
                except disnake.NotFound:
                    print("Сообщение удаления уже было уничтожено пользователем.")
                    
            except Exception as e:
                await inter.send(f"Ошибка при удалении: {e}", ephemeral=True)
        else:
            await inter.send("Ошибка: Папка не найдена.", ephemeral=True)
# Отображение листа персонажа после выбора оного из списка

class DiceDump(disnake.ui.View):
    def __init__(self, extra_data: str):
        # Используем None для бессрочной работы кнопок
        super().__init__(timeout=None) 
        self.extra_data = extra_data

    @disnake.ui.button(label="Подробнее", style=disnake.ButtonStyle.red, row=0)
    async def extend_callback(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        # Берем первый эмбед из сообщения
        embed = inter.message.embeds[0]
        
        # Проверка, чтобы не плодить поля при повторном нажатии (на всякий случай)
        if not any(field.name == "Подробности броска" for field in embed.fields):
            embed.add_field(name="Подробности броска", value=self.extra_data, inline=False)
        
        # Убираем кнопку после использования, чтобы не перегружать интерфейс
        self.clear_items()
        
        # Редактируем сообщение с обновленным эмбедом и пустой вьюшкой
        await inter.response.edit_message(embed=embed, view=self)

class ModifierSendModal(disnake.ui.Modal):
    def __init__(self, return_view):
        self.return_view = return_view
        components = [
            disnake.ui.TextInput(
                label=f"Укажите модификатор",
                placeholder="...",
                custom_id="modifier",
                style=disnake.TextInputStyle.short,
                min_length=1,
                max_length=3
            )
        ]
        super().__init__(title=f"Пользовательский модификатор", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        value = inter.text_values["modifier"]
        try:
            modifier = int(value)
            self.return_view.modifier = modifier
            await inter.response.edit_message(view=self.return_view)
        except ValueError:
            await inter.response.send_message("Пожалуйста, введите целое положительное число!", ephemeral=True)
        except Exception as e:
            import traceback
            traceback.print_exc() 
            await inter.response.send_message(f"Тип ошибки: {type(e).__name__}, Суть: {e}", ephemeral=True)

class CharacterEditView(disnake.ui.View):
    def __init__(self, user_id: str, folder_path: str):
        super().__init__(timeout=900)
        self.user_id = user_id
        self.folder_path = folder_path
        self.character_path = None
        self.message = None
        self.character_folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        options = [
            disnake.SelectOption(label=folder, value=folder)
            for folder in self.character_folders
        ]
        if options:
            select = disnake.ui.Select(
                placeholder="Выберите персонажа",
                options=options,
                custom_id="character_select",
                min_values=1
            )
            select.callback = self.char_select_callback
            self.add_item(select)

    async def char_select_callback(self, inter: disnake.MessageInteraction):
        self.selected_character = inter.data.values[0]
        self.character_path = f"{self.folder_path}/{self.selected_character}"
        self.character_stats_path = f"{self.character_path}/char_stats.json"
        await self.editor_home_callback(inter)

    async def editor_home_callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(with_message=False)
        self.clear_items()
        new_embed = await stats_rendering(inter.bot, self.user_id, self.character_path)
        skill_editor = disnake.ui.Button(label="Редактировать навыки персонажа", custom_id="edit_skills", style=disnake.ButtonStyle.red)
        skill_editor.callback = self.skill_editor_callback
        self.add_item(skill_editor)
        derived_edit = disnake.ui.Button(label="Изменить производные", custom_id="derived_edit", style=disnake.ButtonStyle.red)
        derived_edit.callback = self.derived_edit_callback
        self.add_item(derived_edit)
        if not inter.response.is_done():
            await inter.response.edit_message(embed=new_embed, view=self)
        else:
            await inter.edit_original_message(embed=new_embed, view=self)

    async def skill_editor_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()      
        editor_home = disnake.ui.Button(label="В меню опций", custom_id="editor_home", style=disnake.ButtonStyle.red) 
        editor_home.callback = self.editor_home_callback
        groups_dict = await load_skill_group_names()
        options = []
        for tech_name, display_name in groups_dict.items():
            options.append(
                disnake.SelectOption(
                    label=display_name,
                    value=tech_name
                )
            )
        if options:
            select = disnake.ui.Select(
                placeholder="Выберите группу навыков",
                options=options,
                custom_id="skill_group_select",
                min_values=1
            )
            select.callback = self.sg_select_callback
            self.add_item(select)
        self.add_item(editor_home)
        await inter.response.edit_message(view=self)
    
    async def sg_select_callback(self, inter: disnake.MessageCommandInteraction):
        if hasattr(inter.data, "values") and inter.data.values:
            self.selected_group = inter.data.values[0]
        all_groups = await load_skill_group_names()
        selected_group_display = all_groups.get(self.selected_group, self.selected_group)
        self.clear_items()
        available_skills = await load_skills_by_group(self.selected_group)
        options = [
        disnake.SelectOption(label=display_name, value=tech_name)
        for tech_name, display_name in available_skills.items()
        ]
        if options:
            skill_select = disnake.ui.Select(
            placeholder=f"Выберите навык из группы {selected_group_display}",
            options=options,
            custom_id="specific_skill_select"
        )
        skill_select.callback = self.skill_final_selection_callback 
        self.add_item(skill_select)
        back_button = disnake.ui.Button(label="Назад к группам", style=disnake.ButtonStyle.red)
        back_button.callback = self.skill_editor_callback # Возвращаемся в начало метода
        self.add_item(back_button)
        editor_home = disnake.ui.Button(label="В меню опций", custom_id="editor_home", style=disnake.ButtonStyle.red) 
        editor_home.callback = self.editor_home_callback
        self.add_item(editor_home)
        await inter.response.edit_message(view=self)     
    
    async def skill_final_selection_callback(self, inter: disnake.MessageInteraction):
        # Сохраняем техническое имя выбранного навыка в self, чтобы кнопки знали, что менять
        self.selected_skill_tech = inter.data.values[0]
        
        # Сразу обновляем кнопки на панель управления
        await self.update_control_panel(inter)

    async def update_control_panel(self, inter: disnake.MessageInteraction):
        self.clear_items()
        
        # Кнопка Минус
        btn_minus = disnake.ui.Button(label="-1 ОП", style=disnake.ButtonStyle.red, custom_id="skill_minus")
        btn_minus.callback = self.change_skill_points_callback
        
        # Кнопка Плюс
        btn_plus = disnake.ui.Button(label="+1 ОП", style=disnake.ButtonStyle.red, custom_id="skill_plus")
        btn_plus.callback = self.change_skill_points_callback
        
        # Кнопка Назад (к выбору навыков в той же группе)
        btn_back = disnake.ui.Button(label="К списку навыков", style=disnake.ButtonStyle.red)
        btn_back.callback = self.sg_select_callback # Используем старый коллбэк, он перерисует список

        editor_home = disnake.ui.Button(label="В меню опций", custom_id="editor_home", style=disnake.ButtonStyle.red) 
        editor_home.callback = self.editor_home_callback
        
        self.add_item(btn_minus)
        self.add_item(btn_back)
        self.add_item(btn_plus)
        self.add_item(editor_home)
        
        # Обновляем сообщение (эмбед перерендерится, чтобы показать актуальные ОП)
        new_embed = await stats_rendering(inter.bot, self.user_id, self.character_path)
        await inter.response.edit_message(embed=new_embed, view=self)

    async def change_skill_points_callback(self, inter: disnake.MessageInteraction):
        # Определяем, плюс это или минус
        MAX_SKILL_FP = 21
        delta = 1 if inter.component.custom_id == "skill_plus" else -1
        
        # Читаем файл
        character_stats_path = f"{self.character_path}/char_stats.json"
        async with get_char_lock(self.character_path): 
            async with aiofiles.open(character_stats_path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
        
        # Ищем наш навык во всех группах
        skill_found = False
        for group in data[1:]:
            if self.selected_skill_tech in group:
                current_op = group[self.selected_skill_tech][1]
                if delta > 0 and current_op == MAX_SKILL_FP:
                    # Можно отправить тихое уведомление, что предел достигнут
                    await inter.response.send_message(
                        f"Навык уже развит до максимума (10 уровень, {MAX_SKILL_FP} ОП)!", 
                        ephemeral=True
                    )
                    return   
                new_op = max(0, current_op + delta)
                group[self.selected_skill_tech][1] = new_op
                skill_found = True
                break
                
        if skill_found:
            # Сохраняем обновленный JSON
            async with aiofiles.open(character_stats_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))
        
        # Перерисовываем всё, чтобы ГМ сразу увидел результат в таблице
        new_embed = await stats_rendering(inter.bot, self.user_id, self.character_path)
        
        # Используем edit_original_message, если работаем через коллбэк кнопки
        await inter.response.edit_message(embed=new_embed, view=self)    

    async def derived_edit_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        choices = [
            ("ПЗ", "1"), ("МЗ", "2"), ("РЗ", "3"), ("Переносимый вес", "4"), ("Репутация", "5")
        ]
        options = [
            disnake.SelectOption(label=name, value=val) 
            for name, val in choices
        ]
        if options:
            select = disnake.ui.Select(
                placeholder="Выберите группу навыков",
                options=options,
                custom_id="derived_editor",
                min_values=1,
                row=1
            )
        select.callback = self.derived_editor_select_callback
        self.add_item(select)
        exit_btn = disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.red, row=0)
        exit_btn.callback = self.editor_home_callback
        self.add_item(exit_btn)
        await inter.response.edit_message(view=self)

    async def derived_editor_select_callback(self, inter: disnake.MessageInteraction):
        bruh = inter.data.values[0]
        self.selected_derived = int(bruh)
        prev_view = self
        operation_number = 14
        
        from utems import UnitedTraitsEffectManagmentSystemModal

        await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
            "Укажите значение", 
            "Оно прибавится к производной", 
            "А отрицательное - вычтется",
            "edit_derived",
            "1",
            "5",
            operation_number,
            prev_view
            )
        )

    async def derived_editor_callback(self, inter: disnake.MessageInteraction, result):
        int_result = int(result)
        async with aiofiles.open(f"{self.character_path}/char_stats.json", "r", encoding="utf-8") as f:
            skills_data = json.loads(await f.read())
        option = self.selected_derived
        async with aiofiles.open("chars_data/traits_lib.json", "r", encoding="utf-8") as f:
            traits_lib = json.loads(await f.read())
        async with aiofiles.open("chars_data/effects_lib.json", "r", encoding="utf-8") as f:
            effects_lib = json.loads(await f.read())
        
        skills_data_for_calc = copy.deepcopy(skills_data)
        convertion = await calculate_modificators(skills_data_for_calc, traits_lib, effects_lib, self.character_path)
        source = convertion[0]
    
        actual_heal_points = source.get("heal_points", [0])[0]
        actual_mental_points = source.get("mental_points", [0])[0]
        actual_radiation_points = source.get("radiation_points", [0])[0]
        actual_carry_weight = source.get("carry_weight", [0])[0]

        heal_modificator = source.get("heal_points", [0])[1]
        mental_modificator = source.get("mental_points", [0])[1]
        radiation_modificator = source.get("radiation_points", [0])[1]
    
        skill_persistence = 0
        skill_persistence_modificators = 0

        # 3. Пытаемся найти стойкость
        res_persistence = find_skill(convertion, "skill_persistence")
        if res_persistence:
            skill_persistence = calculate_skill_level(res_persistence[1])
            skill_persistence_modificators = res_persistence[2]

        body_value = int_value = 0
        body_modificator = int_modificator = 0
        for group in convertion[1:]:
            group_info = group.get("skill_group")
            if group_info:
                g_id = group_info[0]
                if g_id == "body":
                    body_value = int(group_info[2])
                    body_modificator = int(group_info[3])
                elif g_id == "intellect":
                    int_value = int(group_info[2])
                    int_modificator = int(group_info[3])
        body_value += body_modificator
        int_value += int_modificator
        
        max_heal = body_value * 5 + 15 + skill_persistence + skill_persistence_modificators + heal_modificator
        max_radiation = body_value * 5 + 15 + radiation_modificator
        max_mental = int_value * 5 + 15 + mental_modificator
    
        if option == 1:
            if actual_heal_points == max_heal and int_result > 0:
                await self.editor_home_callback(inter) 
                return await inter.send(content="Уже достигнут максимум по параметру.", ephemeral=True)
            math = actual_heal_points + int_result
            if math > max_heal:
                int_result = max_heal - actual_heal_points
            option_name = "heal_points"
        elif option == 2:
            if actual_mental_points == max_mental and int_result > 0:
                await self.editor_home_callback(inter)
                return await inter.send(content="Уже достигнут максимум по параметру.", ephemeral=True)
            math = actual_mental_points + int_result
            if math > max_mental:
                int_result = max_mental - actual_mental_points
            option_name = "mental_points"
        elif option == 3:
            if actual_radiation_points == max_radiation:
                await self.editor_home_callback(inter)
                return await inter.send(content="Уже достигнут максимум по параметру. И это плохо!", ephemeral=True)
            math = actual_radiation_points + int_result
            if math > max_radiation:
                int_result = max_radiation - actual_radiation_points
            option_name = "radiation_points"
        elif option == 4:
            math = actual_carry_weight - int_result
            if math < 1 and int_result < 0:
                await self.editor_home_callback(inter)
                return await inter.send(content="Опустить вес ниже нуля нельзя.", ephemeral=True)
            option_name = "carry_weight"
        elif option == 5:
            option_name = "reputation"
        
        skills_data[0][option_name][0] += int_result

        character_stats_path = f"{self.character_path}/char_stats.json"
        async with get_char_lock(self.character_path):
            async with aiofiles.open(character_stats_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))

        await self.editor_home_callback(inter)   
# Редактор персонажа для ГМов и ОС

class CharacterCreationView(disnake.ui.View):
    def __init__(self, user_id: str, bot):
        super().__init__(timeout=900)
        self.user_id = user_id
        self.user_id = int(user_id)
        self.bot = bot
    
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True
    
    @disnake.ui.button(label="Создать нового персонажа", style=disnake.ButtonStyle.red)
    async def select_callback(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        inter.bot.active_creations[self.user_id] = None
        await inter.response.send_modal(CharacterCreationModal(str(inter.author.id), f"user_profiles/{inter.author.id}", bot=self.bot))
        msg = await inter.original_response()
        inter.bot.active_creations[self.user_id] = msg.id
# Отображение окна с предложением создать персонажа, если таковых нет

class CharacterCreationModal(disnake.ui.Modal):
    def __init__(self, user_id: str, folder_path: str, rename_flaq=False, return_view=None, bot=None):
        self.user_id = user_id
        self.user_id = int(user_id)
        self.folder_path = folder_path
        self.rename_flaq = rename_flaq
        self.old_view = return_view
        self.bot = bot
        components = [
            disnake.ui.TextInput(
                label="Имя персонажа",
                placeholder="Введите имя персонажа",
                custom_id="character_name",
                style=disnake.TextInputStyle.short,
                min_length=1,
                max_length=50
            )
        ]
        super().__init__(title="Создание персонажа", custom_id="character_creation_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        character_name = inter.text_values["character_name"].strip()
        clean_name = sanitize_name(character_name)
        character_name = clean_name
        if not clean_name:
            return await inter.followup.send(
            "Имя не может быть пустым или состоять только из спецсимволов!", 
            ephemeral=True
        )
        character_path = f"{self.folder_path}/{character_name}"
        try:
            if os.path.exists(character_path):
                return await inter.response.send_message("У вас уже существует персонаж с таким именем!", ephemeral=True)
            os.makedirs(character_path, exist_ok=True)
            async with aiofiles.open("chars_data/blank_chars.json", "r", encoding="utf-8") as f:
                blank_chars = json.loads(await f.read())
            with open(f"{character_path}/char_stats.json", "w", encoding="utf-8") as f:
                blank_chars[0]["char_name"] = str(character_name)
                json.dump(blank_chars, f, indent=4, ensure_ascii=False)
            if self.rename_flaq == False:
                view = SkillPointDistributionView(
                    user_id=self.user_id,
                    skill_groups=blank_chars,
                    character_path=character_path,
                    bot=self.bot
                )
                embed = await view.create_embed()
                await inter.response.edit_message(embed=embed, view=view)
                view.message = await inter.original_response()
                msg = await inter.original_response()
                self.bot.active_creations[self.user_id] = {"msg_id": msg.id, "folder_path": character_path}
            else:
                await inter.response.defer(with_message=False, ephemeral=True)
                await self.old_view.change_name(inter, character_name)
        except Exception as e:
            await inter.response.send_message(f"Ошибка при создании персонажа: {str(e)}", ephemeral=True)
# Вызов модального окна для запроса имени персонажапри селекторе характеристик при создании персонажа

class SkillPointDistributionModal(disnake.ui.Modal):
    def __init__(self, user_id: str, group_id: str, group_name: str, view):
        self.user_id = user_id
        self.group_id = group_id
        self.group_name = group_name
        self.view = view
        components = [
            disnake.ui.TextInput(
                label=f"Очки для {group_name}",
                placeholder="Введите число от 2 до 8",
                custom_id="skill_points",
                style=disnake.TextInputStyle.short,
                min_length=1,
                max_length=2
            )
        ]
        super().__init__(title=f"Очки для {group_name}", custom_id="skill_points_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        points_input = inter.text_values["skill_points"].strip()
        try:
            points = int(points_input)
            if points < 2 or points > 8:
                await inter.response.send_message(f"Очки должны быть от 2 до 8 для группы {self.group_name}!", ephemeral=True)
                return
            current_points = sum(self.view.points_distributed.values())
            new_total = current_points - self.view.points_distributed.get(self.group_id, 2) + points
            if new_total > 35:
                await inter.response.send_message(f"Нельзя распределить больше 35 очков! Осталось: {35 - current_points}", ephemeral=True)
                return
            self.view.points_distributed[self.group_id] = points
            self.view.points_used = new_total
            self.view.points_remaining = 35 - new_total
            embed = await self.view.create_embed()
            await inter.response.edit_message(embed=embed, view=self.view)
        except ValueError:
            await inter.response.send_message("Пожалуйста, введите число!", ephemeral=True)
        except Exception as e:
            await inter.response.send_message("Что-то пошло не так, повторите попытку!", ephemeral=True)
# Вызов модального окна при селекторе характеристик при создании персонажа

class SkillPointDistributionView(BaseWorkshopView):
    def __init__(self, user_id: str, skill_groups: list, character_path: str, bot):
        super().__init__(bot, user_id, character_path)
        self.message = None
        self.skill_groups = skill_groups
        self.character_path = character_path
        self.points_distributed = {
            group["skill_group"][0]: 2
            for group in skill_groups
            if isinstance(group.get("skill_group"), list) and len(group["skill_group"]) >= 2 and group["skill_group"][0]
        }
        self.points_used = sum(self.points_distributed.values())
        self.points_remaining = 35 - self.points_used
        self.selected_group = None
        self.message = None

        valid_groups = [
            group for group in skill_groups
            if isinstance(group.get("skill_group"), list) and len(group["skill_group"]) >= 2 and group["skill_group"][0]
        ]
        if not valid_groups:
            print(f"Error: No valid skill groups found in blank_chars.json: {skill_groups}")
            return

        options = [
            disnake.SelectOption(
                label=group["skill_group"][1],
                value=group["skill_group"][0]
            ) for group in valid_groups
        ]
        if options:
            select = disnake.ui.Select(
                placeholder="Выберите группу навыков",
                options=options,
                custom_id="skill_group_select",
                min_values=1,
                max_values=1
            )
            select.callback = self.select_callback
            self.add_item(select)

            set_points_button = disnake.ui.Button(
                label="Установить очки",
                style=disnake.ButtonStyle.red,
                custom_id="set_points"
            )
            set_points_button.callback = self.set_points_callback
            self.add_item(set_points_button)

            confirm_button = disnake.ui.Button(
                label="Подтвердить",
                style=disnake.ButtonStyle.red,
                custom_id="confirm_distribution"
            )
            confirm_button.callback = self.confirm_callback
            self.add_item(confirm_button)
    
    @disnake.ui.button(label="Справка", style=disnake.ButtonStyle.red, row=0)
    async def faq(self, button: disnake.ui.Button, inter: disnake.Interaction):
        view = HelpPaginator()
        embed = disnake.Embed(title=view.pages[0]["title"], description=view.pages[0]["description"], color=disnake.Color.red())
        await inter.send(embed=embed, view=view, ephemeral=True)

    async def create_embed(self):
        embed = disnake.Embed(
            title="Распределение очков характеристик",
            description=f"Осталось очков: {self.points_remaining}\nВыберите группу и установите очки (2-8 для каждой группы).",
            color=disnake.Color.red()
        )
        for group_id, points in self.points_distributed.items():
            group_name = None
            for group in self.skill_groups:
                if isinstance(group.get("skill_group"), list) and len(group["skill_group"]) >= 2 and group["skill_group"][0] == group_id:
                    group_name = group["skill_group"][1]
                    break
            if group_name:
                embed.add_field(
                    name=group_name,
                    value=f"Очки: {points}",
                    inline=True
                )
            else:
                print(f"Warning: Group ID {group_id} not found in skill_groups: {self.skill_groups}")
                embed.add_field(
                    name=f"Неизвестная группа (ID: {group_id})",
                    value=f"Очки: {points}",
                    inline=True
                )
        embed.set_footer(text="© By Bon Shinomiya")
        return embed

    async def select_callback(self, inter: disnake.MessageInteraction):
        self.selected_group = inter.data.values[0]
        await inter.response.defer()

    async def set_points_callback(self, inter: disnake.MessageInteraction):
        if not self.selected_group:
            await inter.response.send_message("Пожалуйста, выберите группу навыков!", ephemeral=True)
            return
        group_name = None
        for group in self.skill_groups:
            if isinstance(group.get("skill_group"), list) and len(group["skill_group"]) >= 2 and group["skill_group"][0] == self.selected_group:
                group_name = group["skill_group"][1]
                break
        if not group_name:
            await inter.response.send_message("Ошибка: выбранная группа не найдена!", ephemeral=True)
            return
        modal = SkillPointDistributionModal(self.user_id, self.selected_group, group_name, self)
        await inter.response.send_modal(modal)

    async def confirm_callback(self, inter: disnake.MessageInteraction):
        if self.points_remaining != 0:
            await inter.response.send_message(f"Пожалуйста, распределите все очки! Осталось: {self.points_remaining}", ephemeral=True)
            return 
        char_stats_path = f"{self.character_path}/char_stats.json"
        try:
            async with aiofiles.open(char_stats_path, "r", encoding="utf-8") as f:
                char_stats = json.loads(await f.read())
            for group in char_stats:
                group_id = group["skill_group"][0] if isinstance(group.get("skill_group"), list) and len(group["skill_group"]) >= 2 else None
                if group_id in self.points_distributed:
                    group["skill_group"][2] = self.points_distributed[group_id]
            
            # Запись переведена на асинхронный aiofiles с сохранением кириллицы
            async with aiofiles.open(char_stats_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(char_stats, indent=4, ensure_ascii=False))
            self.stop()
            self.clear_items()
            new_view = CharacterQuestionnaireStart(user_id=self.user_id, folder_path=self.character_path, bot=self.bot)
            new_view.message = self.message
            embed = disnake.Embed(
                title="Следующий этап",
                description="И так, основа ваша персонажа сделана. Но теперь, о нём надо рассказать чуть больше. В этом, поможет опросник, в котором вы определите черты его биографии, которые могут ему помочь в Зоне.",
                color=disnake.Color.red()
            )
            embed.set_footer(text="© By Bon Shinomiya")
            await inter.response.edit_message(embed=embed, view=new_view)
        except Exception as e:
            await inter.response.send_message(f"Ошибка при сохранении данных: {str(e)}", ephemeral=True)
# Отображение списка характеристик и текущего их значения при создании персонажа

class CharacterQuestionnaireStart(disnake.ui.View):
    def __init__(self, user_id: str, folder_path: str, bot):
        super().__init__(timeout=900)
        self.bot=bot
        self.user_id = user_id
        self.folder_path = folder_path
        self.view = self
        self.message = None
        self.next_step_view = CharacterQuestionnaire(self.folder_path, self.user_id, self.bot)

    @disnake.ui.button(label="Начать прохождение", style=disnake.ButtonStyle.red, row=0)
    async def select_callback(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        async with aiofiles.open("chars_data/blank_short_story.json", "r", encoding="utf-8") as f:
            short_story = json.loads(await f.read())
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(short_story, ensure_ascii=False, indent=4))
        self.next_step_view.message = self.message
        
        await inter.response.send_modal(CharacterQuestionnaireAgeModal(self.folder_path, self.next_step_view))

class CharacterQuestionnaireAgeModal(disnake.ui.Modal):
    def __init__(self, folder_path: str, next_step_view=None, return_view=None):
        self.folder_path = folder_path
        self.next_view=next_step_view
        self.return_view = return_view
        components = [
            disnake.ui.TextInput(
                label=f"Укажите возраст вашего персонажа",
                placeholder="Пределы возраста - от 18 до 60 лет.",
                custom_id="age",
                style=disnake.TextInputStyle.short,
                min_length=1,
                max_length=2
            )
        ]
        super().__init__(title=f"Возраст персонажа", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        age = inter.text_values["age"]
        try:
            points = int(age)
            if not (18 <= points <= 60):
                return await inter.response.send_message(f"Пределы возраста - от 18 до 60 лет!", ephemeral=True)
            if self.next_view:
                await self.next_view.selectors_block(inter, age, start=True)
            if self.return_view:
                age = int(age)
                math_age = int(age)
                if math_age >= 18 and math_age < 31:
                    math_age = math_age - 18
                    fp = math_age // 2 + 2
                elif math_age >= 31 and math_age < 51:
                    math_age = math_age - 31
                    fp = math_age // 3 + 8
                elif math_age >= 51:
                    math_age = math_age - 51
                    fp = math_age // 4 + 14
                await self.return_view.change_age(inter, age, fp)
        except ValueError:
            await inter.response.send_message("Пожалуйста, введите целое положительное число!", ephemeral=True)
        except Exception as e:
            import traceback
            traceback.print_exc() 
            await inter.response.send_message(f"Тип ошибки: {type(e).__name__}, Суть: {e}", ephemeral=True)

class CharacterQuestionnaire(BaseWorkshopView):
    def __init__(self, folder_path: str, user_id: str, bot):
        super().__init__(bot, user_id, folder_path)
        self.folder_path = folder_path
        self.message = None
        self.age = None
        self.fp = None
        self.current_fp = None
        self.cq = None
        self.cq_old_pos = 0
        self.role_check = False
        self.access_rank = 0
        self.directions = 0
        self.education = 0
        self.backup_create = False
        self.skill_add = 0
        self.old_view = None
        self.new_view = None
        self.old_embed = None
        self.q11_complete = False
        self.back = False
        self.fp_edit = False
        self.q11_fp_back = False
        self.data = None
        self.value = 0
        self.selected_positive_traits_folder = None
        self.selected_negative_traits_folder = None
        with open("chars_data/questions_lib.json", "r", encoding="utf-8") as f:
            self.questions = json.load(f)
        with open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
            self.stats_list = json.load(f)

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True

    async def start_value_write(self, age: int, fp: int):
        # 1. Читаем (теперь это сразу словарь)
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())
        
        # 2. Модифицируем данные напрямую
        # Обратите внимание: если age и fp в JSON тоже должны быть просто числами, 
        # а не списками [0], можно убрать [0] и здесь. 
        # Но если в JSON структура осталась "age": [0], то оставляем как есть:
        ssd_dict["age"][0] = age
        ssd_dict["fp"][0] = fp
        ssd_dict["current_fp"][0] = fp
        
        self.current_fp = fp
        self.fp = fp
        
        # 3. Сохраняем чистый словарь
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
    
    async def rewrite_selectors(self, question_name: str, value: int, req_fp: int = None):
        # 1. Читаем чистый словарь
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())
        
        # 2. Записываем значение вопроса
        # Судя по вашим данным, вы храните ответы как списки [значение]
        ssd_dict[str(question_name)] = [value]
        
        # 3. Обновляем очки, если переданы
        if req_fp is not None:
            ssd_dict["current_fp"][0] += req_fp
            
        # 4. Сохраняем чистый словарь
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))

    async def create_selector_questionnaire(self, placeholder: str, choices: list, q_name: str):
        options = [
            disnake.SelectOption(label=name, value=val) 
            for name, val in choices
        ]
        select = disnake.ui.Select(
            placeholder=f"{placeholder}",
            options=options,
            custom_id=f"q_{q_name}",
            row=1
            )
        return select
    
    def recalculate_all_fp(self, ssd_dict):
        """Полностью пересчитывает СО с нуля на основе чистых ответов в JSON"""
        # 1. Берем базовые СО от возраста
        age = ssd_dict["age"][0]
        math_age = int(age)
        if 18 <= math_age < 31:
            base_fp = (math_age - 18) // 2 + 2
        elif 31 <= math_age < 51:
            base_fp = (math_age - 31) // 3 + 8
        elif math_age >= 51:
            base_fp = (math_age - 51) // 4 + 14
        else:
            base_fp = 0

        current_fp = base_fp

        # Вспомогательное получение ответа
        def get_ans(q_key):
            val = ssd_dict.get(str(q_key), [0])
            return val[0] if val else 0

        # Вопрос 1: Образование
        q1 = get_ans(1)
        if q1 == 1: current_fp += 2
        elif q1 == 3: current_fp -= 1
        elif q1 == 4: current_fp -= 2

        # Вопрос 2: Направление
        q2 = get_ans(2)
        if q2 == 11: current_fp += 2
        elif q2 == 7: current_fp += 1

        # Вопрос 3: Работа по специальности
        q3 = get_ans(3)
        if q3 == 2: current_fp += 1

        # Вопрос 4: Спорт
        q4 = get_ans(4)
        if q4 == 1: current_fp += 1
        elif q4 == 3: current_fp -= 1
        elif q4 == 4: current_fp -= 2

        # Вопрос 5: Боевые искусства
        q5 = get_ans(5)
        if q5 == 1: current_fp += 1
        elif q5 == 3: current_fp -= 1
        elif q5 == 4: current_fp -= 2
        

        # Вопрос 6: Общительность
        q6 = get_ans(6)
        if q6 == 1: current_fp += 1
        elif q6 == 3: current_fp -= 1

        # Вопрос 7: Армия
        q7 = get_ans(7)
        if q7 == 1:
            current_fp += 1
        elif q7 == 4:
            current_fp -= 2
        elif q7 == 5:
            current_fp -= 3

        # Вопрос 8: Хобби
        q8 = get_ans(8)
        if q8 == 2: current_fp -= 1
        elif q8 == 3: current_fp -= 2

        # Вопрос 9: Криминал
        q9 = get_ans(9)
        if q9 == 2: current_fp -= 1
        elif q9 == 3: current_fp -= 2

        # Вопрос 10: Ранг
        q10 = get_ans(10)
        if q10 == 2: current_fp -= 1
        elif q10 == 3: current_fp -= 2
        elif q10 == 4: current_fp -= 3

        return current_fp
    
    async def selectors_block(self, inter: disnake.MessageInteraction, age=None, start=False):
        if age is not None:
            self.age = int(age)
            math_age = int(age)
            if math_age >= 18 and math_age < 31:
                math_age = math_age - 18
                fp = math_age // 2 + 2
            elif math_age >= 31 and math_age < 51:
                math_age = math_age - 31
                fp = math_age // 3 + 8
                async with get_char_lock(self.folder_path):
                    async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                        ssd_dict = json.loads(await f.read())
                ssd_dict[0]["negative_traits"].append("old")
                async with get_char_lock(self.folder_path):
                    async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                        await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            elif math_age >= 51:
                math_age = math_age - 51
                fp = math_age // 4 + 14
                async with get_char_lock(self.folder_path):
                    async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                        ssd_dict = json.loads(await f.read())
                ssd_dict[0]["negative_traits"].append("very_old")
                async with get_char_lock(self.folder_path):
                    async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                        await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            self.fp = fp
            self.current_fp = fp
            
            await self.start_value_write(age, fp)
            self.cq = 1
        if self.role_check == False:
            role = has_role(inter, 672125117509140510)
            if not role == False:
                self.access_rank = 1
            role = has_role(inter, 672125142326968385)
            if not role == False:
                self.access_rank = 2
            role = has_role(inter, 672125142331031554)
            if not role == False:
                self.access_rank = 3
            self.role_check = True
        if self.back:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats_backup.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())  
            self.current_fp = ssd_dict["current_fp"][0]
            self.back = False
            if ssd_dict[0]["10"] == 1:
                self.cq = 10
            else:
                self.cq = 11
                self.cq_old_pos = 10
        if self.fp_edit:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            ssd_dict["age"][0] = age
            ssd_dict["fp"][0] = fp
            ssd_dict["current_fp"][0] = fp
            self.current_fp = fp
            self.fp = fp
            self.fp_edit = False
        if not self.backup_create:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats_backup.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(self.stats_list, ensure_ascii=False, indent=4))
            self.backup_create = True

        self.old_view = self
        
        if self.cq > 11:
            self.cq = self.cq_old_pos
            self.old_view = self
            await self.analysis_selectors_block(inter)
            return
        
        if self.q11_complete == True:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            ssd_dict["11"] = []
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            if ssd_dict["10"][0] == 2:
                self.directions = 1
            elif ssd_dict["10"][0] == 3:
                self.directions = 2
            elif ssd_dict["10"][0] == 4:
                self.directions = 3
            else:
                self.directions = 0
            self.q11_complete = False

        self.clear_items()
        q_data = self.questions.get(str(self.cq))
        if not q_data:
            return # На случай ошибки в JSON

        # Формируем текст эмбеда
        q_text_raw = q_data.get("question", "")
        q_desc_raw = q_data.get("description", "")

        q_text = q_text_raw.format(directions=self.directions)
        q_desc = q_desc_raw.format(directions=self.directions)
        
        embed = create_embed_bs(
            f"Вопрос {self.cq}/11: {q_text}", 
            f"{q_desc}\n**Ваши СО: {self.current_fp}/{self.fp}**"
        )
        self.old_embed = embed

        # Фильтруем варианты ответов (например, по рангу доступа)
        raw_choices = q_data.get("choices", [])
        final_choices = []
        
        for c in raw_choices:
            # Проверка на минимальный ранг доступа (для вопроса №10)
            if "min_access" in c:
                if self.access_rank >= c["min_access"]:
                    final_choices.append((c["label"], c["value"]))
            else:
                final_choices.append((c["label"], c["value"]))

        # Создаем селектор
        selector = await self.create_selector_questionnaire(
            "Выберите ответ...", 
            final_choices, 
            str(self.cq)
        )      

        selector.callback = self.selectors_block_callback
        self.add_item(selector)
        help = disnake.ui.Button(label="Справка", style=disnake.ButtonStyle.red, row=0)
        back = disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.red, row=0)
        back.callback = self.back_callback
        help.callback = self.faq
        self.add_item(back)
        self.add_item(help)
        if inter.response.is_done():
            await inter.edit_original_message(embed=embed, view=self)
        else:
            await inter.response.edit_message(embed=embed, view=self)

    async def faq(self, inter: disnake.Interaction):
        view = HelpPaginator()
        embed = disnake.Embed(title=view.pages[0]["title"], description=view.pages[0]["description"], color=disnake.Color.red())
        await inter.send(embed=embed, view=view, ephemeral=True)

    async def back_callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())

        current_cq = self.cq
        
        # Стираем ответ на вопрос, с которого уходим, чтобы он не учитывался в калькуляции
        if str(current_cq) in ssd_dict:
            ssd_dict[str(current_cq)] = [0]

        # Определяем целевой шаг при прыжке назад
        target_cq = current_cq - 1

        # Логика обхода пропускаемых вопросов при движении назад
        def get_val(key):
            return ssd_dict.get(str(key), [0])[0]

        if current_cq == 4:
            if get_val(1) == 1: # Если только школа, 2 и 3 вопросы пропускались
                target_cq = 1
            else:
                target_cq = 3

        elif current_cq == 7:
            if get_val(2) == 7: # Социальная сфера пропускала 6 вопрос
                target_cq = 5
            else:
                target_cq = 6

        elif current_cq == 10:
            if get_val(1) == 4 or get_val(2) == 9: # Докторантура или Коп пропускали 9 вопрос
                target_cq = 8
            else:
                target_cq = 9

        if target_cq < 1:
            return await inter.send("Всё, дальше некуда!", ephemeral=True)

        # Применяем новую позицию
        self.cq = target_cq
        self.cq_old_pos = target_cq

        # Стираем ответ на тот вопрос, НА КОТОРЫЙ вернулись (чтобы сбросить старый выбор)
        ssd_dict[str(target_cq)] = [0]

        # Пересчитываем очки начисто!
        new_fp = self.recalculate_all_fp(ssd_dict)
        ssd_dict["current_fp"][0] = new_fp
        self.current_fp = new_fp

        # Сохраняем и обновляем экран
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))

        await self.selectors_block(inter, start=True)

    async def selectors_block_callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        
        raw_value = inter.values[0]
        value = int(raw_value)
        self.value = value

        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())
        if self.cq == 1:
            self.cq_old_pos = self.cq
            int_value = await self.get_char_skill_level("intellect")
            if value == 1:
                ssd_dict["2"][0] = 0
                ssd_dict["3"][0] = 0
                self.cq += 2  
            elif value == 2:
                if not int_value > 3:
                    return await inter.send(f"Ваш персонаж имеет слишком низкий уровень интеллекта для такого уровня образования (мин. - 4)", ephemeral=True)
            elif value == 3:
                if not int_value > 4:
                    return await inter.send(f"Ваш персонаж имеет слишком низкий уровень интеллекта для такого уровня образования (мин. - 5)", ephemeral=True)
                elif not self.age > 22:
                    return await inter.send(f"Ваш персонаж слишком молод для такого уровня образования (23 и старше).", ephemeral=True)            
            elif value == 4: 
                if not int_value > 5:
                    return await inter.send(f"Ваш персонаж имеет слишком низкий уровень интеллекта для такого уровня образования (мин. - 5)", ephemeral=True)
                elif not self.age > 30:
                    return await inter.send(f"Ваш персонаж слишком молод для такого уровня образования (31 и старше)", ephemeral=True)
                ssd_dict["9"][0] = 0
        
        elif self.cq == 2:
            self.cq_old_pos = self.cq
            if value == 10:                
                int_value = await self.get_char_skill_level("reaction")
                if not int_value > 5:
                    return await inter.send(f"Ваш персонаж после получения образования по данной специальности обязан отслужить в армии, но ваша Реакция слишком низкая для этого (требуется 5 или выше).", ephemeral=True)            
            if value == 9 or value == 10:
                if ssd_dict["1"][0] == 4:
                    return await inter.send(f"Ваш персонаж проходил докторантуру, для выбранного направления её нет.", ephemeral=True)
                if value == 10:
                    self.cq += 1
            elif value == 11:
                self.cq += 1
            self.education = value

        elif self.cq == 3:
            self.cq_old_pos = self.cq
        
        elif self.cq == 4:
            self.cq_old_pos = self.cq
       
        elif self.cq == 5:
            self.cq_old_pos = self.cq
            if ssd_dict["2"][0] == 7:
                self.cq += 1
        
        elif self.cq == 6:
            self.cq_old_pos = self.cq
        
        elif self.cq == 7:
            self.cq_old_pos = self.cq
            int_value = await self.get_char_skill_level("reaction")
            if value == 1:
                if ssd_dict["2"][0] == 10:
                    return await inter.send(f"Ваш персонаж имеет военное образование, он точно использовал оружие.", ephemeral=True)
            elif value == 2:
                if ssd_dict["2"][0] == 10:
                    return await inter.send(f"Ваш персонаж имеет военное образование, он точно использовал не только гражданское оружие.", ephemeral=True)
            elif value == 3:
                if ssd_dict["2"][0] == 10:
                    return await inter.send(f"Ваш персонаж имеет военное образование, он не проходил срочную службу.", ephemeral=True)
                if ssd_dict["1"][0] == 4:
                    return await inter.send(f"Ваш персонаж проходил докторантуру, он не мог успеть пройти срочную службу.", ephemeral=True)
            elif value == 4: 
                if not int_value > 4:
                    return await inter.send(f"Ваш персонаж имеет слишком низкую Реакцию для этого (мин. - 5).", ephemeral=True)
                elif ssd_dict["4"][0] == 1:
                    return await inter.send(f"Ваш персонаж не любит спорт, а для такого рода деятельности он жизненно необходим.", ephemeral=True)
                elif ssd_dict["1"][0] == 4:
                    return await inter.send(f"Ваш персонаж проходил докторантуру, после неё люди в армию идут лишь в исключительных случаях. Увы!", ephemeral=True)
                elif ssd_dict["2"][0] == 9 and ssd_dict["3"][0] == 1:
                    return await inter.send(f"Вы уже выбрали, что ваш персонаж работал по специальности полицейского (следователем или криминалистом).", ephemeral=True)
            elif value == 5: 
                if not int_value > 5:
                    return await inter.send(f"Ваш персонаж имеет слишком низкую Реакцию для этого (мин. - 6).", ephemeral=True)
                elif ssd_dict["4"][0] == 1:
                    return await inter.send(f"Ваш персонаж не любит спорт, а для такого рода деятельности он жизненно необходим.", ephemeral=True)
                elif ssd_dict["1"][0] == 4:
                    return await inter.send(f"Ваш персонаж проходил докторантуру, после неё люди в армию идут лишь в исключительных случаях. Увы!", ephemeral=True)
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                    edit_value = json.loads(await f.read())
            
            negative_traits = edit_value[0].get("negative_traits", [])
            
            if value == 5:
                # Если выбрали "Воевал" — добавляем, если её там ещё нет
                if "post_trauma" not in negative_traits:
                    negative_traits.append("post_trauma")
            else:
                # Если выбрали ЛЮБОЙ другой вариант — принудительно вырезаем черту
                if "post_trauma" in negative_traits:
                    negative_traits.remove("post_trauma")
            
            # Синхронно сохраняем изменения в оба файла-слепка
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(edit_value, ensure_ascii=False, indent=4))
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats_backup.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(edit_value, ensure_ascii=False, indent=4))

        elif self.cq == 8:
            self.cq_old_pos = self.cq
            if ssd_dict["1"][0] == 4 or ssd_dict["2"][0] == 9:
                self.cq += 1
                if self.access_rank == 0:
                    self.cq = 12
        
        elif self.cq == 9:
            self.cq_old_pos = self.cq
            if self.access_rank == 0:
                self.cq = 12
        
        elif self.cq == 10:
            self.cq_old_pos = self.cq
            if value == 1:
                self.cq += 1
            elif value == 2: 
                self.directions = 1
            elif value == 3: 
                self.directions = 2
            elif value == 4: 
                self.directions = 3
            self.current_fp = ssd_dict["current_fp"][0]
        
        elif self.cq == 11:
            self.cq_old_pos = self.cq
            ssd_dict[f"{self.cq}"].append(int(value))
            self.directions -= 1
            if self.directions == 0:
                self.q11_complete = True

        # 1. Четко определяем, на какой вопрос мы ТОЛЬКО ЧТО ответили
        answered_q = inter.component.custom_id.replace("q_", "")
        
        # 2. Сохраняем ответ именно в этот вопрос, а не в self.cq

        if not self.cq == 11:
            ssd_dict[answered_q] = [value]

        self.current_fp = self.recalculate_all_fp(ssd_dict)
        ssd_dict["current_fp"][0] = self.current_fp

        # 4. Записываем в файл
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
        
        if not self.directions > 0:
            self.cq += 1
        else:
            if not self.cq == 11:
                self.cq += 1 

        # Обновляем интерфейс
        await self.selectors_block(inter)

    async def get_char_stat(self, stat_id: str):
        character_stats_path = f"{self.folder_path}/char_stats.json"
        try:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(character_stats_path, "r", encoding="utf-8") as f:
                    skills_data = json.loads(await f.read())
            for group in skills_data[1:]:
                group_info = group.get("skill_group")
                if group_info and group_info[0] == stat_id:
                    return group_info[2]
                if stat_id in group:
                    skill_info = group[stat_id]
                    return skill_info[2]
            return 0
        except Exception as e:
            print(f"Ошибка при поиске стата {stat_id}: {e}")
            return 0
    
    async def get_char_skill_level(self, stat_id: str) -> int:
        raw_fp = await self.get_char_stat(stat_id)
        if not stat_id.startswith("skill_") or stat_id == "skill_group":
            return raw_fp
        return calculate_skill_level(raw_fp)
    
    async def apply_to_memory(self, skill_id, bonus_levels):
        """Находит навык в списке и меняет его ОП без записи в файл."""
        for group in self.stats_list[1:]:
            # 1. Проверка на группу (атрибут)
            group_info = group.get("skill_group")
            if group_info and group_info[0] == skill_id:
                try:
                    # Принудительно в int, чтобы не складывать строки
                    group_info[2] = int(group_info[2]) + int(bonus_levels)
                except (ValueError, TypeError):
                    print(f"Ошибка типа данных для группы {skill_id}")
                return

            # 2. Проверка на навык
            if skill_id in group:
                try:
                    # Убеждаемся, что текущие ОП — это число
                    current_fp = int(group[skill_id][1])
                    
                    # Главная точка риска: что внутри этой функции?
                    added_fp = calculate_needed_fp(current_fp, int(bonus_levels))
                    
                    # Если added_fp вернула странное число (например, 2019), 
                    # значит проблема в самой логике calculate_needed_fp
                    group[skill_id][1] = current_fp + added_fp
                except Exception as e:
                    print(f"Ошибка при расчете навыка {skill_id}: {e}")
                return
            
    async def analysis_selectors_block(self, inter: disnake.MessageInteraction):
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
 
        stats_path = f"{self.folder_path}/char_stats.json"
        with open(stats_path, "r", encoding="utf-8") as f:
            self.stats_list = json.load(f)

        # --- ВОПРОС 1: Образование ---
        q1 = data.get("1", [0])[0]
        if q1 == 2: # Среднее полное
            await self.apply_to_memory("skill_attention", 1)
            await self.apply_to_memory("skill_mutants", 1)
            await self.apply_to_memory("skill_anomaly", 1)
            await self.apply_to_memory("skill_artefacts", 1)
            await self.apply_to_memory("skill_zoneknowledge", 1)
        elif q1 == 3: # Специалитет
            await self.apply_to_memory("skill_attention", 2)
            await self.apply_to_memory("skill_mutants", 2)
            await self.apply_to_memory("skill_anomaly", 2)
            await self.apply_to_memory("skill_artefacts", 2)
            await self.apply_to_memory("skill_zoneknowledge", 2)
        elif q1 == 4: # Докторантура
            await self.apply_to_memory("skill_attention", 3)
            await self.apply_to_memory("skill_mutants", 3)
            await self.apply_to_memory("skill_anomaly", 3)
            await self.apply_to_memory("skill_artefacts", 3)
            await self.apply_to_memory("skill_zoneknowledge", 3)
        
        # --- ВОПРОС 2: Направление образования ---
        q2 = data.get("2", [0])[0]
        if q2 == 1: # Медицина
            self.education = 1
            await self.apply_to_memory("skill_medicine", 4)
        elif q2 == 2: # IT
            self.education = 2
            await self.apply_to_memory("skill_infosecurity", 4)
        elif q2 == 3: # Механика
            self.education = 3
            await self.apply_to_memory("skill_basetech", 4)
        elif q2 == 4: # Электроника
            self.education = 4
            await self.apply_to_memory("skill_electronics", 4)
        elif q2 == 5: # Сапёрное дело
            self.education = 5
            await self.apply_to_memory("skill_pyrotech", 4)
        elif q2 == 6: # Экономика
            self.education = 6
            await self.apply_to_memory("skill_trade", 4)
        elif q2 == 7: # Социальная сфера
            self.education = 7
            await self.apply_to_memory("skill_communication", 4)
        elif q2 == 8: # Конструирование оружия
            self.education = 8
            await self.apply_to_memory("skill_armtech", 4)
        elif q2 == 9: # Полицейский
            self.education = 9
            await self.apply_to_memory("skill_communication", 2)
            await self.apply_to_memory("skill_handguns", 2)
            await self.apply_to_memory("skill_strength", 2)
            await self.apply_to_memory("skill_attention", 2)
        elif q2 == 10: # Военное дело
            self.education = 10
            await self.apply_to_memory("skill_handguns", 1)
            await self.apply_to_memory("skill_shotguns", 1)
            await self.apply_to_memory("skill_assaultrifle", 1)
            await self.apply_to_memory("skill_sniperrifle", 1)
            await self.apply_to_memory("skill_heavyweapon", 1)
            await self.apply_to_memory("skill_strength", 2)

        # --- ВОПРОС 3: Работа по специальности ---
        q3 = data.get("3", [0])[0]
        if q3 == 1: # Да (усиление навыков из Q2)
            if self.education == 1:
                await self.apply_to_memory("skill_medicine", 2)    
            if self.education == 2:
                await self.apply_to_memory("skill_infosecurity", 2)
            if self.education == 3:
                await self.apply_to_memory("skill_basetech", 2)
            if self.education == 4:
                await self.apply_to_memory("skill_electronics", 2)
            if self.education == 5:
                await self.apply_to_memory("skill_pyrotech", 2)
            if self.education == 6:
                await self.apply_to_memory("skill_trade", 2)
            if self.education == 7:
                await self.apply_to_memory("skill_communication", 2)
            if self.education == 8:
                await self.apply_to_memory("skill_armtech", 2)
            if self.education == 9:
                await self.apply_to_memory("skill_communication", 2)
                await self.apply_to_memory("skill_handguns", 2)
                await self.apply_to_memory("skill_strength", 2)
                await self.apply_to_memory("skill_attention", 2)

        # --- ВОПРОС 4: Спорт ---
        q4 = data.get("4", [0])[0]
        if q4 == 2: # Любитель
            await self.apply_to_memory("skill_persistence", 2)
            await self.apply_to_memory("skill_strength", 2)
        elif q4 == 3: # Профи
            await self.apply_to_memory("skill_persistence", 4)
            await self.apply_to_memory("skill_strength", 4)
        elif q4 == 4: # Олимпиец
            await self.apply_to_memory("skill_persistence", 6)
            await self.apply_to_memory("skill_strength", 6)

        # --- ВОПРОС 5: Боевые искусства ---
        q5 = data.get("5", [0])[0]
        if q5 == 2: # Улица
            await self.apply_to_memory("skill_agility", 2)
            await self.apply_to_memory("skill_closecombat", 2)
        elif q5 == 3: # Подготовка
            await self.apply_to_memory("skill_agility", 4)
            await self.apply_to_memory("skill_closecombat", 4)
        elif q5 == 4: # Мастер
            await self.apply_to_memory("skill_agility", 6)
            await self.apply_to_memory("skill_closecombat", 6)

        # --- ВОПРОС 6: Общение ---
        q6 = data.get("6", [0])[0]
        if q6 == 2: # Да
            await self.apply_to_memory("skill_communication", 2)
        if q6 == 3: # Был душой компании
            await self.apply_to_memory("skill_communication", 4)

        # --- ВОПРОС 7: Армия и оружие ---
        q7 = data.get("7", [0])[0]
        if q7 == 2: # Гражданская стрельба
            await self.apply_to_memory("skill_handguns", 2)
            await self.apply_to_memory("skill_shotguns", 2)
        elif q7 == 3: # Срочная служба
            await self.apply_to_memory("skill_assaultrifle", 2)
        elif q7 == 4: # Контракт / ОМОН
            await self.apply_to_memory("skill_handguns", 2)
            await self.apply_to_memory("skill_shotguns", 2)
            await self.apply_to_memory("skill_assaultrifle", 4)
            await self.apply_to_memory("skill_sniperrifle", 2)
            await self.apply_to_memory("skill_heavyweapon", 2)
            await self.apply_to_memory("skill_persistence", 2)
            await self.apply_to_memory("skill_strength", 2)
        elif q7 == 5: # Воевал
            await self.apply_to_memory("skill_handguns", 3)
            await self.apply_to_memory("skill_shotguns", 3)
            await self.apply_to_memory("skill_assaultrifle", 5)
            await self.apply_to_memory("skill_sniperrifle", 3)
            await self.apply_to_memory("skill_heavyweapon", 3)
            await self.apply_to_memory("skill_persistence", 2)
            await self.apply_to_memory("skill_strength", 2)
            await self.apply_to_memory("skill_attention", 2)
            await self.apply_to_memory("skill_armtech", 2)
            await self.apply_to_memory("skill_stealth", 2)

        # --- ВОПРОС 8: Техническое хобби ---
        q8 = data.get("8", [0])[0]
        if q8 == 1: # Не имеет
            self.skill_add = 0
        if q8 == 2: # Любитель
            self.skill_add = 2
        elif q8 == 3: # Почти профи
            self.skill_add = 4

        # --- ВОПРОС 9: Криминал ---
        q9 = data.get("9", [0])[0]
        if q9 == 2: # Мелкий грабеж
            await self.apply_to_memory("skill_handguns", 1)
            await self.apply_to_memory("skill_communication", 2)
        elif q9 == 3: # Бандитизм
            await self.apply_to_memory("skill_handguns", 2)
            await self.apply_to_memory("skill_communication", 2)
            await self.apply_to_memory("skill_assaultrifle", 2)
            await self.apply_to_memory("skill_strength", 2)

        # --- ВОПРОС 10: Ранг ---
        q10 = data.get("10", [0])[0]
        if q10 == 2: # Опытный
            await self.apply_to_memory("skill_mutants", 1)
            await self.apply_to_memory("skill_anomaly", 1)
            await self.apply_to_memory("skill_artefacts", 1)
            await self.apply_to_memory("skill_zoneknowledge", 1)
            await self.apply_to_memory("skill_handguns", 1)
            await self.apply_to_memory("skill_shotguns", 1)
            await self.apply_to_memory("skill_assaultrifle", 1)
            await self.apply_to_memory("skill_strength", 1)
        elif q10 == 3: # Ветеран
            await self.apply_to_memory("skill_mutants", 2)
            await self.apply_to_memory("skill_anomaly", 2)
            await self.apply_to_memory("skill_artefacts", 2)
            await self.apply_to_memory("skill_zoneknowledge", 2)
            await self.apply_to_memory("skill_handguns", 2)
            await self.apply_to_memory("skill_shotguns", 2)
            await self.apply_to_memory("skill_assaultrifle", 2)
            await self.apply_to_memory("skill_strength", 2)
            await self.apply_to_memory("skill_persistence", 1)
            await self.apply_to_memory("skill_medicine", 1)
        elif q10 == 4: # Мастер
            await self.apply_to_memory("skill_mutants", 3)
            await self.apply_to_memory("skill_anomaly", 3)
            await self.apply_to_memory("skill_artefacts", 3)
            await self.apply_to_memory("skill_zoneknowledge", 3)
            await self.apply_to_memory("skill_handguns", 3)
            await self.apply_to_memory("skill_shotguns", 3)
            await self.apply_to_memory("skill_assaultrifle", 3)
            await self.apply_to_memory("skill_strength", 3)
            await self.apply_to_memory("skill_persistence", 2)
            await self.apply_to_memory("skill_medicine", 2)
        # --- ВОПРОС 11: Специализации (Список / Multiple Choice) ---
        self.q11_list = data.get("11", [])
        await self.process_next_spec(inter, data)

    async def process_next_spec(self, inter, data):
        try:
            if not self.q11_list:
                return await self.proceed_to_traits(inter, data)
            
            spec = self.q11_list.pop(0)

            if spec == 6: # Тот самый Мастер полевого ремесла
                await self.hobby_direction(inter, direction=True, data=data)
            else:
                if spec == 1: # Артхантер
                    await self.apply_to_memory("skill_attention", 2)
                    await self.apply_to_memory("skill_anomaly", 2)
                    await self.apply_to_memory("skill_artefacts", 2)
                elif spec == 2: # Проводник
                    await self.apply_to_memory("skill_zoneknowledge", 2)
                    await self.apply_to_memory("skill_attention", 2)
                    await self.apply_to_memory("skill_anomaly", 2)
                elif spec == 3: # Охотник на мутантов
                    await self.apply_to_memory("skill_mutants", 2)
                    await self.apply_to_memory("skill_attention", 2)
                    await self.apply_to_memory("skill_shotguns", 2)
                    await self.apply_to_memory("skill_assaultrifle", 2)
                elif spec == 4: # Охотник на людей
                    await self.apply_to_memory("skill_handguns", 2)
                    await self.apply_to_memory("skill_attention", 2)
                    await self.apply_to_memory("skill_sniperrifle", 2)
                    await self.apply_to_memory("skill_assaultrifle", 2)
                elif spec == 5: # Мастер маскировки
                    await self.apply_to_memory("skill_stealth", 3)
                    await self.apply_to_memory("skill_attention", 2)
                await self.process_next_spec(inter, data)
        except Exception as e:
            print(f"Критическая ошибка в конвейере: {e}")
        
    async def proceed_to_traits(self, inter, data):    
        stats_path = f"{self.folder_path}/char_stats.json"
        async with aiofiles.open(stats_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(self.stats_list, ensure_ascii=False, indent=4))
        q8 = data.get("8", [0])[0]
        if not q8 == 1: 
            await self.hobby_direction(inter)
        else:
            async with aiofiles.open("chars_data/traits_lib.json", "r", encoding="utf-8") as f:
                full_library = json.loads(await f.read())
            async with aiofiles.open("chars_data/questions_lib.json", "r", encoding="utf-8") as f:
                questions_lib = json.loads(await f.read())
            self.new_view = TraitQuestionnaireView(self.folder_path, self.user_id, full_library, questions_lib, "positive", self.current_fp, self.old_view)
            self.new_view.message = self.message
            
            from utems import get_filtered_page

            page_items, max_pages, total_count = await get_filtered_page(full_library, "positive", 1, "summon", self.folder_path)
            await self.new_view.prepare_view()

            from utems import create_library_embed  
            # Создаем сам эмбед
            first_embed = await create_library_embed(
                page_items, 
                questions_lib,
                1, 
                max_pages, 
                total_count, 
            )
            embed = await self.new_view.add_choice_map(first_embed)
            # ОТПРАВЛЯЕМ И ТО, И ДРУГОЕ
            if inter.response.is_done():
                await inter.edit_original_message(embed=embed, view=self.new_view)
            else:
                await inter.response.edit_message(embed=embed, view=self.new_view)

    async def hobby_direction(self, inter: disnake.MessageCommandInteraction, direction=False, data=None):
        self.clear_items()
        if not direction:
            embed = create_embed_bs(f"Выбор технического хобби", "Выберите навык, который соответствует техническому хобби вашего персонажа.")
        else:
            embed = create_embed_bs(f"Выбор навыка", "Выберите навык, который хотите повысить при помощи направления «Мастер полевого ремесла».\n*Важно заметить, что система на текущий момент не учитывает то, что какой-то ваш навык уже поднялся до максимума. Посему, будьте внимательны при использовании данной черты.*")
        choices = [
            ("Электроника", "1"), ("Медицина", "2"), ("Базовая техника", "3"), ("Оружейная техника", "4"),
            ("Пиротехника", "5"), ("Информационная безопасность", "6")
        ]
        selector = await self.create_selector_questionnaire("Выберите навык", choices, "extra")
        if not direction:
            selector.callback = self.hobby_direction_callback
        else:
            self.data = data
            selector.callback = self.direction_select_callback
        self.add_item(selector)
        
        if inter.response.is_done():
            await inter.edit_original_message(embed=embed, view=self)
        else:
            await inter.response.edit_message(embed=embed, view=self)

    async def direction_select_callback(self, inter: disnake.MessageInteraction):
        stock_value = inter.values[0]
        value = int(stock_value)
        if value == 1:
            await self.apply_to_memory("skill_electronics", 2)
        elif value == 2:
            await self.apply_to_memory("skill_medicine", 2)
        elif value == 3:
            await self.apply_to_memory("skill_basetech", 2)
        elif value == 4:
            await self.apply_to_memory("skill_armtech", 2)
        elif value == 5:
            await self.apply_to_memory("skill_pyrotech", 2)
        elif value == 6:
            await self.apply_to_memory("skill_infosecurity", 2)
        if hasattr(self, 'q11_list') and self.q11_list:
            await self.process_next_spec(inter, self.data)
        else:
            await self.proceed_to_traits(inter, self.data)

    async def hobby_direction_callback(self, inter: disnake.MessageInteraction):
        stock_value = inter.values[0]
        value = int(stock_value)
        if value == 1:
            if not self.education == 4:
                await modify_skill_fp("skill_electronics", self.skill_add, self.folder_path)
            else:
                return await inter.send(f"Ваше образование уже развивает этот навык.", ephemeral=True)
        elif value == 2:
            if not self.education == 1:
                await modify_skill_fp("skill_medicine", self.skill_add, self.folder_path)
            else:
                return await inter.send(f"Ваше образование уже развивает этот навык.", ephemeral=True)
        elif value == 3:
            if not self.education == 3:
                await modify_skill_fp("skill_basetech", self.skill_add, self.folder_path)
            else:
                return await inter.send(f"Ваше образование уже развивает этот навык.", ephemeral=True)
        elif value == 4:
            if not self.education == 8:
                await modify_skill_fp("skill_armtech", self.skill_add, self.folder_path)
            else:
                return await inter.send(f"Ваше образование уже развивает этот навык.", ephemeral=True)
        elif value == 5:
            if not self.education == 5:
                await modify_skill_fp("skill_pyrotech", self.skill_add, self.folder_path)
            else:
                return await inter.send(f"Ваше образование уже развивает этот навык.", ephemeral=True)
        elif value == 6:
            if not self.education == 2:
                await modify_skill_fp("skill_infosecurity", self.skill_add, self.folder_path)
            else:
                return await inter.send(f"Ваше образование уже развивает этот навык.", ephemeral=True)
        
        async with aiofiles.open("chars_data/traits_lib.json", "r", encoding="utf-8") as f:
            full_library = json.loads(await f.read())
        async with aiofiles.open("chars_data/questions_lib.json", "r", encoding="utf-8") as f:
            questions_lib = json.loads(await f.read())
        self.new_view = TraitQuestionnaireView(self.folder_path, self.user_id, full_library, questions_lib, "positive", self.current_fp, self.old_view)
        await self.new_view.prepare_view()
        
        from utems import get_filtered_page

        page_items, max_pages, total_count = await get_filtered_page(full_library, "positive", 1, "summon", self.folder_path)

        from utems import create_library_embed  
            # Создаем сам эмбед
        first_embed = await create_library_embed(
            page_items, 
            questions_lib,
            1, 
            max_pages, 
            total_count, 
        )
        embed = await self.new_view.add_choice_map(first_embed)
        await inter.response.edit_message(embed=embed, view=self.new_view)

class TraitQuestionnaireView(disnake.ui.View):
    def __init__(self, folder_path, user_id, library, questions_lib, trait_type, initial_so, prev_view):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.library = library
        self.trait_type = trait_type
        self.current_page = 1
        self.charlist_msg = None
        self.folder_path = folder_path
        self.questions_lib = questions_lib
        self.render_type = "summon"
        self.viewA = prev_view
        self.old_embed = None
        self.max_pages = 1  # Дефолтное значение
        self.message = None

        # Состояние игрока
        if not self.viewA.selected_negative_traits_folder:
            self.selected_negative_traits = []
        else: 
            self.selected_negative_traits = self.viewA.selected_negative_traits_folder

        if not self.viewA.selected_positive_traits_folder:
            self.selected_positive_traits = []
        else: 
            self.selected_positive_traits = self.viewA.selected_positive_traits_folder

        self.current_fp = initial_so

        # В конструкторе кнопки пока выключаем — они настроятся асинхронно в prepare_view
        self.select_menu.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = True

    async def on_timeout(self):
        if self.message:
            try:
                # view=None полностью удаляет панель кнопок под сообщением
                await self.message.edit(
                    content="❌ **Время ожидания истекло.** Начните заново через `/pos_ucms`.", 
                    embed=None, 
                    view=None
                )
            except disnake.HTTPException:
                # На случай, если пользователь сам удалил сообщение до таймаута
                pass
        self.stop()

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True

    async def prepare_view(self):
        """Специальный асинхронный метод для безопасной подготовки данных первой страницы"""
        
        from utems import get_filtered_page
        
        page_items, max_pages, total_page = await get_filtered_page(
            self.library, self.trait_type, self.current_page, self.render_type, self.folder_path
        )
        
        self.max_pages = max_pages 

        # Обновляем селект полученными данными
        self.update_select_options(page_items, total_page, max_pages)

        # Настраиваем актуальное состояние кнопок пагинации
        self.prev_page.disabled = (self.current_page <= 1)
        self.next_page.disabled = (self.current_page >= self.max_pages)
        
        return self # Возвращаем объект для удобной цепочки вызовов
    
    async def update_charlist_message(self, interaction: disnake.Interaction):
        # Генерируем "живой" эмбед
        live_embed = await self.render_live_charlist()
        
        if self.charlist_msg:
            try:
                await self.charlist_msg.edit(embed=live_embed)
            except disnake.NotFound:
                self.charlist_msg = await interaction.channel.send(embed=live_embed)
        else:
            # Отправляем новое сообщение, если его еще нет
            self.charlist_msg = await interaction.channel.send(embed=live_embed)
    
    def update_select_options(self, page_items, total_page, max_pages):
        """Вспомогательный метод для подготовки опций селекта"""
        options = []
        if not page_items:
            options.append(disnake.SelectOption(
                label="Пусто", 
                value="none", 
                description="Нет доступных черт на этой странице"
            ))
            self.select_menu.disabled = True
            self.prev_page.disabled = True
            self.next_page.disabled = True
        else:
            self.select_menu.disabled = False
            for tid, data in page_items.items():
                if self.trait_type == "positive":
                    is_sel = tid in self.selected_positive_traits
                elif self.trait_type == "negative":
                    is_sel = tid in self.selected_negative_traits
                options.append(disnake.SelectOption(
                    label=data['name'],
                    value=tid,
                    description=f"{'Выбрано' if is_sel else 'Нажмите, чтобы выбрать'} | {data.get('cost', 0)} СО",
                    emoji="✅" if is_sel else "🔘"
                ))
        self.select_menu.options = options

    async def add_choice_map(self, embed: disnake.Embed):
        """
        Добавляет поле со списком всех текущих выборов игрока к любому эмбеду.
        """
        # 1. Сбор названий выбранных черт
        selected_names = []
        total_cost = 0
        
        if self.trait_type == "negative":
            selected_traits = self.selected_negative_traits
        elif self.trait_type == "positive":
            selected_traits = self.selected_positive_traits
        for tid in selected_traits:
            trait_data = self.library.get(tid, {})
            name = trait_data.get("name", tid)
            cost = trait_data.get("cost", 0)
            total_cost += cost
            selected_names.append(f"• {name} ({cost} СО)")

        # 2. Формирование текста
        if not selected_names:
            choices_text = "*Вы еще ничего не выбрали*"
        else:
            choices_text = "\n".join(selected_names)

        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())  
        self.current_fp = ssd_dict["current_fp"][0] 

        # 3. Добавление полей в конец эмбеда
        embed.add_field(
            name="========== Выбранные черты ==========", 
            value=choices_text, 
            inline=False
        )
        
        embed.add_field(
            name="Оставшиеся СО", 
            value=f"**{self.current_fp} СО**\n Предупреждение - если вы являетесь новичком на проекте, лучше избегайте того, чтобы брать какие-либо черты со старта. Так будет проще.",     
            inline=False
        )
        
        return embed
    
    async def update_view(self, interaction: disnake.Interaction, next_cq=False):
        # 1. Получаем свежие данные для текущей страницы
        
        from utems import get_filtered_page
        
        page_items, max_pages, total_count = await get_filtered_page(self.library, self.trait_type, self.current_page, self.render_type, self.folder_path)
        
        # 2. Обновляем опции и статус disabled кнопок/селектов
        self.update_select_options(page_items, total_count, max_pages)
        
        from utems import create_library_embed
        # 3. Генерируем базовый эмбед библиотеки
        embed = await create_library_embed(
            filtered_data=page_items, 
            page=self.current_page, 
            max_pages=max_pages, 
            total_count=total_count, 
            questions_lib=self.questions_lib
        )

        # 2. Сохраняем max_pages в self, чтобы использовать его в функциях переключения страниц
        self.max_pages = max_pages 

        # 4. И только В ПОСЛЕДНЮЮ ОЧЕРЕДЬ настраиваем кнопки
        self.prev_page.disabled = (self.current_page <= 1)
        self.next_page.disabled = (self.current_page >= self.max_pages)

        # === ВОТ ТУТ ВОЗВРАЩАЕМ КАРТУ ВЫБОРА ===
        # Мы берем свежесозданный эмбед и "наслаиваем" на него выбранные черты и остаток СО
        embed = await self.add_choice_map(embed)
        # ======================================

        self.old_embed = embed

        # 4. ОБЯЗАТЕЛЬНО передаем self в view
        if interaction.response.is_done():
            await interaction.edit_original_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

        if not next_cq:
            await self.update_charlist_message(interaction)

    @disnake.ui.select(placeholder="Выберите черту из списка выше...", min_values=1, max_values=1, row=1)
    async def select_menu(self, select: disnake.ui.Select, interaction: disnake.Interaction):
        trait_id = select.values[0]
        await interaction.response.defer()
        
        trait_data = self.library.get(trait_id, {})
        cost = trait_data.get("cost", 0)
        change = 0
        
        if self.trait_type == "positive":
            if trait_id in self.selected_positive_traits:
                self.selected_positive_traits.remove(trait_id)
                change = cost
            else:
                self.selected_positive_traits.append(trait_id)
                change = -cost
        if self.trait_type == "negative":
            if trait_id in self.selected_negative_traits:
                self.selected_negative_traits.remove(trait_id)
                change = cost
            else:
                self.selected_negative_traits.append(trait_id)
                change = -cost

        self.current_fp -= change
        self.viewA.current_fp -= change

        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())
        ssd_dict["current_fp"][0] -= change
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))

        await self.update_view(interaction)

    @disnake.ui.button(label="Назад", style=disnake.ButtonStyle.red, row=0)
    async def back(self, button: disnake.ui.Button, inter: disnake.Interaction):
        if self.trait_type == "negative":
            await inter.response.defer()
            self.viewA.selected_negative_traits_folder = self.selected_negative_traits
            self.trait_type = "positive"
            self.current_page = 1
            await self.update_view(inter, next_cq=True)
            if self.charlist_msg:
                try:
                    channel = inter.channel
                    message = channel.get_partial_message(self.charlist_msg.id)
                    await message.delete()
                except disnake.NotFound:
                    print("Сообщение уже удалено.")
                except disnake.Forbidden:
                    print("У бота нет прав на удаление этого сообщения.")
        else:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats_backup.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            self.viewA.selected_positive_traits_folder = self.selected_positive_traits
            self.viewA.back == True
            if self.charlist_msg:
                try:
                    channel = inter.channel
                    message = channel.get_partial_message(self.charlist_msg.id)
                    await message.delete()
                except disnake.NotFound:
                    print("Сообщение уже удалено.")
                except disnake.Forbidden:
                    print("У бота нет прав на удаление этого сообщения.")
            await self.viewA.selectors_block(inter)
            await inter.edit_original_response(view=self.viewA)
    
    @disnake.ui.button(label="⬅️", style=disnake.ButtonStyle.red, row=0)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
            from utems import get_filtered_page
            
            _, max_pages, _ = await get_filtered_page(self.library, self.trait_type, self.current_page, self.render_type, self.folder_path)
            if self.current_page > 1:
                self.current_page -= 1
                await self.update_view(interaction)

    @disnake.ui.button(label="➡️", style=disnake.ButtonStyle.red, row=0)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
            from utems import get_filtered_page
            
            _, max_pages, _ = await get_filtered_page(self.library, self.trait_type, self.current_page, self.render_type, self.folder_path)
            if self.current_page < max_pages:
                self.current_page += 1
                await self.update_view(interaction)

    @disnake.ui.button(label="Подтвердить и далее", style=disnake.ButtonStyle.red, row=0)
    async def confirm_btn(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        if self.trait_type == "positive":
            self.viewA.selected_positive_traits_folder = self.selected_positive_traits
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            ssd_dict["12"] = self.selected_positive_traits
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats_backup.json", "r", encoding="utf-8") as f:
                    ssd_dict2 = json.loads(await f.read())
            existing_pos = ssd_dict2[0]["positive_traits"]
            ssd_dict[0]["positive_traits"] = existing_pos
            ssd_dict[0]["positive_traits"].extend(self.selected_positive_traits)
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            self.trait_type = "negative"
            self.current_page = 1
            await self.update_view(interaction, next_cq=True)
        elif self.trait_type == "negative":
            self.viewA.selected_negative_traits_folder = self.selected_negative_traits
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            ssd_dict["13"] = self.selected_negative_traits
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                    ssd_dict = json.loads(await f.read())
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats_backup.json", "r", encoding="utf-8") as f:
                    ssd_dict2 = json.loads(await f.read())
            existing_neg = ssd_dict2[0]["negative_traits"]
            ssd_dict[0]["negative_traits"] = existing_neg
            ssd_dict[0]["negative_traits"].extend(self.selected_negative_traits)
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                    await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
            embed = create_embed_bs("Осталось ещё чуть-чуть...", "Настало время дать вашей творческой свободе волю. Нажмите кнопку для перехода к заполнению особых умений, внешности и характера.")
            prev_view = self
            new_view = CharacterQuestionnnaireModalManager(self.folder_path, self.user_id, prev_view, self.old_embed)
            new_view.message = self.message
            if self.charlist_msg:
                try:
                    channel = interaction.channel
                    message = channel.get_partial_message(self.charlist_msg.id)
                    await message.delete()
                except disnake.NotFound:
                    print("Сообщение уже удалено.")
                except disnake.Forbidden:
                    print("У бота нет прав на удаление этого сообщения.")
            await interaction.response.edit_message(embed=embed, view=new_view)
    
    @disnake.ui.button(label="Справка", style=disnake.ButtonStyle.red, row=4)
    async def faq(self, button: disnake.ui.Button, inter: disnake.Interaction):
        view = HelpPaginator()
        embed = disnake.Embed(title=view.pages[0]["title"], description=view.pages[0]["description"], color=disnake.Color.red())
        await inter.send(embed=embed, view=view, ephemeral=True)
    
    async def render_live_charlist(self):
        """
        Версия stats_rendering, которая учитывает выбранные, 
        но еще не сохраненные черты.
        """
        # 1. Загружаем базу из JSON (как в вашем оригинальном методе)
        character_stats_path = f"{self.folder_path}/char_stats.json"
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(character_stats_path, "r", encoding="utf-8") as f:
                skills_data = json.loads(await f.read())

        # 2. СОБИРАЕМ МОДИФИКАТОРЫ ИЗ ВЫБРАННЫХ ЧЕРТ
        # Создаем временный словарь для суммирования бонусов
        active_mods = {}
        if self.selected_negative_traits:
            for tid in self.selected_negative_traits:
                # Важно: используем .get(..., []), так как в библиотеке теперь список списков
                trait_mods = self.library.get(tid, {}).get("modifiers", [])
                for mod in trait_mods:
                    # mod = ["group", "body", -2]
                    _, target_id, mod_value = mod
                    active_mods[target_id] = active_mods.get(target_id, 0) + mod_value
        if self.selected_positive_traits:
            for tid in self.selected_positive_traits:
                # Важно: используем .get(..., []), так как в библиотеке теперь список списков
                trait_mods = self.library.get(tid, {}).get("modifiers", [])
                for mod in trait_mods:
                    # mod = ["group", "body", -2]
                    _, target_id, mod_value = mod
                    active_mods[target_id] = active_mods.get(target_id, 0) + mod_value

        for tid in skills_data[0].get("negative_traits", []):
            # Берем те же модификаторы из библиотеки для черт из файла
            file_trait_mods = self.library.get(tid, {}).get("modifiers", [])
            for mod in file_trait_mods:
                _, target_id, mod_value = mod
                
                # ПРИБАВЛЯЕМ к тому, что уже может быть в active_mods
                active_mods[target_id] = active_mods.get(target_id, 0) + mod_value
        # 3. Применяем модификаторы к копии данных

# 2. Применение модификаторов
        for group_dict in skills_data[0:7]: 
            for key, value_list in group_dict.items():
                # Пропускаем, если это не список (на всякий случай)
                if not isinstance(value_list, list):
                    continue

                # ОПРЕДЕЛЯЕМ ID: для групп это первый элемент, для остального - ключ
                target_id = value_list[0] if key == "skill_group" else key

                if target_id in active_mods:
                    mod = active_mods[target_id]
                    
                    # ЛОГИКА ДЛЯ ГРУПП (["id", "Название", значение])
                    if key == "skill_group":
                        # В char_stats.json это: ["reaction", "Реакция", 6] -> индекс [2]
                        value_list[3] += mod
                    
                    # ЛОГИКА ДЛЯ НАВЫКОВ (["Название", ОП, Модификатор])
                    elif len(value_list) == 3 and isinstance(value_list[1], int):
                        # В char_stats.json это: ["Пистолеты", 3, 0] -> индекс [2]
                        value_list[2] += mod

                    # ЛОГИКА ДЛЯ ПРОИЗВОДНЫХ (["ХП/Вес", Модификатор]) или ([Текущее, Макс])
                    elif len(value_list) == 2 and isinstance(value_list[0], int):
                        # Если это ХП [0, 0] или перенос веса, модифицируем бонус (индекс [1])
                        value_list[1] += mod
                    
                    elif len(value_list) == 1 and isinstance(value_list[0], int):
                        value_list[0] += mod
        
        char_name = skills_data[0].get("char_name")
        source = skills_data[0]

        heal_modificator = source.get("heal_points", [0])[1]
        mental_modificator = source.get("mental_points", [0])[1]
        radiation_modificator = source.get("radiation_points", [0])[1]
        weight_modificator = source.get("carry_weight", [0])[1]
        speed_modificator = source.get("movement_speed", [0])[0]
        
        skill_data2 = find_skill(skills_data, "skill_strength")
        skill_strength = calculate_skill_level(skill_data2[1])
        skill_strength_modificators = skill_data2[2]
        
        skill_data2 = find_skill(skills_data, "skill_persistence")
        skill_persistence_modificators = skill_data2[2]
        skill_persistence = calculate_skill_level(skill_data2[1])
        
        body_value = dex_value = int_value = 0
        for group in skills_data[1:]:
            group_info = group.get("skill_group")
            if group_info:
                g_id = group_info[0]
                if g_id == "body":
                    body_value = int(group_info[2])
                elif g_id == "dexterity":
                    dex_value = int(group_info[2])
                elif g_id == "intellect":
                    int_value = int(group_info[2])
        max_heal = body_value * 5 + 15 + skill_persistence + skill_persistence_modificators + heal_modificator
        max_radiation = body_value * 5 + 15 + radiation_modificator
        max_mental = int_value * 5 + 15 + mental_modificator
        max_weight = (body_value + skill_strength + skill_strength_modificators) * 3 + weight_modificator
        max_speed = dex_value + 5 + speed_modificator
        embed_chars_main = create_embed_bs (f"Умения персонажа {char_name}", f"ПЗ: {max_heal}\nМЗ: {max_mental}\nРЗ: {max_radiation}\nДвижение: {max_speed} метров\nПереносимый вес: {max_weight} кг")
        for group in skills_data[1:7]:
                group_id = group.get("skill_group", [None])[0]
                if group_id:
                    skill_group_raw = group.get("skill_group", ["unknown", "Неизвестная группа", 0])
                    
                    # Конвертируем значение самой группы, если оно тоже в ОП
                    raw_group_fp = skill_group_raw[2] if isinstance(skill_group_raw, list) else 0
                    skill_group_modificator = skill_group_raw[3] if isinstance(skill_group_raw, list) else 0
                    skill_group_level = raw_group_fp
                    skill_group_name = skill_group_raw[1] if isinstance(skill_group_raw, list) else "Группа"

                    field_name = f"{skill_group_name}: {skill_group_level}+{skill_group_modificator}"
                    field_value = []
                    
                    for key, value in group.items():
                        if key != "skill_group":
                            # display_name оставляем как есть
                            display_name = value[0] if isinstance(value, list) and len(value) > 1 else key
                            
                            # skill_fp_value — это то, что лежит в JSON на 3-м месте (индекс 2)
                            skill_fp_value = value[1] if isinstance(value, list) and len(value) >= 3 else 0
                            skill_modificator = value[2]
                            
                            # КОНВЕРТИРУЕМ ОП в УРОВЕНЬ
                            calculated_level = calculate_skill_level(skill_fp_value)
                            
                            # Формируем строку: Название: Уровень (Сумма ОП)
                            field_value.append(f"*{display_name}*: __{calculated_level}+{skill_modificator}__")
                    
                    embed_chars_main.add_field(
                        name=field_name,
                        value="\n".join(field_value) if field_value else "Нет навыков",
                        inline=True
                    )
        return embed_chars_main
    
class CharacterQuestionnnaireModalManager(disnake.ui.View):
    def __init__(self, folder_path, user_id, prev_view, prev_embed):
        super().__init__(timeout=900)
        self.folder_path = folder_path
        self.question = 1
        self.reply = None
        self.user_id = user_id
        self.viewB = prev_view
        self.prev_embed = prev_embed
        self.old_embed = None
        self.current_fp = 0
        self.fp = 0
        start_btn = disnake.ui.Button(label="Перейти", style=disnake.ButtonStyle.red, row=0)
        start_btn.callback = self.start_callback # Переименуем метод
        self.add_item(start_btn)
        self.message = None

    async def on_timeout(self):
        if self.message:
            try:
                # view=None полностью удаляет панель кнопок под сообщением
                await self.message.edit(
                    content="❌ **Время ожидания истекло.** Начните заново через `/pos_ucms`.", 
                    embed=None, 
                    view=None
                )
            except disnake.HTTPException:
                # На случай, если пользователь сам удалил сообщение до таймаута
                pass
        
        self.stop()
    
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True
    
    async def start_callback(self, inter: disnake.Interaction):
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())
        self.current_fp = ssd_dict["current_fp"][0]
        self.fp = ssd_dict["fp"][0]
        old_view = self
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                edit_value = json.loads(await f.read())
        value = edit_value.get(f"{self.question+13}", [""])[0]
        await inter.response.send_modal(CharacterQuestionnaireCharAppModal(self.question, old_view, value))

    async def modal_callback(self, inter: disnake.MessageInteraction, reply=None):
        question_number = 13 + self.question
        if reply:
            self.reply = reply
            await self.rewrite(question_number, reply)
        else:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                    data = json.loads(await f.read())
                self.reply = data.get(f"{question_number}", [""])[0]
        self.rebuild_interface()
        self.embed = create_embed_bs("Проверьте значение ещё раз", self.reply)
        await inter.response.edit_message(embed=self.embed, view=self)

    def rebuild_interface(self):
        self.clear_items()
        # Собираем кнопки
        back = disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.red, row=0)
        edit_answer = disnake.ui.Button(label="Редактировать ответ", style=disnake.ButtonStyle.red, row=0)
        confirm_answer = disnake.ui.Button(label="Подтвердить ответ", style=disnake.ButtonStyle.red, row=0)
        
        back.callback = self.back_callback
        edit_answer.callback = self.edit_answer_callback
        confirm_answer.callback = self.confirm_answer_callback
        
        self.add_item(back)
        self.add_item(edit_answer)
        self.add_item(confirm_answer)

    async def back_callback(self, inter: disnake.Interaction):
        if self.question > 1:
            self.question -= 1
            await self.modal_callback(inter)
        else:
            await self.viewB.update_view(inter, next_cq=True)
            await inter.edit_original_message(embed=self.prev_embed, view=self.viewB)

    async def edit_answer_callback(self, inter: disnake.MessageInteraction):
        old_view = self
        await inter.response.send_modal(CharacterQuestionnaireCharAppModal(self.question, old_view, self.reply))

    async def confirm_answer_callback(self, inter: disnake.MessageInteraction):
        if self.question == 3:
            await inter.response.defer()
            embed = await stats_rendering(inter.bot, self.user_id, self.folder_path)
            embed.add_field(
                name="==========\nОставшиеся СО", 
                value=f"{self.current_fp}/{self.fp}\nНапоминаем - итоговое количество СО должно быть равно 0.", 
                inline=False
                )
            prev_view = self
            new_view = CharacterQuestionnaireFinal(self.folder_path, self.user_id, prev_view, self.embed)
            new_view.message = self.message
            await new_view.prepare_view()
            await inter.edit_original_message(embed=embed, view=new_view)
        else:
            async with get_char_lock(self.folder_path):
                async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                    edit_value = json.loads(await f.read())
            value = edit_value.get(f"{self.question+14}", [""])[0]
            self.question += 1
            old_view = self
            await inter.response.send_modal(CharacterQuestionnaireCharAppModal(self.question, old_view, value))
    
    async def rewrite(self, question_name: str, value: str):
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())
        
        ssd_dict[str(question_name)] = [value]
        
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4)) 

class CharacterQuestionnaireCharAppModal(disnake.ui.Modal):
    def __init__(self, question, old_view, value=""):
        self.old_view = old_view
        self.question = question
        if self.question == 1:
            components = [
                disnake.ui.TextInput(
                    label=f"Укажите особые умения вашего персонажа",
                    placeholder="500 символов максимум.",
                    value=value,
                    custom_id="special_skills",
                    style=disnake.TextInputStyle.paragraph,
                    max_length=500
                )
            ]
            super().__init__(title=f"Умения персонажа вне системы", components=components)
        elif self.question == 2:
            components = [
                disnake.ui.TextInput(
                    label=f"Опишите характер вашего персонажа",
                    placeholder="500 символов максимум.",
                    value=value,
                    custom_id="character",
                    style=disnake.TextInputStyle.paragraph,
                    max_length=500
                )
            ]
            super().__init__(title=f"Характер персонажа", components=components)        
        elif self.question == 3:
            components = [
                disnake.ui.TextInput(
                    label=f"Опишите внешность вашего персонажа",
                    placeholder="500 символов максимум.",
                    value=value,
                    custom_id="appearance",
                    style=disnake.TextInputStyle.paragraph,
                    max_length=500
                )
            ]
            super().__init__(title=f"Внешность персонажа", components=components)        


    async def callback(self, inter: disnake.ModalInteraction):
        if self.question == 1:
            self.reply = inter.text_values["special_skills"]
        if self.question == 2:
            self.reply = inter.text_values["character"]
        if self.question == 3:
            self.reply = inter.text_values["appearance"]
        await self.old_view.modal_callback(inter, self.reply)

class CharacterQuestionnaireFinal(disnake.ui.View):
    def __init__(self, folder_path, user_id, prev_view, prev_embed):
        super().__init__(timeout=900)
        self.folder_path = folder_path
        self.user_id = user_id
        self.current_fp = 0
        self.fp = 0
        self.fp_to_skill = 0
        self.save.disabled = True
        self.viewC = prev_view
        self.mainclass = self.viewC.viewB.viewA
        self.prev_embed = prev_embed
        self.first_name = None
        self.new_name = None
        self.name = None
        self.view = None
        self.message = None
        if self.current_fp == 0:
            self.save.disabled = False
        else:
            self.save.disabled = True

    async def on_timeout(self):
        # 1. Твоя текущая логика очистки папки
        if self.folder_path and os.path.exists(self.folder_path):
            try:
                shutil.rmtree(self.folder_path, onerror=remove_readonly)
                print(f"Таймаут: Временная папка {self.folder_path} удалена.")
            except Exception as e:
                print(f"Ошибка при удалении папки по таймауту: {e}")

        # 2. А вот и магия убирания кнопок без всяких inter:
        if self.message:
            try:
                # view=None полностью удаляет панель кнопок под сообщением
                await self.message.edit(
                    content="❌ **Время ожидания истекло.** Начните заново через `/pos_ucms`.", 
                    embed=None, 
                    view=None
                )
            except disnake.HTTPException:
                # На случай, если пользователь сам удалил сообщение до таймаута
                pass
        
        self.stop()

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True
    
    async def prepare_view(self):
        """Специальный асинхронный метод для подготовки данных перед отправкой View"""
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read()) 
                
        self.current_fp = ssd_dict["current_fp"][0]
        self.fp = ssd_dict["fp"][0]
        self.fp_to_skill = ssd_dict["fp_to_skill"][0]
        
        # Настраиваем доступность кнопки сохранения на основе реальных СО
        if self.current_fp == 0:
            self.save.disabled = False
        else:
            self.save.disabled = True
        return self # Возвращаем сам объект для удобного вызова цепочкой
    
    @disnake.ui.button(label="Справка", style=disnake.ButtonStyle.red, row=0)
    async def faq(self, button: disnake.ui.Button, inter: disnake.Interaction):
        view = HelpPaginator()
        embed = disnake.Embed(title=view.pages[0]["title"], description=view.pages[0]["description"], color=disnake.Color.red())
        await inter.send(embed=embed, view=view, ephemeral=True)
    
    @disnake.ui.button(label="Назад", style=disnake.ButtonStyle.red, row=0)
    async def back(self, button: disnake.ui.Button, inter: disnake.Interaction):
        old_view = self.viewC
        old_view.rebuild_interface()
        await inter.response.edit_message(embed=self.prev_embed, view=old_view)
    
    @disnake.ui.button(label="Изменить возраст", style=disnake.ButtonStyle.red, row=0)
    async def age_change(self, button: disnake.ui.Button, inter: disnake.Interaction):
        old_view = self
        await inter.response.send_modal(CharacterQuestionnaireAgeModal(self.folder_path, None, old_view))

    @disnake.ui.button(label="Изменить имя", style=disnake.ButtonStyle.red, row=0)
    async def name_change(self, button: disnake.ui.Button, inter: disnake.Interaction):
        old_view = self
        await inter.response.send_modal(CharacterCreationModal(self.user_id, self.folder_path, True, old_view))

    @disnake.ui.button(label="Распределить оставшиеся СО", style=disnake.ButtonStyle.red, row=0)
    async def fp_select(self, button: disnake.ui.Button, inter: disnake.Interaction):
        old_view = self
        new_view = CharacterQuestionnaireSkillEdit(old_view)
        new_view.message = self.message
        await new_view.skill_editor_callback(inter)
        await inter.edit_original_message(view=new_view)

    @disnake.ui.button(label="Сохранить", style=disnake.ButtonStyle.red, row=1)
    async def save(self, button: disnake.ui.Button, inter: disnake.Interaction):
        self.clear_items()
        self.mainclass.stop()
        self.viewC.viewB.stop()
        self.viewC.stop()
        
        if self.user_id in self.mainclass.bot.active_creations:
            self.mainclass.bot.active_creations.pop(self.user_id)
            print(f"Сессия пользователя {self.user_id} закрыта.")
        
        if self.name:
            new_name_path = f"user_profiles/{self.user_id}/{self.name}"
            os.rename(self.folder_path, new_name_path)
            self.folder_path = new_name_path

        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                skills_data = json.loads(await f.read()) # Используем другое имя, чтобы не путать с ssd_dict
        
        async with aiofiles.open("chars_data/traits_lib.json", "r", encoding="utf-8") as f:
            traits_lib = json.loads(await f.read())

        async with aiofiles.open("chars_data/effects_lib.json", "r", encoding="utf-8") as f:
            effects_lib = json.loads(await f.read())

        skills_data_for_calc = copy.deepcopy(skills_data)
        convertion = await calculate_modificators(skills_data_for_calc, traits_lib, effects_lib, self.folder_path)
        source = convertion[0]
        
        heal_modificator = source.get("heal_points", [0])[1]
        mental_modificator = source.get("mental_points", [0])[1]

        skill_persistence = 0
        skill_persistence_modificators = 0

        # 3. Пытаемся найти стойкость
        res_persistence = find_skill(convertion, "skill_persistence")
        if res_persistence:
            skill_persistence = calculate_skill_level(res_persistence[1])
            skill_persistence_modificators = res_persistence[2]

        body_value = int_value = 0
        body_modificator = int_modificator = 0
        for group in convertion[1:]:
            group_info = group.get("skill_group")
            if group_info:
                g_id = group_info[0]
                if g_id == "body":
                    body_value = int(group_info[2])
                    body_modificator = int(group_info[3])
                elif g_id == "intellect":
                    int_value = int(group_info[2])
                    int_modificator = int(group_info[3])
        body_value += body_modificator
        int_value += int_modificator
        max_heal = body_value * 5 + 15 + skill_persistence + skill_persistence_modificators + heal_modificator
        max_mental = int_value * 5 + 15 + mental_modificator

        skills_data[0]["heal_points"][0] = max_heal
        skills_data[0]["mental_points"][0] = max_mental

        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))
        
        with open(os.path.join(self.folder_path, "complete_create"), "w") as f:
            f.write("done")

        try:
            role_id = 672125142628958238
            main_status = inter.guild.get_role(role_id)
            await inter.user.add_roles(main_status)
        except:
            pass
        self.stop()

        embed = create_embed_bs("Персонаж успешно создан!", "Теперь вы можете карточку персонажа, снова воспользовавшись данной командой.")
        await inter.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="Удалить персонажа", style=disnake.ButtonStyle.red, row=1)
    async def delete_folder_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if os.path.exists(self.folder_path):
            try:
                await inter.response.defer()
                # rmtree удаляет папку и всё её содержимое
                shutil.rmtree(self.folder_path, onerror=remove_readonly)
                self.stop()
                self.mainclass.stop()
                if self.user_id in self.mainclass.bot.active_creations:
                    self.mainclass.bot.active_creations.pop(self.user_id)
                    print(f"Сессия пользователя {self.user_id} закрыта.")
                await inter.edit_original_message(embed=None, view=None, content="**Создание персонажа отменено.**")
            except Exception as e:
                await inter.response.send_message(f"Ошибка при удалении: {e}", ephemeral=True)
        else:
            await inter.response.send_message("Ошибка: Папка не найдена.", ephemeral=True)
    
    async def embed_update(self, inter: disnake.Interaction, on_fp_screen=False):
        if self.current_fp == 0:
            self.save.disabled = False
        else:
            self.save.disabled = True
        embed = await stats_rendering(inter.bot, self.user_id, self.folder_path)
        embed.add_field(
            name="==========\nОставшиеся СО", 
            value=f"{self.current_fp}/{self.fp}\nНапоминаем - итоговое количество СО должно быть равно 0.", 
            inline=False
            )
        if not on_fp_screen:
            await inter.edit_original_message(embed=embed, view=self)
        else:
            await inter.edit_original_message(embed=embed)

    async def change_age(self, inter, age, fp):
        # 1. Принудительно делаем числами, чтобы не упасть на сравнении
        age = int(age)
        fp = int(fp)
        
        # Сначала отвечаем дискорду, так как работа с файлами — это долго
        if not inter.response.is_done():
            await inter.response.defer()

        # Читаем историю
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())        
        
        old_fp = int(ssd_dict["fp"][0])
        
        # Считаем ПРАВИЛЬНУЮ разницу для текущих очков
        # Если возраст вырос, разница положительная, очки добавляются.
        diff = fp - old_fp
        new_current_fp = int(ssd_dict["current_fp"][0]) + diff

        ssd_dict["age"][0] = age
        ssd_dict["fp"][0] = fp
        ssd_dict["current_fp"][0] = new_current_fp

        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/short_story.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))

        # Работаем с чертами
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                stats_dict = json.loads(await f.read()) # Используем другое имя, чтобы не путать с ssd_dict
        
        negative_traits = stats_dict[0].get("negative_traits", [])
        
        # Чистим старые возрастные черты
        for trait in ["old", "very_old"]:
            if trait in negative_traits:
                negative_traits.remove(trait)

        # Добавляем актуальную
        if 31 <= age <= 50:
            negative_traits.append("old")
        elif age > 50:
            negative_traits.append("very_old")

        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(stats_dict, ensure_ascii=False, indent=4))
        
        # Обновляем состояние самой View
        self.current_fp = new_current_fp
        self.viewC.viewB.current_fp = new_current_fp
        self.mainclass.current_fp = new_current_fp
        self.fp = fp
        self.viewC.viewB.fp = fp
        self.mainclass.fp = fp
        # Запускаем обновление экрана
        await self.embed_update(inter)
    
    async def change_name(self, inter, new_name):
        clean_name = re.sub(r'[\\/*?:"<>|]', "", new_name)
        new_name = clean_name
        if new_name == "":
            return await inter.response.send_message("Имя персонажа не может быть пустой строкой.", ephemeral=True)
        async with get_char_lock(self.folder_path):
            async with aiofiles.open(f"{self.folder_path}/char_stats.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())
        if not self.first_name:
            self.first_name = ssd_dict[0]["char_name"]
        if not self.first_name == new_name:
            if os.path.exists(f"user_profiles/{self.user_id}/{new_name}"):
                return await inter.response.send_message("У вас уже существует персонаж с таким именем.", ephemeral=True)
        self.name = new_name
        with open(f"{self.folder_path}/char_stats.json", "w", encoding="utf-8") as f:
            ssd_dict[0]["char_name"] = str(new_name)
            json.dump(ssd_dict, f, ensure_ascii=False, indent=4)
        with open(f"{self.folder_path}/char_stats_backup.json", "w", encoding="utf-8") as f:
            ssd_dict[0]["char_name"] = str(new_name)
            json.dump(ssd_dict, f, ensure_ascii=False, indent=4)
        await self.embed_update(inter)
        
class CharacterQuestionnaireSkillEdit(disnake.ui.View):
    def __init__(self, main_view):
        super().__init__(timeout=900)
        self.main_view = main_view
        self.user_id = self.main_view.user_id
        self.selected_group = None
        self.selected_skill_tech = None
        self.message = None

    async def on_timeout(self):
        if self.message:
            try:
                # view=None полностью удаляет панель кнопок под сообщением
                await self.message.edit(
                    content="❌ **Время ожидания истекло.** Начните заново через `/pos_ucms`.", 
                    embed=None, 
                    view=None
                )
            except disnake.HTTPException:
                # На случай, если пользователь сам удалил сообщение до таймаута
                pass
        
        self.stop()
    
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим пользователем.", ephemeral=True)
            return False
        return True
    
    async def skill_editor_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        groups_dict = await load_skill_group_names()
        options = []
        for tech_name, display_name in groups_dict.items():
            options.append(
                disnake.SelectOption(
                    label=display_name,
                    value=tech_name
                )
            )
        if options:
            self.select = disnake.ui.Select(
                placeholder="Выберите группу навыков",
                options=options,
                custom_id="skill_group_select",
                min_values=1,
                row=1
            )
        self.select.callback = self.sg_select_callback
        self.add_item(self.select)

        self.back_main = disnake.ui.Button(label="Вернуться", custom_id="back_to_main", style=disnake.ButtonStyle.red, row=0) 
        self.back_main.callback = self.back_to_main
        self.add_item(self.back_main)

        await inter.response.edit_message(view=self)
    
    async def sg_select_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        if hasattr(inter.data, "values") and inter.data.values:
            self.selected_group = inter.data.values[0]
        all_groups = await load_skill_group_names()
        selected_group_display = all_groups.get(self.selected_group, self.selected_group)
        available_skills = await load_skills_by_group(self.selected_group)
        options = [
        disnake.SelectOption(label=display_name, value=tech_name)
        for tech_name, display_name in available_skills.items()
        ]
        if options:
            self.skill_select = disnake.ui.Select(
            placeholder=f"Выберите навык из группы {selected_group_display}",
            options=options,
            custom_id="specific_skill_select",
            row=1
        )
        self.skill_select.callback = self.skill_final_selection_callback 
        self.add_item(self.skill_select)
        self.back_button = disnake.ui.Button(label="Назад к группам", style=disnake.ButtonStyle.red, row=0)
        self.back_button.callback = self.skill_editor_callback # Возвращаемся в начало метода
        self.add_item(self.back_button)
        self.back_main = disnake.ui.Button(label="Вернуться", custom_id="back_to_main", style=disnake.ButtonStyle.red, row=0) 
        self.back_main.callback = self.back_to_main
        self.add_item(self.back_main)
        await inter.response.edit_message(view=self)     
    
    async def back_to_main(self, inter: disnake.MessageInteraction):
        self.stop()
        await inter.response.edit_message(view=self.main_view)
        
    async def skill_final_selection_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        # Сохраняем техническое имя выбранного навыка в self, чтобы кнопки знали, что менять
        self.selected_skill_tech = inter.data.values[0]

        # Кнопка Минус
        self.btn_minus = disnake.ui.Button(label="-1 уровень", style=disnake.ButtonStyle.red, custom_id="skill_minus", row=2)
        self.btn_minus.callback = self.change_skill_points_callback
        
        # Кнопка Плюс
        self.btn_plus = disnake.ui.Button(label="+1 уровень", style=disnake.ButtonStyle.red, custom_id="skill_plus", row=2)
        self.btn_plus.callback = self.change_skill_points_callback
        
        # Кнопка Назад (к выбору навыков в той же группе)
        self.btn_back = disnake.ui.Button(label="К списку навыков", style=disnake.ButtonStyle.red, row=2)
        self.btn_back.callback = self.sg_select_callback

        self.back_main = disnake.ui.Button(label="Вернуться", custom_id="back_to_main", style=disnake.ButtonStyle.red, row=0) 
        self.back_main.callback = self.back_to_main
        
        self.add_item(self.back_main)
        self.add_item(self.btn_minus)
        self.add_item(self.btn_back)
        self.add_item(self.btn_plus)
    
        await inter.response.edit_message(view=self)

    async def change_skill_points_callback(self, inter: disnake.MessageInteraction):
        MAX_SKILL_FP = 21
        delta = 1 if inter.component.custom_id == "skill_plus" else -1
        
        # 1. Проверка на вложенные СО при попытке уменьшить
        if delta < 0 and self.main_view.fp_to_skill <= 0:
            await inter.response.send_message("Вы не вкладывали СО в навыки.", ephemeral=True)
            return

        # 2. Проверка на наличие СО при попытке увеличить
        if delta > 0 and self.main_view.current_fp <= 0:
            await inter.response.send_message("У вас нет свободных СО.", ephemeral=True)
            return
        
        character_stats_path = f"{self.main_view.folder_path}/char_stats.json"
        short_story_path = f"{self.main_view.folder_path}/short_story.json"
        async with get_char_lock(self.main_view.folder_path):
            async with aiofiles.open(character_stats_path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
        
        skill_found = False
        for group in data[1:]:
            if self.selected_skill_tech in group:
                # Используем индекс [1] для ОП (проверь это в своем JSON!)
                current_op = group[self.selected_skill_tech][1]
                
                # Проверка на максимум при попытке увеличить
                if delta > 0 and current_op >= MAX_SKILL_FP:
                    await inter.response.send_message("Навык уже развит до максимума (10 уровень)!", ephemeral=True)
                    return
                
                added_fp = calculate_needed_fp(current_op, delta)
                group[self.selected_skill_tech][1] += added_fp
                
                # Обновляем счетчики во View
                self.main_view.fp_to_skill += delta
                self.main_view.current_fp -= delta
                self.main_view.viewC.viewB.current_fp += delta 
                self.main_view.viewC.viewB.viewA.current_fp -= delta

                skill_found = True
                break
                
        if skill_found:
            async with aiofiles.open(f"{self.main_view.folder_path}/short_story.json", "r", encoding="utf-8") as f:
                ssd_dict = json.loads(await f.read())  
            ssd_dict["current_fp"][0] = self.main_view.current_fp
            ssd_dict["fp_to_skill"][0] -= delta
            
            async with aiofiles.open(short_story_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(ssd_dict, ensure_ascii=False, indent=4))
                
            async with aiofiles.open(character_stats_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))

        await inter.response.defer(with_message=False, ephemeral=True)
        await self.main_view.embed_update(inter, on_fp_screen=True)

class HelpPaginator(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=120) # Справка закроется через минуту бездействия
        self.page = 0
        
        # Твои фиксированные данные
        self.pages = [
            {
                "title": "Справка: что есть характеристика",
                "description": "ХАРАКТЕРИСТИКОЙ является врождённая предрасположенность персонажа к тем или иным действиям и умениям. Можно сказать, что ХАРАКТЕРИСТИКА является «одарённостью» вашего персонажа. Например, персонаж с хорошей РЕАКЦИЕЙ сумеет удержать пистолет достаточно ровно и плавно нажать на спусковой крючок даже если он ранее не обладал обширным опытом стрельбы. Персонаж с высоким ИНТЕЛЛЕКТОМ догадается о базовых принципах работы аномалий даже при первой встрече с ними. "
            },
            {
                "title": "Справка: что есть навык",
                "description": "Навыки - это знания и умения, приобретённые вашим персонажем в ходе своей жизнедеятельности. В отличие от ХАРАКТЕРИСТИК, навыкам можно обучаться, навыки можно улучшать. Это значит, что ваш персонаж сможет заниматься самосовершенствованием в процессе РП. \n\nСвязь навыков и ХАРАКТЕРИСТИК\n\nПредставьте себе дерево. Ствол дерева - это ваш персонаж. Основа, база, дающая фундамент для роста веток. Ветки - это ХАРАКТЕРИСТИКИ. У веток есть множество мелких сучков - навыков. Равно как у конкретной ветки будут определённые сучья, точно так же у конкретной ХАРАКТЕРИСТИКИ будут определённые навыки."
            },
            {
                "title": "Справка: а зачем вообще всё это надо",
                "description": "У нас на сервере используется СОСП - Система Определения Способностей Персонажа. Под этим понятием мы подразумеваем ролевую систему, которая позволит вашему персонажу в буквальном смысле владеть рядом умений (врождённых и приобретённых в ходе жизни), применять их в Зоне, а также улучшать некоторые из них. У каждого человека существуют как сильные, так и слабые стороны. Кто-то хорош в снайперской стрельбе, но не силён в общении. Кто-то за версту чует аномалии, но при виде крови теряет сознание. А кто-то очень красноречивый, но хилый на здоровье. Идеальных людей не бывает: вам придётся крутиться для того, чтобы выжить. Сама система как раз позволяет чётко определять, что ваш персонаж умеет, а что - нет."
            }
        ]

    async def update_help(self, inter: disnake.MessageInteraction):
        data = self.pages[self.page]
        embed = disnake.Embed(
            title=data["title"],
            description=data["description"],
            color=disnake.Color.red()
        )
        # Обновляем сообщение с новым эмбедом и этой же вьюхой (кнопками)
        await inter.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="⬅️", style=disnake.ButtonStyle.red, row=0)
    async def prev_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.page > 0:
            self.page -= 1
            await self.update_help(inter)
        else:
            await inter.response.send_message("Это первая страница!", ephemeral=True)

    @disnake.ui.button(label="➡️", style=disnake.ButtonStyle.red, row=0)
    async def next_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.page < len(self.pages) - 1:
            self.page += 1
            await self.update_help(inter)
        else:
            await inter.response.send_message("Это последняя страница!", ephemeral=True)