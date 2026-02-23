from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .qbittorrent import QbittorrentClient

STATE_MAP = {
    "error": "出错",
    "missingFiles": "文件缺失",
    "uploading": "做种中",
    "pausedUP": "做种已暂停",
    "queuedUP": "排队做种",
    "stalledUP": "做种等待连接",
    "checkingUP": "做种校验中",
    "forcedUP": "强制做种",
    "allocating": "分配磁盘空间",
    "downloading": "下载中",
    "metaDL": "获取元数据",
    "pausedDL": "下载已暂停",
    "queuedDL": "排队下载",
    "stalledDL": "下载等待连接",
    "checkingDL": "下载校验中",
    "forcedDL": "强制下载",
    "checkingResumeData": "检查恢复数据",
    "moving": "移动中",
    "unknown": "未知状态",
}


@register("qbittorrent", "fengwei-dev", "一个用于管理 qbittorrent 的插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.client = None

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    async def get_client(self):
        if self.client is None:
            conn_info = {
                "host": self.config["server"],
                "username": self.config["username"],
                "password": self.config["password"],
            }
            self.client = QbittorrentClient(**conn_info)
        return self.client

    @filter.command_group("qbittorrent")
    async def qbittorrent(self, event: AstrMessageEvent):
        pass

    @qbittorrent.command("list")
    async def list(self, event: AstrMessageEvent, status_filter: str = "downloading"):
        """查询当前的种子列表，默认只查询下载中的种子"""  # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        client = await self.get_client()
        torrents_info = await client.get_torrents(status_filter=status_filter)  # pyright: ignore[reportArgumentType]
        if len(torrents_info) == 0:
            yield event.plain_result(
                f"当前没有 {status_filter} 中的种子"
            )  # 发送一条纯文本消息
            return
        torrents_info_str = "\n".join(
            [
                f"{i + 1}. {torrent['name']} {STATE_MAP.get(torrent['state'], torrent['state'])} {torrent['progress'] * 100:.2f}%"
                for i, torrent in enumerate(torrents_info)
            ]
        )
        yield event.plain_result(torrents_info_str)  # 发送一条纯文本消息

    @qbittorrent.command("add")
    async def add(self, event: AstrMessageEvent, urls: str):
        """添加一个种子"""  # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        client = await self.get_client()
        res = await client.add_torrent(urls=urls)
        if res == "Ok.":
            yield event.plain_result(f"添加种子 {urls} 成功")  # 发送一条纯文本消息
        else:
            yield event.plain_result(f"添加种子 {urls} 失败")  # 发送一条纯文本消息
