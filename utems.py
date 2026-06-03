import disnake
import os
import aiofiles
import json

from utils import *

async def create_library_embed(filtered_data, questions_lib, page, max_pages, total_count):
    stat_names = await get_stat_names_map()

    embed = create_embed_bs("Энциклопедия влияющих факторов")
    
    for item in filtered_data.values():
        # 1. Описание и Особенность (БЕЗ ИЗМЕНЕНИЙ)
        description = f"*{item.get('description', 'Описание отсутствует.')}*"
        text_mod = item.get("text_modifier")
        if text_mod:
            description += f"\n\n**Особенность:** {text_mod}"

        # 2. Формируем список технических бонусов (ДОБАВЛЕН ПЕРЕВОД)
        mods = item.get("modifiers", [])
        if mods:
            formatted_mods = []
            for mod in mods:
                # Распаковываем три значения (категорию игнорируем через _)
                _, target_id, mod_value = mod
                
                # Получаем человеческое название из мапы
                friendly_name = stat_names.get(target_id, target_id)
                
                # Форматируем строку: "• Сила: `-2`"
                formatted_mods.append(f"• {friendly_name}: `{mod_value:+}`")
            
            mods_str = "\n".join(formatted_mods)
        else:
            mods_str = None

        # 3. Собираем требования (ДОБАВЛЕН ПЕРЕВОД)
        reqs_list = []
        auto_reqs = item.get("requirements", {})
        if auto_reqs:
            for s_id, val in auto_reqs.items():
                # Заменяем s_id на человеческое название
                friendly_name = stat_names.get(s_id, s_id)
                reqs_list.append(f"{friendly_name} {val}+")
        
        # Б) БИОГРАФИЧЕСКИЕ ТРЕБОВАНИЯ (ДИНАМИЧЕСКИЕ)
        bio_reqs = item.get("biografy_requirements", {})
        if bio_reqs:
            for q_id, required_val in bio_reqs.items():
                q_data = questions_lib.get(str(q_id))
                if q_data:
                    q_title = q_data["question"].replace("?", "").strip()
                    
                    # 1. Приводим required_val к списку, даже если там одно значение
                    # Это универсальный способ обработать и [2, 3], и просто 2
                    target_values = required_val if isinstance(required_val, list) else [required_val]
                    # Переводим всё в строки для надежного сравнения
                    target_values = [str(v) for v in target_values]

                    # 2. Собираем все подходящие названия вариантов
                    found_labels = []
                    for choice in q_data.get("choices", []):
                        if str(choice["value"]) in target_values:
                            found_labels.append(choice["label"])
                    
                    # 3. Формируем итоговую строку (через "/" если вариантов несколько)
                    if found_labels:
                        choice_text = " / ".join(found_labels)
                    else:
                        choice_text = "Неизвестно"
                    
                    reqs_list.append(f"**{q_title}**: {choice_text}")
                else:
                    reqs_list.append(f"Параметр {q_id}: {required_val}")
        
        text_reqs = item.get("text_requirements")
        if text_reqs:
            reqs_list.append(text_reqs)

        # 4. Сборка финального блока (БЕЗ ИЗМЕНЕНИЙ)
        field_value = f"{description}\n"
        
        if mods_str:
            field_value += f"\n**Модификаторы навыков:**\n{mods_str}"
            
        if reqs_list:
            field_value += f"\n**Требования:** *{', '.join(reqs_list)}*"
            
        cost = item.get("cost", 0)
        if cost != 0:
            field_value += f"\n**Стоимость:** `{cost} СО`"

        # Заголовок (ТОЛЬКО ПОЛЬЗОВАТЕЛЬСКОЕ ИМЯ)
        embed.add_field(
            name=f"🔹 {item['name']}",
            value=field_value,
            inline=False
        )

    embed.set_footer(text=f"Страница {page} из {max_pages} | Всего: {total_count}")
    return embed

async def check_biography(file_path, bio_reqs):
    if not bio_reqs:
        return True
    """
    Проверяет, соответствуют ли ответы в биографии требованиям черты.
    bio_reqs: dict вида {"1": [2, 3], "7": [4]} 
    (означает: на вопрос 1 ответил 2 или 3, на вопрос 7 ответил 4)
    """
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            user_data = json.loads(await f.read())
        
        for q_id, req_val in bio_reqs.items():
            # 1. Получаем данные пользователя. 
            # Если там [4], превращаем в список [4]. Если там просто 4, тоже в [4].
            user_val = user_data.get(str(q_id), [])
            if not isinstance(user_val, list):
                user_val = [user_val]
            
            # 2. Получаем требования черты.
            # Если там [2, 3], оставляем. Если просто 2, превращаем в [2].
            if isinstance(req_val, list):
                required_list = req_val
            else:
                required_list = [req_val]

            # 3. ПРОВЕРКА: Есть ли хотя бы одно совпадение?
            # Мы проверяем, пересекаются ли списки того, что ЕСТЬ у юзера, 
            # и того, что ТРЕБУЕТ черта.
            has_match = any(val in required_list for val in user_val)
            
            if not has_match:
                # Если по этому вопросу совпадений нет — черта не подходит
                return False
                
        return True
    except Exception as e:
        print(f"Ошибка в check_biography: {e}")
        return False

async def get_filtered_page(library, trait_type, page, render_type, folder_path=None, items_per_page=5):
    filtered = {}

    # 1. Загружаем и подготавливаем статы
    if render_type == "summon":
        stats_path = f"{folder_path}/char_stats.json" if folder_path else None
        flat_stats = {}
        if stats_path and os.path.exists(stats_path):
            async with aiofiles.open(stats_path, "r", encoding="utf-8") as f:
                full_data = json.loads(await f.read())
                # Превращаем список словарей в один плоский словарь для удобного поиска
                for block in full_data[1:7]:
                    for key, value in block.items():
                        # Пропускаем служебные поля типа char_name
                        if key == "char_name":
                            continue
                        
                        # Извлекаем числовое значение стата/навыка
                        # Если это группа: ["body", "Телосложение", 8, 0] -> берем 8
                        # Если это навык: ["Сила", 5, 0] -> берем 5
                        if isinstance(value, list) and len(value) >= 2:
                            # Для групп навыков (skill_group) значение идет индексом 2
                            if value[0] in ["reaction", "craft", "intellect", "dexterity", "body", "empathy"]:
                                pre = value[2]
                                pre_int = int(pre)
                                flat_stats[value[0]] = pre_int
                            # Для обычных навыков и статов значение обычно индексом 1
                            else:
                                pre = value[1]
                                pre_int = int(pre)
                                flat_stats[key] = calculate_skill_level(pre_int)

    # 2. Основной цикл фильтрации
    for tid, data in library.items():
        if data.get("type") == trait_type and data.get("unique") == "no":
            bio_reqs = data.get("biografy_requirements", {})
            stat_reqs = data.get("requirements", {})

            if render_type == "summon":
                bio_path = f"{folder_path}/short_story.json" if folder_path else None
                # Проверка биографии
                bio_pass = not bio_reqs or (bio_path and await check_biography(bio_path, bio_reqs))

                # Проверка характеристик/навыков
                stats_pass = True
                if stat_reqs:
                    for req_id, req_val in stat_reqs.items():
                        # Сравниваем с нашим плоским словарем
                        current_val = flat_stats.get(req_id, 0)
                        if int(current_val) < int(req_val):
                            stats_pass = False
                            break
                
                if bio_pass and stats_pass:
                    filtered[tid] = data
            else:
                filtered[tid] = data

    # 2. Дальше ваша стандартная логика пагинации
    total_items = len(filtered)
    max_pages = (total_items - 1) // items_per_page + 1 if total_items > 0 else 1
    
    # Срез данных
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    # Превращаем отфильтрованные ключи в список и берем нужный кусок
    page_items = dict(list(filtered.items())[start_idx:end_idx])
    
    return page_items, max_pages, total_items

async def load_bio_questions() -> dict:
    # Загружаем ваш файл вопросов
    async with aiofiles.open("chars_data/questions_lib.json", "r", encoding="utf-8") as f:
        data = json.loads(await f.read())
    
    # Фильтруем только нужные ключи (1-2, 4-9)
    target_keys = ["1", "2", "4", "5", "6", "7", "8", "9"]
    return {k: data[k] for k in target_keys if k in data}

async def create_entity_data_embed(data):
    stat_names = await get_stat_names_map()
    async with aiofiles.open("chars_data/questions_lib.json", "r", encoding="utf-8") as f:
        questions_lib = json.loads(await f.read())
    item = data

    embed = create_embed_bs("Данные о сущности")
    
    # 1. Описание и Особенность (БЕЗ ИЗМЕНЕНИЙ)
    description = f"*{item.get('description', 'Описание отсутствует.')}*"
    text_mod = item.get("text_modifier")
    if text_mod:
        description += f"\n\n**Особенность:** {text_mod}"

    # 2. Формируем список технических бонусов (ДОБАВЛЕН ПЕРЕВОД)
    mods = item.get("modifiers", [])
    if mods:
        formatted_mods = []
        for mod in mods:
            # Распаковываем три значения (категорию игнорируем через _)
            _, target_id, mod_value = mod
            
            # Получаем человеческое название из мапы
            friendly_name = stat_names.get(target_id, target_id)
            
            # Форматируем строку: "• Сила: `-2`"
            formatted_mods.append(f"• {friendly_name}: `{mod_value:+}`")
        
        mods_str = "\n".join(formatted_mods)
    else:
        mods_str = None
    # 3. Собираем требования (ДОБАВЛЕН ПЕРЕВОД)
    reqs_list = []
    auto_reqs = item.get("requirements", {})
    if auto_reqs:
        for s_id, val in auto_reqs.items():
            # Заменяем s_id на человеческое название
            friendly_name = stat_names.get(s_id, s_id)
            reqs_list.append(f"{friendly_name} {val}+")
    
    # Б) БИОГРАФИЧЕСКИЕ ТРЕБОВАНИЯ (ДИНАМИЧЕСКИЕ)
    bio_reqs = item.get("biografy_requirements", {})
    if bio_reqs:
        for q_id, required_val in bio_reqs.items():
            q_data = questions_lib.get(str(q_id))
            if q_data:
                q_title = q_data["question"].replace("?", "").strip()
                
                # 1. Приводим required_val к списку, даже если там одно значение
                # Это универсальный способ обработать и [2, 3], и просто 2
                target_values = required_val if isinstance(required_val, list) else [required_val]
                # Переводим всё в строки для надежного сравнения
                target_values = [str(v) for v in target_values]
                # 2. Собираем все подходящие названия вариантов
                found_labels = []
                for choice in q_data.get("choices", []):
                    if str(choice["value"]) in target_values:
                        found_labels.append(choice["label"])
                
                # 3. Формируем итоговую строку (через "/" если вариантов несколько)
                if found_labels:
                    choice_text = " / ".join(found_labels)
                else:
                    choice_text = "Неизвестно"
                
                reqs_list.append(f"**{q_title}**: {choice_text}")
            else:
                reqs_list.append(f"Параметр {q_id}: {required_val}")
    
    text_reqs = item.get("text_requirements")
    if text_reqs:
        reqs_list.append(text_reqs)
    # 4. Сборка финального блока (БЕЗ ИЗМЕНЕНИЙ)
    field_value = f"{description}\n"
    
    if mods_str:
        field_value += f"\n**Модификаторы навыков:**\n{mods_str}"
        
    if reqs_list:
        field_value += f"\n**Требования:** *{', '.join(reqs_list)}*"
        
    cost = item.get("cost", 0)
    if cost != 0:
        field_value += f"\n**Стоимость:** `{cost} СО`"
    # Заголовок (ТОЛЬКО ПОЛЬЗОВАТЕЛЬСКОЕ ИМЯ)
    embed.add_field(
        name=f"🔹 {item['name']}",
        value=field_value,
        inline=False
    )
        
    return embed

def format_traits_list(tech_traits_list, library):
    """
    Принимает список технических ID и возвращает строку с красивыми именами.
    """
    if not tech_traits_list:
        return "Отсутствуют"
        
    # Превращаем каждый технический ID в красивое имя через цикл
    display_names = []
    for tid in tech_traits_list:
        name = get_trait_display_name(tid, library)
        display_names.append(name)
    
    # Склеиваем всё в одну строку через запятую
    return ", ".join(display_names)

def get_filtered_library(library, entry_type=None, is_unique=False):
    """
    Фильтрует библиотеку по типу (positive/negative) и уникальности.
    entry_type: "positive" или "negative"
    is_unique: True (показывать уникальные) или False (только общие)
    """
    filtered = {}
    for tid, data in library.items():
        # Проверка уникальности
        unique_status = "yes" if is_unique else "no"
        if data.get("unique") != unique_status:
            continue
            
        # Проверка типа (если задан)
        if entry_type and data.get("type") != entry_type:
            continue
            
        filtered[tid] = data
    return filtered

def get_trait_display_name(trait_id, library):
    """
    Ищет черту в библиотеке по ID и возвращает её красивое имя 'name'.
    Если черта не найдена, возвращает сам ID.
    """
    # Предполагаем, что self.library — это ваш большой словарь со всеми чертами
    trait_data = library.get(trait_id)
    if trait_data:
        return trait_data.get("name", trait_id)
    return trait_id

class TraitsEffectEnc(disnake.ui.View):
    def __init__(self, trait_type, current_page, render_type, questions_lib, library):
        super().__init__(timeout=900)
        self.trait_type = trait_type
        self.current_page = current_page
        self.render_type = render_type
        self.questions_lib = questions_lib
        self.library = library
        
        # По умолчанию выключаем кнопки, они настроятся в prepare_view
        self.prev_page.disabled = True
        self.next_page.disabled = True 

    async def prepare_view(self):
        """Асинхронная настройка кнопок при первом запуске энциклопедии"""
        # Теперь get_filtered_page вызывается через await без каких-либо проблем
        _, max_pages, _ = await get_filtered_page(
            self.library, self.trait_type, self.current_page, self.render_type
        )
        
        # Настраиваем доступность кнопок на основе реальных страниц
        self.prev_page.disabled = (self.current_page <= 1)
        self.next_page.disabled = (self.current_page >= max_pages)
        
        return self # Возвращаем объект для удобства

    @disnake.ui.button(label="⬅️", style=disnake.ButtonStyle.red, row=0)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
            _, max_pages, _ = await get_filtered_page(self.library, self.trait_type, self.current_page, self.render_type)
            if self.current_page > 1:
                self.current_page -= 1
                await self.update_view(interaction)
                if self.current_page == 1:
                    self.prev_page.disabled = True
                if self.current_page < max_pages:
                    self.next_page.disabled = False
                await self.update_view(interaction)

    @disnake.ui.button(label="➡️", style=disnake.ButtonStyle.red, row=0)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.Interaction):
            _, max_pages, _ = await get_filtered_page(self.library, self.trait_type, self.current_page, self.render_type)
            if self.current_page < max_pages:
                self.current_page += 1
                await self.update_view(interaction)
                if self.current_page == max_pages:
                    self.next_page.disabled = True
                if self.prev_page.disabled:
                    self.prev_page.disabled = False
                await self.update_view(interaction)

    async def update_view(self, interaction: disnake.Interaction):
        # 1. Получаем свежие данные для текущей страницы
        page_items, max_pages, total_count = await get_filtered_page(self.library, self.trait_type, self.current_page, self.render_type)
            
        # 3. Генерируем базовый эмбед библиотеки
        embed = await create_library_embed(
            filtered_data=page_items, 
            page=self.current_page, 
            max_pages=max_pages, 
            total_count=total_count, 
            questions_lib=self.questions_lib
        )
        # 4. ОБЯЗАТЕЛЬНО передаем self в view
        if interaction.response.is_done():
            await interaction.edit_original_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

class UnitedTraitsEffectManagmentSystem(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=900)
        self.edit_path = None
        self.old_tech_name = None
        self.tech_name = None
        self.user_name = None
        self.cost = 0
        self.desc = None
        self.text_mod = ""
        self.ucms_mod = []
        self.ucms_req = {}
        self.bio_req = {}
        self.text_req = ""
        self.type = "Положительная"
        self.unique = "Нет"
        self.questions_lib = "chars_data/questions_lib.json"
        self.blank_chars = "chars_data/blank_chars.json"
        self.choice = None
        self.type_choice = None
        self.value = 0
        self.value_dict = []
        self.mode = 0
        self.global_mode = 0
        self.questions = None
    
    def construct_trait_data(self):
        return {
            "name": self.user_name,
            "cost": self.cost,
            "description": self.desc,
            "text_modifier": self.text_mod,
            "modifiers": self.ucms_mod,
            "requirements": self.ucms_req,
            "biografy_requirements": self.bio_req,
            "text_requirements": self.text_req,
            "type": self.type,
            "unique": self.unique
        }

    def construct_effect_data(self):
        return {
            "name": self.user_name,
            "description": self.desc,
            "text_modifier": self.text_mod,
            "modifiers": self.ucms_mod,
            "type": self.type,
            "unique": self.unique
        }

    async def main_editor_window(self, inter: disnake.MessageInteraction):
        self.clear_items()
        names_map = await get_stat_names_map() # Твоя функция
        mod_lines = []
        for _, m_id, m_val in self.ucms_mod:
            # Ищем красивое имя. Если это навык/группа — из маппера, если нет — оставляем ID
            display_name = names_map.get(m_id, m_id)
            # Добавляем знак плюса для положительных чисел для красоты
            sign = "+" if m_val > 0 else ""
            mod_lines.append(f"• {display_name}: **{sign}{m_val}**")
        loc_ucms_mod = "\n".join(mod_lines) if mod_lines else "Не заданы"
        
        if self.global_mode == 1:
            req_lines = [] # Лучше использовать другое имя переменной, чтобы не путать с модами
            # Используем .items(), так как это словарь {id: value}
            for m_id, m_val in self.ucms_req.items():
                # Ищем красивое имя из маппера
                display_name = names_map.get(m_id, m_id)
                
                # Для требований обычно не нужен знак "+", но если хочешь оставить:
                req_lines.append(f"• {display_name}: **{m_val}**")
            
            loc_ucms_req = "\n".join(req_lines) if req_lines else "Не заданы"

            bio_req_text = []
            questions_cache = await load_bio_questions()

            for q_id, allowed_values in self.bio_req.items():
                question_text = questions_cache[q_id]["question"]
                # Получаем список меток (labels) для выбранных ID
                labels = []
                for choice in questions_cache[q_id]["choices"]:
                    if int(choice["value"]) in allowed_values:
                        labels.append(choice["label"])
                
                bio_req_text.append(f"• **{question_text}**: {', '.join(labels)}")

            loc_bio_req = "\n".join(bio_req_text) if bio_req_text else "Нет требований"
            embed = create_embed_bs("Меню настройки черты", f"**Техническое имя:** {self.tech_name}\n**Отображаемое имя:** {self.user_name}\n**Стоимость в ОС:** {self.cost}\n**Текстовое описание:** {self.desc}\n**Нарративный модификатор:** {self.text_mod}\n**Модификатор бросков:** {loc_ucms_mod}\n**Требования к хар-кам/навыкам:** {loc_ucms_req}\n**Требования к биографии:** {loc_bio_req}\n**Нарративное требование:** {self.text_req}\n**Тип:** {self.type}\n**Уникальность:** {self.unique}")
            if not self.old_tech_name:
                choices = [
                ("Техническое имя", "1"), ("Отображаемое имя", "2"), ("Стоимость в СО", "3"), ("Текстовое описание", "4"),
                ("Нарративный модификатор", "5"), ("Модификатор бросков", "6"), ("Требования к хар-кам/навыкам", "7"),
                ("Требования к биографии", "8"), ("Нарративные требования", "9"), ("Переключить флаг типа черты...", "10"), ("Переключить флаг уникальности...", "11")
                ]
            else:
                choices = [
                ("Отображаемое имя", "2"), ("Стоимость в СО", "3"), ("Текстовое описание", "4"),
                ("Нарративный модификатор", "5"), ("Модификатор бросков", "6"), ("Требования к хар-кам/навыкам", "7"),
                ("Требования к биографии", "8"), ("Нарративные требования", "9"), ("Переключить флаг типа черты...", "10"), ("Переключить флаг уникальности...", "11")  
                ] 
        else:
            embed = create_embed_bs("Меню настройки эффекта", f"**Техническое имя:** {self.tech_name}\n**Отображаемое имя:** {self.user_name}\n**Текстовое описание:** {self.desc}\n**Нарративный модификатор:** {self.text_mod}\n**Модификатор бросков:** {loc_ucms_mod}\n**Тип:** {self.type}\n**Уникальность:** {self.unique}")
            if not self.old_tech_name:
                choices = [
                    ("Техническое имя", "1"), ("Отображаемое имя", "2"), ("Текстовое описание", "4"),
                    ("Нарративный модификатор", "5"), ("Модификатор бросков", "6"),
                    ("Переключить флаг типа эффекта...", "10"), ("Переключить флаг уникальности...", "11")
                ]
            else:
                choices = [
                    ("Отображаемое имя", "2"), ("Текстовое описание", "4"),
                    ("Нарративный модификатор", "5"), ("Модификатор бросков", "6"),
                    ("Переключить флаг типа эффекта...", "10"), ("Переключить флаг уникальности...", "11")
                ]
        options = [
            disnake.SelectOption(label=name, value=val) 
            for name, val in choices
        ]
        select = disnake.ui.Select(
            placeholder="Выберите опцию меню...",
            options=options,
            custom_id=f"utems_main",
            row=1
            )
        select.callback = self.editor_main_select_callback
        self.add_item(select)
        btn_exit = disnake.ui.Button(label="Отменить создание/редакцию", custom_id="btn_exit", style=disnake.ButtonStyle.red, row=0)
        btn_save = disnake.ui.Button(label="Подтвердить создание/редакцию", custom_id="btn_save", style=disnake.ButtonStyle.red, row=0)
        btn_exit.callback = self.btn_exit_callback
        btn_save.callback = self.btn_save_callback
        self.add_item(btn_exit)
        self.add_item(btn_save)
        try:
            # 1. Пробуем отредактировать текущее сообщение (для кнопок и селекторов)
            await inter.response.edit_message(embed=embed, view=self)
        except disnake.errors.InteractionResponded:
            # 2. Если на интеракцию уже ответили (например, из модального окна)
            await inter.edit_original_response(embed=embed, view=self)
        except (disnake.errors.InteractionNotEditable, disnake.errors.HTTPException):
            # 3. Если сообщения еще нет (первый запуск команды) или оно недоступно для правки
            # Используем ephemeral=True, так как ты этого хотел изначально
            await inter.response.send_message(embed=embed, view=self, ephemeral=True)
    
    async def editor_main_select_callback(self, inter: disnake.MessageInteraction):
        raw_value = inter.values[0]
        value = int(raw_value)
        operation_number = value
        prev_view = self
        if value == 1:
            await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
                "Техническое имя", 
                "Только английские буквы и цифры.", 
                "и обязательно маленькие!",
                "edit_tech_name",
                "1",
                "30",
                operation_number,
                prev_view
                )
            )
        elif value == 2:
            await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
                "Отображаемое имя", 
                "Ограничение - 50 символов.", 
                "Ваше имя...",
                "edit_cost",
                "1",
                "50",
                operation_number,
                prev_view
                )
            )
        elif value == 3:
            await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
                "Стоимость в СО", 
                "Чтобы черта отнимала СО, указывайте минус.", 
                "0",
                "edit_cost",
                "1",
                "2",
                operation_number,
                prev_view
                )
            )
        elif value == 4:
            await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
                "Текстовое описание", 
                "Ограничение - 400 символов.", 
                "Ваше описание...",
                "edit_desc",
                "1",
                "400",
                operation_number,
                prev_view
                )
            )
        elif value == 5:
            await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
                "Нарративный модификатор", 
                "Ограничение - 400 символов.", 
                "Нарративный модификатор...",
                "edit_text_mod",
                "1",
                "400",
                operation_number,
                prev_view
                )
            )
        elif value == 6:
            self.clear_items()
            self.mode = 1
            btn_char = disnake.ui.Button(label="Характерстика", custom_id="btn_char", style=disnake.ButtonStyle.red, row=0)
            btn_skill = disnake.ui.Button(label="Навык", custom_id="btn_skill", style=disnake.ButtonStyle.red, row=0)
            btn_derived = disnake.ui.Button(label="Производная", custom_id="btn_derived", style=disnake.ButtonStyle.red, row=0)
            btn_delete = disnake.ui.Button(label="Удалить модификатор", custom_id="btn_delete", style=disnake.ButtonStyle.red, row=0)
            btn_back = disnake.ui.Button(label="Вернуться в меню", custom_id="btn_back", style=disnake.ButtonStyle.red, row=0)
            btn_back.callback = self.btn_back_callback
            btn_char.callback = self.btn_char_callback
            btn_skill.callback = self.btn_skill_callback
            btn_derived.callback = self.btn_derived_callback
            btn_delete.callback = self.btn_delete_callback
            self.add_item(btn_char)
            self.add_item(btn_skill)
            self.add_item(btn_derived)
            self.add_item(btn_delete)
            self.add_item(btn_back)
            await inter.response.edit_message(view=self)
            return
        elif value == 7:
            self.clear_items()
            self.mode = 2
            btn_char = disnake.ui.Button(label="Характерстика", custom_id="btn_char", style=disnake.ButtonStyle.red, row=0)
            btn_skill = disnake.ui.Button(label="Навык", custom_id="btn_skill", style=disnake.ButtonStyle.red, row=0)
            btn_delete = disnake.ui.Button(label="Удалить требование", custom_id="btn_delete", style=disnake.ButtonStyle.red, row=0)
            btn_back = disnake.ui.Button(label="Вернуться в меню", custom_id="btn_back", style=disnake.ButtonStyle.red, row=0)
            btn_back.callback = self.btn_back_callback
            btn_char.callback = self.btn_char_callback
            btn_skill.callback = self.btn_skill_callback
            btn_delete.callback = self.btn_delete_callback
            self.add_item(btn_char)
            self.add_item(btn_skill)
            self.add_item(btn_delete)
            self.add_item(btn_back)
            await inter.response.edit_message(view=self)
            return
        elif value == 8:
            self.clear_items()
            btn_add = disnake.ui.Button(label="Добавить требование", custom_id="btn_skill", style=disnake.ButtonStyle.red, row=0)
            btn_delete_bio_req = disnake.ui.Button(label="Удалить требование", custom_id="btn_delete", style=disnake.ButtonStyle.red, row=0)
            btn_back = disnake.ui.Button(label="Вернуться в меню", custom_id="btn_back", style=disnake.ButtonStyle.red, row=0)
            btn_back.callback = self.btn_back_callback
            btn_add.callback = self.btn_add_callback
            btn_delete_bio_req.callback = self.btn_delete_bio_req
            self.add_item(btn_add)
            self.add_item(btn_delete_bio_req)
            self.add_item(btn_back)
            await inter.response.edit_message(view=self)
            return
        elif value == 9:
            await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
                "Нарративное требование", 
                "Ограничение - 400 символов.", 
                "Нарративное требование...",
                "edit_text_req",
                "1",
                "400",
                operation_number,
                prev_view
                )
            )
        elif value == 10:
            if self.global_mode == 1:
                if self.type == "Положительная":
                    self.type = "Отрицательная"
                else:
                    self.type = "Положительная"
            else:
                if self.type == "Положительный":
                    self.type = "Отрицательный"
                else:
                    self.type = "Положительный"
        elif value == 11:
            if self.unique == "Нет":
                self.unique = "Да"
            else:
                self.unique = "Нет"
        await self.main_editor_window(inter)

    async def btn_char_callback(self, inter: disnake.MessageInteraction):
        self.type_choice = "group"
        await self.transmission(inter)
    
    async def btn_skill_callback(self, inter: disnake.MessageInteraction): 
        self.type_choice = "skill"
        await self.transmission(inter)

    async def btn_derived_callback(self, inter: disnake.MessageInteraction):
        self.type_choice = "derived"
        await self.transmission(inter)

    async def btn_back_callback(self, inter: disnake.MessageInteraction):
        await self.main_editor_window(inter)
    
    async def btn_delete_callback(self, inter: disnake.MessageInteraction):
        if not self.ucms_mod:
            return await inter.response.send_message("Список модификаторов пуст!", ephemeral=True)

        self.clear_items()
        names_map = await get_stat_names_map() # Подтягиваем маппер

        options = []
        for i, mod in enumerate(self.ucms_mod):
            # mod = [type, id, value]
            m_type, m_id, m_val = mod
            display_name = names_map.get(m_id, m_id)
            
            # Формируем читаемое название
            label = f"{display_name}: {m_val}"
            # В value прячем индекс элемента
            options.append(disnake.SelectOption(label=label, value=str(i)))

        select = disnake.ui.Select(
            placeholder="Выберите модификатор для удаления",
            options=options,
            custom_id="delete_select"
        )
        select.callback = self.delete_select_callback
        self.add_item(select)

        btn_back = disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.red)
        btn_back.callback = self.btn_back_callback # Возврат к списку кнопок меню
        self.add_item(btn_back)

        await inter.response.edit_message(view=self)

    async def btn_exit_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        self.stop()
        await inter.response.edit_message("**Создание отменено.**", view=self)

    async def btn_save_callback(self, inter: disnake.MessageInteraction):
            # 1. Валидация: не даем сохранить без ID или Названия
            if not self.tech_name or not self.user_name:
                return await inter.response.send_message(
                    "Ошибка! Обязательно нужно указать технический ID и название.", 
                    ephemeral=True
                )

            file_path = self.edit_path
            
            try:
                # 2. Загружаем существующую библиотеку
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    lib = json.loads(await f.read())
                
                if not self.old_tech_name and self.tech_name in lib:
                    return await inter.response.send_message(
                    "Сущность с таким техническим именем уже существует.", 
                    ephemeral=True
                )
                if self.old_tech_name and self.old_tech_name != self.tech_name:
                    if self.old_tech_name in lib:
                        del lib[self.old_tech_name]

                self.old_tech_name = self.tech_name

                if self.type == "Положительная":
                    self.type = "positive"
                else:
                    self.type = "negative"
                if self.unique == "Да":
                    self.unique = "yes"
                else:
                    self.unique = "no"
                # 3. Добавляем или перезаписываем черту
                if self.global_mode == 1:
                    new_data = self.construct_trait_data()
                else:
                    new_data = self.construct_effect_data()
                lib[self.tech_name] = new_data
                
                # 4. Сохраняем обратно в файл
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(lib, f, indent=4, ensure_ascii=False)
                
                if self.global_mode == 1:
                    await inter.response.send_message(
                        f"✅ Черта **{self.user_name}** (`{self.tech_name}`) успешно сохранена!", 
                        ephemeral=False
                    )
                else:
                    await inter.response.send_message(
                        f"✅ Эффект **{self.user_name}** (`{self.tech_name}`) успешно сохранён!", 
                        ephemeral=False
                    )
                
                # Можно закрыть редактор или деактивировать кнопки
                self.stop() 

            except Exception as e:
                await inter.response.send_message(f"Критическая ошибка при сохранении: {e}", ephemeral=True)

    async def transmission(self, inter: disnake.MessageInteraction):    
        self.clear_items()
        if self.type_choice in ["group", "skill"]:
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
                    min_values=1,
                    row=1
                )    
            if self.type_choice == "group":
                select.callback = self.modifier_select_callback
            else:
                select.callback = self.skill_choice_callback
        else:        
            choices = [
                ("ПЗ", "heal_points"), 
                ("МЗ", "mental_points"), 
                ("РЗ", "radiation_points"), 
                ("Переносимый вес", "carry_weight"), 
                ("Движение", "movement_speed"),
                ("МС", "psi_resist")
            ]
            options = [
            disnake.SelectOption(label=name, value=val) 
            for name, val in choices
            ]
            select = disnake.ui.Select(
                placeholder="Выберите производную...",
                options=options,
                custom_id="derived_select",
                min_values=1,
                row=1
            )
            select.callback = self.modifier_select_callback
        btn_back = disnake.ui.Button(label="Вернуться в меню", custom_id="btn_back", style=disnake.ButtonStyle.red, row=0)
        btn_back.callback = self.btn_back_callback
        self.add_item(btn_back)
        self.add_item(select)
        await inter.response.edit_message(view=self)

    async def skill_choice_callback(self, inter: disnake.MessageInteraction):
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
        self.skill_select.callback = self.modifier_select_callback 
        self.add_item(self.skill_select)
        self.back_button = disnake.ui.Button(label="Назад к группам", style=disnake.ButtonStyle.red, row=0)
        self.back_button.callback = self.transmission
        self.add_item(self.back_button)
        btn_back = disnake.ui.Button(label="Вернуться в меню", custom_id="btn_back", style=disnake.ButtonStyle.red, row=0)
        btn_back.callback = self.btn_back_callback
        self.add_item(btn_back)
        await inter.response.edit_message(view=self)
    
    async def modifier_select_callback(self, inter: disnake.MessageInteraction):
        self.choice = inter.data.values[0]
        prev_view = self
        if self.mode == 1:
            operation_number = 6
        else:
            operation_number = 7
        await inter.response.send_modal(UnitedTraitsEffectManagmentSystemModal(
            "Укажите модификатор", 
            "Может быть и положительным, и отрицательным", 
            "1",
            "edit_modificator_chars",
            "1",
            "2",
            operation_number,
            prev_view
            )
        )

    async def delete_select_callback(self, inter: disnake.MessageInteraction):
        index = int(inter.values[0])

        self.ucms_mod.pop(index)

        await self.main_editor_window(inter)

    async def btn_add_callback(self, inter: disnake.MessageInteraction):
        self.clear_items()
        questions = await load_bio_questions()
        options = [
            disnake.SelectOption(label=q["question"], value=k) 
            for k, q in questions.items()
        ]
            
        select = disnake.ui.Select(
            placeholder="Выберите категорию биографии...",
            options=options,
            custom_id="bio_category_select"
        )
        select.callback = self.bio_category_callback
        self.add_item(select)
        btn_back = disnake.ui.Button(label="Вернуться в меню", custom_id="btn_back", style=disnake.ButtonStyle.red, row=1)
        btn_back.callback = self.btn_back_callback
        self.add_item(btn_back)
        await inter.response.edit_message(view=self)
        # Не забываем кнопку "Назад"
    
    async def bio_category_callback(self, inter: disnake.MessageInteraction):
        self.current_bio_cat = inter.values[0] # Сохраняем ID вопроса (напр. "1")
        self.clear_items()
        
        questions = await load_bio_questions()
        current_q = questions[self.current_bio_cat]
        
        # Создаем опции для МУЛЬТИСЕЛЕКТА
        options = [
            disnake.SelectOption(label=c["label"], value=c["value"])
            for c in current_q["choices"]
        ]
        
        # Включаем мультиселект: max_values равен количеству вариантов
        select = disnake.ui.Select(
            placeholder=f"Выберите варианты для: {current_q['question']}",
            options=options,
            min_values=1,
            max_values=len(options),
            custom_id="bio_values_select"
        )
        select.callback = self.bio_finish_callback
        self.add_item(select)
        await inter.response.edit_message(view=self)

    async def bio_finish_callback(self, inter: disnake.MessageInteraction):
        # Превращаем выбранные значения в список целых чисел
        selected_values = [int(v) for v in inter.values]
        
        # Записываем в словарь требований биографии
        # self.bio_req = {"1": [1, 2, 3]}
        self.bio_req[self.current_bio_cat] = selected_values
        await self.main_editor_window(inter)

    async def btn_delete_bio_req(self, inter: disnake.MessageInteraction):
        if not self.bio_req:
            return await inter.response.send_message("Список требований пуст!", ephemeral=True)

        self.clear_items()
        self.questions = await load_bio_questions()

        options = []
        for cat_id in self.bio_req.keys():
            q_name = self.questions[cat_id]["question"]
            options.append(disnake.SelectOption(label=q_name, value=cat_id))

        select = disnake.ui.Select(
            placeholder="Выберите категорию для удаления требования",
            options=options
        )

        select.callback = self.delete_bio_callback
        self.add_item(select)
        btn_back = disnake.ui.Button(label="Вернуться в меню", custom_id="btn_back", style=disnake.ButtonStyle.red, row=1)
        btn_back.callback = self.btn_back_callback
        self.add_item(btn_back)
        await inter.response.edit_message(view=self)

    async def delete_bio_callback(self, interaction: disnake.MessageInteraction):
        target_cat = interaction.values[0]
        del self.bio_req[target_cat] # Удаляем всю категорию со всеми её значениями
        await self.main_editor_window(interaction)
        await interaction.response.send_message(f"Требование '{self.questions[target_cat]['question']}' удалено.", ephemeral=True)

class UnitedTraitsEffectManagmentSystemModal(disnake.ui.Modal):
    def __init__(self, title, label, placeholder, custom_id, min_length, max_length, operation_number, prev_view):
        self.operation_number = operation_number
        self.prev_view = prev_view
        
        # Сохраняем ID для поля ввода
        self.input_custom_id = custom_id 
        
        components = [
            disnake.ui.TextInput(
                label=label,
                placeholder=placeholder,
                custom_id=self.input_custom_id, # ID конкретного поля
                style=disnake.TextInputStyle.short,
                min_length=int(min_length),
                max_length=int(max_length)
            )
        ]
        
        # ОБЯЗАТЕЛЬНО передаем title и компоненты. 
        # custom_id для самого МОДАЛА можно не указывать (он будет рандомным),
        # но важно, чтобы мы знали ID Текстового поля внутри.
        super().__init__(title=title, components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        # Используем сохраненный ID поля, чтобы вытащить значение
        result = inter.text_values[self.input_custom_id]
        if self.operation_number == 1:
            if not is_valid_tech_id(result):
                return await inter.response.send_message("Ошибка! Техническое имя должно содержать только английские буквы, цифры и '_'.", ephemeral=True)
            self.prev_view.tech_name = result
        if self.operation_number == 2:
            self.prev_view.user_name = result
        if self.operation_number == 3:
            try:
                result_int = int(result)
            except (ValueError, TypeError):
                return await inter.response.send_message("Ошибка! Нужно ввести целое число.", ephemeral=True)
            if self.prev_view.type == "Положительная":
                if result_int > 0:
                    return await inter.response.send_message("Позитивная черта не может прибавлять СО.", ephemeral=True)
            if self.prev_view.type == "Негативная":
                if result_int < 0:
                    return await inter.response.send_message("Негативная черта не может отнимать СО.", ephemeral=True)
            self.prev_view.cost = result_int
        if self.operation_number == 4:
            self.prev_view.desc = result
        if self.operation_number == 5:
            self.prev_view.text_mod = result
        if self.operation_number == 6:
            try:
                result_int = int(result)
            except (ValueError, TypeError):
                return await inter.response.send_message("Ошибка! Нужно ввести целое число.", ephemeral=True)
            found = False
            for mod in self.prev_view.ucms_mod:
                # Проверяем, есть ли уже модификатор для этой цели и этого типа
                if mod[0] == self.prev_view.type_choice and mod[1] == self.prev_view.choice:
                    mod[2] += result_int  # Суммируем значения
                    found = True
                    break

            if not found:
                # Если такой модификатор еще не создавался — добавляем новый
                self.prev_view.ucms_mod.append([self.prev_view.type_choice, self.prev_view.choice, result_int])
        if self.operation_number == 7:
            try:
                result_int = int(result)
            except (ValueError, TypeError):
                return await inter.response.send_message("Ошибка! Нужно ввести целое число.", ephemeral=True)
            if result_int < 1:
                return await inter.response.send_message("Требование не может быть отрицательным или равно нулю.", ephemeral=True)
            self.prev_view.ucms_req[self.prev_view.choice] = result_int
        if self.operation_number == 9:
            self.prev_view.text_req = result
        if self.operation_number == 14:
            await self.prev_view.derived_editor_callback(inter, result)
            return
        await self.prev_view.main_editor_window(inter)
