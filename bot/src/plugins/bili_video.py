"""
B 站视频下载插件

检测消息中的 B 站链接（纯文字+小程序卡片），下载视频并直接发送
"""
import re
import os
import json
import asyncio
import tempfile
import httpx
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.log import logger

BILI_PATTERN = re.compile(
    r"(BV[a-zA-Z0-9]{10})"
    r"|(?:av|AV)(\d+)"
    r"|b23\.tv/([a-zA-Z0-9]+)"
    r"|bilibili\.com/video/(BV[a-zA-Z0-9]{10}|(?:av|AV)\d+)"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

bili_video = on_message(priority=7, block=False)


def _get_cookie() -> str:
    return os.environ.get("BILI_COOKIE", "")


def _search_bili_url(obj) -> str:
    """递归搜索任意层级中包含 bilibili 的 URL 字段"""
    if isinstance(obj, dict):
        for key in ("jumpUrl", "qqdocurl", "url"):
            val = obj.get(key, "")
            if isinstance(val, str) and "bilibili" in val:
                return val
        for v in obj.values():
            result = _search_bili_url(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _search_bili_url(item)
            if result:
                return result
    return ""


def _extract_from_card(seg_data: str) -> str:
    """从 QQ 小程序卡片 JSON 中提取 B 站链接"""
    try:
        return _search_bili_url(json.loads(seg_data))
    except Exception:
        # JSON 不完整时用正则直接搜
        m = re.search(r'https?://[^\s"\']+bilibili\.com/video/[^\s"\']+', seg_data)
        if m:
            return m.group()
        m = re.search(r'https?://b23\.tv/[a-zA-Z0-9]+', seg_data)
        if m:
            return m.group()
    return ""


async def _resolve_short_url(short_code: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
        resp = await client.get(f"https://b23.tv/{short_code}", headers=HEADERS)
        m = re.search(r"BV[a-zA-Z0-9]{10}", str(resp.url))
        return m.group() if m else ""


async def _get_play_info(bvid: str = "", aid: int = 0) -> dict:
    cookie = _get_cookie()
    headers = {**HEADERS, "Cookie": cookie} if cookie else HEADERS

    params = {"bvid": bvid} if bvid else {"aid": aid}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            "https://api.bilibili.com/x/web-interface/view",
            params=params, headers=headers
        )
        data = r.json()
        if data.get("code") != 0:
            raise ValueError(f"获取视频信息失败: {data.get('message')}")
        info = data["data"]
        cid = info["cid"]

    play_params = {
        "bvid": bvid or "",
        "aid": aid or info.get("aid", 0),
        "cid": cid,
        "fnval": 4048,
        "fnver": 0,
        "fourk": 1,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            "https://api.bilibili.com/x/player/wbi/playurl",
            params=play_params, headers=headers
        )
        play_data = r.json()
        if play_data.get("code") != 0:
            raise ValueError(f"获取播放地址失败: {play_data.get('message')}")

    dash = play_data["data"]["dash"]
    videos = sorted(dash["video"], key=lambda x: x["id"], reverse=True)
    video = next((v for v in videos if v["id"] <= 80), videos[-1])
    audio = sorted(dash["audio"], key=lambda x: x["id"], reverse=True)[0]

    return {
        "title": info["title"],
        "video_url": video["baseUrl"],
        "audio_url": audio["baseUrl"],
    }


async def _download_stream(url: str, path: str) -> None:
    headers = {**HEADERS}
    cookie = _get_cookie()
    if cookie:
        headers["Cookie"] = cookie
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        async with client.stream("GET", url, headers=headers) as resp:
            resp.raise_for_status()
            with open(path, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                    f.write(chunk)


async def _merge_video(video_path: str, audio_path: str, output_path: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac",
        output_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg 合并失败")


@bili_video.handle()
async def handle_bili_video(bot: Bot, event: MessageEvent):
    text = event.get_plaintext()

    # 检测小程序卡片
    for seg in event.message:
        if seg.type in ("json", "app"):
            raw = seg.data.get("data", "") or seg.data.get("content", "")
            url = _extract_from_card(raw)
            if url:
                text = url
                break

    match = BILI_PATTERN.search(text)
    if not match:
        return

    bvid = ""
    aid = 0
    if match.group(1):
        bvid = match.group(1)
    elif match.group(2):
        aid = int(match.group(2))
    elif match.group(3):
        bvid = await _resolve_short_url(match.group(3))
        if not bvid:
            await bili_video.finish("短链解析失败")
    elif match.group(4):
        raw = match.group(4)
        if raw.upper().startswith("BV"):
            bvid = raw
        else:
            aid = int(raw[2:])

    await bot.send(event, "正在下载视频，请稍候...")

    try:
        info = await _get_play_info(bvid=bvid, aid=aid)
    except Exception as e:
        logger.error(f"获取播放信息失败: {e}")
        await bili_video.finish(f"获取视频信息失败：{e}")

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.m4s")
        audio_path = os.path.join(tmpdir, "audio.m4s")
        output_path = os.path.join(tmpdir, "output.mp4")

        try:
            await asyncio.gather(
                _download_stream(info["video_url"], video_path),
                _download_stream(info["audio_url"], audio_path),
            )
            await _merge_video(video_path, audio_path, output_path)
        except Exception as e:
            logger.error(f"下载/合并失败: {e}")
            await bili_video.finish(f"下载失败：{e}")

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        if size_mb > 50:
            await bili_video.finish(f"视频太大（{size_mb:.1f}MB），超过 50MB 限制")

        with open(output_path, "rb") as f:
            video_data = f.read()

    await bili_video.finish(MessageSegment.video(video_data))
