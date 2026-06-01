import disnake
import json
import aiofiles
import os
import re
import asyncio
import uuid

from utils import *

ITEMS_LIB_PATH = "chars_data/items_lib.json"

READABLE_ITEM_TYPES = {
    "narrative": "Нарративный предмет",
    "crafts": "Компонент крафта",
    "instruments": "Инструмент",
    "ammo": "Боеприпасы",
    "body_part": "Часть тела мутанта",
    "grenade": "Граната / Взрывчатка",
    "medicine": "Медицина / Препараты",
    "food": "Еда / Напитки",
    "artefact": "Артефакт",
    "weapon": "Огнестрельное оружие",
    "melee_weapon": "Холодное оружие",
    "armor": "Основа брони",
    "head_armor": "Шлем",
    "head_mask": "Противогаз",
    "anomaly_detector": "Детектор аномалий",
    "artefact_detector": "Детектор артефактов",
    "head_eyes": "Оптика / Приборы ночного видения",
    "head_ears": "Гарнитура / Активные наушники",
    "armor_plate": "Бронеплита",
    "add_armor": "Защита конечностей",
    "mounted_mod": "Навесной элемент брони",
    "helmet_mods": "Модификация шлема",
    "anomaly_mod": "Аномальный элемент защиты"
}

# Человеческие названия укрупненных категорий для отображения в селекторе
BACKPACK_CATEGORIES = {
    "all": "Все категории",
    "weaponry": "Оружие и ножи",
    "ammo_grenades": "Боеприпасы и гранаты",
    "medicine_food": "Медицина и провизия",
    "armor_suits": "Костюмы и шлемы",
    "armor_mods": "Модификации и навесы брони",
    "protection_elements": "Защитные плиты и накладки",
    "electronics": "Детекторы и приборы",
    "craft_narrative": "Крафт и квестовые предметы"
}

# Маппинг: связываем все 24 технических типа с 8 укрупненными категориями
ITEM_TYPE_TO_CATEGORY = {
    # Оружие
    "weapon": "weaponry", "melee_weapon": "weaponry",
    # Расходники боевые
    "ammo": "ammo_grenades", "grenade": "ammo_grenades",
    # Жизнеобеспечение
    "medicine": "medicine_food", "food": "medicine_food",
    # Основы экипировки
    "armor": "armor_suits", "head_armor": "armor_suits", "head_mask": "armor_suits",
    # Модификаторы брони (Объединяем в одну группу по твоему запросу)
    "mounted_mod": "armor_mods", "helmet_mods": "armor_mods", "anomaly_mod": "armor_mods", 
    "armor_plate": "armor_mods", "add_armor": "armor_mods",
    # Электроника и детекторы
    "anomaly_detector": "electronics", "artefact_detector": "electronics", 
    "head_eyes": "electronics", "head_ears": "electronics",
    # Хлам, артефакты и нарратив
    "artefact": "craft_narrative", "crafts": "craft_narrative", 
    "instruments": "craft_narrative", "narrative": "craft_narrative", "body_part": "craft_narrative"
}

async def add_item_to_inventory(folder_path: str, item_id: str, items_lib: dict, amount: int = 1) -> bool:
    """Универсальная АСИНХРОННАЯ функция начисления предметов с полной генерацией РП-полей брони/оружия"""
    inv_file = os.path.join(folder_path, "char_inventory.json")
    if not os.path.exists(inv_file) or item_id not in items_lib: return False
    
    item_template = items_lib[item_id]
    is_stackable = item_template.get("stackable", "yes") == "yes"
    
    async with get_char_lock(folder_path):
        try:
            # ИСПРАВЛЕНО: Возвращаем каноничное асинхронное чтение инвентаря
            async with aiofiles.open(inv_file, "r", encoding="utf-8") as f:
                inv_data = json.loads(await f.read())
        except: 
            return False
        
        # --- СЦЕНАРИЙ А: Предмет стакается (медицина, патроны, еда) ---
        if is_stackable:
            static_bag = inv_data["inventory"].setdefault("static", {})
            static_bag[item_id] = static_bag.get(item_id, 0) + amount
            
        # --- СЦЕНАРИЙ Б: Уникальный не стакающийся предмет (оружие, броня, электроника) ---
        else:
            unique_bag = inv_data["inventory"].setdefault("unique", {})
            for _ in range(amount):
                # Генерируем уникальный ID для каждой штучной единицы снаряжения
                u_id = f"u_{item_id}_{uuid.uuid4().hex[:6]}"
                
                # Собираем индивидуальную карточку выданного предмета по шаблонам
                u_card = {
                    "type": item_template.get("type"),
                    "stackable": "no",
                    "template": item_id,
                    "username": item_template.get("name"),
                    "userdesc": None,
                    "userpicture": None
                }
                
                # 1. ГЕНЕРАЦИЯ ДЛЯ ОСНОВЫ БРОНИ (armor) согласно шаблоны.json
                if u_card["type"] == "armor":
                    u_card["issued_effects"] = list(item_template.get("issued_effects", []))
                    u_card["plate"] = None
                    u_card["additional_armor"] = None
                    u_card["armor_points"] = [0, 0] # По умолчанию плиты в новом жилете нет
                    u_card["additional_armor_points"] = [0, 0]
                    
                    # Индивидуальные параметры резистов брони при создании (равны base_anomaly_resist)
                    base_ar = item_template.get("base_anomaly_resist", 0)
                    u_card["electro_resist"] = base_ar
                    u_card["termo_resist"] = base_ar
                    u_card["chemical_resist"] = base_ar
                    u_card["radiation_resist"] = base_ar
                    
                    u_card["anomaly_mods"] = item_template.get("base_anomaly_mods", 6)
                    u_card["setup_anomaly_mods"] = []
                    u_card["setup_mods"] = []
                    u_card["artefact_containers"] = {}
                    u_card["current_artefact_equip"] = []
                
                # 2. ГЕНЕРАЦИЯ ДЛЯ ОРУЖИЯ (weapon)
                elif u_card["type"] == "weapon":
                    u_card["durability"] = 10 # Оружие выдается полностью исправным
                    u_card["modifications"] = []
                    
                # 3. ГЕНЕРАЦИЯ ДЛЯ ЗАЩИТЫ ГОЛОВЫ И МАСОК (head_armor, head_mask)
                elif u_card["type"] in ["head_armor", "head_mask"]:
                    u_card["armor_points"] = [item_template.get("base_armor_points", 0), item_template.get("base_armor_points", 0)]
                    u_card["modifications"] = []
                    
                    # Шлемы и маски копируют резисты индивидуально из своего шаблона
                    u_card["electro_resist"] = item_template.get("electro_resist", 0)
                    u_card["termo_resist"] = item_template.get("termo_resist", 0)
                    u_card["chemical_resist"] = item_template.get("chemical_resist", 0)
                    u_card["radiation_resist"] = item_template.get("radiation_resist", 0)
                    u_card["psy_resist"] = item_template.get("psy_resist", 0)
                
                # 4. ГЕНЕРАЦИЯ ДЛЯ ЧИСТЫХ БРОНЕЭЛЕМЕНТОВ (плиты, накладки)
                elif u_card["type"] in ["armor_plate", "add_armor"]:
                    tmpl_pts = item_template.get("armor_points", [10, 10])
                    u_card["armor_points"] = [tmpl_pts[1], tmpl_pts[1]]

                unique_bag[u_id] = u_card
                
        # ИСПРАВЛЕНО: Переводим на асинхронную запись файла через aiofiles
        try:
            async with aiofiles.open(inv_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(inv_data, ensure_ascii=False, indent=4))
        except:
            return False

    # Принудительно синхронизируем вес облегченного/утяжеленного рюкзака
    await sync_character_weight_and_effects(folder_path)
    return True

async def sync_character_weight_and_effects(folder_path: str):
    """
    Каноничный метод синхронизации веса и наложения дебаффов нагрузки.
    Интегрирован с динамической формулой расчета MaxWeight системы PoS RP.
    """
    inventory_path = os.path.join(folder_path, "char_inventory.json")
    stats_path = os.path.join(folder_path, "char_stats.json")
    items_lib_path = "chars_data/items_lib.json"
    traits_lib_path = "chars_data/traits_lib.json"
    effects_lib_path = "chars_data/effects_lib.json"
    
    if not os.path.exists(inventory_path) or not os.path.exists(stats_path):
        return

    try:
        # 1. Асинхронно считываем все необходимые файлы данных
        async with aiofiles.open(inventory_path, "r", encoding="utf-8") as f:
            inv_data = json.loads(await f.read())
        async with aiofiles.open(stats_path, "r", encoding="utf-8") as f:
            skills_data = json.loads(await f.read())
        async with aiofiles.open(items_lib_path, "r", encoding="utf-8") as f:
            items_lib = json.loads(await f.read())
            
        # Загружаем библиотеки черт и эффектов для симуляции active_mods
        traits_lib = {}
        effects_lib = {}
        if os.path.exists(traits_lib_path):
            async with aiofiles.open(traits_lib_path, "r", encoding="utf-8") as f: traits_lib = json.loads(await f.read())
        if os.path.exists(effects_lib_path):
            async with aiofiles.open(effects_lib_path, "r", encoding="utf-8") as f: effects_lib = json.loads(await f.read())
            
        source = skills_data[0] # Мета-блок [source: 1]
    except Exception as e:
        print(f"[Weight Sync Error] Ошибка чтения конфигурационных файлов: {e}")
        return

    # 2. Высчитываем суммарный вес рюкзака (актуальный вес вещей)
    total_weight = 0.0
    static_items = inv_data.get("inventory", {}).get("static", {})
    for item_id, amount in static_items.items():
        if amount <= 0: continue
        total_weight += items_lib.get(item_id, {}).get("weight_per_item", 0.0) * amount
        
    # Находим этот блок внутри sync_character_weight_and_effects:
    unique_items = inv_data.get("inventory", {}).get("unique", {})
    for u_id, u_data in unique_items.items():
        template_id = u_data.get("template", u_id)
        # Прибавляем базовый вес самой основы/оружия/шлема
        total_weight += items_lib.get(template_id, {}).get("weight_per_item", 0.0)
        
        # Если вставлена плита — её вес уже учтётся здесь, так как она сама лежит в unique_items,
        # НО чтобы избежать путаницы: в твоей логике calculate_inventory_weight плита физически остаётся в unique.
        # Поэтому вес плиты и защиты конечностей функция суммирует, когда натыкается на них как на отдельные предметы в unique_items.
        
        # А вот тут мы СТРОГО считаем физический вес стакающихся модов, которые ИСЧЕЗЛИ из рюкзака:
        if u_data.get("type") == "armor":
            # Считаем вес поглощённых навесных модификаций (setup_mods)
            setup_mods = u_data.get("setup_mods", [])
            for mod_id in setup_mods:
                total_weight += items_lib.get(mod_id, {}).get("weight_per_item", 0.0)
                
            # Считаем вес поглощённых аномальных обшивок (setup_anomaly_mods)
            setup_anom = u_data.get("setup_anomaly_mods", [])
            for mod_id in setup_anom:
                total_weight += items_lib.get(mod_id, {}).get("weight_per_item", 0.0)
            
    current_weight = round(total_weight, 3)

# 3. Симулируем сборку активных модификаторов из черт и баффов/дебаффов
    active_mods = {}
    for tid in source.get("negative_traits", []):
        for _, target_id, val in traits_lib.get(tid, {}).get("modifiers", []): active_mods[target_id] = active_mods.get(target_id, 0) + val
    for tid in source.get("positive_traits", []):
        for _, target_id, val in traits_lib.get(tid, {}).get("modifiers", []): active_mods[target_id] = active_mods.get(target_id, 0) + val
    for tid in source.get("buffs", []):
        for _, target_id, val in effects_lib.get(tid, {}).get("modifiers", []): active_mods[target_id] = active_mods.get(target_id, 0) + val
    
    # Полностью игнорируем весовые штрафы при симуляции дебаффов
    overweight_effects = ["quarter_weight", "half_weight", "limit_weight"]
    for tid in source.get("debuffs", []):
        if tid in overweight_effects: continue
        for _, target_id, val in effects_lib.get(tid, {}).get("modifiers", []): active_mods[target_id] = active_mods.get(target_id, 0) + val

    # Helper для чтения чистых ОП навыка из структуры
    def get_skill_fp(data, s_id):
        for group in data[1:7]:
            if s_id in group: return group[s_id][1] if isinstance(group[s_id], list) and len(group[s_id]) >= 2 else 0
        return 0

    # 4. Берем БАЗОВОЕ значение группы (индекс 2), полностью игнорируя модификаторы из файла
    base_body_value = 0
    for group in skills_data[1:7]:
        group_info = group.get("skill_group")
        if group_info and group_info[0] == "body":
            base_body_value = int(group_info[2])
            break
            
    total_body = base_body_value + active_mods.get("body", 0)

    # Рассчитываем Силу, используя оригинальную функцию перевода ОП в Уровень
    skill_strength_fp = get_skill_fp(skills_data, "skill_strength")
    
    # ИСПРАВЛЕНО: Вместо топорного // 10 вызываем твой оригинальный ролевой расчет!
    from charlists import calculate_skill_level 
    skill_strength_level = calculate_skill_level(skill_strength_fp)
    
    skill_strength_modificators = active_mods.get("skill_strength", 0)

    # Получаем чистый модификатор веса
    weight_modificator = source.setdefault("carry_weight", [0, 0])[1] + active_mods.get("carry_weight", 0)

    # 5. ДИНАМИЧЕСКИЙ РАСЧЕТ МАКСИМАЛЬНОГО ВЕСА
    max_weight = (total_body + skill_strength_level + skill_strength_modificators) * 3 + weight_modificator

    # Записываем вычисленный текущий вес вещей в первый элемент carry_weight
    source["carry_weight"][0] = current_weight

    # 5. ДИНАМИЧЕСКИЙ РАСЧЕТ МАКСИМАЛЬНОГО ВЕСА НА ЧИСТЫХ СТАТАХ
    max_weight = (total_body + skill_strength_level + skill_strength_modificators) * 3 + weight_modificator

    # Записываем вычисленный текущий вес вещей в первый элемент carry_weight
    source["carry_weight"][0] = current_weight

# 6. Очищаем старые весовые дебаффы из списка "debuffs"
    if "debuffs" not in source:
        source["debuffs"] = []
    
    overweight_effects = ["quarter_weight", "half_weight", "limit_weight"]
    source["debuffs"] = [d for d in source["debuffs"] if d not in overweight_effects]

    # 7. ИСПРАВЛЕНО: Строгая проверка изолированных диапазонов нагрузки персонажа
    # Текущий вес >= Максимальный вес -> Штраф: limit_weight
    if current_weight >= max_weight:
        source["debuffs"].append("limit_weight")
        
    # Максимальный вес / 2 <= Текущий вес < Максимальный вес -> Штраф: half_weight
    elif (max_weight / 2) <= current_weight < max_weight:
        source["debuffs"].append("half_weight")
        
    # Максимальный вес / 4 <= Текущий вес < Максимальный вес / 2 -> Штраф: quarter_weight
    elif (max_weight / 4) <= current_weight < (max_weight / 2):
        source["debuffs"].append("quarter_weight")
        
    # Если Текущий вес < Максимальный вес / 4 -> Никаких дебаффов не добавляется, массив остается чистым

    # 8. Записываем обновленный чарлист обратно в файл
    try:
        async with aiofiles.open(stats_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))
    except Exception as e:
        print(f"[Weight Sync Error] Ошибка сохранения результатов: {e}")

async def remove_item_from_inventory(folder_path: str, target_id: str, amount: int = 1) -> bool:
    """Универсальное изъятие предмета (target_id может быть как уникальным UUID, так и техническим ID стака)"""
    inv_file = os.path.join(folder_path, "char_inventory.json")
    if not os.path.exists(inv_file): return False
    
    async with get_char_lock(folder_path):
        try:
            with open(inv_file, "r", encoding="utf-8") as f: inv_data = json.load(f)
        except: return False
        
        static_bag = inv_data.get("inventory", {}).get("static", {})
        unique_bag = inv_data.get("inventory", {}).get("unique", {})
        eq = inv_data.get("equipment", {})
        
        # Если пришёл уникальный UUID шмотки
        if target_id in unique_bag:
            # Если она надета — принудительно разэкипируем перед уничтожением
            for slot, u_id in eq.items():
                if u_id == target_id: eq[slot] = None
            del unique_bag[target_id]
            
        # Если пришёл технический ID стакающегося предмета[cite: 5]
        elif target_id in static_bag:
            if static_bag[target_id] < amount: return False # Недостаточно вещей для удаления
            static_bag[target_id] -= amount
            if static_bag[target_id] <= 0: del static_bag[target_id]
        else:
            return False
            
        with open(inv_file, "w", encoding="utf-8") as f:
            json.dump(inv_data, f, indent=4, ensure_ascii=False)
    
    await sync_character_weight_and_effects(folder_path)
    return True

def is_valid_tech_id(text):
    return bool(re.fullmatch(r'[a-z0-9_]+', text))

def parse_dice_string(text: str) -> list:
    """Парсит строку вида '2d6+3', '-1d6+0' или '15' в формат [кубы, модификатор]."""
    text = text.strip().lower().replace(" ", "")
    # Регулярка для кубов (учитывает возможный минус перед кубами)
    match = re.fullmatch(r'(-?\d+)d6([+-]\d+)?', text)
    if match:
        dice = int(match.group(1))
        mod = int(match.group(2)) if match.group(2) else 0
        return [dice, mod]
    # Если ввели просто жесткое число
    if text.isdigit() or (text.startswith(('-', '+')) and text[1:].isdigit()):
        return [0, int(text)]
    return [0, 0]

def format_dice_array(arr: list) -> str:
    """Преобразует массив [кубы, мод] обратно в строку '2d6+3'."""
    if not arr or not isinstance(arr, list) or len(arr) < 2:
        return "0d6+0"
    dice, mod = arr[0], arr[1]
    if dice == 0:
        return f"{mod}"
    if mod == 0:
        return f"{dice}d6"
    return f"{dice}d6{'+' if mod > 0 else ''}{mod}"

async def load_items_library() -> dict:
    if not os.path.exists(ITEMS_LIB_PATH):
        return {}
    async with aiofiles.open(ITEMS_LIB_PATH, "r", encoding="utf-8") as f:
        try: return json.loads(await f.read())
        except json.JSONDecodeError: return {}

async def save_items_library(library: dict):
    async with aiofiles.open(ITEMS_LIB_PATH, "w", encoding="utf-8") as f:
        await f.write(json.dumps(library, indent=4, ensure_ascii=False))


class UnitedItemsManagementSystem(disnake.ui.View):
    def __init__(self, target_id=None, current_data=None):
        super().__init__(timeout=900)
        self.tech_id = target_id
        self.old_tech_id = target_id
        self.type_selected = True if current_data else False
        self.current_screen = "main"  # Состояния экрана: "main" или "spec"
        self.selected_stat = None  # Инициализируем пустой параметр для селекторов оружия
        self.effects_lib = None
        self.deletable_status = current_data.get("deletable", "yes") if current_data else "yes"

        self.available_types = [
            ("Медицина", "medicine"), ("Еда / Напитки", "food"), ("Артефакты", "artefact"),
            ("Боеприпасы (Патроны)", "ammo"), ("Гранаты", "grenade"), ("Оружейные модификации", "gun_modification"),
            ("Навесные моды брони", "mounted_mod"), ("Модификации шлемов", "helmet_mods"), ("Аномальные модификаторы", "anomaly_mod"),
            ("Бронеплиты", "armor_plate"), ("Защита конечностей", "add_armor"), ("Ресурсы / Крафт", "crafts"),
            ("Инструменты", "instruments"), ("Части мутантов", "body_part"), ("Нарративные предметы", "narrative"),
            ("Основа брони (Костюм)", "armor"), ("Шлемы", "head_armor"), ("Противогазы / Маски", "head_mask"),
            ("Детекторы аномалий", "anomaly_detector"), ("Детекторы артефактов", "artefact_detector"),
            ("Освещение (Слот Зрение)", "head_eyes"), ("Наушники (Слот Уши)", "head_ears"),
            ("Огнестрельное оружие", "weapon"), ("Холодное оружие", "melee_weapon")
        ]

        if current_data:
            self.name = current_data.get("name", "Новый предмет")
            self.description = current_data.get("description", "Описание отсутствует")
            self.item_type = current_data.get("type", "medicine")
            self.weight = current_data.get("weight_per_item", 0.1)
            self.base_price = current_data.get("base_price", 1000)
            self.stackable = current_data.get("stackable", "yes")
            self.count_multiply = current_data.get("count_multiply", 1)
            self.picture_url = current_data.get("picture_url", None)
            self.extra_data = {k: v for k, v in current_data.items() if k not in [
                "name", "description", "type", "weight_per_item", "base_price", "stackable", "count_multiply", "picture_url"
            ]}
        else:
            self.name = "Новый предмет"
            self.description = "Описание отсутствует"
            self.item_type = None
            self.weight = 0.1
            self.base_price = 1000
            self.stackable = "yes"
            self.count_multiply = 1
            self.picture_url = None
            self.extra_data = {}

    def construct_item_json(self) -> dict:
        data = {
            "name": self.name,
            "description": self.description,
            "type": self.item_type,
            "stackable": self.stackable,
            "weight_per_item": self.weight,
            "base_price": self.base_price,
            "count_multiply": self.count_multiply,
            "picture_url": self.picture_url,
            "deletable": getattr(self, "deletable_status", "yes")  # Берем статус напрямую из нашей переменной класса
        }
        data.update(self.extra_data)
        
        # Список категорий уникального снаряжения, поддерживающего кастомизацию имени/описания
        customizable_equipment = [
            "weapon", "melee_weapon", "gun_modification", "armor", "head_armor", "head_mask",
            "anomaly_detector", "artefact_detector", "head_eyes", "head_ears"
        ]
        
        if self.item_type in customizable_equipment:
            if "username" not in data: data["username"] = None
            if "userdesc" not in data: data["userdesc"] = None
            if "userpicture" not in data: data["userpicture"] = None

        # --- 1. Категория: Огнестрельное оружие (weapon) ---
        if self.item_type == "weapon":
            if "base_stats" not in data:
                data["base_stats"] = {"damage": [1, 0], "recoil": 0, "accuracy": 0, "grouping": 3, "reliability": 10, "max_magazine": 30}
            if "text_feature" not in data: data["text_feature"] = ""
            if "weapon_class" not in data: data["weapon_class"] = "Пистолет"
            if "associated_skill" not in data: data["associated_skill"] = "skill_handguns"
            if "auto_fire" not in data: data["auto_fire"] = "no"
            
        # --- 2. Категория: Холодное оружие (melee_weapon) ---
        elif self.item_type == "melee_weapon":
            if "damage" not in data: data["damage"] = [1, 0]
            if "text_feature" not in data: data["text_feature"] = ""

        # --- 3. Категория: Основа брони (armor) ---
        elif self.item_type == "armor":
            if "issued_effects" not in data: data["issued_effects"] = []
            if "base_anomaly_resist" not in data: data["base_anomaly_resist"] = 0 # АЗ (Внутренняя защита)
            if "base_anomaly_mods" not in data: data["base_anomaly_mods"] = 6     # ДАЗ (Ячейки под моды)
            if "text_feature" not in data: data["text_feature"] = ""

        # --- 4. Категория: Защита головы и маски (head_armor, head_mask) ---
        elif self.item_type in ["head_armor", "head_mask"]:
            if "issued_effect" not in data: data["issued_effect"] = None
            if "base_armor_points" not in data: data["base_armor_points"] = 0
            for resist in ["electro_resist", "termo_resist", "chemical_resist", "radiation_resist", "psy_resist"]:
                if resist not in data: data[resist] = 0
            if self.item_type == "head_armor" and "have_mask" not in data:
                data["have_mask"] = "no"

        # --- 5. Категория: Модификации брони и шлемов ---
        elif self.item_type == "anomaly_mod":
            if "anomaly_mod_req" not in data: data["anomaly_mod_req"] = 1
            if "add_resist" not in data: data["add_resist"] = {}
        elif self.item_type in ["armor_plate", "add_armor"]:
            # Гарантируем, что в базе шаблон хранит [макс, макс], например [12, 12]
            if "armor_points" not in data: 
                data["armor_points"] = [10, 10]
            if self.item_type == "add_armor" and "issued_effect" not in data: 
                data["issued_effect"] = None
        elif self.item_type in ["mounted_mod", "helmet_mods"]:
            if "issued_effect" not in data: data["issued_effect"] = []
            if "modificators" not in data: data["modificators"] = {}

        # --- 6. Категория: Детекторы и Электроника ---
        elif self.item_type == "artefact_detector":
            if "class" not in data: data["class"] = 1
        elif self.item_type in ["anomaly_detector", "head_ears"]:
            if "long_effects" not in data: data["long_effects"] = {"add": None}

        # --- 7. Категория: Оружейные моды ---
        elif self.item_type == "gun_modification":
            if "base_stats" not in data:
                data["base_stats"] = {"damage": [0, 0], "recoil": 0, "accuracy": 0, "grouping": 0, "reliability": 0, "max_magazine": 0}
            if "text_feature" not in data: data["text_feature"] = ""
            # ФИКС: Дефолтное влияние обвеса на автоогонь оружия (None - не влияет)
            if "mod_auto_fire" not in data: data["mod_auto_fire"] = None

        return data

    async def send_main_window(self, inter: disnake.Interaction):
        self.clear_items()
        if not self.effects_lib:
            self.effects_lib = await load_items_library()
        
        # ЭТАП 1: Выбор типа создаваемого предмета
        if not self.type_selected:
            embed = disnake.Embed(title="UIMS: Выбор категории", description="Выберите тип создаваемого предмета:", color=disnake.Color.red())
            type_options = [disnake.SelectOption(label=t_name, value=t_val) for t_name, t_val in self.available_types[:25]]
            select_type = disnake.ui.Select(placeholder="Категория снаряжения...", options=type_options, custom_id="uims_init_type")
            select_type.callback = self.select_type_callback
            self.add_item(select_type)
            
            btn_cancel = disnake.ui.Button(label="Отмена", style=disnake.ButtonStyle.red)
            btn_cancel.callback = self.cancel_callback
            self.add_item(btn_cancel)

        # ЭТАП 2: Основной экран параметров карточки (Просмотр)
        elif self.current_screen == "main":
            spec_info = ""
            
            # --- 1. ВЕТКА: Медицина, Еда, Артефакты ---
            if self.item_type in ["medicine", "food", "artefact"]:
                eff = self.extra_data.get("use_effects", {})
                long_eff_data = self.extra_data.get("long_effects", {})
                
                adds = []
                removes = []
                if isinstance(long_eff_data, dict):
                    adds = long_eff_data.get("add", [])
                    removes = long_eff_data.get("remove", [])
                
                adds_names = [self.effects_lib.get(x, {}).get("name", x) for x in adds if x]
                removes_names = [self.effects_lib.get(x, {}).get("name", x) for x in removes if x]
                
                adds_str = ", ".join(adds_names) if adds_names else "Отсутствуют"
                removes_str = ", ".join(removes_names) if removes_names else "Отсутствуют"
                
                if self.item_type != "artefact":
                    spec_info = (
                        f"**[Эффект в момент использования]**\n"
                        f"• Восстановление ПЗ: `{format_dice_array(eff.get('add_hp', [0, 0]))}`\n"
                        f"• Восстановление МЗ: `{format_dice_array(eff.get('add_mp', [0, 0]))}`\n"
                        f"• Вывод радиации (РЗ): `{format_dice_array(eff.get('add_rp', [0, 0]))}`\n"
                        f"**[Продолжительный эффект]**\n"
                        f"• Накладывает статусы: `{adds_str}`\n"
                        f"• Снимает статусы: `{removes_str}`"
                    )
                else:
                    spec_info = (
                        f"**[Продолжительный эффект]**\n"
                        f"• Накладывает статусы: `{adds_str}`\n"
                        f"• Снимает статусы: `{removes_str}`"
                    )
            
            # --- 2. ВЕТКА: Огнестрел, Ножи, Модификации оружия ---
            elif self.item_type in ["weapon", "melee_weapon", "gun_modification"]:
                stats = self.extra_data.get("base_stats", {})
                text_feat = self.extra_data.get("text_feature", "Отсутствует")
                
                if self.item_type == "melee_weapon":
                    dmg = self.extra_data.get("damage", [1, 0])
                    spec_info = (
                        f"**[Боевые характеристики холодного оружия]**\n"
                        f"• Урон: `{format_dice_array(dmg)}`\n"
                        f"• Особое свойство: *{text_feat}*"
                    )
                elif self.item_type == "gun_modification":
                    stats = self.extra_data.get("base_stats", {})
                    text_feat = self.extra_data.get("text_feature", "Отсутствует")
                    
                    # Рендер читаемого статуса влияния на автоогонь
                    mod_af = self.extra_data.get("mod_auto_fire")
                    mod_af_readable = "Включает автоогонь" if mod_af == "yes" else ("Выключает автоогонь" if mod_af == "no" else "Не влияет")
                    
                    spec_info = (
                        f"**[Модификаторы оружейного обвеса]**\n"
                        f"• Изменение автоогня: `{mod_af_readable}`\n"
                        f"• Модификатор урона: `{format_dice_array(stats.get('damage', [0, 0]))}`\n"
                        f"• Изменение отдачи: `{stats.get('recoil', 0)}` | Точность: `{stats.get('accuracy', 0)}`\n"
                        f"• Изменение кучности: `{stats.get('grouping', 0)}` | Надежность: `{stats.get('reliability', 0)}`\n"
                        f"• Изменение магазина: `{stats.get('max_magazine', 0)}`\n"
                        f"• Особое свойство: *{text_feat}*"
                    )
                else:  # weapon
                    stats = self.extra_data.get("base_stats", {})
                    wep_class = self.extra_data.get("weapon_class", "Пистолет")
                    skill_id = self.extra_data.get("associated_skill", "skill_handguns")
                    auto_f = "Да" if self.extra_data.get("auto_fire", "no") == "yes" else "Нет"
                    
                    spec_info = (
                        f"**[Боевые характеристики оружия]**\n"
                        f"• Класс оружия: `{wep_class}`\n"
                        f"• Автоматический огонь: `{auto_f}`\n"
                        f"• Урон: `{format_dice_array(stats.get('damage', [1, 0]))}`\n"
                        f"• Отдача: `{stats.get('recoil', 0)}` | Точность: `{stats.get('accuracy', 0)}`\n"
                        f"• Кучность: `{stats.get('grouping', 3)}` | Надежность: `{stats.get('reliability', 10)}`\n"
                        f"• Магазин: `{stats.get('max_magazine', 30)}`\n"
                        f"• Особое свойство: *{text_feat}*"
                    )
                    
            # --- 3. ВЕТКА: Комбинезоны, Шлемы, Противогазы ---
            elif self.item_type in ["armor", "head_armor", "head_mask"]:
                text_feat = self.extra_data.get("text_feature", "Отсутствует")
                
                if self.item_type == "armor":
                    pts = self.extra_data.get("armor_points", [10, 10])
                    az_val = self.extra_data.get("base_anomaly_resist", 0) # Читаем АЗ
                    daz_val = self.extra_data.get("base_anomaly_mods", 6)   # Читаем ДАЗ
                    issued_effs = self.extra_data.get("issued_effects", [])
                    effs_str = ", ".join([self.effects_lib.get(x, {}).get("name", x) for x in issued_effs if x])
                    
                    spec_info = (
                        f"**[Характеристики комбинезона]**\n"
                        f"• Класс защиты (очки): `{pts[1]} БП`\n"
                        f"• Аномальная защита (АЗ): `{az_val}`\n"
                        f"• Доступный ДАЗ (Ячейки модов): `{daz_val}`\n"
                        f"• Встроенные эффекты: `{effs_str or 'нет'}`\n"
                        f"• Особое свойство: *{text_feat}*"
                    )
                else: # head_armor, head_mask
                    b_armor = self.extra_data.get("base_armor_points", 0)
                    eff = self.extra_data.get("issued_effect", "Отсутствует")
                    readable_eff = self.effects_lib.get(eff, {}).get("name", eff) if eff else "Отсутствуют"
                    
                    resists = (
                        f"• Электрозащита: `{self.extra_data.get('electro_resist', 0)}` | Термозащита: `{self.extra_data.get('termo_resist', 0)}`\n"
                        f"• Химзащита: `{self.extra_data.get('chemical_resist', 0)}` | Рад. защита: `{self.extra_data.get('radiation_resist', 0)}`\n"
                        f"• Пси-защита: `{self.extra_data.get('psy_resist', 0)}`"
                    )
                    mask_info = f"• Совместим с маской: `{ 'Да' if self.extra_data.get('have_mask', 'no') == 'no' else 'Нет' }\n" if self.item_type == "head_armor" else ""
                    
                    spec_info = (
                        f"**[Характеристики защиты головы]**\n"
                        f"• Базовая броня: `{b_armor} ПБ`\n"
                        f"{mask_info}"
                        f"• Эффект при ношении: `{readable_eff}`\n"
                        f"**[Аномальные сопротивления]**\n{resists}"
                    )

            # --- 4. ВЕТКА: Бронеплиты, Модификаторы брони, Навесы ---
            elif self.item_type in ["armor_plate", "add_armor", "mounted_mod", "helmet_mods", "anomaly_mod"]:
                
                # ПОДВЕТКА А: Аномальные модули защиты (Костюмные обшивки)
                if self.item_type == "anomaly_mod":
                    req = self.extra_data.get("anomaly_mod_req", 1)
                    resists = self.extra_data.get("add_resist", {})
                    
                    spec_info = (
                        f"**[Параметры аномального модуля]**\n"
                        f"• Потребление ДАЗ (req): `{req}`\n\n"
                        f"**Модификаторы сопротивления:**\n"
                        f"• Мод. Электрозащиты: `{resists.get('electro_resist', 0)}`\n"
                        f"• Мод. Термозащиты: `{resists.get('termo_resist', 0)}`\n"
                        f"• Мод. Химзащиты: `{resists.get('chemical_resist', 0)}`\n"
                        f"• Мод. Радиационной защиты: `{resists.get('radiation_resist', 0)}`"
                    )

                # ПОДВЕТКА Б: Чистые элементы защиты (Плиты и Накладки конечностей)
                elif self.item_type in ["armor_plate", "add_armor"]:
                    pts = self.extra_data.get("armor_points", [0, 0])
                    eff_str = ""
                    if self.item_type == "add_armor":
                        eff = self.extra_data.get("issued_effect")
                        eff_str = f"• Эффект модуля: `{self.effects_lib.get(eff, {}).get('name', eff) if eff else 'Отсутствует'}`\n"
                    spec_info = (
                        f"**[Параметры бронеэлемента]**\n"
                        f"• Очки брони (armor_points): `{pts[1]} ПБ`\n"
                        f"{eff_str}"
                    )

                # ПОДВЕТКА В: Модификации шлемов (Без эффектов)
                elif self.item_type == "helmet_mods":
                    mods = self.extra_data.get("modificators", {})
                    spec_info = (
                        f"**[Параметры модификатора шлема]**\n"
                        f"• Мод. ПБ шлема: `{mods.get('armor_points', 0)}`\n"
                        f"• Мод. Электрозащиты: `{mods.get('electro_resist', 0)}`\n"
                        f"• Мод. Термозащиты: `{mods.get('termo_resist', 0)}`\n"
                        f"• Мод. Химзащиты: `{mods.get('chemical_resist', 0)}`\n"
                        f"• Мод. Радиационной защиты: `{mods.get('radiation_resist', 0)}`\n"
                        f"• Мод. Пси-защиты: `{mods.get('psy_resist', 0)}`"
                    )

                # ПОДВЕТКА Г: Навесные элементы костюмов (С эффектами, без пси-защиты)
                else: # mounted_mod
                    mods = self.extra_data.get("modificators", {})
                    effs = self.extra_data.get("issued_effect", [])
                    if isinstance(effs, str): effs = [effs]
                    effs_str = ", ".join([self.effects_lib.get(x, {}).get("name", x) for x in effs if x]) if effs else "Отсутствуют"
                    
                    spec_info = (
                        f"**[Параметры навесного элемента]**\n"
                        f"• Мод. ПБ основы костюма: `{mods.get('armor_points', 0)}`\n"
                        f"• Мод. ПБ конечностей: `{mods.get('limb_armor', 0)}`\n"
                        f"• Мод. Электрозащиты: `{mods.get('electro_resist', 0)}`\n"
                        f"• Мод. Термозащиты: `{mods.get('termo_resist', 0)}`\n"
                        f"• Мод. Химзащиты: `{mods.get('chemical_resist', 0)}`\n"
                        f"• Мод. Радиационной защиты: `{mods.get('radiation_resist', 0)}`\n"
                        f"• Накладываемые эффекты: `{effs_str}`"
                    )

            # --- 5. ВЕТКА: Детекторы и Электроника ---
            elif self.item_type in ["anomaly_detector", "artefact_detector", "head_eyes", "head_ears"]:
                text_feat = self.extra_data.get("text_feature", "Отсутствует")
                
                # Собираем эффекты прибора (для artefact_detector, anomaly_detector, head_ears)
                eff_str = "Отсутствуют"
                if self.item_type in ["anomaly_detector", "artefact_detector", "head_ears"]:
                    eff_data = self.extra_data.get("long_effects", {})
                    eff = eff_data.get("add") if isinstance(eff_data, dict) else None
                    if eff:
                        eff_str = self.effects_lib.get(eff, {}).get("name", eff)

                if self.item_type == "artefact_detector":
                    spec_info = (
                        f"**[Параметры электроники]**\n"
                        f"• Класс детектора: `{self.extra_data.get('class', 1)}`\n"
                        f"• Эффект при работе устройства: `{eff_str}`\n"
                        f"• Свойство работы: *{text_feat}*"
                    )
                elif self.item_type in ["anomaly_detector", "head_ears"]:
                    spec_info = (
                        f"**[Параметры электроники]**\n"
                        f"• Встроенный эффект прибора: `{eff_str}`\n"
                        f"• Свойство работы: *{text_feat}*"
                    )
                else: # head_eyes
                    spec_info = f"**[Параметры электроники]**\n• Свойство работы: *{text_feat}*"

            # --- Формирование финальной карточки ---
            readable_type = READABLE_ITEM_TYPES.get(self.item_type, self.item_type)
            if not self.item_type in ["narrative", "crafts", "instruments", "ammo", "body_part", "grenade"]:
                info = (
                    f"**Технический ID:** `{self.tech_id or 'НЕ ЗАДАН'}`\n"
                    f"**Имя:** {self.name}\n"
                    f"**Категория:** `{readable_type}`\n"
                    f"**Вес:** `{self.weight} кг` | **Цена:** `{self.base_price} RU`\n"
                    f"**Множитель закупки:** `x{self.count_multiply}`\n"
                    f"**Описание:** *{self.description}*\n\n"
                    f"**Специфичные свойства предмета:**\n{spec_info}"
                )
            else:
                info = (
                    f"**Технический ID:** `{self.tech_id or 'НЕ ЗАДАН'}`\n"
                    f"**Имя:** {self.name}\n"
                    f"**Категория:** `*{readable_type}*`\n"
                    f"**Вес:** `{self.weight} кг` | **Цена:** `{self.base_price} RU`\n"
                    f"**Множитель закупки:** `x{self.count_multiply}`\n"
                    f"**Описание:** *{self.description}*\n\n"
                )
            
            embed = disnake.Embed(title="Единая Система Управления Предметами (UIMS)", description=info, color=disnake.Color.red())
            if self.picture_url and self.picture_url.startswith(("http://", "https://")):
                embed.set_image(url=self.picture_url)
            embed.set_footer(text="© By Bon Shinomiya")

            # Рендерим кнопки Главного Экрана
            btn_tech = disnake.ui.Button(label="Задать тех ID", style=disnake.ButtonStyle.red, disabled=(self.old_tech_id is not None), row=0)
            btn_base = disnake.ui.Button(label="Базовые свойства", style=disnake.ButtonStyle.red, row=0)
            btn_pic = disnake.ui.Button(label="Картинка предмета", style=disnake.ButtonStyle.red, row=0)
            btn_tech.callback = self.btn_tech_edit_callback; btn_base.callback = self.btn_base_edit_callback; btn_pic.callback = self.btn_pic_edit_callback
            self.add_item(btn_tech); self.add_item(btn_base); self.add_item(btn_pic)

            btn_back_type = disnake.ui.Button(label="Изменить категорию", style=disnake.ButtonStyle.red, disabled=(self.old_tech_id is not None), row=1)
            btn_back_type.callback = self.btn_back_to_type_callback
            self.add_item(btn_back_type)

            # Кнопка изменения флага deletable (Активна ТОЛЬКО при создании)
            current_del = getattr(self, "deletable_status", "yes")
            del_label = "Удаляемый: Да" if current_del == "yes" else "Удаляемый: Нет"
            btn_deletable = disnake.ui.Button(label=del_label, style=disnake.ButtonStyle.red, disabled=(self.old_tech_id is not None), row=1)
            btn_deletable.callback = self.btn_toggle_deletable_callback
            self.add_item(btn_deletable)

            # Кнопка Спец. параметров
            if not self.item_type in ["narrative", "crafts", "instruments", "ammo", "body_part", "grenade"]:
                btn_spec = disnake.ui.Button(label="Настроить спец. параметры", style=disnake.ButtonStyle.red, row=1)
                
                # ИСПРАВЛЕНО: Оружие уходит в специализированное меню сборки классов и ТТХ
                if self.item_type == "weapon":
                    btn_spec.callback = self.btn_weapon_modal_callback
                else:
                    btn_spec.callback = self.btn_spec_toggle_callback
                    
                self.add_item(btn_spec)

            btn_cancel = disnake.ui.Button(label="Отмена", style=disnake.ButtonStyle.red, row=2)
            btn_save = disnake.ui.Button(label="Сохранить предмет", style=disnake.ButtonStyle.red, row=2)
            btn_cancel.callback = self.cancel_callback; btn_save.callback = self.save_callback
            self.add_item(btn_cancel); self.add_item(btn_save)

        # ЭТАП 3: Универсальный экран глубоких настроек
        elif self.current_screen == "spec":
            embed = disnake.Embed(title="UIMS: Дополнительные коэффициенты", color=disnake.Color.red())
            embed.set_footer(text="© By Bon Shinomiya")
            
            # --- СЦЕНАРИЙ 1: Расходники (Еда, Медицина, Артефакты) ---
            if self.item_type in ["medicine", "food", "artefact"]:
                effects = self.main_view_get_dict("use_effects")
                long_eff_data = self.extra_data.get("long_effects", {})
                adds = long_eff_data.get("add", []) if isinstance(long_eff_data, dict) else []
                removes = long_eff_data.get("remove", []) if isinstance(long_eff_data, dict) else []
                adds_str = ", ".join([self.effects_lib.get(x, {}).get("name", x) for x in adds if x])
                removes_str = ", ".join([self.effects_lib.get(x, {}).get("name", x) for x in removes if x])

                embed.description = (
                    f"**Настройка эффектов для:** `{self.name}`\n\n"
                    f"- Лечение ПЗ (кубы): `{format_dice_array(effects.get('add_hp', [0, 0]))}`\n"
                    f"- Восст. МЗ (кубы): `{format_dice_array(effects.get('add_mp', [0, 0]))}`\n"
                    f"- Вывод РЗ (кубы): `{format_dice_array(effects.get('add_rp', [0, 0]))}`\n"
                    f"- Накладывает эффекты: `{adds_str or 'нет'}`\n"
                    f"- Снимает эффекты: `{removes_str or 'нет'}`"
                )
                
                btn_med = disnake.ui.Button(label="Настроить кубы (ПЗ/МЗ/РЗ)", style=disnake.ButtonStyle.red, row=0)
                btn_med.callback = self.btn_med_modal_callback
                btn_long = disnake.ui.Button(label="Настроить эффекты", style=disnake.ButtonStyle.red, row=0)
                btn_long.callback = self.btn_long_effects_callback
                
                if self.item_type != "artefact": self.add_item(btn_med)
                self.add_item(btn_long)

            # --- СЦЕНАРИЙ 2: Оружие, Ножи, Оружейные моды ---
            elif self.item_type in ["weapon", "melee_weapon", "gun_modification"]:
                stats = self.main_view_get_dict("base_stats")
                text_feat = self.extra_data.get("text_feature", "Отсутствует")
                options = []
                
                if self.item_type == "melee_weapon":
                    dmg = self.extra_data.get("damage", [1, 0])
                    embed.description = f"Параметры холодного оружия:\n- Урон кубами: `{format_dice_array(dmg)}`\n- Особенность: *{text_feat}*"
                    options = [disnake.SelectOption(label="Урон оружия", value="damage"), disnake.SelectOption(label="Особенность оружия (Текст)", value="text_feature")]
                elif self.item_type == "gun_modification":
                    embed.description = (
                        f"Модификаторы обвеса для: {self.name}\n\n"
                        f"- Модификатор урона: `{format_dice_array(stats.get('damage', [0, 0]))}`\n"
                        f"- Изменение отдачи: `{stats.get('recoil', 0)}`\n"
                        f"- Изменение точности: `{stats.get('accuracy', 0)}`\n"
                        f"- Изменение кучности: `{stats.get('grouping', 0)}`\n"
                        f"- Изменение надежности: `{stats.get('reliability', 0)}`\n"
                        f"- Изменение магазина: `{stats.get('max_magazine', 0)}`\n"
                        f"- Особенность: *{text_feat}*"
                    )
                    options = [disnake.SelectOption(label="Модификатор урона", value="damage"), disnake.SelectOption(label="Изменение отдачи", value="recoil"), disnake.SelectOption(label="Изменение точности", value="accuracy"), disnake.SelectOption(label="Изменение кучности", value="grouping"), disnake.SelectOption(label="Изменение надежности", value="reliability"), disnake.SelectOption(label="Изменение магазина", value="max_magazine"), disnake.SelectOption(label="Особенность (Текст)", value="text_feature")]
                else: # weapon
                    embed.description = (
                        f"Боевые параметры оружия для: {self.name}\n\n"
                        f"- Урон кубами: `{format_dice_array(stats.get('damage', [1, 0]))}`\n"
                        f"- Отдача: `{stats.get('recoil', 0)}`\n"
                        f"- Точность: `{stats.get('accuracy', 0)}`\n"
                        f"- Кучность: `{stats.get('grouping', 3)}`\n"
                        f"- Надежность: `{stats.get('reliability', 10)}`\n"
                        f"- Вместимость магазина: `{stats.get('max_magazine', 30)}`\n"
                        f"- Особенность оружия: *{text_feat}*"
                    )
                    options = [disnake.SelectOption(label="Урон оружия", value="damage"), disnake.SelectOption(label="Отдача", value="recoil"), disnake.SelectOption(label="Точность", value="accuracy"), disnake.SelectOption(label="Кучность", value="grouping"), disnake.SelectOption(label="Надежность", value="reliability"), disnake.SelectOption(label="Вместимость магазина", value="max_magazine"), disnake.SelectOption(label="Особенность (Текст)", value="text_feature")]

                select = disnake.ui.Select(placeholder="Выберите параметр оружия...", options=options, custom_id="wep_stat_select", row=0)
                select.callback = self.select_callback
                self.add_item(select)
                
                btn_set = disnake.ui.Button(label="Изменить параметр", style=disnake.ButtonStyle.red, row=1)
                btn_set.callback = self.btn_set_callback
                self.add_item(btn_set)

            # --- СЦЕНАРИЙ 3: Комбинезоны, Шлемы, Противогазы ---
            elif self.item_type in ["armor", "head_armor", "head_mask"]:
                text_feat = self.extra_data.get("text_feature", "Отсутствует")
                options = []
                
                if self.item_type == "armor":
                    pts = self.extra_data.get("armor_points", [10, 10])
                    az_val = self.extra_data.get("base_anomaly_resist", 0)
                    daz_val = self.extra_data.get("base_anomaly_mods", 6)
                    issued_effs = self.extra_data.get("issued_effects", [])
                    effs_str = ", ".join([self.effects_lib.get(x, {}).get("name", x) for x in issued_effs if x])
                    
                    embed.description = (
                        f"Параметры комбинезона для: {self.name}\n\n"
                        f"- Очки брони (armor_points): `{pts[0]}/{pts[1]}`\n"
                        f"- Аномальная защита (АЗ): `{az_val}`\n"
                        f"- Доступный ДАЗ (Ячейки модов): `{daz_val}`\n"
                        f"- Встроенные эффекты: `{effs_str or 'нет'}`\n"
                        f"- Особенность костюма (text_feature): *{text_feat}*"
                    )
                    # Добавляем "base_anomaly_resist" в опции селектора
                    options = [
                        disnake.SelectOption(label="Очки брони (Максимум)", value="armor_points"), 
                        disnake.SelectOption(label="Аномальная защита (АЗ костюма)", value="base_anomaly_resist"), 
                        disnake.SelectOption(label="Доступный ДАЗ (Ячейки модов)", value="base_anomaly_mods"), 
                        disnake.SelectOption(label="Особенность костюма (Текст)", value="text_feature")
                    ]
                else: # head_armor, head_mask
                    b_armor = self.extra_data.get("base_armor_points", 0)
                    eff = self.extra_data.get("issued_effect", "Отсутствует")
                    readable_eff = self.effects_lib.get(eff, {}).get("name", eff) if eff else "Отсутствуют"
                    
                    # Получаем статус маски для шлема
                    mask_status = "Запрещена" if self.extra_data.get("have_mask", "no") == "yes" else "Разрешена"
                    mask_str = f"- Совместимость с маской: `{mask_status}`\n" if self.item_type == "head_armor" else ""
                    
                    embed.description = (
                        f"Защита головы для: {self.name}\n\n"
                        f"- Базовая броня: `{b_armor} ПБ`\n"
                        f"{mask_str}"
                        f"- Электрозащита: `{self.extra_data.get('electro_resist', 0)}`\n"
                        f"- Термозащита: `{self.extra_data.get('termo_resist', 0)}`\n"
                        f"- Химзащита: `{self.extra_data.get('chemical_resist', 0)}`\n"
                        f"- Радиационная защита: `{self.extra_data.get('radiation_resist', 0)}`\n"
                        f"- Пси-защита: `{self.extra_data.get('psy_resist', 0)}`\n"
                        f"- Эффект ношения: `{readable_eff}`"
                    )
                    options = [
                        disnake.SelectOption(label="Базовая броня", value="base_armor_points"),
                        disnake.SelectOption(label="Электрозащита", value="electro_resist"),
                        disnake.SelectOption(label="Термозащита", value="termo_resist"),
                        disnake.SelectOption(label="Химзащита", value="chemical_resist"),
                        disnake.SelectOption(label="Радиационная защита", value="radiation_resist"),
                        disnake.SelectOption(label="Пси-защита", value="psy_resist")
                    ]

                select = disnake.ui.Select(placeholder="Выберите параметр брони...", options=options, custom_id="armor_stat_select", row=0)
                select.callback = self.select_callback
                self.add_item(select)
                
                btn_set = disnake.ui.Button(label="Изменить параметр", style=disnake.ButtonStyle.red, row=1)
                btn_set.callback = self.btn_set_callback
                self.add_item(btn_set)
                
                # Фикс кнопки toggler для have_mask (только для шлемов)
                if self.item_type == "head_armor":
                    current_mask = self.extra_data.get("have_mask", "no")
                    mask_label = "Блокировать маску: Да" if current_mask == "yes" else "Блокировать маску: Нет"
                    btn_mask_toggle = disnake.ui.Button(label=mask_label, style=disnake.ButtonStyle.red, row=1)
                    btn_mask_toggle.callback = self.btn_toggle_mask_callback
                    self.add_item(btn_mask_toggle)

                btn_long = disnake.ui.Button(label="Настроить эффекты ношения", style=disnake.ButtonStyle.red, row=1)
                btn_long.callback = self.btn_long_effects_callback
                self.add_item(btn_long)

            # --- СЦЕНАРИЙ 4: Плиты, Модули конечностей, Аномальные моды и Модификации шлемов ---
            elif self.item_type in ["armor_plate", "add_armor", "mounted_mod", "helmet_mods", "anomaly_mod"]:
                options = []
                
                # Подсценарий А: Чистые бронеэлементы (Плиты и Конечности)
                if self.item_type in ["armor_plate", "add_armor"]:
                    pts = self.extra_data.get("armor_points", [0, 0])
                    embed.description = f"Бронеэлемент:\n- Очки брони (armor_points): `{pts[1]}`"
                    options.append(disnake.SelectOption(label="Очки брони", value="armor_points"))
                
                # Подсценарий Б: Аномальные модификаторы брони (БЕЗ ПСИ-ЗАЩИТЫ)
                elif self.item_type == "anomaly_mod":
                    resists = self.extra_data.get("add_resist", {})
                    embed.description = (
                        f"**Аномальный элемент защиты костюма:**\n"
                        f"- Потребление ДАЗ: `{self.extra_data.get('anomaly_mod_req', 1)}`\n\n"
                        f"**Модификаторы сопротивления:**\n"
                        f"- Мод. Электрозащиты: `{resists.get('electro_resist', 0)}`\n"
                        f"- Мод. Термозащиты: `{resists.get('termo_resist', 0)}`\n"
                        f"- Мод. Химзащиты: `{resists.get('chemical_resist', 0)}`\n"
                        f"- Мод. Радиационной защиты: `{resists.get('radiation_resist', 0)}`"
                    )
                    options.append(disnake.SelectOption(label="Потребление ДАЗ", value="anomaly_mod_req"))
                
                # Подсценарий В: Модификации шлемов (Единственные, у кого ЕСТЬ пси-защита)
                elif self.item_type == "helmet_mods":
                    resists = self.extra_data.get("modificators", {})
                    embed.description = (
                        f"**Модификация шлема:**\n\n"
                        f"**Модификаторы характеристик шлема:**\n"
                        f"- Мод. ПБ шлема: `{resists.get('armor_points', 0)}`\n"
                        f"- Мод. Электрозащиты: `{resists.get('electro_resist', 0)}`\n"
                        f"- Мод. Термозащиты: `{resists.get('termo_resist', 0)}`\n"
                        f"- Мод. Химзащиты: `{resists.get('chemical_resist', 0)}`\n"
                        f"- Мод. Радиационной защиты: `{resists.get('radiation_resist', 0)}`\n"
                        f"- Мод. Пси-защиты: `{resists.get('psy_resist', 0)}`"
                    )
                    options.append(disnake.SelectOption(label="Мод. ПБ шлема", value="armor_points"))

                # Подсценарий Г: Навесные элементы костюмов (БЕЗ ПСИ-ЗАЩИТЫ)
                else: # mounted_mod
                    resists = self.extra_data.get("modificators", {})
                    issued_effs = self.extra_data.get("issued_effect", [])
                    if isinstance(issued_effs, str): issued_effs = [issued_effs]
                    effs_str = ", ".join([self.effects_lib.get(x, {}).get("name", x) for x in issued_effs if x])
                    
                    embed.description = (
                        f"**Навесной элемент брони:**\n"
                        f"- Накладываемые эффекты: `{effs_str or 'нет'}`\n\n"
                        f"**Модификаторы характеристик брони:**\n"
                        f"- Мод. ПБ основы костюма: `{resists.get('armor_points', 0)}`\n"
                        f"- Мод. ПБ конечностей: `{resists.get('limb_armor', 0)}`\n"
                        f"- Мод. Электрозащиты: `{resists.get('electro_resist', 0)}`\n"
                        f"- Мод. Термозащиты: `{resists.get('termo_resist', 0)}`\n"
                        f"- Мод. Химзащиты: `{resists.get('chemical_resist', 0)}`\n"
                        f"- Мод. Радиационной защиты: `{resists.get('radiation_resist', 0)}`"
                    )
                    options.extend([
                        disnake.SelectOption(label="Модификатор ПБ основы", value="armor_points"),
                        disnake.SelectOption(label="Модификатор ПБ конечностей", value="limb_armor")
                    ])

                # Динамически заполняем селектор аномальными опциями
                if self.item_type in ["anomaly_mod", "mounted_mod", "helmet_mods"]:
                    options.extend([
                        disnake.SelectOption(label="Мод. Электрозащиты", value="mod_electro"),
                        disnake.SelectOption(label="Мод. Термозащиты", value="mod_termo"),
                        disnake.SelectOption(label="Мод. Химзащиты", value="mod_chemical"),
                        disnake.SelectOption(label="Мод. Радиац. защиты", value="mod_radiation")
                    ])
                    # Добавляем опцию Пси-защиты СТРОГО только для модификаций шлемов!
                    if self.item_type == "helmet_mods":
                        options.append(disnake.SelectOption(label="Мод. Пси-защиты", value="mod_psy"))

                if options:
                    select = disnake.ui.Select(placeholder="Выберите параметр модификатора...", options=options, custom_id="mod_stat_select", row=0)
                    select.callback = self.select_callback
                    self.add_item(select)
                    btn_set = disnake.ui.Button(label="Изменить параметр", style=disnake.ButtonStyle.red, custom_id="mod_btn_set", row=1)
                    btn_set.callback = self.btn_set_callback
                    self.add_item(btn_set)
                
                if self.item_type in ["add_armor", "mounted_mod"]:
                    btn_long = disnake.ui.Button(label="Настроить эффекты модуля", style=disnake.ButtonStyle.red, row=1)
                    btn_long.callback = self.btn_long_effects_callback
                    self.add_item(btn_long)

            # --- СЦЕНАРИЙ 5: Детекторы и Электроника ---
            elif self.item_type in ["anomaly_detector", "artefact_detector", "head_eyes", "head_ears"]:
                embed.description = f"**Электронное устройство для экипировки:**\n"
                
                # По дефолту у всех приборов есть текстовая особенность
                options = [disnake.SelectOption(label="Особенность работы (Текст)", value="text_feature")]
                
                if self.item_type == "artefact_detector":
                    embed.description += f"- Класс прибора (class): `{self.extra_data.get('class', 1)}`"
                    options.append(disnake.SelectOption(label="Класс детектора", value="class"))
                else:
                    embed.description += f"- Служебный электронный модуль."
                
                if self.item_type in ["anomaly_detector", "artefact_detector", "head_ears"]:
                    long_eff_data = self.extra_data.get("long_effects", {})
                    adds = long_eff_data.get("add", []) if isinstance(long_eff_data, dict) else []
                    if isinstance(adds, str): adds = [adds]
                    adds_str = ", ".join([self.effects_lib.get(x, {}).get("name", x) for x in adds if x])
                    embed.description += f"\n- Эффекты при работе устройства: `{adds_str or 'нет'}`"

                # Рендерим селектор (он теперь никогда не будет пустым!)
                select = disnake.ui.Select(placeholder="Выберите параметр...", options=options, custom_id="elec_stat_select", row=0)
                select.callback = self.select_callback
                self.add_item(select)
                
                btn_set = disnake.ui.Button(label="Изменить параметр", style=disnake.ButtonStyle.red, row=1)
                btn_set.callback = self.btn_set_callback
                self.add_item(btn_set)
                
                if self.item_type in ["anomaly_detector", "artefact_detector", "head_ears"]:
                    btn_long = disnake.ui.Button(label="Настроить эффекты прибора", style=disnake.ButtonStyle.red, row=1)
                    btn_long.callback = self.btn_long_effects_callback
                    self.add_item(btn_long)
        
        # Системная кнопка выхода в главное меню — ВСЕГДА В КОНЦЕ ЭКРАНА SPEC
            btn_back = disnake.ui.Button(label="Вернуться в главное меню", style=disnake.ButtonStyle.red, row=2)
            btn_back.callback = self.btn_back_to_main_callback
            self.add_item(btn_back)
        
        # Выполняем чистое переписывание сообщения на месте
        if inter.response.is_done():
            await inter.edit_original_response(embed=embed, view=self)
        else:
            try: await inter.response.edit_message(embed=embed, view=self)
            except: await inter.edit_original_response(embed=embed, view=self)

    def main_view_get_dict(self, key: str) -> dict:
        if key not in self.extra_data or not isinstance(self.extra_data[key], dict):
            self.extra_data[key] = {}
        return self.extra_data[key]

    # ========================================== КОЛБЭКИ ИНТЕРАКЦИЙ ==========================================

    async def select_type_callback(self, inter: disnake.MessageInteraction):
        self.extra_data = {} 
        self.picture_url = None
        self.selected_stat = None
        
        self.item_type = inter.values[0]
        self.type_selected = True
        
        # ИСПРАВЛЕНО: Теперь бронеплиты и защита конечностей ЖЕСТКО определяются как НЕСТАКАЕМЫЕ предмета
        non_stackable_types = [
            "weapon", "melee_weapon", "armor", "head_armor", "head_mask", 
            "anomaly_detector", "artefact_detector", "head_eyes", "head_ears",
            "armor_plate", "add_armor"
        ]
        
        if self.item_type in non_stackable_types:
            self.stackable = "no"
        else:
            self.stackable = "yes"
            
        await self.send_main_window(inter)

    async def btn_toggle_deletable_callback(self, inter: disnake.MessageInteraction):
        """Переключает флаг возможности удаления предмета из базы данных (yes/no)"""
        # Если переменная еще не создана, берем дефолтное "yes"
        current_status = getattr(self, "deletable_status", "yes")
        # Переключаем состояние
        self.deletable_status = "no" if current_status == "yes" else "yes"
        
        # Обновляем окно, чтобы перерисовать название кнопки
        await self.send_main_window(inter)   
   
    async def btn_back_to_type_callback(self, inter: disnake.MessageInteraction):
        self.type_selected = False
        await self.send_main_window(inter)

    async def btn_spec_toggle_callback(self, inter: disnake.MessageInteraction):
        self.current_screen = "spec"
        await self.send_main_window(inter)

    async def btn_back_to_main_callback(self, inter: disnake.MessageInteraction):
        self.current_screen = "main"  # Возвращаемся
        await self.send_main_window(inter)

    async def btn_tech_edit_callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_modal(ItemTechIdModal(self))

    async def btn_base_edit_callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_modal(ItemBaseSettingsModal(self))

    async def btn_pic_edit_callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_modal(ItemPictureModal(self))

    async def btn_med_modal_callback(self, inter: disnake.MessageInteraction):
        sub_menu = ItemEffectsManagementMenu(self)
        await sub_menu.send_menu(inter)

    async def btn_long_effects_callback(self, inter: disnake.MessageInteraction):
        lib = await load_effects_library()
        sub_menu = ItemLongEffectsManagementMenu(self, lib)
        await sub_menu.send_menu(inter)

    async def btn_weapon_modal_callback(self, inter: disnake.MessageInteraction):
        sub_menu = ItemWeaponManagementMenu(self)
        await sub_menu.send_menu(inter)

    async def btn_armor_modal_callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_modal(ArmorStatsModal(self))

    async def select_callback(self, inter: disnake.MessageInteraction):
        """Коллбэк селектора параметров оружия: фиксирует выбранный параметр в памяти сессии"""
        self.selected_stat = inter.values[0]
        # Используем дефер, чтобы зафиксировать выбор без пересоздания сообщения
        await inter.response.defer()

    async def btn_set_callback(self, inter: disnake.MessageInteraction):
        if not hasattr(self, "selected_stat") or not self.selected_stat:
            return await inter.response.send_message("Сначала выберите параметр в списке!", ephemeral=True)
            
        # Распределяем параметры оружия в Weapon-модалку
        if self.selected_stat in ["damage", "recoil", "accuracy", "grouping", "reliability", "max_magazine"]:
            await inter.response.send_modal(WeaponSingleInputModal(self))
            
        # ИСПРАВЛЕНО: Добавлены АЗ (base_anomaly_resist) и ДАЗ (base_anomaly_mods)
        elif self.selected_stat in [
            "armor_points", "limb_armor", "base_anomaly_mods", "base_anomaly_resist", "base_armor_points", 
            "psy_resist", "radiation_resist", "electro_resist", "termo_resist", "chemical_resist",
            "anomaly_mod_req", "class", "mod_electro", "mod_termo", "mod_chemical", "mod_radiation", "mod_psy"
        ]:
            await inter.response.send_modal(ArmorSingleInputModal(self))
            
        # Универсальные текстовые поля
        elif self.selected_stat == "text_feature":
            if self.item_type in ["weapon", "melee_weapon", "gun_modification"]:
                await inter.response.send_modal(WeaponSingleInputModal(self))
            else:
                await inter.response.send_modal(ArmorSingleInputModal(self))

    async def cancel_callback(self, inter: disnake.MessageInteraction):
        self.stop()
        await inter.response.edit_message(content="**Управление предметом отменено.**", embed=None, view=None)

    async def save_callback(self, inter: disnake.MessageInteraction):
        if not self.tech_id:
            return await inter.response.send_message("❌ Ошибка! Не задан технический ID предмета.", ephemeral=True)
        library = await load_items_library()
        if not self.old_tech_id and self.tech_id in library:
            return await inter.response.send_message("❌ Предмет с таким техническим ID уже существует!", ephemeral=True)
        library[self.tech_id] = self.construct_item_json()
        await save_items_library(library)
        self.stop()
        await inter.response.edit_message(content=f"✅ Предмет **{self.name}** (`{self.tech_id}`) сохранен!", embed=None, view=None)

    async def btn_toggle_mask_callback(self, inter: disnake.MessageInteraction):
        """Переключает флаг блокировки совместного ношения шлема с противогазом (yes/no)"""
        current_mask = self.extra_data.get("have_mask", "no")
        self.extra_data["have_mask"] = "no" if current_mask == "yes" else "yes"
        await self.send_main_window(inter)

# ========================================== МОДАЛЬНЫЕ ОКНА СИСТЕМЫ ==========================================

class ItemTechIdModal(disnake.ui.Modal):
    def __init__(self, prev_view: UnitedItemsManagementSystem):
        self.prev_view = prev_view
        super().__init__(title="Ввод Технического ID", components=[
            disnake.ui.TextInput(label="Технический ID (a-z, 0-9, _)", placeholder="Пример: medkit_military", value=prev_view.tech_id or "", custom_id="id")
        ])
    async def callback(self, inter: disnake.ModalInteraction):
        tech_id_raw = inter.text_values["id"].strip().lower()
        if not is_valid_tech_id(tech_id_raw):
            return await inter.response.send_message("❌ Недопустимые символы. Только английские строчные буквы, цифры и подчёркивание.", ephemeral=True)
        self.prev_view.tech_id = tech_id_raw
        await self.prev_view.send_main_window(inter)


class ItemPictureModal(disnake.ui.Modal):
    def __init__(self, prev_view: UnitedItemsManagementSystem):
        self.prev_view = prev_view
        super().__init__(title="Ссылка на изображение", components=[
            disnake.ui.TextInput(label="URL картинки", placeholder="https://...", value=prev_view.picture_url or "", custom_id="url", required=False)
        ])
    async def callback(self, inter: disnake.ModalInteraction):
        self.prev_view.picture_url = inter.text_values["url"].strip() or None
        await self.prev_view.send_main_window(inter)


class ItemBaseSettingsModal(disnake.ui.Modal):
    def __init__(self, prev_view: UnitedItemsManagementSystem):
        self.prev_view = prev_view
        super().__init__(title="Базовые параметры", components=[
            disnake.ui.TextInput(label="Отображаемое имя предмета", value=prev_view.name, custom_id="name"),
            disnake.ui.TextInput(label="Базовая стоимость (RU)", value=str(prev_view.base_price), custom_id="price"),
            disnake.ui.TextInput(label="Вес предмета в кг", value=str(prev_view.weight), custom_id="weight"),
            disnake.ui.TextInput(label="Множитель закупки", value=str(prev_view.count_multiply), custom_id="mult"),
            disnake.ui.TextInput(label="Текстовое описание", value=prev_view.description, custom_id="desc", style=disnake.TextInputStyle.paragraph, max_length=2000)
        ])
    async def callback(self, inter: disnake.ModalInteraction):
        try:
            self.prev_view.base_price = max(0, int(inter.text_values["price"].strip()))
            self.prev_view.weight = round(max(0.0, float(inter.text_values["weight"].strip().replace(",", "."))), 3)
            self.prev_view.count_multiply = max(1, int(inter.text_values["mult"].strip()))
        except ValueError:
            return await inter.response.send_message("❌ Ошибка в формате числовых полей.", ephemeral=True)
        self.prev_view.name = inter.text_values["name"].strip()
        self.prev_view.description = inter.text_values["desc"].strip()
        await self.prev_view.send_main_window(inter)


class MedicineEffectsModal(disnake.ui.Modal):
    def __init__(self, prev_view: UnitedItemsManagementSystem):
        self.prev_view = prev_view
        eff = prev_view.main_view_get_dict("use_effects")
        super().__init__(title="Кубы восстановления (ПЗ/МЗ/РЗ)", components=[
            disnake.ui.TextInput(label="Лечение ПЗ (Пример: 1d6+5 или 0d6+20)", value=format_dice_array(eff.get("add_hp", [0, 0])), custom_id="hp"),
            disnake.ui.TextInput(label="Восстановление МЗ (Пример: 2d6-2)", value=format_dice_array(eff.get("add_mp", [0, 0])), custom_id="mp"),
            disnake.ui.TextInput(label="Вывод РЗ (Пример: -1d6+0 или 0d6-30)", value=format_dice_array(eff.get("add_rp", [0, 0])), custom_id="rp")
        ])
    async def callback(self, inter: disnake.ModalInteraction):
        # Сохраняем кубы во все три параметра (Пункт #3)
        self.prev_view.extra_data["use_effects"] = {
            "add_hp": parse_dice_string(inter.text_values["hp"]),
            "add_mp": parse_dice_string(inter.text_values["mp"]),
            "add_rp": parse_dice_string(inter.text_values["rp"])
        }
        await self.prev_view.send_main_window(inter)

class ArmorStatsModal(disnake.ui.Modal):
    def __init__(self, prev_view: UnitedItemsManagementSystem):
        self.prev_view = prev_view
        ex = prev_view.extra_data
        super().__init__(title="Конфигурация костюмов и элементов", components=[
            disnake.ui.TextInput(label="Аномальная защита костюма (АЗ)", value=str(ex.get("base_anomaly_resist", 0)), custom_id="az", required=False),
            disnake.ui.TextInput(label="Доступный ДАЗ (Ячейки модов)", value=str(ex.get("base_anomaly_mods", 6)), custom_id="daz", required=False),
            disnake.ui.TextInput(label="Поинты брони (Пример для плит: 10 10)", value=f"{ex.get('armor_points', [10, 10])[0]} {ex.get('armor_points', [10, 10])[1]}", custom_id="pts", required=False),
            disnake.ui.TextInput(label="Текстовая фича / Модификатор текста", value=ex.get("text_feature", ""), custom_id="feat", required=False, style=disnake.TextInputStyle.paragraph)
        ])
    async def callback(self, inter: disnake.ModalInteraction):
        try:
            if inter.text_values["az"].strip():
                self.prev_view.extra_data["base_anomaly_resist"] = int(inter.text_values["az"].strip())
            
            if inter.text_values["daz"].strip():
                self.prev_view.extra_data["base_anomaly_mods"] = int(inter.text_values["daz"].strip())
            
            if inter.text_values["pts"].strip():
                pts_parts = inter.text_values["pts"].strip().split()
                p1 = int(pts_parts[0]) if len(pts_parts) > 0 else 10
                p2 = int(pts_parts[1]) if len(pts_parts) > 1 else 10
                self.prev_view.extra_data["armor_points"] = [p1, p2]
                
            self.prev_view.extra_data["text_feature"] = inter.text_values["feat"].strip()
        except ValueError:
            return await inter.response.send_message("❌ Ошибка ввода числовых параметров брони.", ephemeral=True)
        await self.prev_view.send_main_window(inter)

class ItemEffectsManagementMenu(disnake.ui.View):
    """Отдельное подменю для пошагового редактирования use_effects по аналогии с UTEMS"""
    def __init__(self, main_view):
        super().__init__(timeout=600)
        self.main_view = main_view
        self.selected_stat = None  # Какой параметр меняем: add_hp, add_mp, add_rp

    async def send_menu(self, inter: disnake.Interaction):
        self.clear_items()
        eff = self.main_view.extra_data.get("use_effects", {})
        
        info = (
            f"**Редактирование эффектов применения для:** `{self.main_view.name}`\n\n"
            f"Восстановление ПЗ (`add_hp`): `{format_dice_array(eff.get('add_hp', [0, 0]))}`\n"
            f"Восстановление МЗ (`add_mp`): `{format_dice_array(eff.get('add_mp', [0, 0]))}`\n"
            f"Вывод радиации РЗ (`add_rp`): `{format_dice_array(eff.get('add_rp', [0, 0]))}`\n"
        )
        embed = disnake.Embed(title="⚙️ Настройка кубов (use_effects)", description=info, color=disnake.Color.red())
        
        # Селектор выбора параметра для изменения/удаления
        options = [
            disnake.SelectOption(label="Показатель ПЗ (Здоровье)", value="add_hp"),
            disnake.SelectOption(label="Показатель МЗ (Психика)", value="add_mp"),
            disnake.SelectOption(label="Показатель РЗ (Радиация)", value="add_rp")
        ]
        select = disnake.ui.Select(placeholder="Выберите показатель для настройки...", options=options, custom_id="med_stat_select")
        select.callback = self.select_callback
        self.add_item(select)
        
        # Кнопки управления выбранным параметром
        btn_set = disnake.ui.Button(label="Задать / Изменить формулу", style=disnake.ButtonStyle.red, row=1)
        btn_del = disnake.ui.Button(label="Сбросить в 0d6+0", style=disnake.ButtonStyle.red, row=1)
        btn_back = disnake.ui.Button(label="🔙 Назад", style=disnake.ButtonStyle.red, row=1)
        
        btn_set.callback = self.btn_set_callback
        btn_del.callback = self.btn_del_callback
        btn_back.callback = self.btn_back_callback
        
        self.add_item(btn_set); self.add_item(btn_del); self.add_item(btn_back)
        
        await inter.response.edit_message(embed=embed, view=self)

    async def select_callback(self, inter: disnake.MessageInteraction):
        self.selected_stat = inter.values[0]
        # Отвечаем дефером, чтобы зафиксировать выбор в памяти бота
        await inter.response.defer()

    async def btn_set_callback(self, inter: disnake.MessageInteraction):
        if not self.selected_stat:
            return await inter.response.send_message("❌ Сначала выберите изменяемый показатель в списке!", ephemeral=True)
        await inter.response.send_modal(DiceInputModal(self))

    async def btn_del_callback(self, inter: disnake.MessageInteraction):
        if not self.selected_stat:
            return await inter.response.send_message("❌ Сначала выберите показатель в списке!", ephemeral=True)
            
        if "use_effects" not in self.main_view.extra_data:
            self.main_view.extra_data["use_effects"] = {}
            
        self.main_view.extra_data["use_effects"][self.selected_stat] = [0, 0]
        await self.send_menu(inter)

    async def btn_back_callback(self, inter: disnake.MessageInteraction):
        # Возвращаем ГМа на экран спец. параметров
        self.main_view.current_screen = "spec"
        await self.main_view.send_main_window(inter)


class DiceInputModal(disnake.ui.Modal):
    def __init__(self, menu_view: ItemEffectsManagementMenu):
        self.menu_view = menu_view
        super().__init__(title="Ввод формулы кубов", components=[
            disnake.ui.TextInput(
                label="Введите значение (Пример: 2d6+4 или -1d6+0)", 
                placeholder="Формат: Xd6+Y или жесткое число Y", 
                custom_id="dice_val"
            )
        ])
        
    async def callback(self, inter: disnake.ModalInteraction):
        raw_val = inter.text_values["dice_val"].strip()
        parsed_arr = parse_dice_string(raw_val)
        
        if "use_effects" not in self.menu_view.main_view.extra_data:
            self.menu_view.main_view.extra_data["use_effects"] = {}
            
        self.menu_view.main_view.extra_data["use_effects"][self.menu_view.selected_stat] = parsed_arr
        await self.menu_view.send_menu(inter)

async def load_effects_library() -> dict:
    """Подгружает базу эффектов UTEMS из твоего файла эффектов"""
    if not os.path.exists("chars_data/effects_lib.json"):
        return {}
    async with aiofiles.open("chars_data/effects_lib.json", "r", encoding="utf-8") as f:
        try: return json.loads(await f.read())
        except: return {}

class ItemLongEffectsManagementMenu(disnake.ui.View):
    def __init__(self, main_view, effects_lib: dict):
        super().__init__(timeout=600)
        self.main_view = main_view
        self.effects_lib = effects_lib
        
        self.current_page = 0
        self.items_per_page = 20
        self.filter_type = "positive"
        self.selected_effect_tech = None

        # Определяем контекст предмета
        if self.main_view.item_type in ["armor", "head_armor", "head_mask"]:
            self.is_equipment = True
            self.target_key = "issued_effects"
            self.sub_key = None
        else:
            self.is_equipment = False
            self.target_key = "long_effects"
            self.sub_key = "add"  # По умолчанию настраиваем накладываемые эффекты

    def get_filtered_effects(self) -> list:
        filtered = []
        for tech_id, data in self.effects_lib.items():
            eff_type = data.get("type", "positive")
            if eff_type == self.filter_type:
                filtered.append((tech_id, data.get("name", tech_id)))
        return sorted(filtered, key=lambda x: x[1])

    async def send_menu(self, inter: disnake.Interaction):
        self.clear_items()
        
        if self.is_equipment:
            # Снаряжение (Вывод экипируемых эффектов с конвертацией в имена)
            current_effs = self.main_view.extra_data.get(self.target_key, [])
            readable = [f"• {self.effects_lib.get(x, {}).get('name', x)}" for x in current_effs]
            label_context = f"**[Текущие встроенные эффекты]**\n" + (chr(10).join(readable) if readable else "Отсутствуют")
        else:
            # Расходники (Вывод списков без технической инфы add/remove, только имена)
            if self.target_key not in self.main_view.extra_data or not isinstance(self.main_view.extra_data[self.target_key], dict):
                self.main_view.extra_data[self.target_key] = {"add": [], "remove": []}
                
            eff_data = self.main_view.extra_data[self.target_key]
            
            adds = [f"• {self.effects_lib.get(x, {}).get('name', x)}" for x in eff_data.get("add", [])]
            removes = [f"• {self.effects_lib.get(x, {}).get('name', x)}" for x in eff_data.get("remove", [])]
            
            label_context = (
                f"**[Накладываемые эффекты]**\n{chr(10).join(adds) if adds else 'Отсутствуют'}\n\n"
                f"**[Снимаемые эффекты]**\n{chr(10).join(removes) if removes else 'Отсутствуют'}"
            )
            
        all_filtered = self.get_filtered_effects()
        max_pages = max(1, (len(all_filtered) - 1) // self.items_per_page + 1)
        
        if self.current_page >= max_pages:
            self.current_page = max_pages - 1
            
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_effects = all_filtered[start_idx:end_idx]

        info = (
            f"Управление эффектами UTEMS\n"
            f"Предмет: {self.main_view.name}\n\n"
            f"{label_context}\n\n"
            f"Фильтр списка: {'Положительные' if self.filter_type == 'positive' else 'Отрицательные'}\n"
            f"Страница: {self.current_page + 1} из {max_pages}"
        )
        
        if not self.is_equipment:
            info += f"\nТекущая операция: { 'Наложение эффекта' if self.sub_key == 'add' else 'Снятие эффекта' }"

        embed = disnake.Embed(title="UIMS: Привязка статусов UTEMS", description=info, color=disnake.Color.red())

        # Ряд 0: Выпадающий список
        options = []
        for tech_id, name in page_effects:
            options.append(disnake.SelectOption(label=name, value=tech_id, default=(tech_id == self.selected_effect_tech)))
            
        if options:
            select = disnake.ui.Select(placeholder="Выберите статус из списка...", options=options, custom_id="long_eff_select", row=0)
            select.callback = self.select_callback
            self.add_item(select)
        else:
            select = disnake.ui.Select(placeholder="В данной категории нет эффектов", options=[disnake.SelectOption(label="Пусто", value="none")], disabled=True, row=0)
            self.add_item(select)

        # Ряд 1: Переключатели и управление пагинацией
        btn_toggle_filter = disnake.ui.Button(label=f"Тип: {'Положительные' if self.filter_type == 'positive' else 'Отрицательные'}", style=disnake.ButtonStyle.red, row=1)
        btn_prev = disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.red, disabled=(self.current_page == 0), row=1)
        btn_next = disnake.ui.Button(label="Вперед", style=disnake.ButtonStyle.red, disabled=(self.current_page >= max_pages - 1), row=1)
        
        btn_toggle_filter.callback = self.btn_toggle_filter_callback
        btn_prev.callback = self.btn_prev_callback
        btn_next.callback = self.btn_next_callback
        self.add_item(btn_toggle_filter); self.add_item(btn_prev); self.add_item(btn_next)

        if not self.is_equipment:
            btn_mode = disnake.ui.Button(label=f"Режим: {'Наложение' if self.sub_key == 'add' else 'Снятие'}", style=disnake.ButtonStyle.red, row=1)
            btn_mode.callback = self.btn_mode_callback
            self.add_item(btn_mode)

        # Ряд 2: Системные действия
        btn_add = disnake.ui.Button(label="Привязать к предмету", style=disnake.ButtonStyle.red, row=2)
        btn_del = disnake.ui.Button(label="Убрать с предмета", style=disnake.ButtonStyle.red, row=2)
        btn_back = disnake.ui.Button(label="Вернуться в меню настроек", style=disnake.ButtonStyle.red, row=2)
        
        btn_add.callback = self.btn_add_callback
        btn_del.callback = self.btn_del_callback
        btn_back.callback = self.btn_back_callback
        self.add_item(btn_add); self.add_item(btn_del); self.add_item(btn_back)
        
        await inter.response.edit_message(embed=embed, view=self)

    async def select_callback(self, inter: disnake.MessageInteraction):
        self.selected_effect_tech = inter.values[0]
        await inter.response.defer()

    async def btn_toggle_filter_callback(self, inter: disnake.MessageInteraction):
        self.filter_type = "negative" if self.filter_type == "positive" else "positive"
        self.current_page = 0
        self.selected_effect_tech = None
        await self.send_menu(inter)

    async def btn_mode_callback(self, inter: disnake.MessageInteraction):
        self.sub_key = "remove" if self.sub_key == "add" else "add"
        self.selected_effect_tech = None
        await self.send_menu(inter)

    async def btn_prev_callback(self, inter: disnake.MessageInteraction):
        if self.current_page > 0:
            self.current_page -= 1
            self.selected_effect_tech = None
        await self.send_menu(inter)

    async def btn_next_callback(self, inter: disnake.MessageInteraction):
        all_filtered = self.get_filtered_effects()
        max_pages = max(1, (len(all_filtered) - 1) // self.items_per_page + 1)
        if self.current_page < max_pages - 1:
            self.current_page += 1
            self.selected_effect_tech = None
        await self.send_menu(inter)

    async def btn_add_callback(self, inter: disnake.MessageInteraction):
        if not self.selected_effect_tech or self.selected_effect_tech == "none":
            return await inter.response.send_message("Сначала выберите статус в списке!", ephemeral=True)
            
        if self.is_equipment:
            if self.target_key not in self.main_view.extra_data:
                self.main_view.extra_data[self.target_key] = []
            if self.selected_effect_tech not in self.main_view.extra_data[self.target_key]:
                self.main_view.extra_data[self.target_key].append(self.selected_effect_tech)
        else:
            if self.target_key not in self.main_view.extra_data:
                self.main_view.extra_data[self.target_key] = {"add": [], "remove": []}
            if self.selected_effect_tech not in self.main_view.extra_data[self.target_key][self.sub_key]:
                self.main_view.extra_data[self.target_key][self.sub_key].append(self.selected_effect_tech)
                
        await self.send_menu(inter)

    async def btn_del_callback(self, inter: disnake.MessageInteraction):
        if not self.selected_effect_tech or self.selected_effect_tech == "none":
            return await inter.response.send_message("Сначала выберите статус в списке!", ephemeral=True)
            
        if self.is_equipment:
            if self.target_key in self.main_view.extra_data:
                if self.selected_effect_tech in self.main_view.extra_data[self.target_key]:
                    self.main_view.extra_data[self.target_key].remove(self.selected_effect_tech)
        else:
            if self.target_key in self.main_view.extra_data and self.sub_key in self.main_view.extra_data[self.target_key]:
                if self.selected_effect_tech in self.main_view.extra_data[self.target_key][self.sub_key]:
                    self.main_view.extra_data[self.target_key][self.sub_key].remove(self.selected_effect_tech)
                
        await self.send_menu(inter)

    async def btn_back_callback(self, inter: disnake.MessageInteraction):
        self.main_view.current_screen = "spec"
        await self.main_view.send_main_window(inter)

class ItemWeaponManagementMenu(disnake.ui.View):
    """Подменю UIMS для пошагового редактирования характеристик оружия, классов и автоогня"""
    def __init__(self, main_view):
        super().__init__(timeout=600)
        self.main_view = main_view
        self.selected_stat = None

    async def send_menu(self, inter: disnake.Interaction):
        self.clear_items()
        
        # Гарантируем наличие ключей в extra_data
        stats = self.main_view.extra_data.setdefault("base_stats", {"damage": [1, 0], "recoil": 0, "accuracy": 0, "grouping": 3, "reliability": 10, "max_magazine": 30})
        text_feat = self.main_view.extra_data.setdefault("text_feature", "Отсутствует")
        wep_class = self.main_view.extra_data.setdefault("weapon_class", "Пистолет")
        skill_id = self.main_view.extra_data.setdefault("associated_skill", "skill_handguns")
        auto_fire_status = self.main_view.extra_data.setdefault("auto_fire", "no")

        auto_fire_readable = "Да" if auto_fire_status == "yes" else "Нет"

        info = (
            f"**Конфигурация ТТХ оружия для:** `{self.main_view.name}`\n\n"
            f"• Класс оружия: `{wep_class}`\n"
            f"• Наличие автоогня: `{auto_fire_readable}`\n\n"
            f"📊 **Характеристики:**\n"
            f"• Урон кубами: `{format_dice_array(stats.get('damage', [1, 0]))}`\n"
            f"• Отдача: `{stats.get('recoil', 0)}` | Точность: `{stats.get('accuracy', 0)}`\n"
            f"• Кучность: `{stats.get('grouping', 3)}` | Надежность: `{stats.get('reliability', 10)}`\n"
            f"• Вместимость магазина: `{stats.get('max_magazine', 30)}`\n"
            f"• Особенность оружия: *{text_feat}*\n"
        )
            
        embed = disnake.Embed(title="UIMS: Оружейная мастерская ГМа", description=info, color=disnake.Color.red())
        embed.set_footer(text="© By Bon Shinomiya")
        
        # --- 1. РЯД 0: СЕЛЕКТОР КЛАССА ОРУЖИЯ (С ЖЕСТКИМ МАППИНГОМ НАВЫКОВ) ---
        class_options = [
            disnake.SelectOption(label="Пистолет", value="Пистолет"),
            disnake.SelectOption(label="Пистолет-пулемёт", value="Пистолет-пулемёт"),
            disnake.SelectOption(label="Дробовик", value="Дробовик"),
            disnake.SelectOption(label="Штурмовая винтовка", value="Штурмовая винтовка"),
            disnake.SelectOption(label="Снайперская винтовка", value="Снайперская винтовка"),
            disnake.SelectOption(label="Тяжёлое оружие", value="Тяжёлое оружие")
        ]
        
        class_select = disnake.ui.Select(
            placeholder="Задать класс оружия", 
            options=class_options, 
            custom_id="wep_class_select",
            row=0
        )
        
        async def class_select_cb(i: disnake.MessageInteraction):
            chosen_class = i.values[0]
            self.main_view.extra_data["weapon_class"] = chosen_class
            
            # Ролевой маппинг навыков согласно ТЗ PoS RP
            SKILL_MAPPING = {
                "Пистолет": "skill_handguns",
                "Пистолет-пулемёт": "skill_handguns",
                "Дробовик": "skill_shotguns",
                "Штурмовая винтовка": "skill_assaultrifle",
                "Снайперская винтовка": "skill_sniperrifle",
                "Тяжёлое оружие": "skill_heavyweapon"
            }
            self.main_view.extra_data["associated_skill"] = SKILL_MAPPING.get(chosen_class, "skill_handguns")
            await self.send_menu(i)
            
        class_select.callback = class_select_cb
        self.add_item(class_select)

        # --- 2. РЯД 1: СЕЛЕКТОР ОСТАЛЬНЫХ ТТХ ПАРАМЕТРОВ ---
        stat_options = [
            disnake.SelectOption(label="Урон оружия", value="damage"),
            disnake.SelectOption(label="Отдача", value="recoil"),
            disnake.SelectOption(label="Точность", value="accuracy"),
            disnake.SelectOption(label="Кучность", value="grouping"),
            disnake.SelectOption(label="Надежность", value="reliability"),
            disnake.SelectOption(label="Вместимость магазина", value="max_magazine"),
            disnake.SelectOption(label="Особенность оружия (Текст)", value="text_feature")
        ]
        
        stat_select = disnake.ui.Select(placeholder="Выбрать коэффициент для настройки...", options=stat_options, custom_id="wep_stat_select", row=1)
        async def stat_select_cb(i: disnake.MessageInteraction):
            self.selected_stat = i.values[0]
            await i.response.defer()
        stat_select.callback = stat_select_cb
        self.add_item(stat_select)
        
# --- 3. РЯД 2: КНОПКИ УПРАВЛЕНИЯ И ТУМБЛЕРЫ АВТООГНЯ ---
        btn_set = disnake.ui.Button(label="Изменить выбранный коэф.", style=disnake.ButtonStyle.red, row=2)
        async def btn_set_callback(inter_modal: disnake.MessageInteraction):
            if not self.selected_stat:
                return await inter_modal.response.send_message("❌ Сначала выберите параметр во втором списке!", ephemeral=True)
            self.main_view.selected_stat = self.selected_stat
            await inter_modal.response.send_modal(WeaponSingleInputModal(self.main_view))
        btn_set.callback = btn_set_callback
        self.add_item(btn_set)

        # ДИНАМИЧЕСКИЙ ТУМБЛЕР АВТООГНЯ (Разделение логики: Оружие vs Модификация)
        if self.main_view.item_type == "gun_modification":
            # Трёхпозиционный тумблер для обвеса: Не влияет -> Включает -> Выключает -> Не влияет
            current_mod_af = self.main_view.extra_data.get("mod_auto_fire")
            
            if current_mod_af == "yes":
                toggle_label = "Мод. автоогня: ВЛЮЧАЕТ"
            elif current_mod_af == "no":
                toggle_label = "Мод. автоогня: ВЫКЛЮЧАЕТ"
            else:
                toggle_label = "Мод. автоогня: НЕ ВЛИЯЕТ"
                
            btn_auto_fire = disnake.ui.Button(label=toggle_label, style=disnake.ButtonStyle.red, row=2)
            
            async def btn_mod_auto_fire_cb(i: disnake.MessageInteraction):
                state = self.main_view.extra_data.get("mod_auto_fire")
                # Циклическое переключение состояний
                if state is None:
                    self.main_view.extra_data["mod_auto_fire"] = "yes"
                elif state == "yes":
                    self.main_view.extra_data["mod_auto_fire"] = "no"
                else:
                    self.main_view.extra_data["mod_auto_fire"] = None
                await self.send_menu(i)
                
            btn_auto_fire.callback = btn_mod_auto_fire_cb
        else:
            # Двухпозиционный классический тумблер для чистого Оружия
            toggle_label = "Автоогонь: ДА" if auto_fire_status == "yes" else "Автоогонь: НЕТ"
            btn_auto_fire = disnake.ui.Button(label=toggle_label, style=disnake.ButtonStyle.red, row=2)
            
            async def btn_weapon_auto_fire_cb(i: disnake.MessageInteraction):
                current_f = self.main_view.extra_data.get("auto_fire", "no")
                self.main_view.extra_data["auto_fire"] = "no" if current_f == "yes" else "yes"
                await self.send_menu(i)
                
            btn_auto_fire.callback = btn_weapon_auto_fire_cb

        self.add_item(btn_auto_fire)

        # Кнопка возврата в главное меню UIMS
        btn_back = disnake.ui.Button(label="🔙 Назад в главное меню", style=disnake.ButtonStyle.red, row=2)
        async def btn_back_callback(i: disnake.MessageInteraction):
            self.main_view.current_screen = "main"
            await self.main_view.send_main_window(i)
        btn_back.callback = btn_back_callback
        self.add_item(btn_back)
        
        await inter.response.edit_message(embed=embed, view=self)


class WeaponSingleInputModal(disnake.ui.Modal):
    def __init__(self, main_view: UnitedItemsManagementSystem):
        self.main_view = main_view
        stat = main_view.selected_stat
        
        label_text = "Введите значение"
        placeholder_text = ""
        current_value = ""
        
        stats = main_view.extra_data.get("base_stats", {})
        
        if stat == "damage":
            label_text = "Урон кубами (Формат: Xd6+Y)"
            placeholder_text = "Пример: 4d6+0 или 2d6+2"
            current_value = format_dice_array(stats.get("damage", [4, 0]))
        elif stat == "text_feature":
            label_text = "Особенность оружия (Текстовое поле)"
            placeholder_text = "Пример: Игнорирует половину брони."
            current_value = main_view.extra_data.get("text_feature", "")
        elif stat == "accuracy":
            label_text = "Точность оружия (Целое число)"
            placeholder_text = "Введите модификатор точности..."
            current_value = str(stats.get("accuracy", 0))
        elif stat == "grouping":
            label_text = "Изменение кучности (Целое число)"
            placeholder_text = "Пример: -1 (улучшает кучность) или 0"
            current_value = str(stats.get("grouping", 0))
        elif stat == "reliability":
            label_text = "Изменение надежности (Целое число)"
            placeholder_text = "Пример: 2 (повышает износостойкость) или 0"
            current_value = str(stats.get("reliability", 0))
        elif stat == "max_magazine":
            label_text = "Изменение емкости магазина (Целое число)"
            placeholder_text = "Пример: 15 (для увеличенного магазина) или 0"
            current_value = str(stats.get("max_magazine", 0))
        else:
            label_text = f"Параметр {stat} (Целое число)"
            placeholder_text = "Введите целое число..."
            current_value = str(stats.get(stat, 0))

        components = [
            disnake.ui.TextInput(
                label=label_text,
                placeholder=placeholder_text,
                value=current_value,
                custom_id="weapon_val",
                style=disnake.TextInputStyle.paragraph if stat == "text_feature" else disnake.TextInputStyle.short
            )
        ]
        super().__init__(title="Изменение боевого параметра", components=components)
        
    async def callback(self, inter: disnake.ModalInteraction):
        raw_val = inter.text_values["weapon_val"].strip()
        stat = self.main_view.selected_stat
        
        if stat == "text_feature":
            self.main_view.extra_data["text_feature"] = raw_val
        else:
            if "base_stats" not in self.main_view.extra_data:
                self.main_view.extra_data["base_stats"] = {}
                
            if stat == "damage":
                self.main_view.extra_data["base_stats"]["damage"] = parse_dice_string(raw_val)
            else:
                try:
                    self.main_view.extra_data["base_stats"][stat] = int(raw_val)
                except ValueError:
                    return await inter.response.send_message("Ошибка! Значение должно быть целым числом.", ephemeral=True)
                    
        # Возвращаем ГМа на экран глубоких настроек spec
        await self.main_view.send_main_window(inter)

class ArmorSingleInputModal(disnake.ui.Modal):
    def __init__(self, main_view):
        self.view = main_view 
        stat = main_view.selected_stat
        
        label_text = "Введите значение"
        placeholder_text = ""
        current_value = ""
        
        # Динамически определяем заголовки и подсказки модалки
        if stat == "armor_points":
            if main_view.item_type in ["armor", "head_armor", "head_mask"]:
                label_text = "Максимальные очки брони (Целое число)"
                placeholder_text = "Пример: 15 (установит структуру [15, 15])"
            else:
                label_text = "Добавляемые очки брони (Целое число)"
                placeholder_text = "Пример: 5"
            current_value = str(main_view.extra_data.get("armor_points", [0, 0])[1])
            
        elif stat == "limb_armor":
            label_text = "Мод. ПБ конечностей (Целое число)"
            placeholder_text = "Пример: 2"
            current_value = str(main_view.extra_data.get("modificators", {}).get("limb_armor", 0))
            
        # ИСПРАВЛЕНО: Четкие заголовки и подхват текущих значений для АЗ и ДАЗ
        elif stat == "base_anomaly_resist":
            label_text = "Аномальная защита костюма (АЗ) (Целое число)"
            placeholder_text = "Пример: 15"
            current_value = str(main_view.extra_data.get("base_anomaly_resist", 0))

        elif stat == "base_anomaly_mods":
            label_text = "Доступный ДАЗ (Ячейки модов) (Целое число)"
            placeholder_text = "Пример: 6"
            current_value = str(main_view.extra_data.get("base_anomaly_mods", 6))
            
        elif stat == "anomaly_mod_req":
            label_text = "Потребление ДАЗ (Целое число)"
            placeholder_text = "Пример: 1"
            current_value = str(main_view.extra_data.get("anomaly_mod_req", 1))
            
        elif stat == "class":
            label_text = "Технический класс прибора (Целое число)"
            placeholder_text = "Пример: 2"
            current_value = str(main_view.extra_data.get("class", 1))
            
        elif stat in ["mod_electro", "mod_termo", "mod_chemical", "mod_radiation", "mod_psy"]:
            stat_titles = {
                "mod_electro": "Мод. Электрозащиты", "mod_termo": "Мод. Термозащиты",
                "mod_chemical": "Мод. Химзащиты", "mod_radiation": "Мод. Рад. защиты", "mod_psy": "Мод. Пси-защиты"
            }
            dict_name = "add_resist" if main_view.item_type == "anomaly_mod" else "modificators"
            stat_mapping = {
                "mod_electro": "electro_resist", "mod_termo": "termo_resist",
                "mod_chemical": "chemical_resist", "mod_radiation": "radiation_resist", "mod_psy": "psy_resist"
            }
            label_text = f"{stat_titles.get(stat)} (Целое число)"
            placeholder_text = "Пример: 4"
            current_value = str(main_view.extra_data.get(dict_name, {}).get(stat_mapping.get(stat), 0))
            
        else: # Текстовое поле (text_feature)
            label_text = "Особенность / Свойство работы (Текст)"
            placeholder_text = "Введите текстовое описание свойства прибора или костюма..."
            current_value = str(main_view.extra_data.get(stat, ""))

        components = [
            disnake.ui.TextInput(
                label=label_text,
                placeholder=placeholder_text,
                value=current_value,
                custom_id="modal_input_value",
                style=disnake.TextInputStyle.paragraph if stat == "text_feature" else disnake.TextInputStyle.short,
                max_length=500 if stat == "text_feature" else 50,
                required=True
            )
        ]
        super().__init__(title="UIMS: Изменение коэффициента", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        user_value = inter.text_values["modal_input_value"].strip()
        selected_stat = self.view.selected_stat
        
        stat_mapping = {
            "mod_electro": "electro_resist", "mod_termo": "termo_resist",
            "mod_chemical": "chemical_resist", "mod_radiation": "radiation_resist",
            "mod_psy": "psy_resist", "armor_points": "armor_points", "limb_armor": "limb_armor"
        }

        target_key = stat_mapping.get(selected_stat, selected_stat)

        # Сохранение модификаторов во вложенные словари модулей (add_resist или modificators)
        if selected_stat in ["mod_electro", "mod_termo", "mod_chemical", "mod_radiation", "mod_psy", "armor_points", "limb_armor"] and self.view.item_type in ["anomaly_mod", "mounted_mod", "helmet_mods"]:
            if selected_stat == "mod_psy" and self.view.item_type != "helmet_mods":
                return await inter.response.send_message("❌ Ошибка! У модулей брони костюма не может быть модификатора пси-защиты.", ephemeral=True)
                
            dict_name = "add_resist" if self.view.item_type == "anomaly_mod" else "modificators"
            if dict_name not in self.view.extra_data or not isinstance(self.view.extra_data[dict_name], dict):
                self.view.extra_data[dict_name] = {}
                
            try: self.view.extra_data[dict_name][target_key] = int(user_value)
            except ValueError: return await inter.response.send_message("Ошибка! Введите целое число.", ephemeral=True)
        
        # Базовые числовые и текстовые параметры (ИСПРАВЛЕНО: добавлена легитимная обработка base_anomaly_mods и base_anomaly_resist!)
        else:
            try:
                if target_key == "armor_points":
                    val = int(user_value)
                    self.view.extra_data[target_key] = [val, val]
                elif target_key in ["base_anomaly_mods", "base_anomaly_resist", "base_armor_points", "electro_resist", "termo_resist", "chemical_resist", "radiation_resist", "psy_resist", "anomaly_mod_req", "class"]:
                    self.view.extra_data[target_key] = int(user_value)
                else:
                    self.view.extra_data[target_key] = user_value
            except ValueError:
                return await inter.response.send_message("Ошибка! Введите корректное числовое значение.", ephemeral=True)

        # Перерисовываем основное окно
        await self.view.send_main_window(inter)

# =================================================== ИНВЕНТАРЬ ============================================

class PlayerInventoryMenu(disnake.ui.View):
    def __init__(self, parent_view, folder_path: str, interactor_id: int):
        super().__init__(timeout=300)
        self.parent_view = parent_view     # Ссылка на CharacterSelectView для возврата
        self.folder_path = folder_path     # Путь к папке персонажа
        self.interactor_id = interactor_id # ID игрока, открывшего инвентарь
        
        self.current_tab = "character"     # Текущая вкладка: character или backpack
        self.selected_slot = None          # Выбранный слот экипировки
        self.selected_backpack_item = None # Выбранный для действия предмет в рюкзаке
        self.backpack_page = 1             # Текущая страница пагинации рюкзака
        self.filter_category = "all"       # Фильтр категорий рюкзака
        
        # Пути к базам данных
        self.inventory_path = os.path.join(folder_path, "char_inventory.json")
        self.items_lib_path = "chars_data/items_lib.json"
        self.effects_lib_path = "chars_data/effects_lib.json"

    async def load_json_file(self, path: str) -> dict:
        if not os.path.exists(path): return {}
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                return json.loads(await f.read())
        except: return {}

    async def calculate_inventory_weight(self, inv_data: dict, items_lib: dict) -> float:
        """Считает суммарный физический вес всех пожитков, включая поглощённые костюмом моды"""
        total_weight = 0.0
        # 1. Считаем статичные предметы
        static_items = inv_data.get("inventory", {}).get("static", {})
        for item_id, amount in static_items.items():
            if amount <= 0: continue
            total_weight += items_lib.get(item_id, {}).get("weight_per_item", 0.0) * amount
            
        # 2. Считаем уникальные предметы
        unique_items = inv_data.get("inventory", {}).get("unique", {})
        for u_id, u_data in unique_items.items():
            template_id = u_data.get("template", u_id)
            total_weight += items_lib.get(template_id, {}).get("weight_per_item", 0.0)
            
            # Если это костюм, добавляем вес поглощённых static-модификаций
            if u_data.get("type") == "armor":
                setup_mods = u_data.get("setup_mods", [])
                for mod_id in setup_mods:
                    total_weight += items_lib.get(mod_id, {}).get("weight_per_item", 0.0)
                    
                setup_anom = u_data.get("setup_anomaly_mods", [])
                for mod_id in setup_anom:
                    total_weight += items_lib.get(mod_id, {}).get("weight_per_item", 0.0)
                    
        return round(total_weight, 3)

    async def send_inventory_window(self, inter: disnake.Interaction):
        """Главный рендерер окон инвентаря"""
        self.clear_items()
        
        inv_data = await self.load_json_file(self.inventory_path)
        items_lib = await self.load_json_file(self.items_lib_path)
        
        char_stats = await self.load_json_file(os.path.join(self.folder_path, "char_stats.json"))
        char_name = char_stats[0].get("char_name", "Сталкер") if char_stats and isinstance(char_stats, list) else "Сталкер"
        current_weight = await self.calculate_inventory_weight(inv_data, items_lib)

        # ========================================== ВКЛАДКА: ПЕРСОНАЖ ==========================================
        if self.current_tab == "character":
            eq = inv_data.get("equipment", {})
            unique_bag = inv_data.get("inventory", {}).get("unique", {})
            
            def get_slot_status(slot_key: str) -> str:
                item_u_id = eq.get(slot_key)
                if not item_u_id: return "• *Слот пуст*"
                
                item_info = unique_bag.get(item_u_id, {})
                template_id = item_info.get("template", item_u_id)
                item_template = items_lib.get(template_id, {})
                
                name = item_info.get("username") or item_template.get("name", template_id)
                durability = f" [{item_info['durability']}/10]" if "durability" in item_info else ""
                
                if slot_key == "armor_slot" and item_info.get("plate"):
                    p_name = items_lib.get(item_info["plate"], {}).get("name", item_info["plate"])
                    return f"• **{name}**{durability} (Плита: {p_name})"
                return f"• **{name}**{durability}"

            slots_desc = (
                f"**Оружие в первом слоте:**\n{get_slot_status('weapon_slot')}\n\n"
                f"**Оружие во втором слоте:**\n{get_slot_status('weapon_slot_2')}\n\n"
                f"**Холодное оружие:**\n{get_slot_status('melee_slot')}\n\n"
                f"**Комбинезон:**\n{get_slot_status('armor_slot')}\n\n"
                f"**Шлем:**\n{get_slot_status('head_slot')}\n\n"
                f"**Противогаз:**\n{get_slot_status('mask_slot')}\n\n"
                f"**Детектор аномалий:**\n{get_slot_status('detector_anomaly_slot')}\n\n"
                f"**Детектор артефактов:**\n{get_slot_status('detector_artefact_slot')}\n\n"
                f"**Прибор на глаза (ПНВ):**\n{get_slot_status('eyes_slot')}\n\n"
                f"**Активные наушники:**\n{get_slot_status('ears_slot')}"
            )
            
            embed = disnake.Embed(title=f"Экипировка персонажа — {char_name}", description=slots_desc, color=disnake.Color.red())

            slot_names_readable = {
                "weapon_slot": "Оружие в первом слоте", "weapon_slot_2": "Оружие во втором слоте", 
                "melee_slot": "Холодное оружие", "armor_slot": "Комбинезон", "head_slot": "Шлем", 
                "mask_slot": "Противогаз", "detector_anomaly_slot": "Детектор аномалий", 
                "detector_artefact_slot": "Детектор артефактов", "eyes_slot": "Прибор на глаза (ПНВ)", "ears_slot": "Активные наушники"
            }
            
            select_options = [
                disnake.SelectOption(label=slot_names_readable[k], value=k, description=f"Надето: {unique_bag.get(v, {}).get('username') or items_lib.get(unique_bag.get(v, {}).get('template'), {}).get('name', 'Вещь')}")
                for k, v in eq.items() if v
            ]
            
            if select_options:
                slot_select = disnake.ui.Select(placeholder="Выберите надетый предмет для взаимодействия...", options=select_options, custom_id="eq_slot_select", row=2)
                slot_select.callback = self.eq_slot_select_callback
                self.add_item(slot_select)
                
                if hasattr(self, "selected_slot") and self.selected_slot in eq and eq[self.selected_slot]:
                    btn_unequip = disnake.ui.Button(label="Снять в рюкзак", style=disnake.ButtonStyle.red, custom_id="btn_unequip", row=3)
                    btn_unequip.callback = self.btn_unequip_callback
                    self.add_item(btn_unequip)

# ========================================== ВКЛАДКА: РЮКЗАК ==========================================
        elif self.current_tab == "backpack":
            static_bag = inv_data.get("inventory", {}).get("static", {})
            unique_bag = inv_data.get("inventory", {}).get("unique", {})
            eq_slots = inv_data.get("equipment", {})
            equipped_u_ids = set(eq_slots.values())
            
            raw_backpack_list = [] # Список кортежей: (id_для_действия, строка_для_вывода, тех_тип)

            # 1. Сбор статичных предметов
            for item_id, amount in static_bag.items():
                if amount <= 0: continue
                
                item_template = items_lib.get(item_id, {})
                i_type = item_template.get("type", "narrative")
                
                # Переводим технический тип предмета в укрупненную категорию
                item_category = ITEM_TYPE_TO_CATEGORY.get(i_type, "craft_narrative")
                
                # Фильтруем по категории
                if self.filter_category != "all" and item_category != self.filter_category: 
                    continue
                
                name = item_template.get("name", item_id)
                raw_backpack_list.append((item_id, f"📦 **{name}** — `{amount} шт.`", i_type))

            # 2. Сбор уникальных предметов (исключая надетые и встроенные в броню)
            eq_slots = inv_data.get("equipment", {})
            equipped_u_ids = set(eq_slots.values())
            
            # Собираем ID всех плит и модулей, которые уже зашиты внутрь других костюмов
            embedded_u_ids = set()
            for u_id, u_card in unique_bag.items():
                if u_card.get("type") == "armor":
                    if u_card.get("plate"): embedded_u_ids.add(u_card["plate"])
                    if u_card.get("additional_armor"): embedded_u_ids.add(u_card["additional_armor"])

            for u_id, u_data in unique_bag.items():
                # Если вещь надета на куклу ИЛИ вшита как плита/модуль конечностей — скрываем из рюкзака!
                if u_id in equipped_u_ids or u_id in embedded_u_ids: 
                    continue
                
                i_type = u_data.get("type")
                if not i_type:
                    template_id = u_data.get("template", u_id)
                    i_type = items_lib.get(template_id, {}).get("type", "weapon")
                
                item_category = ITEM_TYPE_TO_CATEGORY.get(i_type, "craft_narrative")
                if self.filter_category != "all" and item_category != self.filter_category: 
                    continue
                
                template_id = u_data.get("template", u_id)
                item_template = items_lib.get(template_id, {})
                name = u_data.get("username") or item_template.get("name", template_id)
                
                durability_str = ""
                if "durability" in u_data:
                    durability_str = f" *[{u_data['durability']}/10]*"
                elif "armor_points" in u_data and isinstance(u_data["armor_points"], list) and len(u_data["armor_points"]) >= 2:
                    durability_str = f" *[{u_data['armor_points'][0]}/{u_data['armor_points'][1]} ПБ]*"
                
                raw_backpack_list.append((u_id, f"🔺 **{name}**{durability_str}", i_type))

            # --- ПАГИНАЦИЯ И СБОРКА FIELDS (Синхронизировано под жесткий лимит Discord в 25 опций) ---
            items_per_field = 15
            items_per_page = 25 # ТВОЙ ФИКС: теперь страница рюкзака строго равна емкости селектора!
            total_items = len(raw_backpack_list)
            max_pages = (total_items - 1) // items_per_page + 1 if total_items > 0 else 1
            
            if self.backpack_page > max_pages: 
                self.backpack_page = max_pages
            
            start_idx = (self.backpack_page - 1) * items_per_page
            page_items = raw_backpack_list[start_idx : start_idx + items_per_page]

            readable_filter = READABLE_ITEM_TYPES.get(self.filter_category, "Все предметы")
            bp_notif = ""
            if hasattr(self, "backpack_notification") and self.backpack_notification:
                bp_notif = f"{self.backpack_notification}\n\n"
                self.backpack_notification = None # Стираем

            embed = disnake.Embed(
                title=f"Содержимое рюкзака — {char_name}",
                description=f"{bp_notif}" # Выводим плашку на самый верх описания рюкзака
                            f"Текущий фильтр: `*{readable_filter}*`\n\nДля взаимодействия выберите предмет в меню ниже.",
                color=disnake.Color.red()
            )

            # Распределяем 25 предметов по двум полям (до 15 в первое, остаток до 10 — во второе)
            if page_items:
                field_1 = [x[1] for x in page_items[0:items_per_field]]
                field_2 = [x[1] for x in page_items[items_per_field:items_per_page]]
                
                if field_1: embed.add_field(name="📋 Секция рюкзака I", value="\n".join(field_1), inline=False)
                if field_2: embed.add_field(name="📋 Секция рюкзака II", value="\n".join(field_2), inline=False)
            else:
                embed.description += "\n\n*В рюкзаке не найдено предметов данной категории.*"

            embed.set_footer(text=f"Суммарный вес вещей: {current_weight} кг | Страница {self.backpack_page}/{max_pages} | Всего позиций: {total_items}")

            # --- СЕЛЕКТОР ФИЛЬТРОВ (Статический, красивый и укрупненный) ---
            filter_options = [
                disnake.SelectOption(label="Все категории", value="all", emoji="🎒"),
                disnake.SelectOption(label="Оружие и ножи", value="weaponry", emoji="🔫"),
                disnake.SelectOption(label="Боеприпасы и гранаты", value="ammo_grenades", emoji="📦"),
                disnake.SelectOption(label="Медицина и провизия", value="medicine_food", emoji="💉"),
                disnake.SelectOption(label="Костюмы и шлемы", value="armor_suits", emoji="👕"),
                disnake.SelectOption(label="Модификации брони", value="armor_mods", emoji="🛠️"),
                disnake.SelectOption(label="Детекторы и приборы", value="electronics", emoji="📟"),
                disnake.SelectOption(label="Крафт / Трофеи / Нарратив", value="craft_narrative", emoji="🧬")
            ]

            filter_select = disnake.ui.Select(
                placeholder="Отфильтровать рюкзак...", 
                options=filter_options, 
                custom_id="bp_filter_select", 
                row=2
            )
            async def filter_cb(i: disnake.MessageInteraction):
                if i.author.id != self.interactor_id: return
                self.filter_category = i.values[0]
                self.backpack_page = 1
                await self.send_inventory_window(i)
            filter_select.callback = filter_cb
            self.add_item(filter_select)

            # --- СЕЛЕКТОР ДЕЙСТВИЯ НАД ПРЕДМЕТОМ ИЗ РЮКЗАКА ---
            action_options = []
            for item_id, _, item_type in page_items:
                if item_id in unique_bag:
                    t_id = unique_bag[item_id].get("template", item_id)
                    i_name = unique_bag[item_id].get("username") or items_lib.get(t_id, {}).get("name", t_id)
                else:
                    i_name = items_lib.get(item_id, {}).get("name", item_id)
                
                # Показываем игроку красивое ролевое название подтипа в описании действия
                readable_type = READABLE_ITEM_TYPES.get(item_type, item_type)
                action_options.append(disnake.SelectOption(
                    label=i_name[:50], 
                    value=item_id, 
                    description=f"Тип: {readable_type}"
                ))

            if action_options:
                action_select = disnake.ui.Select(placeholder="Выберите предмет из рюкзака для действия...", options=action_options[:25], custom_id="bp_action_select", row=3)
                action_select.callback = self.bp_action_select_callback
                self.add_item(action_select)

                if hasattr(self, "selected_backpack_item") and self.selected_backpack_item:
                    is_unique = self.selected_backpack_item in unique_bag
                    target_type = unique_bag[self.selected_backpack_item].get("type") if is_unique else items_lib.get(self.selected_backpack_item, {}).get("type")
                    
                    equipable_types = ["weapon", "melee_weapon", "armor", "head_armor", "head_mask", "anomaly_detector", "artefact_detector", "head_eyes", "head_ears"]
                    
                    if target_type in equipable_types:
                        btn_equip = disnake.ui.Button(label="Экипировать на персонажа", style=disnake.ButtonStyle.red, custom_id="btn_equip", row=4)
                        btn_equip.callback = self.btn_equip_callback
                        self.add_item(btn_equip)
                    elif target_type in ["medicine", "food"]:
                        btn_use = disnake.ui.Button(label="Использовать (Съесть/Вколоть)", style=disnake.ButtonStyle.red, custom_id="btn_use_consumable", row=4)
                        btn_use.callback = self.btn_use_consumable_callback
                        self.add_item(btn_use)

            # Стрелочки страниц рюкзака
            if max_pages > 1:
                btn_prev = disnake.ui.Button(label="⬅️", style=disnake.ButtonStyle.red, disabled=(self.backpack_page <= 1), row=4 if action_options else 3)
                btn_next = disnake.ui.Button(label="➡️", style=disnake.ButtonStyle.red, disabled=(self.backpack_page >= max_pages), row=4 if action_options else 3)
                async def p_cb(i: disnake.MessageInteraction): self.backpack_page -= 1; await self.send_inventory_window(i)
                async def n_cb(i: disnake.MessageInteraction): self.backpack_page += 1; await self.send_inventory_window(i)
                btn_prev.callback = p_cb; btn_next.callback = n_cb
                self.add_item(btn_prev); self.add_item(btn_next)

        # ТВОЙ жесткий подвал эмбеда[cite: 3]
        embed.set_footer(text=f"Суммарный вес вещей: {current_weight} кг | © By Bon Shinomiya")

        # Вкладки и возврат
        btn_tab_char = disnake.ui.Button(label="Персонаж", style=disnake.ButtonStyle.red, disabled=(self.current_tab == "character"), custom_id="inv_tab_char", row=0)
        btn_tab_pack = disnake.ui.Button(label="Рюкзак", style=disnake.ButtonStyle.red, disabled=(self.current_tab == "backpack"), custom_id="inv_tab_pack", row=0)
        btn_back = disnake.ui.Button(label="Вернуться в меню персонажа", style=disnake.ButtonStyle.red, custom_id="inv_btn_back", row=1)
        
        async def tab_char_cb(i: disnake.MessageInteraction): self.current_tab = "character"; self.selected_backpack_item = None; await self.send_inventory_window(i)
        async def tab_pack_cb(i: disnake.MessageInteraction): self.current_tab = "backpack"; self.selected_slot = None; await self.send_inventory_window(i)
        
        btn_tab_char.callback = tab_char_cb; btn_tab_pack.callback = tab_pack_cb; btn_back.callback = self.btn_back_to_character_menu_callback
        self.add_item(btn_tab_char); self.add_item(btn_tab_pack); self.add_item(btn_back)

        if inter.response.is_done(): await inter.edit_original_response(content=None, embed=embed, view=self)
        else: await inter.response.edit_message(content=None, embed=embed, view=self)

# ========================================== ОБРАБОТЧИКИ ДЕЙСТВИЙ И КНОПОК ==========================================

    async def btn_back_to_character_menu_callback(self, inter: disnake.MessageInteraction):
        """Останавливает инвентарь и принудительно возвращает интерфейс в исходное меню чарлиста"""
        if inter.author.id != self.interactor_id:
            return await inter.response.send_message("❌ Это не ваш инвентарь!", ephemeral=True)
            
        self.stop() # Полностью гасим ресурсы текущего View инвентаря
        
        # Передаем управление напрямую в главный метод отрисовки анкеты персонажа
        if hasattr(self.parent_view, "main_view"):
            # Метод main_view сам определит, что интеракция уже завершена,
            # сотрет надписи через content=None, вызовет stats_rendering
            # и нарисует свежую карточку со всеми эффектами!
            await self.parent_view.main_view(inter)
        else:
            # Аварийный фоллбэк на случай непредвиденных обстоятельств
            await inter.response.edit_message(content="Возврат...", embed=None, view=self.parent_view)

    async def send_item_context_menu(self, inter: disnake.Interaction):
        """Контекстное меню конкретного предмета с выводом всех специфических ТТХ из UIMS"""
        self.clear_items()
        
        inv_data = await self.load_json_file(self.inventory_path)
        items_lib = await self.load_json_file(self.items_lib_path)
        
        static_bag = inv_data.get("inventory", {}).get("static", {})
        unique_bag = inv_data.get("inventory", {}).get("unique", {})
        
        item_id = self.selected_backpack_item
        is_unique = item_id in unique_bag
        
        # --- БАЗОВАЯ ИНИЦИАЛИЗАЦИЯ ДЛЯ ПРЕДОТВРАЩЕНИЯ UnboundLocalError ---
        name = str(item_id)
        description = "*Описание отсутствует.*"
        picture_url = None  # Строго чистый None без str()
        item_type = "medicine"
        weight = 0.0
        
        from inventory import format_dice_array
        stats_lines = []
        
        # --- СЦЕНАРИЙ А: УНИКАЛЬНЫЙ ПРЕДМЕТ (Оружие, Броня, Шлемы, Детекторы) ---
        if is_unique:
            u_data = unique_bag[item_id]
            template_id = u_data.get("template", item_id)
            item_template = items_lib.get(template_id, {})
            
            # Приоритет кастомным РП-данным от ГМа
            name = u_data.get("username") or item_template.get("name", template_id)
            description = u_data.get("userdesc") or item_template.get("description", "*Описание отсутствует.*")
            picture_url = u_data.get("userpicture") or item_template.get("picture_url")
            item_type = u_data.get("type") or item_template.get("type", "weapon")
            weight = item_template.get("weight_per_item", 0.0)
            
            # 1. Специфические свойства: Огнестрельное оружие (weapon)
            if item_type == "weapon":
                base_stats = item_template.get("base_stats", {})
                wep_class = item_template.get("weapon_class", "Пистолет")
                auto_fire_readable = "Да" if item_template.get("auto_fire", "no") == "yes" else "Нет"
                
                stats_lines.extend([
                    f"**Прочность:** `{u_data.get('durability', 10)}/10`",
                    f"**Класс оружия:** `{wep_class}`",
                    f"**Автоматический огонь:** `{auto_fire_readable}`",
                    f"**Урон оружия:** `{format_dice_array(base_stats.get('damage', [1, 0]))}`",
                    f"**Точность:** `{base_stats.get('accuracy', 0)}` | **Кучность:** `{base_stats.get('grouping', 3)}`",
                    f"**Отдача:** `{base_stats.get('recoil', 0)}` | **Надежность:** `{base_stats.get('reliability', 10)}`",
                    f"**Вместимость магазина:** `{base_stats.get('max_magazine', 30)}`"
                ])
                if item_template.get("text_feature"):
                    stats_lines.append(f"**Особенность:** *{item_template['text_feature']}*")

            # 2. Специфические свойства: Холодное оружие (melee_weapon)
            elif item_type == "melee_weapon":
                stats_lines.append(f"**Урон в ближнем бою:** `{format_dice_array(item_template.get('damage', [1, 0]))}`")
                if item_template.get("text_feature"):
                    stats_lines.append(f"**Особенность:** *{item_template['text_feature']}*")

            # 3. Специфические свойства: Основа брони / Костюмы (armor)
            elif item_type == "armor":
                armor_pts = u_data.get("armor_points", [0, 0])
                add_armor_pts = u_data.get("additional_armor_points", [0, 0])
                anom_mods = u_data.get("anomaly_mods", item_template.get("base_anomaly_mods", 6))
                
                # Точки базовых резистов (если их нет в инвентаре, берем base_anomaly_resist из шаблона)
                base_ar = item_template.get("base_anomaly_resist", 0)
                electro = u_data.get('electro_resist', base_ar)
                termo = u_data.get('termo_resist', base_ar)
                chemical = u_data.get('chemical_resist', base_ar)
                radiation = u_data.get('radiation_resist', base_ar)
                
                # --- ДИНАМИЧЕСКИЙ РАСЧЕТ БОНУСОВ ОТ УСТАНОВЛЕННЫХ АНОМАЛЬНЫХ МОДОВ ---
                setup_anom = u_data.get("setup_anomaly_mods", [])
                for mod_id in setup_anom:
                    mod_tmpl = items_lib.get(mod_id, {})
                    add_resist = mod_tmpl.get("add_resist", {}) # Достаем словарь бонусов из шаблона мода
                    
                    # Аккуратно суммируем модификаторы
                    electro += add_resist.get("electro_resist", 0)
                    termo += add_resist.get("termo_resist", 0)
                    chemical += add_resist.get("chemical_resist", 0)
                    radiation += add_resist.get("radiation_resist", 0)

                # Собираем базовые защитные характеристики с учетом бонусов
                stats_lines.extend([
                    f"🛡️ **Класс защиты (очки брони):** `{armor_pts[0]}/{armor_pts[1]} ПБ`",
                    f"📟 **Доступный ДАЗ (Ячейки):** `{anom_mods}`",
                    f"⚡ **Электрозащита:** `+{electro}`",
                    f"🔥 **Термозащита:** `+{termo}`",
                    f"🧪 **Химзащита:** `+{chemical}`",
                    f"☢️ **Рад. защита:** `+{radiation}`"
                ])
                
                stats_lines.append("\n🧩 **Компоненты и модули экипировки:**")
                
                # Бронеплита
                if u_data.get("plate"):
                    p_uid = u_data.get("plate")
                    p_card = unique_bag.get(p_uid, {})
                    p_template = p_card.get("template", p_uid)
                    p_name = p_card.get("username") or items_lib.get(p_template, {}).get("name", p_template)
                    stats_lines.append(f"• **Бронеплита:** {p_name} `({armor_pts[0]}/{armor_pts[1]} ПБ)`")
                else:
                    stats_lines.append("• **Бронеплита:** *Не установлена (Слот пуст)*")
                    
                # Защита конечностей
                if u_data.get("additional_armor"):
                    l_uid = u_data.get("additional_armor")
                    l_card = unique_bag.get(l_uid, {})
                    l_template = l_card.get("template", l_uid)
                    l_name = l_card.get("username") or items_lib.get(l_template, {}).get("name", l_template)
                    stats_lines.append(f"• **Защита конечностей:** {l_name} `({add_armor_pts[0]}/{add_armor_pts[1]} ПБ)`")
                else:
                    stats_lines.append("• **Защита конечностей:** *Отсутствует*")
                    
                # Навесные модификации (setup_mods)
                setup_mods = u_data.get("setup_mods", [])
                if setup_mods:
                    readable_mods = [f"`{items_lib.get(m, {}).get('name', m)}`" for m in setup_mods]
                    stats_lines.append(f"• **Навесные модификации:** {', '.join(readable_mods)}")
                else:
                    stats_lines.append("• **Навесные модификации:** *Отсутствуют*")

                # Аномальные модификации (setup_anomaly_mods)
                if setup_anom:
                    readable_anom = [f"`{items_lib.get(m, {}).get('name', m)}`" for m in setup_anom]
                    stats_lines.append(f"• **Аномальные моды:** {', '.join(readable_anom)}")
                else:
                    stats_lines.append("• **Аномальные моды:** *Отсутствуют*")

                # Контейнеры артефактов (artefact_containers)
                containers = u_data.get("artefact_containers", {})
                if containers:
                    cont_lines = []
                    for c_num, c_info in containers.items():
                        art_id, rad_class = c_info[0], c_info[1]
                        art_name = items_lib.get(art_id, {}).get("name", "Пусто") if art_id else "Пусто"
                        cont_lines.append(f"  └ Контейнер #{c_num}: `[{art_name}]` (Рад. защита: класс {rad_class})")
                    stats_lines.append("• **Контейнеры артефактов:**\n" + "\n".join(cont_lines))
                else:
                    stats_lines.append("• **Контейнеры артефактов:** *Не установлены*")

                if item_template.get("text_feature"):
                    stats_lines.append(f"\n**Особенность костюма:** *{item_template['text_feature']}*")

            # 4. Специфические свойства: Шлемы и Противогазы (head_armor, head_mask)
            elif item_type in ["head_armor", "head_mask"]:
                b_armor = item_template.get("base_armor_points", 0)
                stats_lines.extend([
                    f"**Базовая броня головы:** `{b_armor} ПБ`",
                    f"**Электрозащита:** `+{u_data.get('electro_resist', item_template.get('electro_resist', 0))}`",
                    f"**Термозащита:** `+{u_data.get('termo_resist', item_template.get('termo_resist', 0))}`",
                    f"**Химзащита:** `+{u_data.get('chemical_resist', item_template.get('chemical_resist', 0))}`",
                    f"**Рад. защита:** `+{u_data.get('radiation_resist', item_template.get('radiation_resist', 0))}`",
                    f"**Пси-защита:** `+{u_data.get('psy_resist', item_template.get('psy_resist', 0))}`"
                ])
                if item_type == "head_armor":
                    mask_status = "Запрещена" if item_template.get("have_mask") == "yes" else "Разрешена"
                    stats_lines.append(f"**Совместимость с противогазом:** `{mask_status}`")

            # 5. Специфические свойства: Бронеплиты и Защита конечностей (armor_plate, add_armor)
            elif item_type in ["armor_plate", "add_armor"]:
                pts = u_data.get("armor_points", item_template.get("armor_points", [0, 0]))
                stats_lines.append(f"**Очки брони элемента защиты:** `{pts[0]}/{pts[1]} ПБ`")

            # 6. Специфические свойства: Детекторы и Электроника
            elif item_type == "artefact_detector":
                stats_lines.append(f"**Технический класс детектора:** `{item_template.get('class', 1)}`")
                if item_template.get("text_feature"):
                    stats_lines.append(f"**Свойство работы:** *{item_template['text_feature']}*")
            elif item_type in ["anomaly_detector", "head_eyes", "head_ears"]:
                if item_template.get("text_feature"):
                    stats_lines.append(f"**Свойство работы прибора:** *{item_template['text_feature']}*")

        # --- СЦЕНАРИЙ Б: СТАТИЧНЫЙ ПРЕДМЕТ (Медицина, Еда, Патроны, Хлам) ---
        else:
            if item_id not in static_bag:
                self.selected_backpack_item = None
                return await self.send_inventory_window(inter)
                
            item_template = items_lib.get(item_id, {})
            
            # Подтягиваем данные из статического шаблона items_lib
            name = item_template.get("name", item_id)
            description = item_template.get("description", "*Описание отсутствует.*")
            picture_url = item_template.get("picture_url")
            item_type = item_template.get("type", "medicine")
            weight = item_template.get("weight_per_item", 0.0)
            
            stats_lines.append(f"📦 **Количество в рюкзаке:** `{static_bag[item_id]} шт.`")
            
            # Специфические свойства расходников: медицина и еда
            if item_type in ["medicine", "food"]:
                eff = item_template.get("use_effects", {})
                if eff and eff.get("add_hp"): stats_lines.append(f"❤️ **Регенерация ПЗ (Здоровье):** `{format_dice_array(eff['add_hp'])}`")
                if eff and eff.get("add_mp"): stats_lines.append(f"🧠 **Восстановление МЗ (Психика):** `{format_dice_array(eff['add_mp'])}`")
                if eff and eff.get("add_rp"): stats_lines.append(f"☢️ **Вывод РЗ (Радиация):** `{format_dice_array(eff['add_rp'])}`")

        # =====================================================================================
        # ВЫЧИСЛЕНИЕ ДИНАМИЧЕСКОГО ВЕСА (Учитывает все вшитые static и unique компоненты)
        # =====================================================================================
        display_weight = weight
        if is_unique and item_type == "armor":
            if u_data.get("plate"):
                p_tmpl = unique_bag.get(u_data["plate"], {}).get("template")
                if p_tmpl: display_weight += items_lib.get(p_tmpl, {}).get("weight_per_item", 0.0)
            if u_data.get("additional_armor"):
                l_tmpl = unique_bag.get(u_data["additional_armor"], {}).get("template")
                if l_tmpl: display_weight += items_lib.get(l_tmpl, {}).get("weight_per_item", 0.0)
            for mod_id in u_data.get("setup_mods", []):
                display_weight += items_lib.get(mod_id, {}).get("weight_per_item", 0.0)
            for mod_id in u_data.get("setup_anomaly_mods", []):
                display_weight += items_lib.get(mod_id, {}).get("weight_per_item", 0.0)
        
        display_weight = round(display_weight, 3)

        # =====================================================================================
        # СБОРКА И ФИЛЬТРАЦИЯ ЭМБЕДА (БЕЗОПАСНЫЙ РЕНДЕР КАРТИНКИ)
        # =====================================================================================
        embed = disnake.Embed(
            title=f"🎒 Осмотр: {name}",
            description=f"{description}\n\n**Специфические свойства и параметры:**\n" + ("\n".join(stats_lines) if stats_lines else "• *Особых свойств нет*"),
            color=disnake.Color.red()
        )
        embed.add_field(name="Вес единицы", value=f"`{display_weight} кг`", inline=True)
        embed.add_field(name=" Категория", value=f"`{READABLE_ITEM_TYPES.get(item_type, item_type)}`", inline=True)
        
        # ЧИСТАЯ ПРОВЕРКА ССЫЛКИ: Защищена от падений UnboundLocalError и от паразитного str(None)
        if picture_url and isinstance(picture_url, str) and picture_url.startswith(("http://", "https://")):
            embed.set_image(url=picture_url)
            
        embed.set_footer(text="© By Bon Shinomiya")

        # 3. ГЕНЕРАЦИЯ КНОПОК ДЕЙСТВИЙ
        btn_back_to_bag = disnake.ui.Button(label="⬅️ Вернуться в рюкзак", style=disnake.ButtonStyle.red, custom_id="btn_back_to_bag", row=0)
        async def back_to_bag_cb(i: disnake.MessageInteraction):
            if i.author.id != self.interactor_id: return
            self.selected_backpack_item = None
            await self.send_inventory_window(i)
        btn_back_to_bag.callback = back_to_bag_cb
        self.add_item(btn_back_to_bag)

        equipable_types = ["weapon", "melee_weapon", "armor", "head_armor", "head_mask", "anomaly_detector", "artefact_detector", "head_eyes", "head_ears"]
        
        if is_unique:
            if item_type in equipable_types:
                btn_equip = disnake.ui.Button(label="👕 Экипировать на персонажа", style=disnake.ButtonStyle.red, custom_id="ctx_btn_equip", row=1)
                btn_equip.callback = self.btn_equip_callback
                self.add_item(btn_equip)
                
                if item_type == "armor":
                    btn_modify = disnake.ui.Button(label="🛠️ Мастерская брони (ГМ)", style=disnake.ButtonStyle.red, custom_id="ctx_btn_modify_armor", row=1)
                    async def modify_armor_cb(i: disnake.MessageInteraction):
                        if i.author.id != self.interactor_id: return
                        menu = GMArmorModificationMenu(self)
                        await menu.send_menu(i)
                    btn_modify.callback = modify_armor_cb
                    self.add_item(btn_modify)
                    
        # Если предмет СТАТИЧНЫЙ (аптечки, еда, энергетики)
        else:
            # ИСПРАВЛЕНО: Четкая проверка типа для вывода кнопки использования
            if item_type in ["medicine", "food"]:
                btn_use = disnake.ui.Button(label="Использовать предмет", style=disnake.ButtonStyle.red, custom_id="ctx_btn_use_static", row=1)
                btn_use.callback = self.btn_use_consumable_callback  # Убедись, что имя коллбэка совпадает с твоим проектом
                self.add_item(btn_use)

        # --- ОБНОВЛЕННЫЙ БЛОК ВЫБРАСЫВАНИЯ С МИНИ-КЛАССОМ МОДАЛКИ ---
        btn_drop = disnake.ui.Button(label="Выбросить из рюкзака", style=disnake.ButtonStyle.red, custom_id="ctx_btn_drop", row=1)
        
        async def btn_drop_callback(i: disnake.MessageInteraction):
            if i.author.id != self.interactor_id: return
            
            # --- СЦЕНАРИЙ 1: ДЛЯ СТАТИЧНЫХ ПРЕДМЕТОВ (Вызываем мини-класс модалки) ---
            if not is_unique:
                current_max = static_bag[item_id]
                await i.response.send_modal(
                    DropStaticCountModal(
                        inventory_view=self,
                        item_id=item_id,
                        item_name=name,
                        max_amount=current_max
                    )
                )
                
            # --- СЦЕНАРИЙ 2: ДЛЯ УНИКАЛЬНЫХ ПРЕДМЕТОВ — ПРОМЕЖУТОЧНЫЙ ЭКРАН ПОДТВЕРЖДЕНИЯ ---
            else:
                self.clear_items()
                
                confirm_embed = disnake.Embed(
                    title="⚠️ Подтверждение удаления снаряжения",
                    description=f"Вы уверены, что хотите выбросить из рюкзака предмет:\n"
                                f"**{name}**?\n\n"
                                f"🚨 *Внимание: вещь будет безвозвратно уничтожена из вашего инвентаря!*",
                    color=disnake.Color.orange()
                )
                confirm_embed.set_footer(text="Защита от случайного выбрасывания снаряжения")

                btn_yes = disnake.ui.Button(label="Да, выбросить", style=disnake.ButtonStyle.danger, row=0)
                btn_no = disnake.ui.Button(label="Отмена", style=disnake.ButtonStyle.secondary, row=0)

                async def yes_cb(interaction: disnake.MessageInteraction):
                    if interaction.author.id != self.interactor_id: return
                    from inventory import remove_item_from_inventory
                    
                    success = await remove_item_from_inventory(self.folder_path, self.selected_backpack_item, amount=1)
                    if success:
                        self.backpack_notification = f"⚠️ **Вещь выброшена:** Вы скинули на землю **{name}**."
                    
                    self.selected_backpack_item = None
                    await self.send_inventory_window(interaction)

                async def no_cb(interaction: disnake.MessageInteraction):
                    if interaction.author.id != self.interactor_id: return
                    await self.send_item_context_menu(interaction)

                btn_yes.callback = yes_cb
                btn_no.callback = no_cb
                self.add_item(btn_yes)
                self.add_item(btn_no)
                
                await i.response.edit_message(embed=confirm_embed, view=self)

        btn_drop.callback = btn_drop_callback
        self.add_item(btn_drop)

        if inter.response.is_done(): await inter.edit_original_response(embed=embed, view=self)
        else: await inter.response.edit_message(embed=embed, view=self)
    
    async def bp_action_select_callback(self, inter: disnake.MessageInteraction):
        if inter.author.id != self.interactor_id: return
        self.selected_backpack_item = inter.values[0]
        # Вместо полной перерисовки рюкзака уходим в специализированное меню предмета!
        await self.send_item_context_menu(inter)
    async def eq_slot_select_callback(self, inter: disnake.MessageInteraction):
        """Перехватывает выбор слота в выпадающем списке куклы персонажа"""
        if inter.author.id != self.interactor_id: return
        
        # Фиксируем выбранный слот в памяти
        self.selected_slot = inter.values[0]
        
        # ИСПРАВЛЕНО: Вместо ленивого edit_message(view=self) вызываем полноценный рендерер!
        # Он очистит старые кнопки, увидит, что selected_slot теперь не пустой,
        # и честно добавит кнопку "Снять в рюкзак" на row=3.
        await self.send_inventory_window(inter)

    async def btn_unequip_callback(self, inter: disnake.MessageInteraction):
        """Логика снятия шмотки из слота обратно в рюкзак с очисткой long_effects и пересчетом веса"""
        if inter.author.id != self.interactor_id: return
        if not hasattr(self, "selected_slot") or not self.selected_slot:
            return await inter.response.send_message("❌ Сначала выберите слот в списке!", ephemeral=True)

        stats_path = os.path.join(self.folder_path, "char_stats.json")
        effects_lib_path = "chars_data/effects_lib.json"

        # Входим под асинхронный замок для безопасной перезаписи файлов
        async with get_char_lock(self.folder_path):
            inv_data = await self.load_json_file(self.inventory_path)
            items_lib = await self.load_json_file(self.items_lib_path)
            
            eq = inv_data.get("equipment", {})
            unique_bag = inv_data.get("inventory", {}).get("unique", {})
            
            item_u_id = eq.get(self.selected_slot)
            if not item_u_id:
                return await inter.response.send_message("❌ Этот слот уже пуст!", ephemeral=True)
                
            # Подгружаем чарлист персонажа и библиотеку эффектов для чистки
            async with aiofiles.open(stats_path, "r", encoding="utf-8") as f:
                skills_data = json.loads(await f.read())
                
            effects_lib = {}
            if os.path.exists(effects_lib_path):
                async with aiofiles.open(effects_lib_path, "r", encoding="utf-8") as f:
                    effects_lib = json.loads(await f.read())

            source = skills_data[0] # Мета-блок параметров
            if "buffs" not in source: source["buffs"] = []
            if "debuffs" not in source: source["debuffs"] = []

            log_details = []

            # --- НАЧАЛО БЛОКА ДЕМОНТАЖА ЭФФЕКТОВ (LONG_EFFECTS) ---
            if item_u_id in unique_bag:
                u_data = unique_bag[item_u_id]
                template_id = u_data.get("template", item_u_id)
                item_template = items_lib.get(template_id, {})
                name = u_data.get("username") or item_template.get("name", template_id)
                
                log_details.append(f"🔄 Снят предмет: **{name}**.")
                
                # Ищем, какие эффекты давал этот предмет в графе "add"
                long_effects = item_template.get("long_effects", {})
                if "add" in long_effects:
                    add_targets = long_effects["add"]
                    if isinstance(add_targets, str): 
                        add_targets = [add_targets]
                    
                    # Безжалостно вырезаем эти ID из массивов персонажа
                    for eff_id in add_targets:
                        removed_flag = False
                        if eff_id in source["buffs"]:
                            source["buffs"].remove(eff_id)
                            removed_flag = True
                        if eff_id in source["debuffs"]:
                            source["debuffs"].remove(eff_id)
                            removed_flag = True
                        
                        if removed_flag:
                            eff_name = effects_lib.get(eff_id, {}).get("name", eff_id)
                            log_details.append(f"❌ Снят эффект прибора: `[ {eff_name} ]`")
            else:
                log_details.append(f"🔄 Освобожден слот: `{self.selected_slot}`.")

            # --- КОНЕЦ БЛОКА ДЕМОНТАЖА ---

            # Физически освобождаем слот на кукле
            eq[self.selected_slot] = None
            
            # Сохраняем измененный чарлист персонажа (без эффектов прибора)
            async with aiofiles.open(stats_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))
            
            # Сохраняем измененный инвентарь
            with open(self.inventory_path, "w", encoding="utf-8") as f:
                json.dump(inv_data, f, indent=4, ensure_ascii=False)

        # Вызываем универсальный метод синхронизации веса и динамических дебаффов нагрузки
        await sync_character_weight_and_effects(self.folder_path)

        # Генерируем красивую бесшовную плашку уведомления для вкладки "character"
        self.backpack_notification = "⚙️ **Изменение экипировки персонажа:**\n" + "\n".join(log_details)
        
        # Сбрасываем фокус выбранного слота и перерисовываем куклу
        self.selected_slot = None
        await self.send_inventory_window(inter)

    async def btn_equip_callback(self, inter: disnake.MessageInteraction):
        """Ролевой движок экипировки уникальных предметов с динамическим наложением long_effects"""
        if inter.author.id != self.interactor_id: return

        # 1. Загружаем актуальные файлы данных
        inv_data = await self.load_json_file(self.inventory_path)
        items_lib = await self.load_json_file(self.items_lib_path)
        
        stats_path = os.path.join(self.folder_path, "char_stats.json")
        effects_lib_path = "chars_data/effects_lib.json"

        unique_bag = inv_data.get("inventory", {}).get("unique", {})
        eq_slots = inv_data.setdefault("equipment", {})
        
        u_id = self.selected_backpack_item

        # Защита: проверяем, существует ли этот уникальный предмет в рюкзаке
        if u_id not in unique_bag:
            self.selected_backpack_item = None
            return await self.send_inventory_window(inter)

        u_data = unique_bag[u_id]
        template_id = u_data.get("template", u_id)
        item_template = items_lib.get(template_id, {})
        
        item_type = u_data.get("type") or item_template.get("type")
        name = u_data.get("username") or item_template.get("name", template_id)

        # Каноничный SLOT_MAPPING с правильными ID слотов
        SLOT_MAPPING = {
            "anomaly_detector": "detector_anomaly_slot",
            "artefact_detector": "detector_artefact_slot",
            "head_eyes": "eyes_slot",
            "head_ears": "ears_slot",
            "weapon": "weapon_slot",       
            "melee_weapon": "melee_slot",   
            "armor": "armor_slot",         
            "head_armor": "head_slot",     
            "head_mask": "mask_slot"       
        }

        if item_type not in SLOT_MAPPING:
            return await inter.response.send_message("❌ Этот тип предметов нельзя экипировать в активные слоты!", ephemeral=True)

        target_slot = SLOT_MAPPING[item_type]
        old_equipped_uid = eq_slots.get(target_slot)

        if old_equipped_uid == u_id:
            return await inter.response.send_message("🔹 Этот предмет уже экипирован на вашем персонаже!", ephemeral=True)

        # Читаем чарлист персонажа и подгружаем библиотеку эффектов
        async with aiofiles.open(stats_path, "r", encoding="utf-8") as f:
            skills_data = json.loads(await f.read())
            
        effects_lib = {}
        if os.path.exists(effects_lib_path):
            async with aiofiles.open(effects_lib_path, "r", encoding="utf-8") as f:
                effects_lib = json.loads(await f.read())
                
        source = skills_data[0] # Мета-блок параметров
        if "buffs" not in source: source["buffs"] = []
        if "debuffs" not in source: source["debuffs"] = []

        log_details = []

        # 2. ШАГ А: СНЯТИЕ СТАРОЙ ВЕЩИ И ОЧИСТКА ЕЁ ЭФФЕКТОВ
        if old_equipped_uid:
            old_u_data = unique_bag.get(old_equipped_uid, {})
            old_template_id = old_u_data.get("template", old_equipped_uid)
            old_template = items_lib.get(old_template_id, {})
            old_name = old_u_data.get("username") or old_template.get("name", old_template_id)
            
            log_details.append(f"🔄 Снят предмет: **{old_name}** (возвращен в рюкзак).")
            
            # Чистим долгосрочные эффекты, которые давал старый прибор
            old_long_effects = old_template.get("long_effects", {})
            if "add" in old_long_effects:
                old_add_targets = old_long_effects["add"]
                if isinstance(old_add_targets, str): old_add_targets = [old_add_targets]
                
                for eff_id in old_add_targets:
                    if eff_id in source["buffs"]: source["buffs"].remove(eff_id)
                    if eff_id in source["debuffs"]: source["debuffs"].remove(eff_id)
                    
                    eff_name = effects_lib.get(eff_id, {}).get("name", eff_id)
                    log_details.append(f"❌  Удален эффект прибора: `[ {eff_name} ]`")

        # 3. ШАГ Б: НАЛОЖЕНИЕ ЭФФЕКТОВ НОВОГО ПРЕДМЕТА (long_effects -> add)
        new_long_effects = item_template.get("long_effects", {})
        if "add" in new_long_effects:
            new_add_targets = new_long_effects["add"]
            if isinstance(new_add_targets, str): new_add_targets = [new_add_targets]
            
            for eff_id in new_add_targets:
                # Избегаем дублирования эффектов
                if eff_id in source["buffs"] or eff_id in source["debuffs"]:
                    continue
                    
                eff_data = effects_lib.get(eff_id, {})
                eff_name = eff_data.get("name", eff_id)
                is_buff = eff_data.get("type") == "buff"
                
                if is_buff:
                    source["buffs"].append(eff_id)
                    log_details.append(f"🟢  Наложен бафф прибора: `[ {eff_name} ]`")
                else:
                    source["debuffs"].append(eff_id)
                    log_details.append(f"🔴  Наложен дебафф прибора: `[ {eff_name} ]`")

        # 4. ФИЗИЧЕСКАЯ УСТАНОВКА В СЛОТ И СОХРАНЕНИЕ ХАРАКТЕРИСТИК
        eq_slots[target_slot] = u_id
        log_details.append(f"📟 Экипирован прибор: **{name}** в слот `{target_slot}`.")

        # Сохраняем обновленный чарлист персонажа
        async with aiofiles.open(stats_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))

        # Сохраняем обновленный инвентарь (equipment)
        with open(self.inventory_path, "w", encoding="utf-8") as f:
            json.dump(inv_data, f, indent=4, ensure_ascii=False)

        # 5. ПРИНУДИТЕЛЬНАЯ СИНХРОНИЗАЦИЯ ВЕСА И ДЕБАФФОВ НАГРУЗКИ
        await sync_character_weight_and_effects(self.folder_path)

        # 6. ВЫВОД БЕСШОВНОГО СТАТУСА УСПЕХА В РЮКЗАК
        self.backpack_notification = "⚙️ **Изменение экипировки персонажа:**\n" + "\n".join(log_details)

        # Сбрасываем фокус осмотра предмета и красиво возвращаем сталкера к общему списку рюкзака
        self.selected_backpack_item = None
        await self.send_inventory_window(inter)

    async def btn_use_consumable_callback(self, inter: disnake.MessageInteraction):
        """Ролевой движок использования медицины и еды (d6, пулы, оверхил + long_effects)"""
        if inter.author.id != self.interactor_id: return

        inv_data = await self.load_json_file(self.inventory_path)
        items_lib = await self.load_json_file(self.items_lib_path)
        
        stats_path = os.path.join(self.folder_path, "char_stats.json")
        effects_lib_path = "chars_data/effects_lib.json" # Путь к базе эффектов

        static_bag = inv_data.get("inventory", {}).get("static", {})
        item_id = self.selected_backpack_item

        if item_id not in static_bag or static_bag[item_id] <= 0:
            self.selected_backpack_item = None
            return await self.send_inventory_window(inter)

        item_template = items_lib.get(item_id, {})
        use_effects = item_template.get("use_effects", {})
        long_effects = item_template.get("long_effects", {}) # Подгружаем долгосрочные эффекты
        name = item_template.get("name", item_id)

        # Читаем чарлист и подгружаем библиотеку эффектов
        async with aiofiles.open(stats_path, "r", encoding="utf-8") as f:
            skills_data = json.loads(await f.read())
            
        effects_lib = {}
        if os.path.exists(effects_lib_path):
            async with aiofiles.open(effects_lib_path, "r", encoding="utf-8") as f:
                effects_lib = json.loads(await f.read())
        
        source = skills_data[0] # Мета-блок параметров

        # --- ДИНАМИЧЕСКИЙ РАСЧЕТ МАКСИМУМОВ ПУЛОВ ---
        body_value = body_modificator = int_value = int_modificator = 0
        for group in skills_data[1:7]:
            group_info = group.get("skill_group")
            if group_info:
                g_id = group_info[0]
                if g_id == "body":
                    body_value = int(group_info[2]); body_modificator = int(group_info[3])
                elif g_id == "intellect":
                    int_value = int(group_info[2]); int_modificator = int(group_info[3])
                    
        body_value += body_modificator
        int_value += int_modificator

        def get_skill_fp(data, s_id):
            for g in data[1:7]:
                if s_id in g: return g[s_id][1] if isinstance(g[s_id], list) and len(g[s_id]) >= 2 else 0
            return 0
            
        from charlists import calculate_skill_level
        skill_persistence_fp = get_skill_fp(skills_data, "skill_persistence")
        skill_persistence_level = calculate_skill_level(skill_persistence_fp)

        max_heal = body_value * 5 + 15 + skill_persistence_level + source.get("heal_points", [0, 0])[1]
        max_mental = int_value * 5 + 15 + source.get("mental_points", [0, 0])[1]
        max_radiation = body_value * 5 + 15 + source.get("radiation_points", [0, 0])[1]

        # --- МАТЕМАТИКА БРОСКА КУБИКОВ d6 ---
        import random
        def roll_pool_effect(effect_array):
            if not isinstance(effect_array, list) or len(effect_array) < 2: return 0
            d6_count = effect_array[0]
            strict_mod = effect_array[1]
            total_rolled = 0
            rolled_log = []
            
            if d6_count > 0:
                for _ in range(d6_count):
                    roll = random.randint(1, 6)
                    total_rolled += roll
                    rolled_log.append(str(roll))
            
            final_value = total_rolled + strict_mod
            log_str = f"({'+'.join(rolled_log)})" if rolled_log else ""
            if strict_mod != 0:
                log_str += f"{'+' if strict_mod > 0 and log_str else ''}{strict_mod}"
            return final_value, log_str if log_str else f"{final_value}"

        changelog = []

        # --- 1. ПРИМЕНЕНИЕ ЭФФЕКТОВ НА ПУЛЫ ---
        if "add_hp" in use_effects:
            hp_change, hp_log = roll_pool_effect(use_effects["add_hp"])
            old_hp = source.setdefault("heal_points", [0, 0])[0]
            new_hp = min(max_heal, old_hp + hp_change)
            source["heal_points"][0] = new_hp
            changelog.append(f"❤️ **Здоровье:** `+{new_hp - old_hp}` [{hp_log}] ➔ `{new_hp}/{max_heal}`")

        if "add_mp" in use_effects:
            mp_change, mp_log = roll_pool_effect(use_effects["add_mp"])
            old_mp = source.setdefault("mental_points", [0, 0])[0]
            new_mp = min(max_mental, old_mp + mp_change)
            source["mental_points"][0] = new_mp
            changelog.append(f"🧠 **Психика:** `+{new_mp - old_mp}` [{mp_log}] ➔ `{new_mp}/{max_mental}`")

        if "add_rp" in use_effects:
            rp_change, rp_log = roll_pool_effect(use_effects["add_rp"])
            old_rp = source.setdefault("radiation_points", [0, 0])[0]
            new_rp = max(0, old_rp - rp_change)
            source["radiation_points"][0] = new_rp
            changelog.append(f"☢️ **Радиация:** `-{old_rp - new_rp}` [{rp_log}] ➔ `{new_rp}/{max_radiation}`")

        # --- 2. ОБРАБОТКА LONG_EFFECTS (ДОБАВЛЕНИЕ / ИЗЪЯТИЕ СТАТУСОВ) ---
        if "buffs" not in source: source["buffs"] = []
        if "debuffs" not in source: source["debuffs"] = []

        # А. Снятие эффектов (remove)
        if "remove" in long_effects:
            # Приводим к списку на случай, если там одна строка или массив строк
            rem_targets = long_effects["remove"]
            if isinstance(rem_targets, str): rem_targets = [rem_targets]
            
            for effect_id in rem_targets:
                removed_flag = False
                if effect_id in source["buffs"]:
                    source["buffs"].remove(effect_id)
                    removed_flag = True
                if effect_id in source["debuffs"]:
                    source["debuffs"].remove(effect_id)
                    removed_flag = True
                
                if removed_flag:
                    # Ищем красивое название эффекта в библиотеке
                    eff_name = effects_lib.get(effect_id, {}).get("name", effect_id)
                    changelog.append(f"✨ **Снят эффект:** `[ {eff_name} ]`")

        # Б. Наложение эффектов (add)
        if "add" in long_effects:
            add_targets = long_effects["add"]
            if isinstance(add_targets, str): add_targets = [add_targets]
            
            for effect_id in add_targets:
                # Проверяем, нет ли уже такого эффекта на персонаже
                if effect_id in source["buffs"] or effect_id in source["debuffs"]:
                    continue
                
                # Заглядываем в effects_lib, чтобы понять, куда слать эффект: в баффы или дебаффы
                eff_data = effects_lib.get(effect_id, {})
                eff_name = eff_data.get("name", effect_id)
                
                # Твоя система: если тип эффекта "buff" (или определяем по структуре), пушим в buffs, иначе в debuffs
                # Если в библиотеке эффектов нет четкого типа, дебаффом у нас по умолчанию считается всё, что вешает штрафы
                is_buff = eff_data.get("type") == "positive"
                
                if is_buff:
                    source["buffs"].append(effect_id)
                    changelog.append(f"🟢 **Получен бафф:** `[ {eff_name} ]`")
                else:
                    source["debuffs"].append(effect_id)
                    changelog.append(f"🔴 **Получен дебафф:** `[ {eff_name} ]`")

        # --- 3. СОХРАНЕНИЕ ДАННЫХ И СУБ-ВЫЗОВЫ ---
        async with aiofiles.open(stats_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))

        # Удаляем 1 ед. расходника из рюкзака
        from inventory import remove_item_from_inventory
        await remove_item_from_inventory(self.folder_path, item_id, amount=1)

        # Выводим отчет в рюкзак
        effects_summary = "\n".join(changelog) if changelog else "• *Особых изменений пулов и статусов нет*"
        self.backpack_notification = (
            f"💊 **Вы использовали предмет:** **{name}**.\n"
            f"📊 **Изменения состояния персонажа:**\n{effects_summary}"
        )

        self.selected_backpack_item = None
        await self.send_inventory_window(inter)

class DropStaticCountModal(disnake.ui.Modal):
    def __init__(self, inventory_view, item_id, item_name, max_amount):
        self.inventory_view = inventory_view
        self.item_id = item_id
        self.item_name = item_name
        self.max_amount = max_amount

        components = [
            disnake.ui.TextInput(
                label=f"Сколько скинуть? (Доступно: {max_amount})",
                placeholder="Введите целое число...",
                custom_id="drop_amount",
                min_length=1,
                max_length=10,
                required=True
            )
        ]
        super().__init__(title="Выбросить предметы", custom_id=f"drop_static_{item_id}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        raw_count = inter.text_values["drop_amount"].strip()
        
        try:
            count_to_drop = int(raw_count)
            if count_to_drop <= 0: 
                raise ValueError
        except ValueError:
            return await inter.response.send_message("❌ Некорректное количество предметов!", ephemeral=True)

        if count_to_drop > self.max_amount:
            return await inter.response.send_message("❌ У вас нет такого количества предметов в рюкзаке!", ephemeral=True)

        # Вызываем функцию удаления прямо из модалки
        from inventory import remove_item_from_inventory
        success = await remove_item_from_inventory(self.inventory_view.folder_path, self.item_id, amount=count_to_drop)
        
        if success:
            # Задаем уведомление для рюкзака
            self.inventory_view.backpack_notification = f"⚠️ **Вещи выброшены:** Вы скинули на землю **{self.item_name}** — `{count_to_drop} шт.`"
        
        # Сбрасываем выбранный предмет и красиво возвращаем игрока в рюкзак
        self.inventory_view.selected_backpack_item = None
        await self.inventory_view.send_inventory_window(inter)

# ============================================ МАГАЗИН =============================

class UniversalNPCShopView(disnake.ui.View):
    def __init__(self, user_id: int, character_path: str, items_lib: dict):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.character_path = character_path
        self.items_lib = items_lib
        
        # Состояния интерфейса магазина
        self.filter_category = "all"
        self.selected_shop_item = None
        self.shop_page = 1
        
        self.stats_path = os.path.join(character_path, "char_stats.json")
        self.inventory_path = os.path.join(character_path, "char_inventory.json")

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это меню вызвано другим сталкером.", ephemeral=True)
            return False
        return True

    async def send_shop_window(self, inter: disnake.Interaction):
        self.clear_items()

        # 1. Загружаем баланс кошелька из char_stats.json
        try:
            async with aiofiles.open(self.stats_path, "r", encoding="utf-8") as f:
                char_stats = json.loads(await f.read())
            current_rubles = char_stats[0].get("rubles", 0)
            char_name = char_stats[0].get("char_name", "Сталкер")
        except:
            return await inter.response.send_message("❌ Ошибка чтения данных персонажа. Проверьте чарлист.", ephemeral=True)

        # 2. Фильтруем ассортимент по укрупненным ролевым категориям
        filtered_shop_items = []
        for item_id, data in self.items_lib.items():
            i_type = data.get("type", "narrative")
            item_category = ITEM_TYPE_TO_CATEGORY.get(i_type, "craft_narrative")
            
            if self.filter_category != "all" and item_category != self.filter_category:
                continue
                
            filtered_shop_items.append((item_id, data))

        # Сортируем по названию для удобства
        filtered_shop_items.sort(key=lambda x: x[1].get("name", x[0]))

        # 3. Настраиваем пагинацию (по 25 товаров, чтобы не сломать селектор Дискорда!)
        items_per_page = 25
        total_items = len(filtered_shop_items)
        max_pages = (total_items - 1) // items_per_page + 1 if total_items > 0 else 1
        
        if self.shop_page > max_pages: 
            self.shop_page = max_pages
            
        start_idx = (self.shop_page - 1) * items_per_page
        page_items = filtered_shop_items[start_idx : start_idx + items_per_page]

        # 4. Рендерим красивый прайс-лист в add_field по твоей блочной схеме
        readable_filter = BACKPACK_CATEGORIES.get(self.filter_category, "Все товары")
        
        notification_text = ""
        if hasattr(self, "purchase_notification") and self.purchase_notification:
            notification_text = f"{self.purchase_notification}\n\n"
            self.purchase_notification = None # Сразу стираем, чтобы не висело при следующем перелистывании страницы

        embed = disnake.Embed(
            title=f"🏪 Торговец — Магазин Зоны",
            description=f"{notification_text}" # Выводим плашку успеха на самый верх описания
                        f"Клиент: **{char_name}** | Баланс: `{current_rubles} RU`\n"
                        f"Категория товаров: `*{readable_filter}*`\n\n"
                        f"Выберите интересующий товар в меню пониже, чтобы оформить покупку.",
            color=disnake.Color.red()
        )

        if page_items:
            price_list_1 = []
            price_list_2 = []
            
            for idx, (item_id, data) in enumerate(page_items):
                name = data.get("name", item_id)
                price = data.get("base_price", 1000)
                mult = data.get("count_multiply", 1)
                
                # Формируем компактную строчку прайса
                mult_str = f" (пачка x{mult})" if mult > 1 else ""
                item_line = f"• **{name}**{mult_str} — `{price} RU`"
                
                if idx < 13:
                    price_list_1.append(item_line)
                else:
                    price_list_2.append(item_line)

            if price_list_1: embed.add_field(name="📋 Прейскурант (Часть I)", value="\n".join(price_list_1), inline=False)
            if price_list_2: embed.add_field(name="📋 Прейскурант (Часть II)", value="\n".join(price_list_2), inline=False)
        else:
            embed.description += "\n\n*У торговца нет товаров в данной категории.*"

        embed.set_footer(text=f"Страница {self.shop_page}/{max_pages} | Всего позиций: {total_items} | © By Bon Shinomiya")

        # --- СЕЛЕКТОР КАТЕГОРИЙ (Твоя укрупненная сортировка) ---
        filter_options = [
            disnake.SelectOption(label="Все категории", value="all", emoji="🎒"),
            disnake.SelectOption(label="Оружие и ножи", value="weaponry", emoji="🔫"),
            disnake.SelectOption(label="Боеприпасы и гранаты", value="ammo_grenades", emoji="📦"),
            disnake.SelectOption(label="Медицина и провизия", value="medicine_food", emoji="💉"),
            disnake.SelectOption(label="Костюмы и шлемы", value="armor_suits", emoji="👕"),
            disnake.SelectOption(label="Модификации брони", value="armor_mods", emoji="🛠️"),
            disnake.SelectOption(label="Защитные плиты / Накладки", value="protection_elements", emoji="🛡️"),
            disnake.SelectOption(label="Детекторы и приборы", value="electronics", emoji="📟"),
            disnake.SelectOption(label="Крафт / Трофеи / Нарратив", value="craft_narrative", emoji="🧬")
        ]
        
        filter_select = disnake.ui.Select(placeholder="Выбрать другую категорию товаров...", options=filter_options, custom_id="shop_filter_select", row=2)
        async def filter_cb(i: disnake.MessageInteraction):
            self.filter_category = i.values[0]; self.shop_page = 1; self.selected_shop_item = None; await self.send_shop_window(i)
        filter_select.callback = filter_cb
        self.add_item(filter_select)

        # --- СЕЛЕКТОР ВЫБОРА ТОВАРА ДЛЯ ПОКУПКИ (Строго до 25 элементов) ---
        buy_options = []
        for item_id, data in page_items:
            name = data.get("name", item_id)
            price = data.get("base_price", 1000)
            buy_options.append(disnake.SelectOption(label=name[:50], value=item_id, description=f"Цена: {price} RU"))

        if buy_options:
            buy_select = disnake.ui.Select(placeholder="Выберите товар для покупки...", options=buy_options, custom_id="shop_buy_select", row=3)
            async def buy_select_cb(i: disnake.MessageInteraction):
                self.selected_shop_item = i.values[0]; await self.send_shop_window(i)
            buy_select.callback = buy_select_cb
            self.add_item(buy_select)

            # Если товар выбран — выкатываем кнопку «Купить»
            if self.selected_shop_item:
                btn_buy = disnake.ui.Button(label="Подтвердить покупку", style=disnake.ButtonStyle.red, custom_id="btn_confirm_buy", row=4)
                btn_buy.callback = self.btn_confirm_buy_callback
                self.add_item(btn_buy)

        # Кнопки страниц (стрелочки)
        if max_pages > 1:
            btn_prev = disnake.ui.Button(label="⬅️", style=disnake.ButtonStyle.red, disabled=(self.shop_page <= 1), row=4 if self.selected_shop_item else 3)
            btn_next = disnake.ui.Button(label="➡️", style=disnake.ButtonStyle.red, disabled=(self.shop_page >= max_pages), row=4 if self.selected_shop_item else 3)
            async def p_cb(i: disnake.MessageInteraction): self.shop_page -= 1; await self.send_shop_window(i)
            async def n_cb(i: disnake.MessageInteraction): self.shop_page += 1; await self.send_shop_window(i)
            btn_prev.callback = p_cb; btn_next.callback = n_cb
            self.add_item(btn_prev); self.add_item(btn_next)

        # Рендерим изменения
        if inter.response.is_done(): 
            await inter.edit_original_response(content=None, embed=embed, view=self)
        else:
            # Если это клик по кнопке/селектору ИЛИ отправка модалки — бесшовно редактируем старое сообщение!
            if isinstance(inter, (disnake.MessageInteraction, disnake.ModalInteraction)):
                await inter.response.edit_message(content=None, embed=embed, view=self)
            else:
                # Если это первый вызов слэш-команды
                await inter.response.send_message(embed=embed, view=self, ephemeral=True)

    async def btn_confirm_buy_callback(self, inter: disnake.MessageInteraction):
        """Перенаправляет игрока в модальное окно для выбора количества покупаемого товара"""
        item_id = self.selected_shop_item
        item_data = self.items_lib.get(item_id)
        if not item_data: return
        
        base_price = item_data.get("base_price", 1000)
        count_multiply = item_data.get("count_multiply", 1) # Твой параметр из шаблоны.json
        name = item_data.get("name", item_id)

        # Вызываем созданный мини-класс модалки закупки
        await inter.response.send_modal(
            ShopBuyCountModal(
                shop_view=self,
                item_id=item_id,
                item_name=name,
                base_price=base_price,
                count_multiply=count_multiply
            )
        )

class ShopBuyCountModal(disnake.ui.Modal):
    def __init__(self, shop_view, item_id, item_name, base_price, count_multiply):
        self.shop_view = shop_view
        self.item_id = item_id
        self.item_name = item_name
        self.base_price = base_price
        self.count_multiply = count_multiply

        # Настраиваем лаконичное описание для игрока
        pack_info = f" (пачка x{count_multiply})" if count_multiply > 1 else ""
        components = [
            disnake.ui.TextInput(
                label=f"Укажите количество{pack_info}:",
                placeholder="Введите целое число (например: 1, 5, 10)...",
                custom_id="buy_amount",
                min_length=1,
                max_length=5,
                required=True
            )
        ]
        super().__init__(title=f"Закупка: {item_name[:20]}", custom_id=f"shop_buy_{item_id}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        raw_count = inter.text_values["buy_amount"].strip()
        
        try:
            buy_units = int(raw_count)
            if buy_units <= 0: 
                raise ValueError
        except ValueError:
            return await inter.response.send_message("❌ Некорректное количество для покупки!", ephemeral=True)

        # Математика стоимости и начисления
        total_price = self.base_price * buy_units
        actual_items_to_give = buy_units * self.count_multiply

        async with get_char_lock(self.shop_view.character_path):
            # Проверяем кошелёк сталкера
            async with aiofiles.open(self.shop_view.stats_path, "r", encoding="utf-8") as f:
                char_stats = json.loads(await f.read())
            
            current_rubles = char_stats[0].get("rubles", 0)
            if current_rubles < total_price:
                return await inter.response.send_message(
                    f"❌ Недостаточно средств! У вас `{current_rubles} RU`, а закупка `{buy_units} шт.` стоит `{total_price} RU`.", 
                    ephemeral=True
                )

            # Проводим транзакцию
            char_stats[0]["rubles"] = current_rubles - total_price

            async with aiofiles.open(self.shop_view.stats_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(char_stats, ensure_ascii=False, indent=4))

        # Выдаем хабар в рюкзак (автоматически пересчитает вес и дебаффы!)
        from inventory import add_item_to_inventory
        await add_item_to_inventory(self.shop_view.character_path, self.item_id, self.shop_view.items_lib, amount=actual_items_to_give)

        # Записываем плашку успеха в родительский View магазина
        mult_str = f" (всего {actual_items_to_give} шт.)" if self.count_multiply > 1 else ""
        self.shop_view.purchase_notification = (
            f"🟩 **Успешная сделка:** Вы приобрели **{self.item_name}** в количестве `{buy_units} шт.`{mult_str} за `{total_price} RU`!"
        )
        
        self.shop_view.selected_shop_item = None
        await self.shop_view.send_shop_window(inter)

class GMArmorModificationMenu(disnake.ui.View):
    """Игровой верстак для кастомизации, установки и демонтажа модулей брони из рюкзака игрока"""
    def __init__(self, inventory_view):
        super().__init__(timeout=600)
        self.inv_view = inventory_view
        self.selected_op = None

    async def send_menu(self, inter: disnake.Interaction):
        self.clear_items()
        
        # Перечитываем файлы жестко при каждом открытии меню верстака
        inv_data = await self.inv_view.load_json_file(self.inv_view.inventory_path)
        items_lib = await self.inv_view.load_json_file(self.inv_view.items_lib_path)
        unique_bag = inv_data.get("inventory", {}).get("unique", {})
        u_id = self.inv_view.selected_backpack_item
        
        if u_id not in unique_bag:
            return await inter.response.send_message("❌ Ошибка контекста предмета.", ephemeral=True)
            
        u_data = unique_bag[u_id]
        
        # Блок определения человеческого имени Бронеплиты
        plate_status = "*Пусто*"
        if u_data.get("plate"):
            p_uid = u_data.get("plate")
            p_card = unique_bag.get(p_uid, {})
            p_template = p_card.get("template", p_uid)
            p_name = p_card.get("username") or items_lib.get(p_template, {}).get("name", p_template)
            plate_status = f"**{p_name}** `({u_data['armor_points'][0]}/{u_data['armor_points'][1]} ПБ)`"
            
        # Блок определения человеческого имени Защиты конечностей
        layer_status = "*Пусто*"
        if u_data.get("additional_armor"):
            l_uid = u_data.get("additional_armor")
            l_card = unique_bag.get(l_uid, {})
            l_template = l_card.get("template", l_uid)
            l_name = l_card.get("username") or items_lib.get(l_template, {}).get("name", l_template)
            layer_status = f"**{l_name}** `({u_data['additional_armor_points'][0]}/{u_data['additional_armor_points'][1]} ПБ)`"
        
        # Собираем списки текущих модов для вывода в инфо-окно верстака
        setup_mods = u_data.get("setup_mods", [])
        readable_mods = [items_lib.get(m, {}).get('name', m) for m in setup_mods] if setup_mods else ["нет"]
        
        setup_anom = u_data.get("setup_anomaly_mods", [])
        readable_anom = [items_lib.get(m, {}).get('name', m) for m in setup_anom] if setup_anom else ["нет"]

        info = (
            f"🛠️ **Ремонтный верстак снаряжения**\n"
            f"Модифицируем: **{u_data.get('username')}**\n"
            f"Свободных ячеек ДАЗ: `{u_data.get('anomaly_mods', 0)}`\n\n"
            f"⚙️ **Текущая сборка костюма:**\n"
            f"• Бронеплита: {plate_status}\n"
            f"• Защита конечностей: {layer_status}\n"
            f"• Навесные модификации: *{', '.join(readable_mods)}*\n"
            f"• Аномальные моды: *{', '.join(readable_anom)}*\n\n"
            f"Выберите операцию под кодом. Демонтированные элементы честно вернутся к вам в рюкзак!"
        )
        embed = disnake.Embed(title="🔧 Верстак: Модернизация комбинезона", description=info, color=disnake.Color.red())
        
        # ИСПРАВЛЕНО: Добавлены опции снятия навесов и аномальных обшивок
        options = [
            disnake.SelectOption(label="Переименовать костюм (РП)", value="username", emoji="📝"),
            disnake.SelectOption(label="Изменить описание костюма (РП)", value="userdesc", emoji="✍️"),
            disnake.SelectOption(label="Изменить нашивку/внешний вид (URL)", value="userpicture", emoji="🖼️"),
            disnake.SelectOption(label="🎴 Установить бронеплиту из рюкзака", value="install_plate"),
            disnake.SelectOption(label="🎴 Снять установленную бронеплиту", value="remove_plate"),
            disnake.SelectOption(label="🦾 Установить защиту конечностей", value="install_layer"),
            disnake.SelectOption(label="🦾 Снять защиту конечностей", value="remove_layer"),
            disnake.SelectOption(label="🛠️ Навесить модификацию костюма", value="install_mod"),
            disnake.SelectOption(label="🛠️ Демонтировать модификацию в рюкзак", value="remove_mod"),
            disnake.SelectOption(label="🧬 Навесить аномальную обшивку", value="install_anom"),
            disnake.SelectOption(label="🧬 Демонтировать аномальную обшивку", value="remove_anom")
        ]
        
        select = disnake.ui.Select(placeholder="Что планируете сделать?...", options=options, custom_id="player_armor_op_select")
        
        async def select_cb(i: disnake.MessageInteraction):
            self.selected_op = i.values[0]
            await i.response.defer()
        select.callback = select_cb
        self.add_item(select)
        
        btn_action = disnake.ui.Button(label="Приступить к работе", style=disnake.ButtonStyle.red, row=1)
        btn_back = disnake.ui.Button(label="🔙 Назад к осмотру", style=disnake.ButtonStyle.red, row=1)
        
        async def btn_action_cb(i: disnake.MessageInteraction):
            if not self.selected_op:
                return await i.response.send_message("❌ Сначала выберите тип работ в списке!", ephemeral=True)
                
            # Снятие жестких слотов (Плита и Кожа)
            if self.selected_op == "remove_plate":
                return await self.handle_demount_component(i, "plate")
            elif self.selected_op == "remove_layer":
                return await self.handle_demount_component(i, "additional_armor")
                
            # ИСПРАВЛЕНО: Перенаправление на динамические селекторы снятия навесных элементов
            elif self.selected_op in ["remove_mod", "remove_anom"]:
                return await self.open_installed_mods_selector(i)
                
            # Текстовые модалки
            if self.selected_op in ["username", "userdesc", "userpicture"]:
                await i.response.send_modal(GMArmorInputModal(self))
            else:
                # Установка элементов из рюкзака
                await self.open_backpack_material_selector(i)
            
        async def btn_back_cb(i: disnake.MessageInteraction):
            await self.inv_view.send_item_context_menu(i)
            
        btn_action.callback = btn_action_cb; btn_back.callback = btn_back_cb
        self.add_item(btn_action); self.add_item(btn_back)
        
        if inter.response.is_done(): await inter.edit_original_response(embed=embed, view=self)
        else: await inter.response.edit_message(embed=embed, view=self)

    # Движок демонтажа жестких компонентов (плиты, конечности)
    async def handle_demount_component(self, inter: disnake.MessageInteraction, slot_key: str):
        inv_data = await self.inv_view.load_json_file(self.inv_view.inventory_path)
        u_id = self.inv_view.selected_backpack_item
        u_data = inv_data["inventory"]["unique"][u_id]
        
        target_item_uid = u_data.get(slot_key)
        if not target_item_uid:
            return await inter.response.send_message("❌ В этом слоте костюма ничего не установлено!", ephemeral=True)
            
        u_data[slot_key] = None
        if slot_key == "plate": u_data["armor_points"] = [0, 0]
        elif slot_key == "additional_armor": u_data["additional_armor_points"] = [0, 0]
            
        with open(self.inv_view.inventory_path, "w", encoding="utf-8") as f:
            json.dump(inv_data, f, indent=4, ensure_ascii=False)
            
        await sync_character_weight_and_effects(self.inv_view.folder_path)
        await self.send_menu(inter)

    # ========================== НОВЫЙ МЕТОД: СЕЛЕКТОР СНЯТИЯ УСТАНОВЛЕННЫХ НАВЕСОВ ==========================
    async def open_installed_mods_selector(self, inter: disnake.MessageInteraction):
        """Сканирует костюм и выводит выпадающий список установленных модов для их поштучного извлечения"""
        self.clear_items()
        inv_data = await self.inv_view.load_json_file(self.inv_view.inventory_path)
        items_lib = await self.inv_view.load_json_file(self.inv_view.items_lib_path)
        u_id = self.inv_view.selected_backpack_item
        u_data = inv_data["inventory"]["unique"][u_id]

        # Определяем, какой массив чистим в зависимости от выбранного пункта
        is_anomaly_op = (self.selected_op == "remove_anom")
        target_array_key = "setup_anomaly_mods" if is_anomaly_op else "setup_mods"
        installed_list = u_data.get(target_array_key, [])

        if not installed_list:
            btn_back = disnake.ui.Button(label="🔙 Назад на верстак", style=disnake.ButtonStyle.red)
            btn_back.callback = self.send_menu
            self.add_item(btn_back)
            msg = "❌ На этом костюме не обнаружено установленных аномальных обшивок!" if is_anomaly_op else "❌ На этом костюме нет установленных навесных модификаций!"
            embed = disnake.Embed(title="Верстак: Нечего снимать", description=msg, color=disnake.Color.red())
            return await inter.response.edit_message(embed=embed, view=self)

        # Собираем опции для селектора.
        # Так как моды хранятся как технические строки шаблонов (например, 'passive_exo'),
        # мы выводим их понятные имена, а в value передаем ИНДЕКС элемента в массиве,
        # чтобы корректно удалить конкретную вещь, если установлено несколько одинаковых!
        options = []
        for idx, template_id in enumerate(installed_list):
            m_name = items_lib.get(template_id, {}).get("name", template_id)
            options.append(disnake.SelectOption(label=f"{m_name} (Слот #{idx+1})", value=str(idx)))

        embed = disnake.Embed(
            title="🔧 Демонтаж компонентов", 
            description="Выберите из списка ниже установленный модуль, который техник должен снять и вернуть вам в рюкзак:", 
            color=disnake.Color.red()
        )
        
        demount_select = disnake.ui.Select(placeholder="Какой модуль снимаем?...", options=options[:25])

        # КОЛЛБЭК БЕЗОПАСНОГО ИЗВЛЕЧЕНИЯ И ВОЗВРАТА В РЮКЗАК
        async def demount_select_cb(i: disnake.MessageInteraction):
            target_idx = int(i.values[0])
            
            # Перечитываем базу
            inv_data_fresh = await self.inv_view.load_json_file(self.inv_view.inventory_path)
            items_lib_fresh = await self.inv_view.load_json_file(self.inv_view.items_lib_path)
            
            fresh_armor = inv_data_fresh["inventory"]["unique"][u_id]
            fresh_array = fresh_armor.get(target_array_key, [])
            
            if target_idx >= len(fresh_array):
                return await i.response.send_message("❌ Ошибка синхронизации данных верстака.", ephemeral=True)

            # Вырезаем технический ID шаблона из куклы брони
            removed_template_id = fresh_array.pop(target_idx)
            
            # Если это был аномальный модуль — возвращаем поглощенные им очки ДАЗ основы комбинезона!
            if is_anomaly_op:
                mod_req_daz = items_lib_fresh.get(removed_template_id, {}).get("anomaly_mod_req", 1)
                fresh_armor["anomaly_mods"] = fresh_armor.get("anomaly_mods", 6) + mod_req_daz

            with open(self.inv_view.inventory_path, "w", encoding="utf-8") as f:
                json.dump(inv_data_fresh, f, indent=4, ensure_ascii=False)

            # Честно воссоздаем этот модуль в рюкзаке игрока как новый уникальный не надетый предмет!
            from inventory import add_item_to_inventory
            await add_item_to_inventory(self.inv_view.folder_path, removed_template_id, items_lib_fresh, amount=1)
            
            # Обновляем верстак
            await self.send_menu(i)

        demount_select.callback = demount_select_cb
        self.add_item(demount_select)
        await inter.response.edit_message(embed=embed, view=self)

    # Селектор материалов из рюкзака (без изменений)
    async def open_backpack_material_selector(self, inter: disnake.MessageInteraction):
        """Сканирует рюкзак игрока (и static, и unique) и выводит селектор подходящих под операцию предметов"""
        self.clear_items()
        inv_data = await self.inv_view.load_json_file(self.inv_view.inventory_path)
        items_lib = await self.inv_view.load_json_file(self.inv_view.items_lib_path)
        
        static_bag = inv_data.get("inventory", {}).get("static", {})
        unique_bag = inv_data.get("inventory", {}).get("unique", {})
        equipped_u_ids = set(inv_data.get("equipment", {}).values())
        current_armor_uid = self.inv_view.selected_backpack_item
        
        OP_MAPPING = {
            "install_plate": "armor_plate",
            "install_layer": "add_armor",
            "install_mod": "mounted_mod",
            "install_anom": "anomaly_mod"
        }
        target_type = OP_MAPPING[self.selected_op]
        
        options = []

        # СЦЕНАРИЙ 1: Ищем в стакающихся предметах (медицина, патроны, расходные моды)
        for item_id, amount in static_bag.items():
            if amount <= 0: continue
            item_template = items_lib.get(item_id, {})
            if item_template.get("type") == target_type:
                options.append(disnake.SelectOption(
                    label=f"📦 {item_template.get('name', item_id)} — ({amount} шт.)", 
                    value=f"static_{item_id}"  # Маркируем, что это стак
                ))

        # СЦЕНАРИЙ 2: Ищем в уникальных штучных предметах (плиты, модули)
        for u_id, u_card in unique_bag.items():
            if u_id == current_armor_uid or u_id in equipped_u_ids: continue
            
            i_type = u_card.get("type") or items_lib.get(u_card.get("template"), {}).get("type")
            if i_type == target_type:
                options.append(disnake.SelectOption(
                    label=f"🔺 {u_card['username'][:40]}", 
                    value=f"unique_{u_id}"  # Маркируем, что это уникалка
                ))
                
        if not options:
            btn_back = disnake.ui.Button(label="🔙 Назад на верстак", style=disnake.ButtonStyle.red)
            btn_back.callback = self.send_menu
            self.add_item(btn_back)
            msg = f"❌ В вашем рюкзаке не найдено подходящих компонентов!"
            embed = disnake.Embed(title="Верстак: Нечего устанавливать", description=msg, color=disnake.Color.red())
            return await inter.response.edit_message(embed=embed, view=self)

        embed = disnake.Embed(title="🔧 Выберите деталь из рюкзака", description="Ниже выведены все подходящие модули, находящиеся в вашей сумке. Выберите один для монтажа:", color=disnake.Color.red())
        
        material_select = disnake.ui.Select(placeholder="Какую деталь ставим?...", options=options[:25])
        
        # ВНУТРЕННИЙ ОБРАБОТЧИК МОНТАЖА
        async def material_select_cb(i: disnake.MessageInteraction):
            raw_choice = i.values[0]
            choice_type, target_id = raw_choice.split("_", 1) # Разделяем префикс и реальный ID
            
            inv_data_fresh = await self.inv_view.load_json_file(self.inv_view.inventory_path)
            items_lib_fresh = await self.inv_view.load_json_file(self.inv_view.items_lib_path)
            armor_card = inv_data_fresh["inventory"]["unique"][current_armor_uid]
            
            # Определяем шаблон и карточку в зависимости от того, откуда берем предмет
            if choice_type == "static":
                mat_template = items_lib_fresh.get(target_id, {})
                template_id = target_id
            else:
                material_card = inv_data_fresh["inventory"]["unique"][target_id]
                template_id = material_card.get("template", "")
                mat_template = items_lib_fresh.get(template_id, {})
            
            # --- ВЫПОЛНЕНИЕ ОПЕРАЦИЙ ---
            if self.selected_op == "install_plate":
                if armor_card.get("plate"): return await i.response.send_message("❌ В костюме уже стоит плита!", ephemeral=True)
                if choice_type == "static": return await i.response.send_message("❌ Плиты не могут быть складываемыми предметами!", ephemeral=True)
                armor_card["plate"] = target_id
                armor_card["armor_points"] = list(inv_data_fresh["inventory"]["unique"][target_id].get("armor_points", [10, 10]))
                
            elif self.selected_op == "install_layer":
                if armor_card.get("additional_armor"): return await i.response.send_message("❌ Модуль конечностей уже установлен!", ephemeral=True)
                if choice_type == "static": return await i.response.send_message("❌ Модули конечностей должны быть уникальными!", ephemeral=True)
                armor_card["additional_armor"] = target_id
                armor_card["additional_armor_points"] = list(inv_data_fresh["inventory"]["unique"][target_id].get("armor_points", [5, 5]))
                
            elif self.selected_op == "install_mod":
                armor_card.setdefault("setup_mods", []).append(template_id)
                # Списываем ресурс
                if choice_type == "static":
                    inv_data_fresh["inventory"]["static"][target_id] -= 1
                    if inv_data_fresh["inventory"]["static"][target_id] <= 0: del inv_data_fresh["inventory"]["static"][target_id]
                else:
                    if target_id in inv_data_fresh["inventory"]["unique"]: del inv_data_fresh["inventory"]["unique"][target_id]
                
            elif self.selected_op == "install_anom":
                req_daz = mat_template.get("anomaly_mod_req", 1)
                current_daz = armor_card.get("anomaly_mods", 6)
                if current_daz < req_daz: return await i.response.send_message(f"❌ Недостаточно ячеек ДАЗ!", ephemeral=True)
                
                armor_card["anomaly_mods"] = current_daz - req_daz
                armor_card.setdefault("setup_anomaly_mods", []).append(template_id)
                
                # Списываем ресурс
                if choice_type == "static":
                    inv_data_fresh["inventory"]["static"][target_id] -= 1
                    if inv_data_fresh["inventory"]["static"][target_id] <= 0: del inv_data_fresh["inventory"]["static"][target_id]
                else:
                    if target_id in inv_data_fresh["inventory"]["unique"]: del inv_data_fresh["inventory"]["unique"][target_id]

            # Сохраняем и обновляем
            with open(self.inv_view.inventory_path, "w", encoding="utf-8") as f:
                json.dump(inv_data_fresh, f, indent=4, ensure_ascii=False)
                
            await sync_character_weight_and_effects(self.inv_view.folder_path)
            await self.send_menu(i)

        material_select.callback = material_select_cb
        self.add_item(material_select)
        await inter.response.edit_message(embed=embed, view=self)
class GMArmorInputModal(disnake.ui.Modal):
    def __init__(self, menu_view):
        self.menu_view = menu_view
        op = menu_view.selected_op
        
        titles = {
            "username": "Кастомное имя костюма (РП)", 
            "userdesc": "Кастомное описание (РП)", 
            "userpicture": "Ссылка на уникальный арт костюма (URL)"
        }
        
        style = disnake.TextInputStyle.paragraph if op == "userdesc" else disnake.TextInputStyle.short
        components = [
            disnake.ui.TextInput(
                label=titles.get(op, "Ввод РП-данных"),
                placeholder="Заполните строчку...",
                custom_id="player_input",
                style=style,
                required=True
            )
        ]
        super().__init__(title="Кастомизация снаряжения", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        raw_val = inter.text_values["player_input"].strip()
        op = self.menu_view.selected_op
        
        inv_data = await self.menu_view.inv_view.load_json_file(self.menu_view.inv_view.inventory_path)
        u_id = self.menu_view.inv_view.selected_backpack_item
        
        inv_data["inventory"]["unique"][u_id][op] = raw_val
        
        with open(self.menu_view.inv_view.inventory_path, "w", encoding="utf-8") as f:
            json.dump(inv_data, f, indent=4, ensure_ascii=False)
            
        await self.menu_view.send_menu(inter)