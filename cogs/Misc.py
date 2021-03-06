#!/usr/bin/env python3
# Copyright (c) 2016-2017, henry232323
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import discord
from discord.ext import commands
import datetime
from collections import Counter
from random import randint, choice
from time import monotonic
import os
import psutil
from itertools import chain


class Misc(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["rollthedice", "dice"])
    async def rtd(self, ctx, *dice: str):
        """Roll a number of dice with given sides (ndx notation)
        Example: rp!rtd 3d7 2d4
        Optional Additions:
            Test for success by adding a >/<#
            Grab the top n rolls by adding ^n
            Add to the final roll by just adding a number (pos or neg)
            
            Examples of all:
                rp!rtd 8d8 -12 15 ^4 >32
                
                -> Roll failed (30 > 32) ([8 + 7 + 6 + 6] + -12 + 15) (Grabbed top 4 out of 8)"""
        try:
            dice = list(dice)
            rolls = dict()
            add = []
            rel = None
            pp = None

            for die in dice:
                try:
                    number, sides = die.split("d")
                    number, sides = int(number), int(sides)
                    if number > 10:
                        await ctx.send("Too many dice! Cant roll that many!")
                        return
                    if sides > 1000:
                        await ctx.send("That die has much too many sides!")
                        return

                    rolls[sides] = [randint(1, sides) for x in range(number)]
                except ValueError:
                    try:
                        add.append(int(die))
                    except ValueError:
                        if die.startswith((">", "<")):
                            rel = die
                            val = int(rel.strip("<>"))
                            type = rel[0]
                        elif die.startswith("^"):
                            pp = int(die.strip("^"))

            if pp:
                s = list(chain(*rolls.values()))
                rolls.clear()
                rolls[0] = list()
                for d in range(pp):
                    mx = max(s)
                    s.remove(mx)
                    rolls[0].append(mx)

            total = sum(sum(x) for x in rolls.values()) + sum(add)

            if rel is not None:
                if type == "<":
                    if total < val:
                        succ = "suceeded"
                    else:
                        succ = "failed"
                else:
                    if total > val:
                        succ = "suceeded"
                    else:
                        succ = "failed"

                fmt = "Roll **{0}** ({1} {2} {3}) ([{4}] + {5})" if add else "Roll **{0}** ({1} {2} {3}) ([{4}])"
                all = "] + [".join(" + ".join(map(lambda x: str(x), roll)) for roll in rolls.values())
                msg = fmt.format(succ, total, type, val, all, " + ".join(map(lambda x: str(x), add)))
            else:
                fmt = "Rolled **{0}** ([{1}] + {2})" if add else "Rolled **{0}** ([{1}])"
                all = "] + [".join(" + ".join(map(lambda x: str(x), roll)) for roll in rolls.values())
                msg = fmt.format(total, all, " + ".join(map(lambda x: str(x), add)))

            if pp:
                msg += f" (Grabbed top {pp} out of {len(s) + pp})"

            await ctx.send(msg)
        except Exception as e:
            from traceback import print_exc
            print_exc()
            await ctx.send("Invalid syntax!")

    @commands.command()
    async def ping(self, ctx):
        '''
        Test the bot's connection ping
        '''
        a = monotonic()
        await (await self.bot.ws.ping())
        b = monotonic()
        ping = "`{:.3f}ms`".format((b - a) * 1000)
        msg = f"P{choice('aeiou')}ng {ping}"
        await ctx.send(msg)

    @commands.command()
    async def info(self, ctx):
        """Bot Info"""
        me = self.bot.user if not ctx.guild else ctx.guild.me
        appinfo = await self.bot.application_info()
        embed = discord.Embed()
        embed.set_author(name=me.display_name, icon_url=appinfo.owner.avatar_url, url="https://github.com/henry232323/PokeRPG-Bot")
        embed.add_field(name="Author", value='Henry#6174 (Discord ID: 122739797646245899)')
        embed.add_field(name="Library", value='discord.py (Python)')
        embed.add_field(name="Uptime", value=await self.bot.get_bot_uptime())
        embed.add_field(name="Servers", value="{} servers".format(len(self.bot.guilds)))
        embed.add_field(name="Commands Run", value='{} commands'.format(sum(self.bot.commands_used.values())))

        total_members = sum(len(s.members) for s in self.bot.guilds)
        total_online = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
        unique_members = set(map(lambda x: x.id, self.bot.get_all_members()))
        channel_types = Counter(isinstance(c, discord.TextChannel) for c in self.bot.get_all_channels())
        voice = channel_types[False]
        text = channel_types[True]
        embed.add_field(name="Total Members", value='{} ({} online)'.format(total_members, total_online))
        embed.add_field(name="Unique Members", value='{}'.format(len(unique_members)))
        embed.add_field(name="Channels", value='{} text channels, {} voice channels'.format(text, voice))

        a = monotonic()
        await (await self.bot.ws.ping())
        b = monotonic()
        ping = "{:.3f}ms".format((b - a) * 1000)

        embed.add_field(name="CPU Percentage", value="{}%".format(psutil.cpu_percent()))
        embed.add_field(name="Memory Usage", value=self.bot.get_ram())
        embed.add_field(name="Observed Events", value=sum(self.bot.socket_stats.values()))
        embed.add_field(name="Ping", value=ping)

        embed.add_field(name="Source", value="[Github](https://github.com/henry232323/RPGBot)")

        embed.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(delete_after=60, embed=embed)

    @commands.command()
    async def totalcmds(self, ctx):
        """Get totals of commands and their number of uses"""
        embed = discord.Embed()
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        for val in self.bot.commands_used.most_common(25):
            embed.add_field(name=val[0], value=val[1])
        embed.set_footer(text=str(ctx.message.created_at))
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx, command: str = None):
        """Displays my full source code or for a specific command.
        To display the source code of a subcommand you have to separate it by
        periods, e.g. tag.create for the create subcommand of the tag command.
        """
        source_url = 'https://github.com/henry232323/RPGBot'
        if command is None:
            await ctx.send(source_url)
            return

        code_path = command.split('.')
        obj = self.bot
        for cmd in code_path:
            try:
                obj = obj.get_command(cmd)
                if obj is None:
                    await ctx.send('Could not find the command ' + cmd)
                    return
            except AttributeError:
                await ctx.send('{0.name} command has no subcommands'.format(obj))
                return

        # since we found the command we're looking for, presumably anyway, let's
        # try to access the code itself
        src = obj.callback.__code__

        if not obj.callback.__module__.startswith('discord'):
            # not a built-in command
            location = os.path.relpath(src.co_filename).replace('\\', '/')
            final_url = '<{}/tree/master/{}#L{}>'.format(source_url, location, src.co_firstlineno)
        else:
            location = obj.callback.__module__.replace('.', '/') + '.py'
            base = 'https://github.com/Rapptz/discord.py'
            final_url = '<{}/blob/master/{}#L{}>'.format(base, location, src.co_firstlineno)

        await ctx.send(final_url)

    @commands.command()
    async def donate(self, ctx):
        """Donation information"""
        await ctx.send("Keeping the bots running takes money, "
                       "if several people would buy me a coffee each month, "
                       "I wouldn't have to worry about it coming out of my pocket. "
                       "If you'd like, you can donate to me here: https://ko-fi.com/henrys")

    @commands.command()
    async def feedback(self, ctx, *, feedback):
        """Give me some feedback on the bot"""
        with open("feedback.txt", "a+") as f:
            f.write(feedback + "\n")
        await ctx.send("Thank you for the feedback!")

    @commands.command(hidden=True)
    async def socketstats(self, ctx):
        delta = datetime.datetime.utcnow() - self.bot.uptime
        minutes = delta.total_seconds() / 60
        total = sum(self.bot.socket_stats.values())
        cpm = total / minutes

        fmt = '%s socket events observed (%.2f/minute):\n%s'
        await ctx.send(fmt % (total, cpm, self.bot.socket_stats))
