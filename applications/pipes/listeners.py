"""
MIT License

Copyright (c) 2024-present japandotorg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import contextlib
import logging
from typing import Any, Dict, Optional

import discord
import TagScriptEngine as tse
from redbot.core import commands
from redbot.core.utils.chat_formatting import box

from ..abc import PipeMeta
from ..common.models import Answer, Application, Response, Types
from ..common.tagscript import DEFAULT_SETTINGS_MESSAGE, SettingsAdapter
from ..common.utils import GuildInteraction
from ..common.views import CancelButton, CancelView, ChoiceView, PatchedConfirmView, SkipButton

log: logging.Logger = logging.getLogger("red.seina.applications.pipes.listeners")


class Listeners(PipeMeta):

    @commands.Cog.listener()
    async def on_application_applied(
        self, interaction: GuildInteraction, app: Application
    ) -> None:
        if not app.questions:
            return await interaction.followup.send(
                "There are no questions configured for this application!", ephemeral=True
            )
        response: Response = Response(user=interaction.user.id)
        started_message: str = "\n".join(
            [
                "{idx}. {text}".format(idx=idx + 1, text=ques.text)
                for idx, ques in enumerate(app.questions)
            ]
        )
        try:
            original: discord.Message = await interaction.user.send(
                embed=discord.Embed(
                    title=app.description.title(),
                    description="**__Questions__**\n\n" + started_message,
                    timestamp=discord.utils.utcnow(),
                )
                .set_footer(text=interaction.guild.name)
                .set_thumbnail(url=getattr(interaction.guild.icon, "url", None))
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                "I failed to send you a dm, please check your dm settings.", ephemeral=True
            )
        except (ValueError, TypeError, discord.HTTPException) as exc:
            log.exception("Something went wrong!", exc_info=exc)
            return await interaction.followup.send(
                "Something went wrong, please try again later!", ephemeral=True
            )
        for idx, question in enumerate(app.questions):
            embed: discord.Embed = discord.Embed(
                title=app.description.title(),
                description="**__Question {}__**\n{}".format(idx + 1, question.text),
                color=discord.Color.from_str(app.settings.color),
            )
            embed.set_thumbnail(url=getattr(interaction.guild.icon, "url", None))
            embed.set_footer(text='click the "cancel" button to cancel the submission')
            content: str = discord.utils.MISSING
            type: Types = question.type
            if type.lower() == "text":
                view: CancelView = CancelView(required=question.required)
                try:
                    view.message = await interaction.user.send(embed=embed, view=view)
                except discord.HTTPException:
                    return await interaction.followup.send(
                        "Something went wrong, please try again later!", ephemeral=True
                    )
                try:
                    message: discord.Message = await interaction.client.wait_for(
                        "message",
                        check=lambda m: m.channel.id == original.channel.id,
                        timeout=300.0,
                    )
                except asyncio.TimeoutError:
                    await view.on_timeout()
                    with contextlib.suppress(discord.HTTPException):
                        await interaction.user.send(
                            "Application timed out while waiting for your response.",
                            reference=original.to_reference(fail_if_not_exists=False),
                        )
                    return await interaction.followup.send(
                        "Application timed out.", ephemeral=True
                    )
                await view.on_timeout()
                log.debug(view.cancel)
                if view.cancel:
                    return await interaction.followup.send(
                        "Application cancelled!", ephemeral=True
                    )
                elif view.skip:
                    content: str = "Skipped"
                elif message.content:
                    content: str = message.content
                else:
                    with contextlib.suppress(discord.HTTPException):
                        await interaction.user.send(
                            "Something went wrong, I failed to parse your response.",
                            reference=original.to_reference(fail_if_not_exists=False),
                        )
                    return await interaction.followup.send(
                        "Application failed, try again later.", ephemeral=True
                    )
            elif type.lower() == "choices" and len(question.choices) > 0:
                choice: ChoiceView = ChoiceView(question, required=question.required)
                choice.message = message = await interaction.user.send(embed=embed, view=choice)
                if not await choice.wait():
                    await choice.on_timeout()
                log.debug(choice.cancel)
                if choice.cancel:
                    return await interaction.followup.send(
                        "Application cancelled!", ephemeral=True
                    )
                elif choice.skip:
                    content: str = "Skipped"
                elif choice.answer is discord.utils.MISSING:
                    with contextlib.suppress(discord.HTTPException):
                        await interaction.user.send(
                            "Something went wrong, I failed to parse your response.",
                            reference=original.to_reference(fail_if_not_exists=False),
                        )
                    return await interaction.followup.send(
                        "Application failed, try again later.", ephemeral=True
                    )
                else:
                    content: str = choice.answer
            elif type.lower() == "boolean":
                confirm: PatchedConfirmView = PatchedConfirmView(
                    interaction.user, timeout=120.0, disable_buttons=True
                )
                confirm.confirm_button.label = None
                confirm.confirm_button.emoji = "✔️"
                confirm.dismiss_button.label = None
                confirm.dismiss_button.emoji = "✖️"
                confirm.add_item(CancelButton())
                if not question.required:
                    confirm.add_item(SkipButton())
                confirm.message = message = await interaction.user.send(embed=embed, view=confirm)
                await confirm.wait()
                log.debug(confirm.cancel)
                if confirm.cancel:
                    await confirm.on_timeout()
                    return await interaction.followup.send(
                        "Application cancelled!", ephemeral=True
                    )
                elif confirm.skip:
                    await confirm.on_timeout()
                    content: str = "Skipped"
                elif confirm.result is None:
                    await confirm.on_timeout()
                    with contextlib.suppress(discord.HTTPException):
                        await interaction.user.send(
                            "Application timed out while waiting for your response.",
                            reference=original.to_reference(fail_if_not_exists=False),
                        )
                    return await interaction.followup.send(
                        "Application timed out.", ephemeral=True
                    )
                elif confirm.result is False:
                    content: str = "No"
                else:
                    content: str = "Yes"
            else:
                continue
            answer: Answer = Answer(question=question.text, type=type.lower(), answer=content)
            response.answers.append(answer)
            try:
                await interaction.user.send(
                    "Your answer for question no. **{}** is -\n{}".format(
                        idx + 1, box(content[:1950])
                    )
                )
            except discord.HTTPException:
                return await interaction.followup.send(
                    "Something went wrong, I failed to send you a dm, please check your dm settings!",
                    ephemeral=True,
                )
        embed: discord.Embed = discord.Embed(
            title="Response",
            description=(
                "**Name**: {name}\n"
                "**Description**: {description}\n"
                "**User:** {user.mention} [`@{user.global_name} ({user.id})`]\n"
                "**Response ID**: {response}"
            ).format(
                name=app.name.lower(),
                description=app.description,
                user=interaction.user,
                response=response.id,
            ),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=interaction.user.global_name, icon_url=interaction.user.display_avatar.url
        )
        for idx, answer in enumerate(response.answers[:25]):
            embed.add_field(
                name="Question {}".format(idx + 1),
                value="- **{}**\n- {}".format(answer.question, answer.answer),
                inline=False,
            )
        channel: Optional[discord.TextChannel] = interaction.guild.get_channel(
            app.settings.channel
        )  # type: ignore
        if not channel:
            with contextlib.suppress(discord.HTTPException):
                await interaction.user.send(
                    "Something went wrong with the application settings, please contact an admin!",
                    reference=original.to_reference(fail_if_not_exists=False),
                )
            return await interaction.followup.send(
                "Something went wrong with the application settings, please contact an admin!",
                ephemeral=True,
            )
        try:
            message: discord.Message = await channel.send(embed=embed)
        except discord.HTTPException:
            with contextlib.suppress(discord.HTTPException):
                await interaction.user.send(
                    "Something went wrong with the application settings, please contact an admin!",
                    reference=original.to_reference(fail_if_not_exists=False),
                )
            return await interaction.followup.send(
                "Something went wrong with the application settings, please contact an admin!",
                ephemeral=True,
            )
        if app.settings.thread:
            with contextlib.suppress(discord.HTTPException):
                await message.create_thread(name="Response {}".format(response.id))
        app.responses.append(response)
        async with self.config.guild_from_id(interaction.guild.id).apps() as apps:
            try:
                apps[app.name.lower()]["responses"].append(response.model_dump(mode="python"))
            except KeyError:
                with contextlib.suppress(discord.HTTPException):
                    await interaction.user.send(
                        "Something went wrong, the application doesn't seem to exist anymore!",
                        reference=original.to_reference(fail_if_not_exists=False),
                    )
                return await interaction.followup.send(
                    "Failed because the application doesn't seem to exist anymore!", ephemeral=True
                )
        kwargs: Dict[str, Any] = await self.manager.process_tagscript(
            app.settings.message,
            {
                "settings": SettingsAdapter(app.settings),
                "guild": tse.GuildAdapter(interaction.guild),
                "server": tse.GuildAdapter(interaction.guild),
                "responses": tse.IntAdapter(len(app.responses)),
            },
        )
        if not kwargs:
            await self.manager.edit_setting_for(
                interaction.guild.id,
                name=app.name.lower(),
                object="message",
                value=DEFAULT_SETTINGS_MESSAGE,
            )
            kwargs: Dict[str, Any] = await self.manager.process_tagscript(
                DEFAULT_SETTINGS_MESSAGE,
                {
                    "settings": SettingsAdapter(app.settings),
                    "guild": tse.GuildAdapter(interaction.guild),
                    "server": tse.GuildAdapter(interaction.guild),
                    "responses": tse.IntAdapter(len(app.responses)),
                },
            )
        with contextlib.suppress(discord.HTTPException):
            await interaction.edit_original_response(**kwargs)
        with contextlib.suppress(discord.HTTPException):
            await interaction.user.send(
                "Application successfully submitted!\n\n**Response ID**: `{}`".format(response.id),
                reference=original.to_reference(fail_if_not_exists=False),
            )
        await interaction.followup.send(
            "Application successfully submitted!\n\n**Response ID**: `{}`".format(response.id),
            ephemeral=True,
        )
