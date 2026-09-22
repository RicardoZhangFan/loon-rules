# loon-rules

个人维护的 Loon 远程分流规则，目前包含 Pixiv 和 Meta Muse，并为以后加入 OpenAI、Claude、Gemini、Steam、PlayStation、Xbox、Nintendo、YouTube、Netflix 和 Spotify 等服务预留统一结构。

## 设计原则

- `.lsr` 文件只描述“哪些请求属于某个服务”，不把节点名称或线路写死。
- 出口策略由 Loon 主配置中 `[Remote Rule]` 的 `policy=` 指定，因此同一个规则文件可以随时切换日本、香港或其他策略组。
- 每个服务单独一个文件，规则变更后只需更新 GitHub，Loon 即可更新远程规则。
- 采用“最小充分集”：只加入服务自身域名，不把 Cloudflare、Google、Akamai 等公共 CDN 整体纳入。

## 目录结构

```text
loon-rules/
├── README.md
├── Loon/
│   ├── MetaMuse.lsr
│   └── Pixiv.lsr
└── examples/
    └── loon-remote-rule.conf
```

## 立即在 Loon 中使用

确保你的 Loon 配置中已经存在名为 `日本策略` 的策略组，然后把下面这一行放到 `[Remote Rule]` 段：

```ini
https://raw.githubusercontent.com/RicardoZhangFan/loon-rules/main/Loon/Pixiv.lsr, policy=日本策略, tag=Pixiv, enabled=true
https://raw.githubusercontent.com/RicardoZhangFan/loon-rules/main/Loon/MetaMuse.lsr, policy=美国策略, tag=MetaMuse, enabled=true
```

如果你的策略组名称不同，只替换对应 `policy=` 后面的名称；不要修改 Raw URL。规则更新后，在 Loon 的远程规则面板手动更新，或等待 Loon 的更新机制执行。

## Pixiv 规则范围

### 核心域名

`Loon/Pixiv.lsr` 当前用两条核心规则覆盖 Pixiv 的主要流量：

```text
DOMAIN-SUFFIX,pixiv.net
DOMAIN-SUFFIX,pximg.net
```

- `pixiv.net` 是后缀匹配，会同时覆盖 `www.pixiv.net`、`app-api.pixiv.net`、`oauth.secure.pixiv.net` 等子域，不需要逐个重复添加。
- `pximg.net` 覆盖 Pixiv 图片和漫画等资源常用的图片域名，例如 `i.pximg.net`。只配置 `pixiv.net` 而遗漏它，常见结果是网页能打开但图片加载异常。

### 已纳入的官方关联服务

以下域名已放入同一个文件，但单独标为关联服务；如果你只使用 Pixiv 主站和 App，可以将这四行删除或注释：

```text
DOMAIN-SUFFIX,fanbox.cc
DOMAIN-SUFFIX,pixivision.net
DOMAIN-SUFFIX,pixiv.me
DOMAIN-SUFFIX,pixivsketch.net
```

- `fanbox.cc`：pixivFANBOX。
- `pixivision.net`：pixivision 相关站点。
- `pixiv.me`：Pixiv 旧式/短链接域名，保留它可避免旧链接未按预期分流。
- `pixivsketch.net`：Pixiv Sketch 相关域名。

默认没有加入 `booth.pm`、`pixiv.co.jp`、`pixiv.help`、`pixiv.org`、`pixiv.cat`、`ads-pixiv.net` 或 `pixiv-recommend.net`。它们要么是独立服务、帮助/企业站点、历史/边缘域名，要么不属于 Pixiv 主站的必要依赖；如果以后确认自己需要，再单独加入，避免误伤其他流量。

## Meta Muse 规则范围

### 推荐的 Loon 配置

在 `[Remote Rule]` 中加入：

```ini
https://raw.githubusercontent.com/RicardoZhangFan/loon-rules/main/Loon/MetaMuse.lsr, policy=美国策略, tag=MetaMuse, enabled=true
```

`美国策略` 应该是一个固定、稳定的美国出口。注册、首次登录和前几次使用建议保持同一个美国出口，不要在美国、日本、香港之间来回切换。Loon 只能处理本机客户端到 Muse/Meta 的连接，不能改变账号的地区资格；Meta 官方当前仍说明 Muse 正在美国的 iOS、Android 和 `muse.ai` rollout。

### 文件里包含的域名

`Loon/MetaMuse.lsr` 不是把所有 Meta 业务整体代理，而是覆盖当前公开 Web 客户端能观察到的几类依赖：

- `muse.ai`：Muse Web 客户端、`auth.muse.ai` 等子域。
- `meta.ai`：Meta AI/Muse 的实时通道和相关接口子域。
- `auth.meta.com`、`www.facebook.com`、`www.instagram.com`：当前 Muse 登录跳转链。
- `fbcdn.net`、`cdninstagram.com`、`fbsbx.com`、`connect.facebook.net`：第一方脚本、媒体和登录资源。
- `metaaiusercontent.com`、`ecto1usercontent.com`、`meta-agents-apps.workers.dev`：当前 Web 客户端声明的内容和嵌入资源域名。

这里没有加入整个 `facebook.com`、`instagram.com`、`meta.com`、`stripe.com` 或 Google 域名，以免把其他 App 的全部流量一起送进美国策略。如果你之后启用了 Facebook/Instagram Connector，并且只在 OAuth 授权阶段出现循环，可临时在主配置的 `[Rule]` 段加入：

```ini
DOMAIN-SUFFIX,facebook.com,美国策略
DOMAIN-SUFFIX,instagram.com,美国策略
```

### Loon 能解决什么、不能解决什么

Loon 规则可以帮助你：

- 打开 `muse.ai`，完成客户端和 Meta 登录跳转。
- 让 Muse Web/App 的本地会话、实时连接和资源加载走美国出口。
- 减少中国大陆网络下白屏、登录循环和对话连接失败。

Loon 规则不能保证：

- Meta 账号一定获得 Muse 资格；官方仍可能按账号历史、地区和 rollout 状态判断。
- Muse Secure VM 中的浏览器使用美国出口。Muse 的任务执行和 Connector 流量主要发生在 Meta 云端 VM，不经过你设备上的 Loon。
- 国内网站、验证码、扫码登录、微信/支付宝支付等在 Muse 云端 VM 中一定可用。

如果你在 Loon 中已经使用了全局美国策略，可以先只加上面的远程规则；如果使用自动分流，确认 `MetaMuse` 规则位于最终 `FINAL` 兜底之前，并且 `policy=美国策略` 的策略组确实存在。

## `.lsr` 文件怎么写

远程规则文件使用 Loon 支持的规则类型，每行一条；不要在文件里写策略名：

```text
# 精确匹配
DOMAIN,api.example.com

# 匹配该域名及所有子域名
DOMAIN-SUFFIX,example.com

# IP 规则需要时可使用 no-resolve
IP-CIDR,203.0.113.0/24,no-resolve
```

规则文件中的 `DOMAIN-SUFFIX,example.com` 只是匹配条件，真正的出口由主配置中的 `policy=` 决定。

## 新增一个服务

例如新增 Claude：

1. 创建 `Loon/Claude.lsr`，只放 Claude 自身确认过的域名。
2. 在主配置 `[Remote Rule]` 中添加：

   ```ini
   https://raw.githubusercontent.com/RicardoZhangFan/loon-rules/main/Loon/Claude.lsr, policy=美国策略, tag=Claude, enabled=true
   ```

3. 检查域名是否误包含公共 CDN 或其他服务的共享域名。
4. 提交并推送到 `main` 分支，Loon 更新远程规则即可同步。

## 如何获得 GitHub Raw URL

通用格式为：

```text
https://raw.githubusercontent.com/<USERNAME>/<REPOSITORY>/<BRANCH>/<PATH>
```

本仓库当前的 Pixiv Raw URL 是：

```text
https://raw.githubusercontent.com/RicardoZhangFan/loon-rules/main/Loon/Pixiv.lsr
```

Meta Muse Raw URL：

```text
https://raw.githubusercontent.com/RicardoZhangFan/loon-rules/main/Loon/MetaMuse.lsr
```

也可以在 GitHub 文件页面点击 **Raw** 获取；Loon 使用 Raw 文本地址，不使用普通的 `github.com/.../blob/...` 页面地址。

## 维护流程

推荐在本地维护：

```bash
git clone https://github.com/RicardoZhangFan/loon-rules.git
cd loon-rules

# 编辑或新增 Loon/*.lsr
git diff --check
git add README.md Loon/ examples/
git commit -m "Update Loon rules"
git push origin main
```

如果从另一个空目录初始化仓库，可使用：

```bash
git init
git branch -M main
git remote add origin https://github.com/RicardoZhangFan/loon-rules.git
git add README.md Loon/ examples/
git commit -m "Add Loon remote rules"
git push -u origin main
```

## 参考

- [Loon 官方手册](https://github.com/Loon0x00/LoonManual)
- [Loon 官方示例配置](https://github.com/Loon0x00/LoonExampleConfig/blob/master/example.conf)
- [Loon 官方远程规则示例文件](https://github.com/Loon0x00/LoonExampleConfig/blob/master/Rule/ExampleRule.list)
- [luestr/ProxyResource 配置索引](https://github.com/luestr/ProxyResource)
- [ACL4SSR Pixiv 规则（用于交叉核对核心域名）](https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Pixiv.list)
- [pixiv 官方账号说明](https://www.pixiv.help/hc/en-us/articles/55002843574681-About-pixiv-official-accounts)
- [pixivFANBOX 官方帮助中心](https://fanbox.pixiv.help/hc/en-us/)
- [Meta：Introducing Muse](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/)
- [Meta：How We Built Safety Into Muse](https://security.muse.ai/)
- [Muse 官方入口](https://muse.ai/)
