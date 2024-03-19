from typing import Any, Dict, Final, List, final

import TagScriptEngine as tse
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number

boosted: Final[str] = "{member(mention)} just boosted the server."
unboosted: Final[str] = "{member(mention)} just unboosted the server."

TAGSCRIPT_LIMIT: Final[int] = 10_000

blocks: List[tse.Block] = [
    tse.LooseVariableGetterBlock(),
    tse.AssignmentBlock(),
    tse.CommandBlock(),
    tse.EmbedBlock(),
]

engine: tse.Interpreter = tse.Interpreter(blocks)


def process_tagscript(content: str, seed_variables: Dict[str, tse.Adapter] = {}) -> Dict[str, Any]:
    output: tse.Response = engine.process(content, seed_variables)
    kwargs: Dict[str, Any] = {}
    if output.body:
        kwargs["content"] = output.body[:2000]
    if embed := output.actions.get("embed"):
        kwargs["embed"] = embed
    return kwargs


class TagError(Exception):
    """Base exception class."""


@final
class TagCharacterLimitReached(TagError):
    """Raised when the TagScript character limit is reached."""

    def __init__(self, limit: int, length: int):
        super().__init__(
            f"TagScript cannot be longer than {humanize_number(limit)} (**{humanize_number(length)}**)."
        )


@final
class TagscriptConverter(commands.Converter[str]):
    async def convert(self, ctx: commands.Context, argument: str) -> str:  # type: ignore
        try:
            await ctx.cog.validate_tagscript(argument)  # type: ignore
        except TagError as e:
            raise commands.BadArgument(str(e))
        return argument
