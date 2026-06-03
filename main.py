import disnake
from disnake.ext import commands
import json
import os
import shutil
from disnake.ext import commands
from charlists import *
from location_explorer import *
from inventory import *
from utems import *
from posmoney import setup
from dotenv import load_dotenv
from utils import *

load_dotenv()

intents = disnake.Intents.all()
intents.message_content = True
checker_list = open('check_data.txt', 'a')
votuum_gm_list = open('data.txt', 'a')
intents.members = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Белый список ID серверов, на которых боту разрешено работать
ALLOWED_GUILDS = [659346867250790421,  # Тестовый сервер
    1370395321796001932   # PoS RP
    ]

@bot.before_slash_command_invoke
async def global_before_whitelist_check(inter: disnake.ApplicationCommandInteraction):
    # 1. Если список пуст — тотальный блок
    if not ALLOWED_GUILDS:
        await inter.response.send_message("❌ Бот временно заблокирован администратором.", ephemeral=True)
        # Бросаем ошибку, чтобы жестко прервать выполнение самой команды
        raise commands.CheckFailure("Глобальный белый список пуст.")

    # 2. Блок ЛС
    if inter.guild is None:
        await inter.response.send_message("❌ Команды в ЛС запрещены.", ephemeral=True)
        raise commands.CheckFailure("Попытка вызова в ЛС.")

    # 3. Блок чужих серверов
    if inter.guild.id not in ALLOWED_GUILDS:
        await inter.response.send_message("❌ Доступ заблокирован. Сервер не в белом списке.", ephemeral=True)
        raise commands.CheckFailure(f"Чужой сервер: {inter.guild.id}")

view_store = {}

bot.active_creations = {} # {user_id: message_id}

@bot.slash_command(name="pos_buffer_clear", description="Очистить буфер активных сессий (дебаг)")
async def buffer_clear(inter: disnake.ApplicationCommandInteraction):
    bot.active_creations = {}
    print(f"Текущие активные сессии: {bot.active_creations}")
    await inter.response.send_message(content="Буфер активных сессий успешно очищен.", ephemeral=True)

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

@bot.event
async def on_raw_message_delete(payload):
    target_user_id = None
    
    for user_id, data in bot.active_creations.items():
        # Проверяем, что data — это действительно словарь, а не None
        if isinstance(data, dict) and data.get("msg_id") == payload.message_id:
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

@bot.event
async def on_interaction(inter):
    """Отладочный обработчик для всех взаимодействий."""
    interaction_id = get_interaction_id(inter)
    custom_id = inter.data.get('custom_id') if inter.data else None
    print(f"Interaction received: type={inter.type}, custom_id={custom_id}, user={inter.author.id}, message_id={inter.message.id if hasattr(inter, 'message') and inter.message else 'None'}, interaction_id={interaction_id}, interaction_type={type(inter).__name__}")

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
                is_active_session = inter.author.id in bot.active_creations

                if not is_complete and not is_active_session:
                    # Вызов в коде:
                    try:
                        # Используем onexc вместо onerror
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
    
    await sync_character_weight_and_effects(char_stats_path)

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
    embed = await create_entity_data_embed(data)
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
    await view.prepare_view()
    page_items, max_pages, total_count = await get_filtered_page(library, trait_type, current_page, render_type)
    embed = await create_library_embed(page_items, questions_lib, current_page, max_pages, total_count)
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
        unique = data.get("unique")
        if unique == "no":
            unique = "Нет"
        else:
            unique = "Да"
        view.unique = unique

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

@bot.slash_command(name="pos_start_votuum", description="Начать вотуум.")
async def votuum(inter: disnake.ApplicationCommandInteraction, gm_name: str):
    if disnake.utils.get(inter.author.roles, name="Главный Гейм Мастер"):
        print('command completed')
    elif disnake.utils.get(inter.author.roles, name="О-Сознание"):
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

@bot.slash_command(name="pos_item_manage", description="Управление библиотекой предметов (создание, редакция, удаление)")
async def pos_item_manage(
    inter: disnake.ApplicationCommandInteraction,
    target: str = commands.Param(default=None, description="Введите тех. ID предмета для редактирования"),
    operation: str = commands.Param(default="Редактировать", choices=["Редактировать", "Удалить"], description="Действие с предметом")
):
    await inter.response.defer(ephemeral=True)
    library = await load_items_library() # подтянем из inventory.py

    if target is None:
        # Режим создания
        view = UnitedItemsManagementSystem()
        await view.send_main_window(inter)
        return

    if target not in library:
        return await inter.send(f"❌ Предмет `{target}` не найден в базе данных.", ephemeral=True)

    if operation == "Удалить":
        del library[target]
        await save_items_library(library)
        return await inter.send(f"✅ Предмет `{target}` успешно удален из библиотеки.")

    # Режим редактирования
    view = UnitedItemsManagementSystem(target_id=target, current_data=library[target])
    await view.send_main_window(inter)

@pos_item_manage.autocomplete("target")
async def item_manage_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    library = await load_items_library()
    choices = []
    for tech_id, data in library.items():
        name = data.get("name", tech_id)
        if string.lower() in name.lower() or string.lower() in tech_id.lower():
            choices.append(disnake.OptionChoice(name=name, value=tech_id))
    return choices[:25]

@bot.event
async def on_button_click(inter: disnake.MessageInteraction):
    custom_id = inter.component.custom_id
    try:
        action, gm_name = custom_id.split(":")
        if action == "agree_vote" or action == "opposite_vote":
            channel_id = 1305584809036484618
            channel = bot.get_channel(channel_id)
            
            action, gm_name = custom_id.split(":")
            user_vote_string = f"{inter.user.name} {gm_name}"
        
            # Проверяем, голосовал ли уже пользователь за данного ГМа
            with open('data.txt', 'r', encoding='utf-8') as votuum_gm_list:
                votes = votuum_gm_list.readlines()
                if any(user_vote_string in vote for vote in votes):
                    await inter.response.send_message("Вы уже проголосовали!", ephemeral=True)
                    return
        
            # Записываем голос пользователя
            if action == 'agree_vote':
                with open('data.txt', 'a', encoding='utf-8') as file:
                    file.write(f"{user_vote_string} agree\n")
            elif action == 'opposite_vote':
                with open('data.txt', 'a', encoding='utf-8') as file:
                    file.write(f"{user_vote_string} opposite,   \n")
        
            # Подсчитываем количество голосов "agree" и "opposite" за каждый gm_name
            agree_count = 0
            opposite_count = 0
            with open('data.txt', 'r', encoding='utf-8') as votuum_gm_list:
                votes = votuum_gm_list.readlines()
                for vote in votes:
                    if gm_name in vote:
                        if "agree" in vote:
                            agree_count += 1
                        elif "opposite" in vote:
                            opposite_count += 1
        
            # Деактивируем все кнопки после голосования
            for row in inter.message.components:
                for button in row.children:
                    button.disabled = True
        
            # Редактируем сообщение и отправляем подтверждение пользователю
            try:
                await inter.response.edit_message(components=inter.message.components)
                await inter.followup.send(
                    f"Вы успешно проголосовали!",
                    ephemeral=True),
                embed = disnake.Embed(
                    title=f"Счет за {gm_name}",
                    description=f"**За** {gm_name}: {agree_count}. \n **Против** {gm_name}: {opposite_count}",
                    color=disnake.Color.blurple()
                )
                await channel.send(embed=embed)
            except Exception as e:
                await inter.response.send_message(
                    f"Вы успешно проголосовали!",
                    ephemeral=True),
                embed = disnake.Embed(
                    title=f"Счет за {gm_name}",
                    description=f"**За**: {agree_count}. \n **Против**: {opposite_count}",
                    color=disnake.Color.blurple()
                )
                await channel.send(embed=embed)
                print(f"Error: {e}")
    except:
       pass
    view = view_store.get(inter.message.id)
    interaction_id = get_interaction_id(inter)
    print(f"Button clicked: {inter.data.custom_id} by user {inter.author.id}, message_id={inter.message.id if inter.message else 'None'}, interaction_id={interaction_id}, interaction_type={type(inter).__name__}")
    custom_id = inter.data.custom_id
    view = view_store.get(inter.message.id) if inter.message else None
    print(f"View for {custom_id}: {type(view).__name__ if view else 'None'}, interaction_id={interaction_id}")

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

@bot.slash_command(name="pos_get_locations", description="Получить список локаций с доступными на них переходами.")
async def pos_get_locations(inter):
    await inter.response.send_message(locations)

@bot.slash_command(name="pos_item_check", description="Посмотреть данные зарегистрированного предмета")
async def pos_item_check(
    inter: disnake.ApplicationCommandInteraction,
    target: str = commands.Param(description="Начните вводить название или ID предмета для просмотра")
):
    # Подгружаем актуальные библиотеки
    library = await load_items_library()
    effects_lib = await load_effects_library() # Нужна для красивой конвертации ID эффектов в имена

    item_data = library.get(target)
    if not item_data:
        return await inter.response.send_message(
            f"❌ Предмет с техническим ID `{target}` не найден в базе данных.", 
            ephemeral=True
        )

    # Собираем данные предмета из JSON для рендеринга карточки
    item_type = item_data.get("type", "unknown")
    name = item_data.get("name", target)
    weight = item_data.get("weight_per_item", 0.0)
    base_price = item_data.get("base_price", 0)
    count_multiply = item_data.get("count_multiply", 1)
    description = item_data.get("description", "Описание отсутствует.")
    picture_url = item_data.get("picture_url")
    
    spec_info = ""

    # --- 1. ВЕТКА: Медицина, Еда, Артефакты ---
    if item_type in ["medicine", "food", "artefact"]:
        eff = item_data.get("use_effects", {})
        long_eff_data = item_data.get("long_effects", {})
        
        adds = long_eff_data.get("add", []) if isinstance(long_eff_data, dict) else []
        removes = long_eff_data.get("remove", []) if isinstance(long_eff_data, dict) else []
        
        adds_names = [effects_lib.get(x, {}).get("name", x) for x in adds if x]
        removes_names = [effects_lib.get(x, {}).get("name", x) for x in removes if x]
        
        adds_str = ", ".join(adds_names) if adds_names else "Отсутствуют"
        removes_str = ", ".join(removes_names) if removes_names else "Отсутствуют"
        
        if item_type != "artefact":
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
    
    # --- 2. ВЕТКА: Огнестрел, Ножи, Модификации оружия (ОБНОВЛЕНО) ---
    elif item_type in ["weapon", "melee_weapon", "gun_modification"]:
        stats = item_data.get("base_stats", {})
        text_feat = item_data.get("text_feature", "Отсутствует")
        
        if item_type == "melee_weapon":
            dmg = item_data.get("damage", [1, 0])
            spec_info = (
                f"**[Боевые характеристики холодного оружия]**\n"
                f"• Урон: `{format_dice_array(dmg)}`\n"
                f"• Особое свойство: *{text_feat}*"
            )
        elif item_type == "gun_modification":
            mod_af = item_data.get("mod_auto_fire")
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
            wep_class = item_data.get("weapon_class", "Пистолет")
            auto_fire_readable = "Да" if item_data.get("auto_fire", "no") == "yes" else "Нет"
            
            spec_info = (
                f"**[Боевые характеристики оружия]**\n"
                f"• Класс оружия: `{wep_class}`\n"
                f"• Автоматический огонь: `{auto_fire_readable}`\n"
                f"• Урон: `{format_dice_array(stats.get('damage', [1, 0]))}`\n"
                f"• Отдача: `{stats.get('recoil', 0)}` | Точность: `{stats.get('accuracy', 0)}`\n"
                f"• Кучность: `{stats.get('grouping', 3)}` | Надежность: `{stats.get('reliability', 10)}`\n"
                f"• Магазин: `{stats.get('max_magazine', 30)}`\n"
                f"• Особое свойство: *{text_feat}*"
            )
            
    # --- 3. ВЕТКА: Комбинезоны, Шлемы, Противогазы ---
    elif item_type in ["armor", "head_armor", "head_mask"]:
        text_feat = item_data.get("text_feature", "Отсутствует")
        
        if item_type == "armor":
            pts = item_data.get("armor_points", [10, 10]) 
            issued_effs = item_data.get("issued_effects", []) 
            issued_names = [effects_lib.get(x, {}).get("name", x) for x in issued_effs if x]
            effs_str = ", ".join(issued_names) if issued_names else "Отсутствуют"
            
            az_val = item_data.get("base_anomaly_resist", 0) # Читаем АЗ костюма
            daz_val = item_data.get("base_anomaly_mods", 6)   # Читаем ДАЗ костюма
            
            spec_info = (
                f"**[Характеристики комбинезона]**\n"
                f"• Класс защиты (очки): `{pts[1]} БП`\n"
                f"• Аномальная защита (АЗ): `{az_val}`\n"
                f"• Доступный ДАЗ (Ячейки модов): `{daz_val}`\n"
                f"• Встроенные эффекты: `{effs_str}`\n"
                f"• Особое свойство: *{text_feat}*"
            )
        else: # head_armor, head_mask
            b_armor = item_data.get("base_armor_points", 0)
            eff = item_data.get("issued_effect", "Отсутствует")
            readable_eff = effects_lib.get(eff, {}).get("name", eff) if eff else "Отсутствуют"
            
            resists = (
                f"• Электрозащита: `{item_data.get('electro_resist', 0)}` | Термозащита: `{item_data.get('termo_resist', 0)}`\n"
                f"• Химзащита: `{item_data.get('chemical_resist', 0)}` | Рад. защита: `{item_data.get('radiation_resist', 0)}`\n"
                f"• Пси-защита: `{item_data.get('psy_resist', 0)}`"
            )
            mask_info = f"• Совместим с маской: `{ 'Да' if item_data.get('have_mask', 'no') == 'no' else 'Нет' }\n" if item_type == "head_armor" else ""
            
            spec_info = (
                f"**[Характеристики защиты головы]**\n"
                f"• Базовая броня: `{b_armor} ПБ`\n"
                f"{mask_info}"
                f"• Эффект при ношении: `{readable_eff}`\n"
                f"**[Аномальные статы]**\n{resists}"
            )

    # --- 4. ВЕТКА: Бронеплиты, Модификаторы брони, Навесы ---
    elif item_type in ["armor_plate", "add_armor", "mounted_mod", "helmet_mods", "anomal_mod"]:
        if item_type == "anomal_mod":
            req = item_data.get("anomaly_mod_req", 1)
            resists = item_data.get("add_resist", {})
            spec_info = (
                f"**[Параметры аномального модуля]**\n"
                f"• Потребление ДАЗ (req): `{req}`\n\n"
                f"**Модификаторы сопротивления:**\n"
                f"• Мод. Электрозащиты: `{resists.get('electro_resist', 0)}`\n"
                f"• Мод. Термозащиты: `{resists.get('termo_resist', 0)}`\n"
                f"• Мод. Химзащиты: `{resists.get('chemical_resist', 0)}`\n"
                f"• Мод. Радиационной защиты: `{resists.get('radiation_resist', 0)}`"
            )
        elif item_type in ["armor_plate", "add_armor"]:
            pts = item_data.get("armor_points", [0, 0])
            eff_str = ""
            if item_type == "add_armor":
                eff = item_data.get("issued_effect")
                eff_str = f"• Эффект модуля: `{effects_lib.get(eff, {}).get('name', eff) if eff else 'Отсутствует'}`\n"
            spec_info = (
                f"**[Параметры бронеэлемента]**\n"
                f"• Очки брони (armor_points): `{pts[1]} ПБ`\n"
                f"{eff_str}"
            )
        elif item_type == "helmet_mods":
            mods = item_data.get("modificators", {})
            spec_info = (
                f"**[Параметры модификатора шлема]**\n"
                f"• Мод. ПБ шлема: `{mods.get('armor_points', 0)}`\n"
                f"• Мод. Электрозащиты: `{mods.get('electro_resist', 0)}`\n"
                f"• Мод. Термозащиты: `{mods.get('termo_resist', 0)}`\n"
                f"• Мод. Химзащиты: `{mods.get('chemical_resist', 0)}`\n"
                f"• Мод. Радиационной защиты: `{mods.get('radiation_resist', 0)}`\n"
                f"• Мод. Пси-защиты: `{mods.get('psy_resist', 0)}`"
            )
        else: # mounted_mod
            mods = item_data.get("modificators", {})
            effs = item_data.get("issued_effect", [])
            if isinstance(effs, str): effs = [effs]
            effs_str = ", ".join([effects_lib.get(x, {}).get("name", x) for x in effs if x]) if effs else "Отсутствуют"
            
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
    elif item_type in ["anomaly_detector", "artefact_detector", "head_eyes", "head_ears"]:
        eff_str = "Отсутствуют"
        if item_type in ["anomaly_detector", "artefact_detector", "head_ears"]:
            eff_data = item_data.get("long_effects", {})
            eff = eff_data.get("add") if isinstance(eff_data, dict) else None
            if eff: eff_str = effects_lib.get(eff, {}).get("name", eff)

        if item_type == "artefact_detector":
            spec_info = (
                f"**[Параметры электроники]**\n"
                f"• Класс прибора: `{item_data.get('class', 1)}`\n"
                f"• Эффект при работе устройства: `{eff_str}`\n"
                f"• Свойство работы: *{item_data.get('text_feature', 'Отсутствует')}*"
            )
        elif item_type in ["anomaly_detector", "head_ears"]:
            spec_info = (
                f"**[Параметры электроники]**\n"
                f"• Встроенный эффект прибора: `{eff_str}`\n"
                f"• Свойство работы: *{item_data.get('text_feature', 'Отсутствует')}*"
            )
        else: # head_eyes
            spec_info = f"**[Параметры электроники]**\n• Свойство работы: *{item_data.get('text_feature', 'Отсутствует')}*"
    elif item_type in ["artefact_container", "container_mod"]:
        if item_type == "artefact_container":
            spec_info = (
                f"**[Параметры контейнера артефактов]**\n"
                f"• Количество внутренних слотов: `{item_data.get('slots', 1)}`\n"
                f"• Класс радиационной защиты: `{item_data.get('radiation_protection_class', 1)}`"
            )
        else:
            spec_info = (
                f"**[Модификаторы контейнеров]**\n"
                f"• Изменение емкости (слоты): `+{item_data.get('mod_slots', 0)}`\n"
                f"• Повышение рад. защиты (класс): `+{item_data.get('mod_radiation_protection', 0)}`"
            )
    else:
        spec_info = "**[Статичный предмет]**\nУникальные боевые или медицинские коэффициенты отсутствуют."

    # --- Сборка читаемого описания ---
    readable_type = READABLE_ITEM_TYPES.get(item_type, item_type)
    stack_status = "Да" if item_data.get("stackable") == "yes" else "Нет"
    del_status = "Нет" if item_data.get("deletable") == "no" else "Да"
    
    info = (
        f"**Технический ID:** `{target}`\n"
        f"**Имя:** {name}\n"
        f"**Категория:** `{readable_type}`\n"
        f"**Вес:** `{weight} кг` | **Цена:** `{base_price} RU`\n"
        f"**Множитель закупки:** `x{count_multiply}`\n"
        f"**Складываемый:** `{stack_status}` | **Удаляемый:** `{del_status}`\n"
        f"**Описание:** *{description}*\n\n"
    )
    
    if item_type not in ["narrative", "crafts", "instruments", "ammo", "body_part", "grenade"]:
        info += f"**Специфичные свойства предмета:**\n{spec_info}"

    embed = disnake.Embed(title="Информация о предмете", description=info, color=disnake.Color.red())
    if picture_url and picture_url.startswith(("http://", "https://")):
        embed.set_image(url=picture_url)
    embed.set_footer(text="© By Bon Shinomiya")

    await inter.response.send_message(embed=embed, ephemeral=True)

@pos_item_check.autocomplete("target")
async def pos_item_check_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    # Загружаем библиотеку предметов
    try:
        library = await load_items_library()
    except:
        return []
    
    choices = []
    for tech_id, data in library.items():
        name = data.get("name", tech_id)
        # Ищем совпадения без учета регистра по имени или техническому ID
        if string.lower() in name.lower() or string.lower() in tech_id.lower():
            choices.append(disnake.OptionChoice(name=f"{name} ({tech_id})", value=tech_id))
            
    # Discord поддерживает максимум 25 вариантов в выпадающем списке автокомплита
    return choices[:25]

@bot.slash_command(name="pos_money_rp_add", description="Выдать рубли конкретному персонажу игрока")
async def pos_money_rp_add(
    inter: disnake.ApplicationCommandInteraction, 
    target: disnake.Member,
    char: str = commands.Param(description="Выберите персонажа игрока"),
    amount: int = commands.Param(description="Количество рублей")
):
    if amount <= 0: return await inter.response.send_message("❌ Сумма должна быть больше нуля!", ephemeral=True)
    
    character_path = f"user_profiles/{target.id}/{char}"
    stats_file = f"{character_path}/char_stats.json"
    
    if not os.path.exists(stats_file):
        return await inter.response.send_message("❌ Указанный персонаж или его файл характеристик не найдены.", ephemeral=True)
    
    async with get_char_lock(character_path):
        async with aiofiles.open(stats_file, "r", encoding="utf-8") as f:
            stats_data = json.loads(await f.read())
            
        if "rubles" not in stats_data[0]: stats_data[0]["rubles"] = 0
        stats_data[0]["rubles"] += amount
        
        async with aiofiles.open(stats_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(stats_data, ensure_ascii=False, indent=4))
            
    await inter.response.send_message(f"✅ Успешно выдано `{amount} RU` персонажу **{char}** (Игрок: {target.display_name}).")

@bot.slash_command(name="pos_money_rp_remove", description="Изъять рубли у конкретного персонажа игрока")
async def pos_money_rp_remove(
    inter: disnake.ApplicationCommandInteraction, 
    target: disnake.Member,
    char: str = commands.Param(description="Выберите персонажа игрока"),
    amount: int = commands.Param(description="Количество рублей")
):
    if amount <= 0: return await inter.response.send_message("❌ Сумма должна быть больше нуля!", ephemeral=True)
    
    character_path = f"user_profiles/{target.id}/{char}"
    stats_file = f"{character_path}/char_stats.json"
    
    if not os.path.exists(stats_file):
        return await inter.response.send_message("❌ Указанный персонаж не найден.", ephemeral=True)
    
    async with get_char_lock(character_path):
        async with aiofiles.open(stats_file, "r", encoding="utf-8") as f:
            stats_data = json.loads(await f.read())
            
        current = stats_data[0].get("rubles", 0)
        stats_data[0]["rubles"] = max(0, current - amount)
        
        async with aiofiles.open(stats_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(stats_data, ensure_ascii=False, indent=4))
            
    await inter.response.send_message(f"✅ Изъято `{amount} RU` у персонажа **{char}**.")

@bot.slash_command(name="pos_money_rp_pay", description="Передать рубли другому сталкеру")
async def pos_money_rp_pay(inter: disnake.ApplicationCommandInteraction, target: disnake.Member, amount: int, char: str = commands.Param(description="Выберите своего персонажа"), target_char: str = commands.Param(description="Выберите персонажа принимающего игрока")):
    if target.id == inter.author.id: return await inter.response.send_message("❌ Нельзя передавать деньги самому себе!", ephemeral=True)
    if amount <= 0: return await inter.response.send_message("❌ Сумма должна быть больше нуля!", ephemeral=True)
    
    character_path = f"user_profiles/{target.id}/{char}"
    target_character_path = f"user_profiles/{inter.author.id}/{char}"
    
    if not character_path: return await inter.response.send_message("❌ У вас нет персонажей.", ephemeral=True)
    if not target_character_path: return await inter.response.send_message("❌ У вас нет активного персонажа.", ephemeral=True)
    if not target: return await inter.response.send_message("❌ Получатель не найден в системе.", ephemeral=True)
    
    # Чтобы избежать дедлока при одновременной блокировке двух замков, упорядочиваем их по строковому пути
    paths = sorted([character_path, target_character_path])
    
    async with get_char_lock(paths[0]):
        async with get_char_lock(paths[1]):
            # Читаем и меняем у себя
            my_file = os.path.join(character_path, "char_stats.json")
            async with aiofiles.open(my_file, "r", encoding="utf-8") as f: my_stats = json.loads(await f.read())
            
            if my_stats[0].get("rubles", 0) < amount:
                return await inter.response.send_message("❌ У вашего персонажа недостаточно денег для перевода!", ephemeral=True)
                
            # Читаем и меняем у цели
            target_file = os.path.join(target_character_path, "char_stats.json")
            async with aiofiles.open(target_file, "r", encoding="utf-8") as f: target_stats = json.loads(await f.read())
            
            my_stats[0]["rubles"] = my_stats[0].get("rubles", 0) - amount
            target_stats[0]["rubles"] = target_stats[0].get("rubles", 0) + amount
            
            async with aiofiles.open(my_file, "w", encoding="utf-8") as f: await f.write(json.dumps(my_stats, ensure_ascii=False, indent=4))
            async with aiofiles.open(target_file, "w", encoding="utf-8") as f: await f.write(json.dumps(target_stats, ensure_ascii=False, indent=4))
            
    await inter.response.send_message(f"💸 Сталкер **{my_stats[0].get('char_name')}** передал **{target_stats[0].get('char_name')}** `{amount} RU` из рук в руки.")

@pos_money_rp_pay.autocomplete("target_char")
async def pos_money_rp_pay_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    player = inter.filled_options.get("target")
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


# Привязываем автокомплиты к командам валюты
@pos_money_rp_add.autocomplete("char")
@pos_money_rp_remove.autocomplete("char")
@pos_money_rp_add.autocomplete("char")
async def money_char_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    return await gms_char_autocomplete(inter, string)

@bot.slash_command(name="pos_item_give", description="Выдать предмет конкретному персонажу")
async def pos_item_give(
    inter: disnake.ApplicationCommandInteraction, 
    target: disnake.Member,
    char: str = commands.Param(description="Выберите персонажа игрока"),
    item_id: str = commands.Param(description="Технический ID предмета из UIMS"),
    amount: int = commands.Param(default=1, description="Количество предметов")
):
    character_path = f"user_profiles/{target.id}/{char}"
    
    items_lib = await load_items_library() # Функция загрузки базы из inventory.py
    if item_id not in items_lib: 
        return await inter.response.send_message("❌ Такого технического ID нет в общей базе!", ephemeral=True)
    
    # Наша универсальная функция начисления из inventory.py
    success = await add_item_to_inventory(character_path, item_id, items_lib, amount)
    if success:
        await inter.response.send_message(f"📦 ГМ выдал предмет **{items_lib[item_id].get('name')}** (`{amount} шт.`) персонажу **{char}**.")
    else:
        await inter.response.send_message("❌ Не удалось выдать предмет. Проверьте, создан ли у персонажа инвентарь.", ephemeral=True)

@pos_item_give.autocomplete("item_id")
async def item_id_autocomplete(inter: disnake.ApplicationCommandInteraction, string: str):
    items_lib = await load_items_library()
    choices = []
    for tech_id, data in items_lib.items():
        name = data.get("name", tech_id)
        if string.lower() in name.lower() or string.lower() in tech_id.lower():
            choices.append(disnake.OptionChoice(name=name, value=tech_id))
    return choices[:25]

@bot.slash_command(name="pos_item_take", description="Изъять предмет у конкретного персонажа")
async def pos_item_take(
    inter: disnake.ApplicationCommandInteraction,
    target: disnake.Member,
    char: str = commands.Param(description="Выберите персонажа игрока"),
    target_id: str = commands.Param(description="Технический ID стака ИЛИ уникальный UUID предмета"),
    amount: int = commands.Param(default=1, description="Количество для стакающихся предметов")
):
    character_path = f"user_profiles/{target.id}/{char}"
    
    # Наша универсальная функция удаления из inventory.py[cite: 3]
    success = await remove_item_from_inventory(character_path, target_id, amount)
    if success:
        await inter.response.send_message(f"📉 ГМ успешно изъял предмет(ы) `[ID: {target_id}]` из инвентаря персонажа **{char}**.")
    else:
        await inter.response.send_message("❌ Ошибка изъятия! Неверный ID/UUID или у персонажа нет такого количества предметов.", ephemeral=True)

@pos_item_take.autocomplete("target_id")
async def item_take_autocomplete(inter: disnake.ApplicationCommandInteraction, string: str):
    # Узнаем, какого игрока и персонажа ГМ выбрал на предыдущих шагах
    player = inter.filled_options.get("target")
    char = inter.filled_options.get("char")
    
    u_id = None
    if hasattr(player, "id"):
        u_id = str(player.id)
    elif isinstance(player, str) and player.isdigit():
        u_id = player
        
    if not u_id or not char:
        return [disnake.OptionChoice(name="❌ Сначала выберите игрока и персонажа!", value="none")]

    # Формируем путь к файлу инвентаря конкретного персонажа
    inventory_path = f"user_profiles/{u_id}/{char}/char_inventory.json"
    items_lib_path = "chars_data/items_lib.json"
    
    if not os.path.exists(inventory_path):
        return []

    try:
        # Асинхронно читать не обязательно в автокомплите, чтобы не дропать таймаут Дискорда
        with open(inventory_path, "r", encoding="utf-8") as f:
            inv_data = json.load(f)
        with open(items_lib_path, "r", encoding="utf-8") as f:
            items_lib = json.load(f)
            
        static_bag = inv_data.get("inventory", {}).get("static", {})
        unique_bag = inv_data.get("inventory", {}).get("unique", {})
        
        choices = []
        
        # 1. Сканируем стакающиеся предметы в рюкзаке[cite: 3]
        for item_id, amount in static_bag.items():
            if amount <= 0: continue
            item_template = items_lib.get(item_id, {})
            name = item_template.get("name", item_id)
            
            display_name = f"📦 {name} [{item_id}] — {amount} шт."
            if string.lower() in display_name.lower():
                choices.append(disnake.OptionChoice(name=display_name[:100], value=item_id))

        # 2. Сканируем штучные уникальные предметы[cite: 3]
        for u_id, u_data in unique_bag.items():
            template_id = u_data.get("template", u_id)
            item_template = items_lib.get(template_id, {})
            name = u_data.get("username") or item_template.get("name", template_id)
            
            # Показываем ГМу прочность оружия/плиты, чтобы он видел, что удаляет[cite: 3]
            condition = ""
            if "durability" in u_data:
                condition = f" ({u_data['durability']}/10)"
            elif "armor_points" in u_data and isinstance(u_data["armor_points"], list):
                condition = f" ({u_data['armor_points'][0]}/{u_data['armor_points'][1]} ПБ)"
                
            display_name = f"🔺 {name}{condition} [{u_id}]"
            if string.lower() in display_name.lower():
                choices.append(disnake.OptionChoice(name=display_name[:100], value=u_id))
                
        # Сортируем и возвращаем первые 25 совпадений
        return choices[:25]
        
    except Exception:
        return []

# Привязываем автокомплиты к командам предметов
@pos_item_give.autocomplete("char")
@pos_item_take.autocomplete("char")
async def items_char_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    return await gms_char_autocomplete(inter, string)

@bot.slash_command(name="pos_shop", description="Открыть универсальный магазин Зоны")
async def pos_shop(
    inter: disnake.ApplicationCommandInteraction,
    char: str = commands.Param(description="Выберите вашего персонажа, который совершает покупку")
):
    character_path = f"user_profiles/{inter.author.id}/{char}"
    stats_file = f"{character_path}/char_stats.json"
    
    if not os.path.exists(stats_file):
        return await inter.response.send_message("❌ Указанный персонаж не найден или ещё не завершил создание.", ephemeral=True)
        
    items_lib = await load_items_library()
    if not items_lib:
        return await inter.response.send_message("❌ Техническая база предметов UIMS пуста. Обратитесь к ГМу.", ephemeral=True)

    # Создаем экземпляр торгового окна
    shop_menu = UniversalNPCShopView(
        user_id=inter.author.id,
        character_path=character_path,
        items_lib=items_lib
    )
    
    # Отрисовываем магазин (команда отправляет сообщение, видимое только самому игроку!)
    await shop_menu.send_shop_window(inter)

# Привязываем твой рабочий автокомплит персонажей, чтобы игрок видел только своих чаров
@pos_shop.autocomplete("char")
async def shop_char_autocomp(inter: disnake.ApplicationCommandInteraction, string: str):
    folder_path = f"user_profiles/{inter.author.id}"
    if not os.path.exists(folder_path): return []
    try:
        character_folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
        return [c for c in character_folders if string.lower() in c.lower()][:25]
    except: return []

@bot.event
async def on_ready():
    print(f"Запущен как {bot.user}!")


setup(bot)
bot.run(os.getenv("BOT_TOKEN"))

