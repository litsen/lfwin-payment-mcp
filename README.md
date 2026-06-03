# LFWin Payment MCP Server

[![CI](https://github.com/litsen/lfwin-payment-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/litsen/lfwin-payment-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![npm](https://img.shields.io/npm/v/@litsen/lfwin-payment-mcp.svg)](https://www.npmjs.com/package/@litsen/lfwin-payment-mcp)
[![SafeSkill 91/100](https://img.shields.io/badge/SafeSkill-91%2F100_Verified%20Safe-brightgreen)](https://safeskill.dev/scan/litsen-lfwin-payment-mcp)

LFWin Payment MCP Server 是一个面向 AI Agent 的支付能力服务。它通过标准 MCP 协议，把创建支付订单、查询支付状态、发起退款、查询退款状态等能力开放给 Cursor、Cline、Claude Desktop、企业智能助手和自研 Agent 应用。

项目同时提供两种实现：

- Node.js 版：位于 [node-mcp](node-mcp/)，推荐普通 MCP 用户通过 `npx` 快速启动。
- Python 版：位于 [payment_mcp](payment_mcp/)，适合已有 Python 环境或需要二次开发的用户。

两种实现提供相同的 MCP 工具能力。获取支付权限或密钥，请联系服务商客服。

## 功能

- `create_payment_order`：创建统一收银台支付订单
- `query_payment_order`：查询支付订单状态
- `refund_payment_order`：发起退款
- `query_refund_status`：查询退款状态

创建支付订单时会返回支付链接和二维码相关字段：

- `pay_url`：统一收银台支付跳转链接
- `qrcode`：同 `pay_url`，用于兼容需要扫码内容的调用方
- `pay_qrcode_image`：基于 `pay_url` 生成的二维码 PNG `data:image/png;base64,...`
- `pay_qrcode_base64`：同一张二维码 PNG 的裸 base64，不包含 `data:image/png;base64,` 前缀
- `pay_qrcode_mime_type`：固定为 `image/png`，用于 MCP 图片内容块或自研客户端渲染
- `pay_qrcode_markdown`：可直接展示的 Markdown 图片文本
- `payment_display_examples`：按 Markdown、HTML/img、MCP image content、支付链接兜底等场景给出的展示示例

Node.js 版还会在 MCP 工具结果中额外返回 `type: "image"` 的 PNG 内容块，方便支持图片渲染的 MCP 客户端直接显示二维码。

## AI Agent 使用规则

### 下单后的二维码展示

`create_payment_order` 调用成功后，统一收银台接口原始返回中的 `data` 表示支付跳转 URL 或支付参数。`data` 可能是字符串，也可能是包含 `payUrl`、`url`、`qrcode`、`code_url` 等字段的对象。本 MCP 服务会把它标准化为字符串 `pay_url`，并同时提供二维码字段，避免把对象错误展示为 `[object Object]`。AI Agent 应按客户端能力选择展示方式：

- 支持 Markdown 的对话窗口：优先直接输出 `pay_qrcode_markdown`。
- 支持 MCP 图片内容块的客户端：Node.js 版工具结果里会带 `type: "image"` 的 PNG 内容块，可直接展示。
- 需要前端自行渲染图片：使用 `pay_qrcode_image`，这是完整的 `data:image/png;base64,...` data URL，可直接作为 `<img src>`。
- 只接受裸 base64 的客户端：使用 `pay_qrcode_base64`，并将媒体类型设置为 `pay_qrcode_mime_type`。
- 需要跳转支付或自行生成二维码：使用 `pay_url`；`qrcode` 与 `pay_url` 相同，仅作为兼容字段。

不要只告诉用户“已创建订单”而不展示二维码或支付链接。面向用户时应展示二维码，并保留 `pay_url` 作为扫码失败时的备用链接。

### 支付字段展示调用示例

假设 `create_payment_order` 返回结果保存为 `order`：

Markdown 对话窗口可直接输出：

```md
{order.pay_qrcode_markdown}
```

Web 前端可把完整 data URL 放进图片标签：

```html
<img alt="Payment QR Code" src="{order.pay_qrcode_image}" />
```

React/Vue 等前端可直接绑定图片地址：

```tsx
<img alt="Payment QR Code" src={order.pay_qrcode_image} />
```

MCP 或自研客户端只接受图片内容块时，使用裸 base64 和 MIME：

```json
{
  "type": "image",
  "mimeType": "image/png",
  "data": "{order.pay_qrcode_base64}"
}
```

如果图片无法展示，必须展示备用支付链接：

```md
[点击打开支付链接]({order.pay_url})
```

如果客户端需要自己生成二维码，使用 `qrcode` 或 `pay_url` 作为二维码内容，不要把 `pay_qrcode_image` 再当文本编码进二维码。

### 订单号使用规则

`merchant_order_no` 和 `order_no` 不是同一个编号：

- `merchant_order_no`：商户订单号，创建订单时传入，对应接口文档里的 `mch_orderid`，用于商户系统内部关联和展示。
- `order_no`：平台订单号，由支付平台返回，对应接口文档里的 `orderid`，用于本 MCP 服务的订单查询、退款和退款查询。

AI Agent 必须保存 `create_payment_order` 返回的 `order_no`。后续调用 `query_payment_order`、`refund_payment_order`、`query_refund_status` 时，优先且默认使用这个 `order_no`，不要把创建订单时传入的 `merchant_order_no` 当作 `order_no` 使用。

接口文档说明底层订单查询接口也支持 `mch_orderid`，但当只传商户订单号时必须同时传 `order_time` 才能定位订单。本 MCP 当前的 `query_payment_order(order_no)` 参数语义是平台订单号，因此不应传 `merchant_order_no`。

### 查询和退款状态判断

- 支付查询：`query_payment_order` 的 `order_no` 必须传平台订单号。返回 `status=10000` 且 `paystatus=1` 表示支付成功；`paystatus=0` 表示待付款；`paystatus=2` 表示支付失败。
- 发起退款：`refund_payment_order` 的 `order_no` 必须传平台订单号，`mch_refund_no` 是商户退款流水号。同一笔订单多次部分退款时，每次退款应使用不同的 `mch_refund_no`。
- 退款不是发起即成功：退款请求返回 `status=4001` 或 `status=10000` 只表示请求已被接受或处理中，不代表退款成功。必须继续调用 `query_refund_status` 查询实际结果。
- 退款查询：`query_refund_status` 的 `order_no` 必须传平台订单号；如果发起退款时传了 `mch_refund_no`，查询时也应带上同一个 `mch_refund_no`。返回 `status=4001` 表示处理中；`status=10000` 且 `refund_status=1` 表示退款成功；`status=10000` 且 `refund_status=2` 表示退款失败。

## 环境变量

正常使用只需要配置：

```env
PAYMENT_API_KEY=your_api_key_here
PAYMENT_SIGN_KEY=your_sign_key_here
```

默认配置：

- 接口域名：`https://api2.lfwin.com`
- 签名方式：`MD5`

通常不需要额外配置接口域名和签名方式。

`PAYMENT_SIGN_KEY` 只在 MCP Server 本地生成请求签名时使用，不会作为请求字段发送到 LFWin 接口，也不会出现在 MCP 工具返回结果中。通过 MCPB、Glama 等支持敏感字段的安装方式配置时，该字段已标记为 sensitive。

## 安装方式一：Node.js 版

推荐普通用户使用 Node.js 版。发布到 npm 后，可直接通过 `npx` 启动：

```bash
npx -y @litsen/lfwin-payment-mcp
```

Cursor 配置示例：

```json
{
  "mcpServers": {
    "payment-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@litsen/lfwin-payment-mcp"],
      "env": {
        "PAYMENT_API_KEY": "your_api_key_here",
        "PAYMENT_SIGN_KEY": "your_sign_key_here"
      }
    }
  }
}
```

本地源码调试 Node.js 版：

```bash
cd node-mcp
npm install
npm run build
node dist/index.js
```

更多说明见 [node-mcp/README.md](node-mcp/README.md)。

## 安装方式二：Python 版

如果你已有 Python 3.12 或更高版本，也可以使用 Python 版。

从 GitHub 安装：

```bash
pip install git+https://github.com/litsen/lfwin-payment-mcp.git
```

安装完成后会得到 MCP 启动命令：

```bash
payment-mcp
```

Cursor 配置示例：

```json
{
  "mcpServers": {
    "payment-mcp": {
      "type": "stdio",
      "command": "cmd",
      "args": ["/c", "payment-mcp"],
      "env": {
        "PAYMENT_API_KEY": "your_api_key_here",
        "PAYMENT_SIGN_KEY": "your_sign_key_here"
      }
    }
  }
}
```

源码开发时也可以这样运行：

```bash
pip install -r requirements.txt
python -m payment_mcp.mcp_stdio
```

## Cline 配置

Node.js 版：

```json
{
  "mcpServers": {
    "payment-mcp": {
      "command": "npx",
      "args": ["-y", "@litsen/lfwin-payment-mcp"],
      "env": {
        "PAYMENT_API_KEY": "your_api_key_here",
        "PAYMENT_SIGN_KEY": "your_sign_key_here"
      },
      "disabled": false
    }
  }
}
```

Python 版：

```json
{
  "mcpServers": {
    "payment-mcp": {
      "command": "cmd",
      "args": ["/c", "payment-mcp"],
      "env": {
        "PAYMENT_API_KEY": "your_api_key_here",
        "PAYMENT_SIGN_KEY": "your_sign_key_here"
      },
      "disabled": false
    }
  }
}
```

## 工具参数

### create_payment_order

创建支付订单。

参数：

- `merchant_order_no`：商户订单号，必须唯一
- `amount`：支付金额，单位为元
- `notify_url`：异步通知地址，可选

返回结果：

- `order_no`：平台订单号，对应接口文档里的 `orderid`。后续查询、退款、退款查询必须优先使用该值。
- `merchant_order_no`：商户订单号，对应创建订单时传入的 `merchant_order_no` / 接口文档里的 `mch_orderid`，不要用它替代 `order_no` 查询。
- `pay_url` / `qrcode` / `pay_qrcode_image` / `pay_qrcode_base64` / `pay_qrcode_mime_type` / `pay_qrcode_markdown` / `payment_display_examples`：支付展示字段。返回结果中的 `pay_qrcode_markdown` 可以直接让 AI 输出给用户，用于扫码支付；`pay_qrcode_image` 可直接作为 `<img src>`；`pay_qrcode_base64` 搭配 `pay_qrcode_mime_type` 可用于 MCP 图片内容块或只接受裸 base64 的客户端。

### query_payment_order

查询支付订单状态。

参数：

- `order_no`：平台订单号，即 `create_payment_order` 返回的 `order_no` / 接口文档里的 `orderid`。不要传 `merchant_order_no`。

### refund_payment_order

发起退款。

参数：

- `order_no`：平台订单号，即 `create_payment_order` 返回的 `order_no` / 接口文档里的 `orderid`。不要传 `merchant_order_no`。
- `refund_amount`：退款金额，单位为元
- `reason`：退款原因
- `mch_refund_no`：商户退款流水号，必须唯一。同一订单多次部分退款时，每次使用不同值。

退款请求返回 `status=4001` 或 `status=10000` 只表示请求已被接受或处理中，不代表退款成功。必须继续调用 `query_refund_status`。

### query_refund_status

查询退款状态。

参数：

- `order_no`：平台订单号，即 `create_payment_order` 返回的 `order_no` / 接口文档里的 `orderid`。不要传 `merchant_order_no`。
- `mch_refund_no`：商户退款流水号，可选；如果发起退款时传入了该值，查询时应使用同一个值定位退款记录。

状态判断：

- `status=4001`：退款处理中，需要稍后再次查询。
- `status=10000` 且 `refund_status=1`：退款成功。
- `status=10000` 且 `refund_status=2`：退款失败。

## Open Plugins / Cursor Directory

仓库根目录提供 [mcp.json](mcp.json)，用于 Open Plugins / Cursor Directory 识别 MCP 组件。

## Glama

仓库根目录提供 [glama.json](glama.json)、[Dockerfile](Dockerfile)、[LICENSE](LICENSE)、[SECURITY.md](SECURITY.md) 和 GitHub Actions CI，用于提升 Glama 收录和评分。

## 发布

Python 版构建 wheel 包：

```bash
pip install build
python -m build
```

Node.js 版发布 npm 包：

```bash
cd node-mcp
npm login
npm publish --access public
```

GitHub Release：

```bash
git tag v0.1.6
git push origin v0.1.6
```

推送 `v*` tag 后，Release workflow 会自动构建 `.mcpb` 并上传到 GitHub Release。

## MCPB 打包

`.mcpb` 是一个包含本地 MCP Server 和 `manifest.json` 的 zip 包，适合 Claude Desktop 等支持 MCPB 的客户端一键安装。

本项目推荐用 Node.js 版打 MCPB，因为 Claude Desktop 在 macOS 和 Windows 上自带 Node 运行环境，用户不需要额外安装 Python。

先构建 Node.js 版：

```bash
cd node-mcp
npm install
npm run build
```

然后回到项目根目录执行：

```powershell
.\scripts\build-mcpb.ps1
```

生成文件：

```text
dist/lfwin-payment-mcp-0.1.6.mcpb
```

MCPB 安装时会提示用户填写：

- `Payment API Key`
- `Payment Sign Key`

这两个值会通过 [mcpb/manifest.json](mcpb/manifest.json) 的 `user_config` 注入为 `PAYMENT_API_KEY` 和 `PAYMENT_SIGN_KEY`，不会写死在包里。其中 `Payment Sign Key` 已标记为敏感字段，只用于本地签名。

## 安全说明

- 不要把真实的 `PAYMENT_API_KEY`、`PAYMENT_SIGN_KEY` 提交到 GitHub。
- 建议通过环境变量、IDE Secret 或服务器密钥管理系统注入密钥。
- 本项目默认使用 `stdio` 方式作为本地 MCP 服务运行。
- 如果要部署成远程 MCP 服务，请自行增加认证、租户隔离、访问控制和 Origin 校验。

## 演示示例
Cursor安装后，可选择启用哪些能力
<img width="973" height="302" alt="image" src="https://github.com/user-attachments/assets/da186c6c-e7dc-4c93-bf2d-234efe1b51a3" />

智能体调用时会自动生成对应的支付订单，可引导用户扫码完成支付

**发起支付：**
<img width="999" height="883" alt="image" src="https://github.com/user-attachments/assets/8dbae19e-d421-479a-885e-eedd386ab8d1" />

**发起退款：**
<img width="975" height="767" alt="image" src="https://github.com/user-attachments/assets/f1673711-dd41-4be1-838b-6f2c597b8bc6" />
