# CPBot

A simple Discord bot that assists with competitive programming

This is intended to be a learning project for me, and a small tool to be used by the members of my college's Discord group for programmers.

### Features

- CPBot can fetch a list of upcoming contests from supported competitive programming sites. These are displayed when the associated command is invoked. Supports filtering by site and limiting by count.
- CPBot can monitor profiles of users on supported programming sites. This allows users to subscribe using their handle and be notified when their rating is updated after participation in a contest.

**Warning**: CPBot is intended to be a simple bot, and is not expected to be very robust or handle a large amount of activity. Much of that can be alleviated by using an official API wrapper such as [discord.py](https://github.com/Rapptz/discord.py), which I decided against for the sake of learning.

