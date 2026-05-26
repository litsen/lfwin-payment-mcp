# LFWin Payment MCP Server

[![CI](https://github.com/litsen/lfwin-payment-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/litsen/lfwin-payment-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![npm](https://img.shields.io/npm/v/@litsen/lfwin-payment-mcp.svg)](https://www.npmjs.com/package/@litsen/lfwin-payment-mcp)

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
- `pay_qrcode_markdown`：可直接展示的 Markdown 图片文本

Node.js 版还会在 MCP 工具结果中额外返回 `type: "image"` 的 PNG 内容块，方便支持图片渲染的 MCP 客户端直接显示二维码。

## 环境变量

正常使用只需要配置：

```env
PAYMENT_API_KEY=your_api_key_here
PAYMENT_SIGN_KEY=your_sign_key_here
```

默认配置：

- 接口域名：`http://api2.lfwin.com`
- 签名方式：`MD5`

通常不需要额外配置接口域名和签名方式。

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
<!-- - `currency`：币种，默认 `CNY`
- `channel`：支付渠道，默认 `comm`
- `subject`：订单说明 -->
- `notify_url`：异步通知地址，可选

返回结果中的 `pay_qrcode_markdown` 可以直接让 AI 输出给用户，用于扫码支付。

### query_payment_order

查询支付订单状态。

参数：

- `order_no`：平台订单号

### refund_payment_order

发起退款。

参数：

- `order_no`：平台订单号
- `refund_amount`：退款金额，单位为元
- `reason`：退款原因
- `mch_refund_no`：商户退款单号，必须唯一

### query_refund_status

查询退款状态。

参数：

- `order_no`：平台订单号
- `mch_refund_no`：商户退款单号，可选

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
git tag v0.1.1
git push origin v0.1.1
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
dist/lfwin-payment-mcp-0.1.1.mcpb
```

MCPB 安装时会提示用户填写：

- `Payment API Key`
- `Payment Sign Key`

这两个值会通过 [mcpb/manifest.json](mcpb/manifest.json) 的 `user_config` 注入为 `PAYMENT_API_KEY` 和 `PAYMENT_SIGN_KEY`，不会写死在包里。

## 安全说明

- 不要把真实的 `PAYMENT_API_KEY`、`PAYMENT_SIGN_KEY` 提交到 GitHub。
- 建议通过环境变量、IDE Secret 或服务器密钥管理系统注入密钥。
- 本项目默认使用 `stdio` 方式作为本地 MCP 服务运行。
- 如果要部署成远程 MCP 服务，请自行增加认证、租户隔离、访问控制和 Origin 校验。
