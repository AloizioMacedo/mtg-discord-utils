import shlex
from typing import Any, Callable

import discord


def commands(f: Callable) -> Callable:
    async def wrapper(self, message: discord.Message, rest_of_command: str):
        content = rest_of_command

        content = content.strip()
        sh = shlex.shlex(content)
        sh.whitespace = " "
        sh.whitespace_split = True
        split_content = list(sh)

        organized_commands: dict[str, Any] = {
            "message": message,
            "main": "",
            "self": self,
        }

        while split_content:
            if split_content[0].startswith("--"):
                if len(split_content) == 1 or split_content[1].startswith(
                    "--"
                ):
                    organized_commands[split_content[0][2::]] = True
                    split_content = split_content[1::]
                else:
                    organized_commands[split_content[0][2::]] = split_content[
                        1
                    ].strip('"')
                    split_content = split_content[2::]
            else:
                organized_commands["main"] = " ".join(split_content)
                split_content = []

        return await f(**organized_commands)

    return wrapper
