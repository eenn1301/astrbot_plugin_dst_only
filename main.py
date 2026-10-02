import json
import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger

PLUGIN_NAME = "astrbot_plugin_dst_only"
TAVILY_API_URL = "https://api.tavily.com/search"


class DSTOnlyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        logger.info(
            f"[{PLUGIN_NAME}] 插件已加载，白名单域名: "
            f"{self.config.get('allowed_domains', [])}"
        )

    @filter.llm_tool(name="web_search_tavily")
    async def search_with_domain_restriction(
        self,
        event: AstrMessageEvent,
        query: str,
        max_results: int = 5,
    ):
        """
        使用 Tavily 进行联网搜索，自动限制为允许的域名范围。

        Args:
            query(string): 搜索关键词。
            max_results(int): 返回结果数量，默认 5 条。
        """
        # 读取域名白名单，过滤空字符串
        allowed_domains = [
            d.strip()
            for d in self.config.get("allowed_domains", [])
            if d.strip()
        ]

        # 读取 Tavily API Key
        tavily_keys = self.config.get("websearch_tavily_key", [])
        if not tavily_keys:
            yield event.plain_result("未配置 Tavily API Key，无法执行搜索。")
            return

        api_key = tavily_keys[0] if isinstance(tavily_keys, list) else tavily_keys

        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
        }

        # 核心修改：当存在白名单域名时，强制启用硬过滤模式
        if allowed_domains:
            payload["include_domains"] = allowed_domains
            # 关键参数：filter 模式会强制只返回白名单内的结果
            payload["include_domains_mode"] = "filter"

        logger.info(
            f"[{PLUGIN_NAME}] Tavily 搜索: query='{query}', "
            f"domains={allowed_domains}, mode=filter"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    TAVILY_API_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(
                            f"[{PLUGIN_NAME}] Tavily API 返回 {resp.status}: "
                            f"{error_text}"
                        )
                        yield event.plain_result(
                            f"Tavily 搜索失败（HTTP {resp.status}），请检查 API Key 和配置。"
                        )
                        return

                    data = await resp.json()

        except Exception as e:
            logger.error(f"[{PLUGIN_NAME}] Tavily 请求异常: {e}")
            yield event.plain_result(f"Tavily 请求出错: {str(e)}")
            return

        # 获取结果并进行二次过滤
        results = data.get("results", [])

        # 二次过滤：确保结果只来自指定域名
        filtered_results = [
            r for r in results
            if "dontstarve.huijiwiki.com" in r.get("url", "")
        ]

        if not filtered_results:
            yield event.plain_result(
                f"未找到与「{query}」相关的结果（已限制域名: {allowed_domains}）。"
            )
            return

        # 格式化输出
        lines = [f"🔍 搜索「{query}」的结果（仅限指定域名）：\n"]
        for i, r in enumerate(filtered_results, 1):
            title = r.get("title", "无标题")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            lines.append(f"**{i}. {title}**")
            lines.append(f"   {url}")
            if snippet:
                lines.append(f"   {snippet[:200]}...")
            lines.append("")

        yield event.plain_result("\n".join(lines))

    async def terminate(self):
        logger.info(f"[{PLUGIN_NAME}] 插件已卸载")