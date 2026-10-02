# AstrBot 阿里云 DDNS Wiki 域名固定插件

## 📖 简介

本插件通过阿里云 DNS API，自动将你指定的 **Wiki 域名**解析到 AstrBot 所在服务器的当前公网 IP。  
无论服务器 IP 如何变化，你都可以通过固定的域名访问自建的 Wiki，例如：

- 饥荒 Wiki（Don't Starve Wiki）
- Minecraft Wiki
- Terraria Wiki
- 其他任何自建 Wiki 或 Web 服务

插件不局限于某一个 Wiki，你可以同时配置多个域名，分别指向不同的 Wiki 服务。

## ✨ 功能特性

- ✅ 自动检测服务器公网 IP 变化
- ✅ 通过阿里云 DNS API 实时更新解析记录
- ✅ 支持同时固定多个 Wiki 域名
- ✅ 可自定义检查间隔、TTL、解析类型（A / AAAA）
- ✅ 配置热重载，修改后无需重启 AstrBot
- ✅ 兼容 AstrBot 插件体系，开箱即用

## 🎯 适用场景

- 将 AstrBot 部署在家庭宽带或动态 IP 服务器上
- 自建 Wiki 服务（如饥荒 Wiki、Minecraft Wiki 等）需要固定域名访问
- 希望 AstrBot 通过固定域名调用 Wiki API 或进行网页搜索
- 需要对外提供稳定的 Wiki 访问入口

## 📦 安装

1. 在 AstrBot 插件市场搜索 **“阿里云 DDNS Wiki 固定”** 并安装。
2. 或手动将本插件文件夹放入 `AstrBot/data/plugins/` 目录下。
3. 安装依赖：

```bash
pip install aliyun-python-sdk-core aliyun-python-sdk-alidns
```

## ⚙️ 配置

在 AstrBot 配置文件中添加以下配置（请根据实际情况修改）：

```yaml
wiki_ddns:
  enabled: true
  access_key_id: "你的阿里云 AccessKey ID"
  access_key_secret: "你的阿里云 AccessKey Secret"
  region_id: "cn-hangzhou"          # 阿里云区域，通常保持默认
  check_interval: 300                # 检查间隔（秒）
  ip_echo_url: "https://api.ipify.org"  # 获取公网 IP 的接口
  domains:
    # 饥荒 Wiki 示例
    - domain: "dontstarve.example.com"
      rr: "@"                        # 主机记录，@ 表示根域名
      type: "A"
      ttl: 600
    # 其他 Wiki 示例
    - domain: "mcwiki.example.com"
      rr: "wiki"
      type: "A"
      ttl: 600
    - domain: "terraria.example.com"
      rr: "@"
      type: "A"
      ttl: 600
```

### 配置项说明

| 字段 | 说明 |
|------|------|
| `enabled` | 是否启用插件 |
| `access_key_id` | 阿里云 AccessKey ID，需具备 DNS 解析权限 |
| `access_key_secret` | 阿里云 AccessKey Secret |
| `region_id` | 阿里云区域，如 `cn-hangzhou` |
| `check_interval` | IP 检测间隔，单位秒，建议 300 以上 |
| `ip_echo_url` | 用于获取公网 IP 的 URL，可更换为其他可靠服务 |
| `domains` | 域名列表，每个条目包含 `domain`、`rr`、`type`、`ttl` |

## 🚀 使用

1. 完成上述配置后，重启 AstrBot 或重载插件。
2. 插件会在后台按 `check_interval` 定时检查公网 IP。
3. 一旦发现 IP 与 DNS 记录不符，会自动调用阿里云 API 更新解析。
4. 你可以在 AstrBot 日志中查看更新记录，例如：

```text
[WikiDDNS] 公网 IP 未变化，跳过更新。
[WikiDDNS] 检测到 IP 变化：1.2.3.4 -> 5.6.7.8，正在更新 dontstarve.example.com...
[WikiDDNS] 域名 dontstarve.example.com 更新成功。
```

## 📝 示例：同时固定饥荒 Wiki 和其他 Wiki

假设你有两台服务器或两个 Wiki 服务，分别使用不同的子域名：

```yaml
domains:
  - domain: "dontstarve.example.com"
    rr: "@"
    type: "A"
    ttl: 600
  - domain: "minecraft.example.com"
    rr: "wiki"
    type: "A"
    ttl: 600
```

插件会同时维护这两个域名的解析记录，确保它们始终指向当前服务器的公网 IP。

## ⚠️ 注意事项

- 请确保阿里云 AccessKey 具有 **AliyunDNSFullAccess** 或至少包含 DNS 解析权限。
- 公网 IP 获取依赖外部接口，若接口不稳定可自行更换 `ip_echo_url`。
- 本插件仅负责更新 DNS 解析，不涉及 Wiki 内容部署或 AstrBot 内部搜索逻辑。
- 如果服务器位于 NAT 后，请确保获取到的是真正的公网 IP。
- 首次使用建议将 `check_interval` 设置得稍短（如 60 秒）以便快速验证。

## 📄 许可证

MIT License

## 🙏 贡献与反馈

如有问题或建议，欢迎在 AstrBot 社区或插件仓库提交 Issue。