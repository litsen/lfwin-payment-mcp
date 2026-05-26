# LFWin Payment MCP Server Node.js 版

这是 LFWin Payment MCP Server 的 Node.js/TypeScript 实现，适合在 Cursor、Cline 等 MCP 客户端中通过 `npx` 启动。

## 功能

- `create_payment_order`：创建统一收银台支付订单
- `query_payment_order`：查询支付订单状态
- `refund_payment_order`：发起退款
- `query_refund_status`：查询退款状态

创建支付订单时会返回：

- `pay_url`：统一收银台支付跳转链接
- `qrcode`：同 `pay_url`
- `pay_qrcode_image`：基于 `pay_url` 生成的二维码 PNG data URL
- `pay_qrcode_markdown`：可直接展示的 Markdown 二维码图片

Node.js 版还会在 MCP 工具结果中额外返回 `type: "image"` 的 PNG 内容块，方便支持图片渲染的 MCP 客户端直接显示二维码。

## 环境变量

```env
PAYMENT_API_KEY=your_api_key_here
PAYMENT_SIGN_KEY=your_sign_key_here
```

默认系统变量：

```env
PAYMENT_API_BASE_URL=https://api2.lfwin.com
PAYMENT_SIGN_TYPE=MD5
PAYMENT_REQUEST_TIMEOUT_MS=15000
```

`PAYMENT_SIGN_KEY` 只在本地生成签名时使用，不会作为请求字段发送到 LFWin 接口，也不会出现在 MCP 工具返回结果中。

## Cursor 配置

发布到 npm 后推荐这样使用：

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

## 工具参数

### create_payment_order

- `merchant_order_no`：商户订单号，必须唯一
- `amount`：支付金额，单位为元
- `notify_url`：异步通知地址，可选

## 开发

```bash
npm install
npm run build
npm start
```

## 发布

```bash
npm login
npm publish --access public
```

发布后用户可以直接通过 `npx -y @litsen/lfwin-payment-mcp` 使用。
