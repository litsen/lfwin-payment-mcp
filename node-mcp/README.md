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
- `pay_qrcode_base64`：同一张二维码 PNG 的裸 base64，不包含 `data:image/png;base64,` 前缀
- `pay_qrcode_mime_type`：固定为 `image/png`，用于 MCP 图片内容块或自研客户端渲染
- `pay_qrcode_markdown`：可直接展示的 Markdown 二维码图片
- `payment_display_examples`：按 Markdown、HTML/img、MCP image content、支付链接兜底等场景给出的展示示例

Node.js 版还会在 MCP 工具结果中额外返回 `type: "image"` 的 PNG 内容块，方便支持图片渲染的 MCP 客户端直接显示二维码。

## AI Agent 使用规则

### 下单后的二维码展示

`create_payment_order` 调用成功后会返回支付链接。统一收银台接口原始返回中的 `data` 可能是字符串，也可能是包含 `payUrl`、`url`、`qrcode`、`code_url` 等字段的对象。本 Node.js MCP 服务会把它标准化为字符串 `pay_url`，并同时提供二维码字段，避免把对象错误展示为 `[object Object]`。

AI Agent 应按客户端能力选择展示方式：

- 支持 Markdown 的对话窗口：优先直接输出 `pay_qrcode_markdown`。
- 支持 MCP 图片内容块的客户端：工具结果里会带 `type: "image"` 的 PNG 内容块，可直接展示。
- 需要前端自行渲染图片：使用 `pay_qrcode_image`，这是完整的 `data:image/png;base64,...` data URL，可直接作为 `<img src>`。
- 只接受裸 base64 的客户端：使用 `pay_qrcode_base64`，并将媒体类型设置为 `pay_qrcode_mime_type`。
- 需要跳转支付或自行生成二维码：使用 `pay_url`；`qrcode` 与 `pay_url` 相同，仅作为兼容字段。

不要只告诉用户“已创建订单”而不展示二维码或支付链接。面向用户时应展示二维码，并保留 `pay_url` 作为图片展示失败时的备用链接。

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

`merchant_order_no`、`order_no` 和 `order_time` 不是同一个编号：

- `merchant_order_no`：商户订单号，创建订单时传入，对应接口文档里的 `mch_orderid`，用于商户系统内部关联和展示。
- `order_no`：平台订单号，由支付平台返回，对应接口文档里的 `orderid`，用于本 MCP 服务的订单查询、退款和退款查询。
- `order_time`：本 MCP 创建支付订单时记录的下单时间，格式为 `yyyyMMddHHmmss`。当统一收银台 `pre_order` 没有返回平台 `orderid` 时，后续支付状态轮询必须使用 `merchant_order_no + order_time`。

AI Agent 必须保存 `create_payment_order` 返回的 `order_no`、`merchant_order_no` 和 `order_time`：

- 如果 `order_no_available=true` 且 `order_no` 不为空，后续调用 `query_payment_order`、`refund_payment_order`、`query_refund_status` 时优先使用 `order_no`。
- 如果 `order_no_available=false` 或 `order_no=null`，不要把 `merchant_order_no` 当作 `order_no` 使用；支付状态轮询应调用 `query_payment_order`，并传入创建订单返回的 `merchant_order_no` 和 `order_time`。
- 退款相关工具仍需要平台 `order_no/orderid`。如果创建订单没有返回平台订单号，必须先通过支付查询拿到平台 `orderid` 后再发起退款或退款查询。

### 查询和退款状态判断

- 支付查询：优先传 `order_no`。如果创建订单时 `order_no` 为空，则传 `merchant_order_no` 和 `order_time`。返回 `status=10000` 且 `paystatus=1` 表示支付成功；`paystatus=0` 表示待付款；`paystatus=2` 表示支付失败。使用 `merchant_order_no + order_time` 查询时，如果用户尚未扫码或打开支付链接，平台支付订单可能还未生成，底层接口可能返回 `raw_status=3040` / `raw_message=订单号不存在`；本 MCP 会将其标准化为 `status=PENDING`，并返回 `pending_reason=WAITING_FOR_USER_SCAN_OR_PAYMENT_ORDER_CREATION`。
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

- `order_no`：平台订单号，对应接口文档里的 `orderid`。如果统一收银台未返回平台订单号，该字段为 `null`。
- `order_no_available`：是否拿到了平台订单号。
- `merchant_order_no`：商户订单号，对应创建订单时传入的 `merchant_order_no` / 接口文档里的 `mch_orderid`。
- `order_time`：下单时间，格式为 `yyyyMMddHHmmss`。当 `order_no` 为 `null` 时，支付轮询使用 `merchant_order_no + order_time`。
- `pay_url` / `qrcode` / `pay_qrcode_image` / `pay_qrcode_base64` / `pay_qrcode_mime_type` / `pay_qrcode_markdown` / `payment_display_examples`：支付展示字段。返回结果中的 `pay_qrcode_markdown` 可以直接让 AI 输出给用户，用于扫码支付；`pay_qrcode_image` 可直接作为 `<img src>`；`pay_qrcode_base64` 搭配 `pay_qrcode_mime_type` 可用于 MCP 图片内容块或只接受裸 base64 的客户端。

### query_payment_order

- `order_no`：平台订单号，即 `create_payment_order` 返回的 `order_no` / 接口文档里的 `orderid`。当该字段存在时优先使用。
- `merchant_order_no`：商户订单号，可选；当 `order_no` 为空时必须与 `order_time` 一起传入。
- `order_time`：下单时间，可选；当 `order_no` 为空时必须与 `merchant_order_no` 一起传入，使用 `create_payment_order` 返回的 `order_time`。

当使用 `merchant_order_no + order_time` 查询且用户尚未扫码时，返回 `raw_status=3040` 是正常的待支付/待落库状态。本 MCP 会返回 `status=PENDING`，前端应继续展示待支付并继续轮询，而不是提示支付失败。

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
