import aiohttp
import json
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import ProviderRequest

PLUGIN_NAME = "astrbot_plugin_dst_only"
TAVILY_API_URL = "https://api.tavily.com/search"


@register(PLUGIN_NAME, "你的名字", "仅允许 Tavily 搜索指定域名的插件", "1.0.0")
class DSTOnlyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.config = context.get_config()

    async def initialize(self):
        """插件加载时读取配置，并将域名白名单注入到 LLM 请求中。"""
        self.logger.info(f"[{PLUGIN_NAME}] 插件已加载，白名单域名: {self.config.get('allowed_domains', [])}")

    # ------------------------------------------------------------------
    # 方案 A：通过 OnLLMRequestEvent 拦截并修改内置工具的参数
    # ------------------------------------------------------------------
    @filter.on_llm_request()
    async def modify_tavily_tool_params(self, event: AstrMessageEvent, req: ProviderRequest):
        """
        在 LLM 请求发送前，如果请求中包含 web_search_tavily 工具调用，
        则自动追加 include_domains 和 include_domains_mode 参数。

        OnLLMRequestEvent 在 ProviderRequest 被核心预填充之后、
        发送给 LLM 提供者之前触发，可以安全地修改请求内容[reference:3]。
        """
        allowed_domains = self.config.get("allowed_domains", [])
        include_mode = self.config.get("include_domains_mode", "restrict")

        if not allowed_domains:
            return

        # 遍历所有消息，查找 assistant 的 tool_calls
        for msg in req.messages:
            if msg.get("role") != "assistant":
                continue
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                continue

            for tool_call in tool_calls:
                func = tool_call.get("function", {})
                if func.get("name") != "web_search_tavily":
                    continue

                # 解析原有参数
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}

                # 注入域名白名单参数
                args["include_domains"] = allowed_domains
                args["include_domains_mode"] = include_mode

                # 写回
                func["arguments"] = json.dumps(args, ensure_ascii=False)
                self.logger.info(
                    f"[{PLUGIN_NAME}] 已注入 Tavily 域名限制: "
                    f"domains={allowed_domains}, mode={include_mode}"
                )

    # ------------------------------------------------------------------
    # 方案 B（备选）：注册一个自定义工具，完全替代内置搜索
    # ------------------------------------------------------------------
    @filter.llm_tool(name="web_search_tavily")
    async def custom_tavily_search(
        self,
        event: AstrMessageEvent,
        query: str,
        max_results: int = 5,
    ):
        """
        自定义的 Tavily 搜索工具。该工具的名称与内置工具相同，
        如果 AstrBot 允许插件工具覆盖内置工具，则会优先调用此版本。
        如果内置工具优先，则方案 A 会生效。
        """
        allowed_domains = self.config.get("allowed_domains", [])
        include_mode = self.config.get("include_domains_mode", "restrict")

        tavily_keys = self.config.get("websearch_tavily_key", [])
        if not tavily_keys:
            return {"error": "未配置 Tavily API Key"}

        api_key = tavily_keys[0]

        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_domains": allowed_domains,
        }

        # restrict 模式下 Tavily 要求必须设置 include_domains[reference:4]
        if allowed_domains and include_mode == "restrict":
            payload["include_domains_mode"] = "restrict"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    TAVILY_API_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return {"error": f"Tavily API 返回 {resp.status}: {text}"}
                    data = await resp.json()
                    return data
        except Exception as e:
            return {"error": f"Tavily 请求失败: {str(e)}"}

    async def terminate(self):
        self.logger.info(f"[{PLUGIN_NAME}] 插件已卸载")