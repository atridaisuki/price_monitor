#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoneBot2 机器人入口文件
"""
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter

# 初始化 NoneBot
nonebot.init()

# 获取驱动器
driver = nonebot.get_driver()

# 注册适配器
driver.register_adapter(ONEBOT_V11Adapter)

# 加载内置插件
# nonebot.load_builtin_plugins("echo")

# 加载第三方插件
# nonebot.load_plugin("nonebot_plugin_resolver2")

# 从配置文件加载插件（会自动加载 pyproject.toml 中配置的 plugin_dirs）
nonebot.load_from_toml("pyproject.toml")

# 加载自定义插件（已在 pyproject.toml 中配置，无需重复加载）
# nonebot.load_plugins("src/plugins")


if __name__ == "__main__":
    nonebot.run()
