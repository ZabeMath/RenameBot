#!/usr/bin/env python
from sseclient import SSEClient as EventSource
from ib3 import Bot
from ib3.auth import SASL
from ib3.connection import SSL
from ib3.mixins import DisconnectOnError
from ib3.nick import Ghost
from irc.client import NickMask
import irc.client
import threading
import json

import config

def nm_to_n(nm):
    """Convert nick mask from source to nick."""
    return NickMask(nm).nick

class FreenodeBot(SASL, SSL, DisconnectOnError, Ghost, Bot):
    def __init__(self):
        self.channel = config.channel
        self.nickname = config.nick

        super().__init__(
            server_list=[(config.server, 6697)],
            nickname=self.nickname,
            realname=self.nickname,
            ident_password=config.password,
            channels=[self.channel]
        )

    def on_ctcp(self, c, event):
        if event.arguments[0] == "VERSION":
            c.ctcp_reply(
                nm_to_n(event.source),
                "Bot for informing about global renames on " + self.channel
            )
        elif event.arguments[0] == "PING" and len(event.arguments) > 1:
            c.ctcp_reply(nm_to_n(event.source), "PING " + event.arguments[1])

    def msg(self, message, target=None):
        if not target:
            target = self.channel
        try:
            self.connection.privmsg(target, message)
        except:
            self.connection.privmsg(target, "The message is too long.")


class RecentChangesBot:
    def __init__(self):
        self.should_exit = False

    def start(self):
        stream = 'https://stream.wikimedia.org/v2/stream/recentchange'
        while not self.should_exit:
            try:
                for event in EventSource(stream):
                    if self.should_exit:
                        break

                    if event.event == 'message':
                        try:
                            change = json.loads(event.data)
                        except ValueError:
                            continue
                        if change['wiki'] == 'metawiki':
                            if change['type'] == 'log':
                                if change['log_type'] == 'gblrename':
                                    if change['log_action'] == 'rename':
                                        bot1.msg(
                                            "03%s globally renamed 12%s to 12%s: 07%s" %
                                            (
                                                change['user'],
                                                change['log_params']['olduser'],
                                                change['log_params']['newuser'],
                                                change['comment']
                                            )
                                        )
            except StopIteration:
                    pass
            except Exception as error:
                    print('Recent changes listener encountered an error: ' + repr(error))

class BotThread(threading.Thread):
    def __init__(self, bot):
        threading.Thread.__init__(self)
        self.b = bot

    def run(self):
        self.b.start()

def main():
    global bot1, bot2
    bot1 = FreenodeBot()
    bot2 = RecentChangesBot()

    try:
        freenodeThread = BotThread(bot1)
        rcThread = BotThread(bot2)

        freenodeThread.start()
        rcThread.start()
    except KeyboardInterrupt:
        bot1.disconnect('Killed by a KeyboardInterrupt')
    except Exception:
        bot1.disconnect('RenameBot encountered an unhandled exception')
    finally:
        raise SystemExit()

if __name__ == "__main__":
    main()
