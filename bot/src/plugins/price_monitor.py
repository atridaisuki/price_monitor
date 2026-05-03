"""
价格监控插件

提供商品管理相关指令
"""
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="价格监控",
    description="商品价格监控管理",
    usage="""
    /添加商品 <名称> <URL> <目标价格> - 添加商品到监控
    /商品列表 - 查看所有监控商品
    /检查价格 - 手动触发价格检查
    /删除商品 <ID> - 删除指定商品
    """,
    type="application",
    homepage="https://github.com/yourusername/price-monitor",
    supported_adapters={"~onebot.v11"},
)

import httpx
from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.log import logger
from nonebot.rule import to_me

# 获取配置
config = get_driver().config
API_BASE_URL = getattr(config, "api_base_url", "http://web:8000")

# 注册指令
add_product = on_command(
    "添加商品",
    aliases={"add", "添加"},
    priority=5,
    block=True
)

list_products = on_command(
    "商品列表",
    aliases={"list", "列表"},
    priority=5,
    block=True
)

check_price = on_command(
    "检查价格",
    aliases={"check", "检查"},
    priority=5,
    block=True
)

delete_product = on_command(
    "删除商品",
    aliases={"del", "删除"},
    priority=5,
    block=True
)

get_product = on_command(
    "商品详情",
    aliases={"detail", "详情"},
    priority=5,
    block=True
)


@add_product.handle()
async def handle_add_product(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    添加商品到监控列表

    用法: /添加商品 商品名称 商品URL 目标价格
    示例: /添加商品 赛博朋克2077 https://store.steampowered.com/app/1091500 100
    """
    args_text = args.extract_plain_text().strip()

    if not args_text:
        await add_product.finish(
            "📝 用法说明\n"
            "━━━━━━━━━━━━━━━━\n"
            "/添加商品 <名称> <URL> <目标价格>\n\n"
            "示例:\n"
            "/添加商品 赛博朋克2077 https://store.steampowered.com/app/1091500 100"
        )

    parts = args_text.split()
    if len(parts) < 3:
        await add_product.finish("❌ 参数不足！需要：商品名称 商品URL 目标价格")

    name = parts[0]
    url = parts[1]

    try:
        target_price = float(parts[2])
    except ValueError:
        await add_product.finish("❌ 目标价格必须是数字！")

    # 调用 API 添加商品
    user_qq = str(event.get_user_id())
    try:
        async with httpx.AsyncClient() as client: #Bot->后端 通过http api交互
            response = await client.post(
                f"{API_BASE_URL}/api/products/",
                json={
                    "name": name,
                    "url": url,
                    "platform": "steam",
                    "target_price": target_price,
                    "user_qq": user_qq,
                },
                timeout=10.0
            )

            if response.status_code == 201:
                data = response.json()
                await add_product.finish(
                    f"✅ 商品添加成功！\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"ID: {data['id']}\n"
                    f"名称: {data['name']}\n"
                    f"目标价格: ¥{data['target_price']}\n"
                    f"绑定 QQ: {data.get('user_qq', user_qq)}\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"系统将自动监控价格变动"
                )
            else:
                error_msg = response.text
                await add_product.finish(f"❌ 添加失败: {error_msg}")

    except httpx.TimeoutException:
        await add_product.finish("❌ 请求超时，请稍后重试")
    except httpx.RequestError as e:
        logger.error(f"添加商品请求失败: {e}")
        await add_product.finish("❌ 网络错误，请检查服务是否正常")
    except Exception as e:
        logger.error(f"添加商品失败: {e}")
        await add_product.finish(f"❌ 添加失败: {str(e)}")


@list_products.handle()
async def handle_list_products(bot: Bot, event: MessageEvent):
    """查询商品列表"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/products/",
                timeout=10.0
            )

            if response.status_code == 200:
                products = response.json()

                if not products:
                    await list_products.finish("📦 暂无监控商品\n\n使用 /添加商品 开始监控")

                msg = "📦 商品监控列表\n" + "━" * 30 + "\n"

                for i, p in enumerate(products, 1):
                    current = f"¥{p['current_price']}" if p['current_price'] else "未检查"
                    status = "✅" if p['current_price'] and p['current_price'] <= p['target_price'] else "⏳"

                    msg += (
                        f"\n{status} [{p['id']}] {p['name']}\n"
                        f"   当前: {current} | 目标: ¥{p['target_price']}\n"
                        f"   平台: {p['platform']}\n"
                    )

                    if i < len(products):
                        msg += "   " + "─" * 25 + "\n"

                msg += "\n" + "━" * 30
                msg += f"\n共 {len(products)} 个商品"

                await list_products.finish(msg)
            else:
                await list_products.finish(f"❌ 查询失败: {response.text}")

    except httpx.TimeoutException:
        await list_products.finish("❌ 请求超时，请稍后重试")
    except Exception as e:
        logger.error(f"查询商品列表失败: {e}")
        await list_products.finish(f"❌ 查询失败: {str(e)}")


@check_price.handle()
async def handle_check_price(bot: Bot, event: MessageEvent):
    """手动触发价格检查"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/tasks/check-prices",
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                await check_price.finish(
                    "✅ 价格检查完成\n"
                    "━━━━━━━━━━━━━━━━\n"
                    f"商品总数: {summary.get('total_products', 0)}\n"
                    f"成功: {summary.get('success_count', 0)}\n"
                    f"失败: {summary.get('failure_count', 0)}\n"
                    f"历史记录: {summary.get('history_count', 0)}\n"
                    f"通知数: {summary.get('notification_count', 0)}"
                )
            else:
                await check_price.finish(f"❌ 启动失败: {response.text}")

    except httpx.TimeoutException:
        await check_price.finish("❌ 请求超时，请稍后重试")
    except Exception as e:
        logger.error(f"触发价格检查失败: {e}")
        await check_price.finish(f"❌ 启动失败: {str(e)}")


@delete_product.handle()
async def handle_delete_product(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    删除商品

    用法: /删除商品 商品ID
    示例: /删除商品 1
    """
    args_text = args.extract_plain_text().strip()

    if not args_text:
        await delete_product.finish(
            "📝 用法说明\n"
            "━━━━━━━━━━━━━━━━\n"
            "/删除商品 <商品ID>\n\n"
            "示例: /删除商品 1\n"
            "提示: 使用 /商品列表 查看商品ID"
        )

    try:
        product_id = int(args_text)
    except ValueError:
        await delete_product.finish("❌ 商品ID必须是数字！")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_BASE_URL}/api/products/{product_id}",
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                await delete_product.finish(
                    f"✅ 删除成功\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"已删除商品: {data['name']}"
                )
            elif response.status_code == 404:
                await delete_product.finish(f"❌ 商品不存在: ID {product_id}")
            else:
                await delete_product.finish(f"❌ 删除失败: {response.text}")

    except httpx.TimeoutException:
        await delete_product.finish("❌ 请求超时，请稍后重试")
    except Exception as e:
        logger.error(f"删除商品失败: {e}")
        await delete_product.finish(f"❌ 删除失败: {str(e)}")


@get_product.handle()
async def handle_get_product(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    查询商品详情

    用法: /商品详情 商品ID
    示例: /商品详情 1
    """
    args_text = args.extract_plain_text().strip()

    if not args_text:
        await get_product.finish(
            "📝 用法说明\n"
            "━━━━━━━━━━━━━━━━\n"
            "/商品详情 <商品ID>\n\n"
            "示例: /商品详情 1"
        )

    try:
        product_id = int(args_text)
    except ValueError:
        await get_product.finish("❌ 商品ID必须是数字！")

    try:
        async with httpx.AsyncClient() as client:
            # 获取商品信息
            response = await client.get(
                f"{API_BASE_URL}/api/products/{product_id}",
                timeout=10.0
            )

            if response.status_code == 404:
                await get_product.finish(f"❌ 商品不存在: ID {product_id}")
            elif response.status_code != 200:
                await get_product.finish(f"❌ 查询失败: {response.text}")

            product = response.json()

            # 获取价格历史
            history_response = await client.get(
                f"{API_BASE_URL}/api/products/{product_id}/history?limit=5",
                timeout=10.0
            )

            history = history_response.json() if history_response.status_code == 200 else []

            # 构造消息
            current = f"¥{product['current_price']}" if product['current_price'] else "未检查"
            status = "✅ 已达标" if product['current_price'] and product['current_price'] <= product['target_price'] else "⏳ 监控中"

            msg = (
                f"📦 商品详情\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"ID: {product['id']}\n"
                f"名称: {product['name']}\n"
                f"平台: {product['platform']}\n"
                f"当前价格: {current}\n"
                f"目标价格: ¥{product['target_price']}\n"
                f"状态: {status}\n"
            )

            if product.get('last_checked_time'):
                msg += f"最后检查: {product['last_checked_time'][:19]}\n"

            msg += f"链接: {product['url']}\n"

            if history:
                msg += f"\n📊 价格历史（最近5次）\n"
                msg += "━━━━━━━━━━━━━━━━\n"
                for h in history:
                    msg += f"¥{h['price']} - {h['check_time'][:19]}\n"

            await get_product.finish(msg)

    except httpx.TimeoutException:
        await get_product.finish("❌ 请求超时，请稍后重试")
    except Exception as e:
        logger.error(f"查询商品详情失败: {e}")
        await get_product.finish(f"❌ 查询失败: {str(e)}")
