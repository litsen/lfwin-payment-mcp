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

## AI Agent 使用规则

### 下单后的二维码展示

`create_payment_order` 调用成功后会返回支付链接，本 Node.js MCP 服务会把它标准化为 `pay_url`，并同时提供二维码字段。

AI Agent 应按客户端能力选择展示方式：

- 支持 Markdown 的对话窗口：优先直接输出 `pay_qrcode_markdown`。
- 支持 MCP 图片内容块的客户端：工具结果里会带 `type: "image"` 的 PNG 内容块，可直接展示。
- 需要前端自行渲染图片：使用 `pay_qrcode_image`，这是 `data:image/png;base64,...` 格式。
- 需要跳转支付或自行生成二维码：使用 `pay_url`；`qrcode` 与 `pay_url` 相同，仅作为兼容字段。

不要只告诉用户“已创建订单”而不展示二维码或支付链接。面向用户时应展示二维码，并保留 `pay_url` 作为图片展示失败时的备用链接。

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

返回结果：

- `order_no`：平台订单号，对应接口文档里的 `orderid`。后续查询、退款、退款查询必须优先使用该值。
- `merchant_order_no`：商户订单号，对应创建订单时传入的 `merchant_order_no` / 接口文档里的 `mch_orderid`，不要用它替代 `order_no` 查询。
- `pay_url` / `qrcode` / `pay_qrcode_image` / `pay_qrcode_markdown`：支付展示字段。返回结果中的 `pay_qrcode_markdown` 可以直接让 AI 输出给用户，用于扫码支付。

### query_payment_order

- `order_no`：平台订单号，即 `create_payment_order` 返回的 `order_no` / 接口文档里的 `orderid`。不要传 `merchant_order_no`。

### refund_payment_order

- `order_no`：平台订单号，即 `create_payment_order` 返回的 `order_no` / 接口文档里的 `orderid`。不要传 `merchant_order_no`。
- `refund_amount`：退款金额，单位为元。
- `reason`：退款原因。
- `mch_refund_no`：商户退款流水号，必须唯一。同一订单多次部分退款时，每次使用不同值。

退款请求返回 `status=4001` 或 `status=10000` 只表示请求已被接受或处理中，不代表退款成功。必须继续调用 `query_refund_status`。

### query_refund_status

- `order_no`：平台订单号，即 `create_payment_order` 返回的 `order_no` / 接口文档里的 `orderid`。不要传 `merchant_order_no`。
- `mch_refund_no`：商户退款流水号，可选；如果发起退款时传入了该值，查询时应使用同一个值定位退款记录。

状态判断：

- `status=4001`：退款处理中，需要稍后再次查询。
- `status=10000` 且 `refund_status=1`：退款成功。
- `status=10000` 且 `refund_status=2`：退款失败。

## 开发

用户可以直接通过 `npx -y @litsen/lfwin-payment-mcp` 使用。
