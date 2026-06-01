# Авторство кода - Discord: @joemendozacomposer4432

import disnake
from configs import *

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

