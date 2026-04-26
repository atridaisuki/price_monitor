"""
点赞插件

给指定用户点赞（每天最多10次）
用法：/点赞 @用户  或  /点赞 QQ号
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.log import logger

like_cmd = on_command("点赞", aliases={"赞", "like"}, priority=5, block=True)


@like_cmd.handle()
async def handle_like(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    # 优先从 @mention 取 user_id
    target_id = None
    for seg in args:
        if seg.type == "at":
            target_id = int(seg.data["qq"])
            break

    # 没有 @ 就尝试从文本解析 QQ 号
    if target_id is None:
        text = args.extract_plain_text().strip()
        if text.isdigit():
            target_id = int(text)

    if target_id is None:
        await like_cmd.finish("用法：/点赞 @用户  或  /点赞 QQ号")

    try:
        await bot.send_like(user_id=target_id, times=10)
        await like_cmd.finish(f"已给 {target_id} 点赞 10 次！")
    except Exception as e:
        logger.error(f"点赞失败: {e}")
        await like_cmd.finish(f"点赞失败：{e}")
