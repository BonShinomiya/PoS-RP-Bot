import disnake
from disnake.ext import commands
import json
import aiofiles
import os
import uuid
import asyncio

character_locks = {}

def get_char_lock(path):
    if path not in character_locks:
        character_locks[path] = asyncio.Lock()
    return character_locks[path]

ITEMS_LIB_PATH = "chars_data/items_lib.json"

async def load_item_library() -> dict:
    """Загружает общую статическую базу предметов (items_lib.json)."""
    # Если файл лежит в другой папке, поправь путь (например, 'chars_data/items_lib.json')
    path = "items_lib.json"
    if not os.path.exists(path):
        return {}
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return json.loads(await f.read())

async def calculate_inventory_weight(skills_data: list, items_lib: dict) -> float:
    """
    Сканирует инвентарь персонажа и рассчитывает текущий суммарный вес.
    Защищено от отсутствующих в базе предметов.
    """
    inventory = skills_data[0].get("inventory", {})
    total_weight = 0.0

    for item_key, item_data in inventory.items():
        # Для стакаемых предметов ключ совпадает с ID (ammo_5.45)
        # Для уникальных (оружие/броня) берем базовый шаблон из поля 'template'
        lib_key = item_data.get("template", item_key)
        lib_item = items_lib.get(lib_key)
        
        if not lib_item:
            continue
            
        weight_per_item = lib_item.get("weight_per_item", 0.0)
        amount = item_data.get("amount", 1)  # Оружие/броня по дефолту 1 шт.
        
        # Добавляем вес самого предмета, помноженный на количество
        total_weight += weight_per_item * amount
        
        # (Опционально) Если в оружии установлены модификации, добавляем их вес
        if "modifications" in item_data:
            for mod_key in item_data["modifications"]:
                mod_item = items_lib.get(mod_key)
                if mod_item:
                    total_weight += mod_item.get("weight_per_item", 0.0)
                    
    return round(total_weight, 3)


class CharacterInventoryView(disnake.ui.View):
    def __init__(self, user_id: int, character_path: str, main_character_view, message=None):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.character_path = character_path
        self.main_character_view = main_character_view  # Ссылка на CharacterSelectView для возврата
        self.message = message
        
        self.current_page = 1
        self.items_per_page = 5
        self.max_pages = 1
        
        # Изначально блокируем кнопки пагинации, настроим при рендере
        self.prev_page.disabled = True
        self.next_page.disabled = True

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != self.user_id:
            await inter.send("Извините, но это чужой рюкзак. Вы не можете им управлять.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        """Убирает кнопки из сообщения, если игрок «заснул» в инвентаре."""
        if self.message:
            try:
                await self.message.edit(
                    content="❌ **Время сессии инвентаря истекло.** Откройте рюкзак заново.", 
                    embed=None, 
                    view=None
                )
            except disnake.HTTPException:
                pass
        self.stop()

    async def render_inventory_embed(self, skills_data: list, items_lib: dict) -> disnake.Embed:
        """Формирует красивый UI-эмбед со списком предметов на текущей странице."""
        inventory = skills_data[0].get("inventory", {})
        char_name = skills_data[0].get("char_name", ["Сталкер"])[0] if isinstance(skills_data[0].get("char_name"), list) else skills_data[0].get("char_name", "Сталкер")
        
        # Расчет веса
        current_weight = await calculate_inventory_weight(skills_data, items_lib)
        
        # Здесь должна быть твоя формула максимального веса из базовых характеристик (например, Силы)
        # Пока поставим заглушку в 40 кг. Сюда можно передать значение из skills_data
        max_weight = 40.0 

        embed = disnake.Embed(
            title=f"🎒 Рюкзак: {char_name}",
            description=f"**Вес:** `{current_weight}` / `{max_weight}` кг\n\n*Выберите предмет в выпадающем списке под сообщением для взаимодействия.*",
            color=disnake.Color.dark_green()
        )
        embed.set_footer(text="© By Bon Shinomiya")

        inv_items = list(inventory.items())
        total_items = len(inv_items)
        self.max_pages = (total_items - 1) // self.items_per_page + 1 if total_items > 0 else 1

        # Ограничиваем срез предметов для пагинации
        start = (self.current_page - 1) * self.items_per_page
        end = start + self.items_per_page
        page_items = inv_items[start:end]

        # Контроль доступности кнопок стрелочек
        self.prev_page.disabled = (self.current_page <= 1)
        self.next_page.disabled = (self.current_page >= self.max_pages)

        select_options = []

        if not page_items:
            embed.description += "\n\n*В рюкзаке сейчас абсолютно пусто...*"
            select_options.append(disnake.SelectOption(label="Пусто", value="none", description="Тут ничего нет"))
            self.item_select.disabled = True
        else:
            self.item_select.disabled = False
            for item_id, item_data in page_items:
                lib_key = item_data.get("template", item_id)
                lib_item = items_lib.get(lib_key, {})
                
                # Приоритет отображения имени: кастомное имя игрока -> стандартное имя из базы
                display_name = item_data.get("username") or lib_item.get("name", item_id)
                
                # Текст подписи (кол-во для расходников, прочность для снаряжения)
                if item_data.get("stackable") == "yes":
                    info_str = f"Количество: {item_data.get('amount', 1)} шт."
                else:
                    info_str = f"Состояние: {item_data.get('durability', 100)}%"

                # Считаем вес пачки или единицы снаряжения (вместе с обвесами)
                item_weight = lib_item.get("weight_per_item", 0.0) * item_data.get("amount", 1)
                if "modifications" in item_data:
                    for m in item_data["modifications"]:
                        if m in items_lib:
                            item_weight += items_lib[m].get("weight_per_item", 0.0)

                embed.add_field(
                    name=f"📦 {display_name}",
                    value=f"↳ *{info_str}* | Вес: `{round(item_weight, 3)}` кг",
                    inline=False
                )

                # Добавляем элемент в выпадающее меню
                select_options.append(disnake.SelectOption(
                    label=display_name[:100],  # Защита от лимита Discord в 100 символов
                    value=item_id,
                    description=info_str[:100]
                ))

        self.item_select.options = select_options
        embed.set_footer(text=f"Страница {self.current_page} из {self.max_pages} | Всего уникальных позиций: {total_items} | © By Bon Shinomiya")
        return embed

    async def update_screen(self, inter: disnake.MessageInteraction):
        """Внутренний метод обновления интерфейса, защищенный единым Lock'ом папки."""
        async with get_char_lock(self.character_path):
            async with aiofiles.open(f"{self.character_path}/char_stats.json", "r", encoding="utf-8") as f:
                skills_data = json.loads(await f.read())
        
        items_lib = await load_item_library()
        embed = await self.render_inventory_embed(skills_data, items_lib)
        await inter.response.edit_message(embed=embed, view=self)

    @disnake.ui.select(placeholder="Выберите предмет для взаимодействия...", min_values=1, max_values=1, row=1)
    async def item_select(self, select: disnake.ui.Select, inter: disnake.MessageInteraction):
        item_id = select.values[0]
        if item_id == "none":
            await inter.response.defer()
            return
            
        # Заглушка под меню действий (Использовать, Осмотреть, Выбросить)
        await inter.response.send_message(f"Вы выбрали предмет с ID: `{item_id}`. Логика контекстных действий будет здесь!", ephemeral=True)

    @disnake.ui.button(label="⬅️ Предыдущая", style=disnake.ButtonStyle.green, row=0)
    async def prev_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.current_page > 1:
            self.current_page -= 1
            await self.update_screen(inter)

    @disnake.ui.button(label="Следующая ➡️", style=disnake.ButtonStyle.green, row=0)
    async def next_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.current_page < self.max_pages:
            self.current_page += 1
            await self.update_screen(inter)

    @disnake.ui.button(label="↩️ Вернуться на главную", style=disnake.ButtonStyle.red, row=0)
    async def back_to_main(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.stop()
        # Вызываем базовый метод рендеринга персонажа из твоего CharacterSelectView
        if self.main_character_view:
            await self.main_character_view.main_view(inter)

# ==========================================
# 1. МЕНЕДЖЕР БАЗЫ ДАННЫХ ПРЕДМЕТОВ (CRUD)
# ==========================================

class ItemsLibraryManager:
    @staticmethod
    async def load_lib() -> dict:
        if not os.path.exists(ITEMS_LIB_PATH):
            async with aiofiles.open(ITEMS_LIB_PATH, "w", encoding="utf-8") as f:
                await f.write(json.dumps({}, ensure_ascii=False, indent=4))
            return {}
        async with aiofiles.open(ITEMS_LIB_PATH, "r", encoding="utf-8") as f:
            try:
                return json.loads(await f.read())
            except json.JSONDecodeError:
                return {}

    @staticmethod
    async def save_lib(data: dict):
        async with aiofiles.open(ITEMS_LIB_PATH, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=4))

    @classmethod
    async def add_or_update_item(cls, item_id: str, item_data: dict):
        lib = await cls.load_lib()
        lib[item_id] = item_data
        await cls.save_lib(lib)

    @classmethod
    async def delete_item(cls, item_id: str) -> bool:
        lib = await cls.load_lib()
        if item_id in lib:
            del lib[item_id]
            await cls.save_lib(lib)
            return True
        return False

# ==========================================
# 2. МОДАЛЬНЫЕ ОКНА РЕДАКТИРОВАНИЯ
# ==========================================

class AmmoEditModal(disnake.ui.Modal):
    def __init__(self, tech_id: str = "", current_data: dict = None):
        self.tech_id = tech_id
        self.is_edit = current_data is not None
        
        # Собираем компоненты динамически
        components = []
        
        # Если это НЕ редактирование, добавляем поле для ввода нового ID
        if not self.is_edit:
            components.append(disnake.ui.TextInput(
                label="Технический ID", 
                placeholder="ammo_5.45", 
                custom_id="tech_id"
            ))
            
        components.extend([
            disnake.ui.TextInput(label="Название патронов", placeholder="Патроны 5.45х39 мм", custom_id="name", value=current_data.get("name", "") if current_data else ""),
            disnake.ui.TextInput(label="Описание", placeholder="Текст описания...", custom_id="description", style=disnake.TextInputStyle.paragraph, value=current_data.get("description", "") if current_data else ""),
            disnake.ui.TextInput(label="Вес (за 1 шт в кг)", placeholder="0.012", custom_id="weight", value=str(current_data.get("weight_per_item", "")) if current_data else ""),
            disnake.ui.TextInput(label="Базовая цена", placeholder="13", custom_id="price", value=str(current_data.get("base_price", "")) if current_data else "")
        ])
        
        super().__init__(title="Настройка: Патроны/Расходники", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        # Если редактируем — берем ID из инстанса класса, если создаем — из поля ввода
        t_id = self.tech_id if self.is_edit else inter.text_values["tech_id"].strip()
        try:
            item_data = {
                "name": inter.text_values["name"].strip(),
                "description": inter.text_values["description"].strip(),
                "type": "ammo",
                "weight_per_item": float(inter.text_values["weight"]),
                "base_price": int(inter.text_values["price"])
            }
            await ItemsLibraryManager.add_or_update_item(t_id, item_data)
            await inter.response.send_message(f"✅ Шаблон предмета `{t_id}` успешно сохранен в базу.", ephemeral=True)
        except ValueError:
            await inter.response.send_message("❌ Ошибка: Вес должен быть дробным числом (через точку), а цена — целым.", ephemeral=True)


class WeaponEditModal(disnake.ui.Modal):
    def __init__(self, tech_id: str = "", current_data: dict = None):
        self.tech_id = tech_id
        self.is_edit = current_data is not None
        
        base_stats = current_data.get("base_stats", {}) if current_data else {}
        damage = base_stats.get("damage", [0, 0])
        compatible_ammo = current_data.get("compatible_ammo", [""]) if current_data else [""]

        components = []
        
        # Если это НЕ редактирование, добавляем поле технического ID
        if not self.is_edit:
            components.append(disnake.ui.TextInput(
                label="Технический ID", 
                placeholder="ak74", 
                custom_id="tech_id"
            ))

        components.extend([
            disnake.ui.TextInput(label="Название оружия", placeholder="Автомат Калашникова АК-74", custom_id="name", value=current_data.get("name", "") if current_data else ""),
            disnake.ui.TextInput(label="Описание", placeholder="Описание оружия...", custom_id="description", style=disnake.TextInputStyle.paragraph, value=current_data.get("description", "") if current_data else ""),
            disnake.ui.TextInput(label="Вес (кг) | Базовая цена (через пробел)", placeholder="3.6 15000", custom_id="weight_price", value=f"{current_data.get('weight_per_item', '')} {current_data.get('base_price', '')}".strip() if current_data else ""),
            disnake.ui.TextInput(label="Урон Мин Макс Магазин Патроны (ч/з пробел)", placeholder="4 0 30 ammo_5.45", custom_id="stats", value=f"{damage[0]} {damage[1]} {base_stats.get('max_magazine', '')} {compatible_ammo[0]}".strip() if current_data else "")
        ])
        super().__init__(title="Настройка: Оружие", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        t_id = self.tech_id if self.is_edit else inter.text_values["tech_id"].strip()
        try:
            wp_data = inter.text_values["weight_price"].split()
            st_data = inter.text_values["stats"].split()
            
            item_data = {
                "name": inter.text_values["name"].strip(),
                "description": inter.text_values["description"].strip(),
                "type": "weapon",
                "weight_per_item": float(wp_data[0]),
                "base_price": int(wp_data[1]),
                "base_stats": {
                    "damage": [int(st_data[0]), int(st_data[1])],
                    "accuracy": 0,
                    "reliability": 10,
                    "grouping": 3,
                    "max_magazine": int(st_data[2])
                },
                "compatible_ammo": [st_data[3]]
            }
            await ItemsLibraryManager.add_or_update_item(t_id, item_data)
            await inter.response.send_message(f"✅ Шаблон оружия `{t_id}` сохранен.", ephemeral=True)
        except Exception:
            await inter.response.send_message("❌ Ошибка ввода. Проверьте разделение пробелами и типы данных.", ephemeral=True)


# ==========================================
# 3. ИНТЕРФЕЙСЫ ОЖИДАНИЯ И ПАНЕЛИ ГМ (VIEW)
# ==========================================

class ItemTypeSelectView(disnake.ui.View):
    """Панель выбора типа создаваемого предмета (аналог эффектов)"""
    def __init__(self):
        super().__init__(timeout=300)

    @disnake.ui.button(label="Патроны / Расходники", style=disnake.ButtonStyle.green)
    async def type_ammo(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(AmmoEditModal())

    @disnake.ui.button(label="Оружие", style=disnake.ButtonStyle.green)
    async def type_weapon(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(WeaponEditModal())


class ItemSelectorView(disnake.ui.View):
    """Выпадающий список существующих шаблонов для редактирования/удаления"""
    def __init__(self, lib_data: dict, action_type: str):
        super().__init__(timeout=300)
        self.lib_data = lib_data
        self.action_type = action_type # "edit" или "delete"

        options = []
        for t_id, data in lib_data.items():
            options.append(disnake.SelectOption(
                label=f"{data.get('name', t_id)} ({t_id})",
                value=t_id,
                description=f"Тип: {data.get('type')} | Цена: {data.get('base_price')}"
            ))
        
        self.select_item.options = options[:25] # Лимит дискорда

    @disnake.ui.select(placeholder="Выберите предмет из базы данных...")
    async def select_item(self, select: disnake.ui.Select, inter: disnake.MessageInteraction):
        t_id = select.values[0]
        current_data = self.lib_data[t_id]

        if self.action_type == "delete":
            await ItemsLibraryManager.delete_item(t_id)
            await inter.response.edit_message(content=f"🗑️ Шаблон предмета `{t_id}` полностью удалён из базы данных.", embed=None, view=None)
        elif self.action_type == "edit":
            if current_data.get("type") == "ammo":
                await inter.response.send_modal(AmmoEditModal(tech_id=t_id, current_data=current_data))
            elif current_data.get("type") == "weapon":
                await inter.response.send_modal(WeaponEditModal(tech_id=t_id, current_data=current_data))
            else:
                await inter.response.send_message("Редактирование данного типа пока не поддерживается через UI.", ephemeral=True)


class ItemDatabaseMainView(disnake.ui.View):
    """Главное интерактивное меню /item_db"""
    def __init__(self):
        super().__init__(timeout=300)

    @disnake.ui.button(label="➕ Создать шаблон предмета", style=disnake.ButtonStyle.green, row=0)
    async def create_item(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        view = ItemTypeSelectView()
        await inter.response.edit_message(content="🔧 Выберите категорию создаваемого предмета:", view=view)

    @disnake.ui.button(label="📝 Редактировать шаблон", style=disnake.ButtonStyle.blurple, row=0)
    async def edit_item(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        lib = await ItemsLibraryManager.load_lib()
        if not lib:
            await inter.response.send_message("База данных предметов пуста.", ephemeral=True)
            return
        view = ItemSelectorView(lib, "edit")
        await inter.response.edit_message(content="📝 Выберите предмет для изменения характеристик:", view=view)

    @disnake.ui.button(label="🗑️ Удалить шаблон", style=disnake.ButtonStyle.red, row=0)
    async def delete_item(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        lib = await ItemsLibraryManager.load_lib()
        if not lib:
            await inter.response.send_message("База данных предметов пуста.", ephemeral=True)
            return
        view = ItemSelectorView(lib, "delete")
        await inter.response.edit_message(content="⚠️ **ВНИМАНИЕ:** Выбранный в списке предмет будет удалён безвозвратно!", view=view)


# ==========================================
# 4. КОГ АДМИНИСТРАТИВНЫХ СЛЭШ-КОМАНД
# ==========================================

class InventoryAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="item_db", description="Открыть визуальный редактор глобальной базы предметов")
    @commands.default_member_permissions(administrator=True)
    async def item_db_cmd(self, inter):
        embed = disnake.Embed(
            title="🛠️ Панель управления предметами ЧЗО",
            description="Позволяет на лету конфигурировать шаблоны оружия, патронов и снаряжения, сохраняя изменения напрямую в общую библиотеку.",
            color=disnake.Color.orange()
        )
        embed.set_footer(text="© By Bon Shinomiya")
        await inter.response.send_message(embed=embed, view=ItemDatabaseMainView(), ephemeral=True)

    @commands.slash_command(name="item", description="Управление рюкзаками игроков")
    @commands.default_member_permissions(administrator=True)
    async def item_player(self, inter):
        pass

    @item_player.sub_command(name="give", description="Выдать предмет в инвентарь игрока")
    async def give_item(
        self, inter,
        player: disnake.Member = commands.Param(desc="Игрок"),
        tech_id: str = commands.Param(desc="Технический ID шаблона из базы"),
        amount: int = commands.Param(default=1, desc="Количество предметов")
    ):
        lib = await ItemsLibraryManager.load_lib()
        if tech_id not in lib:
            await inter.response.send_message(f"❌ Шаблон `{tech_id}` не найден в базе. Сначала создайте его через `/item_db`.", ephemeral=True)
            return

        user_dir = f"user_profiles/{player.id}"
        if not os.path.exists(user_dir):
            await inter.response.send_message("❌ У игрока нет активных профилей персонажей.", ephemeral=True)
            return
            
        subdirs = [os.path.join(user_dir, d) for d in os.listdir(user_dir) if os.path.isdir(os.path.join(user_dir, d))]
        if not subdirs:
            await inter.response.send_message("❌ Папка профиля пуста.", ephemeral=True)
            return
            
        char_path = subdirs[0] 
        stats_file = f"{char_path}/char_stats.json"
        item_template = lib[tech_id]
        is_stackable = "yes" if item_template["type"] in ["ammo", "medicine"] else "no"

        async with get_char_lock(char_path):
            async with aiofiles.open(stats_file, "r", encoding="utf-8") as f:
                skills_data = json.loads(await f.read())

            if "inventory" not in skills_data[0]:
                skills_data[0]["inventory"] = {}
            inventory = skills_data[0]["inventory"]

            if is_stackable == "yes":
                if tech_id in inventory:
                    inventory[tech_id]["amount"] += amount
                else:
                    inventory[tech_id] = {
                        "type": item_template["type"],
                        "stackable": "yes",
                        "amount": amount
                    }
                log_text = f"Выдано: {item_template['name']} x{amount}"
            else:
                for _ in range(amount):
                    unique_id = str(uuid.uuid4())[:8]
                    if item_template["type"] == "weapon":
                        inventory[unique_id] = {
                            "type": "weapon",
                            "stackable": "no",
                            "template": tech_id,
                            "username": None,
                            "userdesc": None,
                            "durability": 100,
                            "magazine": [0, item_template["base_stats"]["max_magazine"]],
                            "modifications": []
                        }
                log_text = f"Выдано уникальное снаряжение: {item_template['name']} ({amount} шт.)"

            async with aiofiles.open(stats_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))

        await inter.response.send_message(f"✅ {log_text} пользователю {player.mention}.", ephemeral=True)

    @item_player.sub_command(name="take", description="Забрать предмет из инвентаря игрока")
    async def take_item(
        self, inter,
        player: disnake.Member = commands.Param(desc="Игрок"),
        item_id: str = commands.Param(desc="ID слота (tech_id для стаков или уникальный ID пушки)"),
        amount: int = commands.Param(default=1, desc="Количество для удаления")
    ):
        user_dir = f"user_profiles/{player.id}"
        subdirs = [os.path.join(user_dir, d) for d in os.listdir(user_dir) if os.path.isdir(os.path.join(user_dir, d))]
        if not subdirs:
            await inter.response.send_message("Профиль не найден.", ephemeral=True)
            return
            
        char_path = subdirs[0]
        stats_file = f"{char_path}/char_stats.json"

        async with get_char_lock(char_path):
            async with aiofiles.open(stats_file, "r", encoding="utf-8") as f:
                skills_data = json.loads(await f.read())

            inventory = skills_data[0].get("inventory", {})
            if item_id not in inventory:
                await inter.response.send_message(f"❌ У игрока нет предмета с ID `{item_id}`.", ephemeral=True)
                return

            item_data = inventory[item_id]
            if item_data.get("stackable") == "yes":
                if item_data["amount"] <= amount:
                    del inventory[item_id]
                    msg = f"Изъята вся пачка `{item_id}`."
                else:
                    item_data["amount"] -= amount
                    msg = f"Изъято {amount} шт. Осталось: {item_data['amount']}"
            else:
                del inventory[item_id]
                msg = f"Уникальный предмет `{item_id}` удалён."

            async with aiofiles.open(stats_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(skills_data, ensure_ascii=False, indent=4))

        await inter.response.send_message(f"✅ {msg} у {player.mention}.", ephemeral=True)


def setupinventory(bot):
    bot.add_cog(InventoryAdminCog(bot))