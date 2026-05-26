# LFWin 鏀粯 MCP Server

[![CI](https://github.com/litsen/lfwin-payment-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/litsen/lfwin-payment-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![npm](https://img.shields.io/npm/v/@litsen/lfwin-payment-mcp.svg)](https://www.npmjs.com/package/@litsen/lfwin-payment-mcp)

杩欐槸涓€涓潰鍚?Cursor銆丆line 绛?MCP 瀹㈡埛绔殑 LFWin 鏀粯宸ュ叿鍖呫€傞」鐩悓鏃朵繚鐣欎袱绉嶅疄鐜帮細

- Python 鐗堬細浣嶄簬 `payment_mcp/`锛岄€傚悎宸叉湁 Python 鐜鐨勭敤鎴枫€?
- Node.js 鐗堬細浣嶄簬 `node-mcp/`锛岄€傚悎閫氳繃 `npx` 蹇€熷惎鍔紝鎺ㄨ崘缁欐櫘閫?MCP 浣跨敤鑰呫€?

涓ょ瀹炵幇鎻愪緵鐩稿悓鐨?MCP 宸ュ叿鑳藉姏锛岀敤鎴峰彲浠ユ寜鑷繁鐨勭幆澧冮€夋嫨瀹夎鏂瑰紡銆?

鑾峰彇鏀粯鏉冮檺鎴栧瘑閽ワ紝璇疯仈绯绘湇鍔″晢瀹㈡湇銆?

## 鍔熻兘

- `create_payment_order`锛氬垱寤虹粺涓€鏀堕摱鍙版敮浠樿鍗?
- `query_payment_order`锛氭煡璇㈡敮浠樿鍗曠姸鎬?
- `refund_payment_order`锛氬彂璧烽€€娆?
- `query_refund_status`锛氭煡璇㈤€€娆剧姸鎬?

鍒涘缓鏀粯璁㈠崟鏃跺彧浼氳皟鐢ㄧ粺涓€鏀堕摱鍙版帴鍙ｇ敓鎴愪竴娆¤鍗曪紝骞惰繑鍥炴敮浠橀摼鎺ュ拰浜岀淮鐮佸浘鐗囷細

- `pay_url`锛氱粺涓€鏀堕摱鍙版敮浠樿烦杞摼鎺?
- `qrcode`锛氬悓 `pay_url`锛岀敤浜庡吋瀹归渶瑕佹壂鐮佸唴瀹圭殑璋冪敤鏂?
- `pay_qrcode_image`锛氬熀浜?`pay_url` 鐢熸垚鐨勪簩缁寸爜 PNG 鍥剧墖 `data:image/png;base64,...` 鍦板潃
- `pay_qrcode_markdown`锛氬彲鐩存帴灞曠ず鐨?Markdown 鍥剧墖鏂囨湰

## 鐜鍙橀噺

涓ょ瀹炵幇閮介渶瑕佷互涓嬬幆澧冨彉閲忥細

```env
PAYMENT_API_KEY=your_api_key_here
PAYMENT_SIGN_KEY=your_sign_key_here
```

榛樿閰嶇疆锛?

- 鎺ュ彛鍦板潃锛歚http://api2.lfwin.com`
- 绛惧悕鏂瑰紡锛歚MD5`

閫氬父鍙渶瑕侀厤缃?`PAYMENT_API_KEY` 鍜?`PAYMENT_SIGN_KEY`銆?

## 瀹夎鏂瑰紡涓€锛歂ode.js 鐗?

鎺ㄨ崘鏅€氱敤鎴蜂娇鐢?Node.js 鐗堛€傚彂甯冨埌 npm 鍚庯紝鍙互鐩存帴閫氳繃 `npx` 鍚姩锛?

```bash
npx -y @litsen/lfwin-payment-mcp
```

Cursor 閰嶇疆绀轰緥锛?

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

鏈湴婧愮爜璋冭瘯 Node.js 鐗堬細

```bash
cd node-mcp
npm install
npm run build
node dist/index.js
```

鏇村璇存槑瑙?[node-mcp/README.md](node-mcp/README.md)銆?

## 瀹夎鏂瑰紡浜岋細Python 鐗?

濡傛灉浣犲凡缁忔湁 Python 3.12 鎴栨洿楂樼増鏈紝涔熷彲浠ヤ娇鐢?Python 鐗堛€?

浠?GitHub 瀹夎锛?

```bash
pip install git+https://github.com/litsen/lfwin-payment-mcp.git
```

瀹夎瀹屾垚鍚庝細寰楀埌 MCP 鍚姩鍛戒护锛?

```bash
payment-mcp
```

Cursor 閰嶇疆绀轰緥锛?

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

婧愮爜寮€鍙戞椂涔熷彲浠ヨ繖鏍疯繍琛岋細

```bash
pip install -r requirements.txt
python -m payment_mcp.mcp_stdio
```

## Cline 閰嶇疆

Node.js 鐗堬細

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

Python 鐗堬細

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

## 宸ュ叿鍙傛暟

### create_payment_order

鍒涘缓鏀粯璁㈠崟銆?

鍙傛暟锛?

- `merchant_order_no`锛氬晢鎴疯鍗曞彿锛屽繀椤诲敮涓€
- `amount`锛氭敮浠橀噾棰濓紝鍗曚綅涓哄厓
- `currency`锛氬竵绉嶏紝榛樿 `CNY`
- `channel`锛氭敮浠樻笭閬擄紝榛樿 `comm`
- `subject`锛氳鍗曡鏄?
- `notify_url`锛氬紓姝ラ€氱煡鍦板潃锛屽彲閫?

杩斿洖缁撴灉涓殑 `pay_qrcode_markdown` 鍙互鐩存帴璁?AI 杈撳嚭缁欑敤鎴凤紝鐢ㄤ簬鎵爜鏀粯銆?

### query_payment_order

鏌ヨ鏀粯璁㈠崟鐘舵€併€?

鍙傛暟锛?

- `order_no`锛氬钩鍙拌鍗曞彿

### refund_payment_order

鍙戣捣閫€娆俱€?

鍙傛暟锛?

- `order_no`锛氬钩鍙拌鍗曞彿
- `refund_amount`锛氶€€娆鹃噾棰濓紝鍗曚綅涓哄厓
- `reason`锛氶€€娆惧師鍥?
- `mch_refund_no`锛氬晢鎴烽€€娆惧崟鍙凤紝蹇呴』鍞竴

### query_refund_status

鏌ヨ閫€娆剧姸鎬併€?

鍙傛暟锛?

- `order_no`锛氬钩鍙拌鍗曞彿
- `mch_refund_no`锛氬晢鎴烽€€娆惧崟鍙凤紝鍙€?

## 鍙戝竷

Python 鐗堟瀯寤?wheel 鍖咃細

```bash
pip install build
python -m build
```

Node.js 鐗堝彂甯?npm 鍖咃細

```bash
cd node-mcp
npm login
npm publish --access public
```


GitHub Release:

```bash
git tag v0.1.1
git push origin v0.1.1
```

Pushing a `v*` tag runs the Release workflow and uploads the `.mcpb` file as a release asset.
## MCPB 鎵撳寘

`.mcpb` 鏄竴涓寘鍚湰鍦?MCP server 鍜?`manifest.json` 鐨?zip 鍖咃紝閫傚悎 Claude Desktop 绛夋敮鎸?MCPB 鐨勫鎴风涓€閿畨瑁呫€?
鏈」鐩帹鑽愮敤 Node.js 鐗堟墦 MCPB锛屽洜涓?Claude Desktop 鍦?macOS 鍜?Windows 涓婅嚜甯?Node 杩愯鐜锛岀敤鎴蜂笉闇€瑕侀澶栧畨瑁?Python銆?
鍏堟瀯寤?Node.js 鐗堬細

```bash
cd node-mcp
npm install
npm run build
```

鐒跺悗鍥炲埌椤圭洰鏍圭洰褰曟墽琛岋細

```powershell
.\scripts\build-mcpb.ps1
```

鐢熸垚鏂囦欢锛?
```text
dist/lfwin-payment-mcp-0.1.1.mcpb
```

MCPB 瀹夎鏃朵細鎻愮ず鐢ㄦ埛濉啓锛?
- `Payment API Key`
- `Payment Sign Key`

杩欎袱涓€间細閫氳繃 `manifest.json` 鐨?`user_config` 娉ㄥ叆涓?`PAYMENT_API_KEY` 鍜?`PAYMENT_SIGN_KEY`锛屼笉浼氬啓姝诲湪鍖呴噷銆?
## 瀹夊叏璇存槑

- 涓嶈鎶婄湡瀹炵殑 `PAYMENT_API_KEY`銆乣PAYMENT_SIGN_KEY` 鎻愪氦鍒?GitHub銆?
- 寤鸿閫氳繃鐜鍙橀噺銆両DE Secret 鎴栨湇鍔″櫒瀵嗛挜绠＄悊绯荤粺娉ㄥ叆瀵嗛挜銆?
- 鏈」鐩粯璁や娇鐢?`stdio` 鏂瑰紡浣滀负鏈湴 MCP 鏈嶅姟杩愯銆?
- 濡傛灉瑕侀儴缃叉垚杩滅▼ MCP 鏈嶅姟锛岃鑷澧炲姞璁よ瘉銆佺鎴烽殧绂汇€佽闂帶鍒跺拰 Origin 鏍￠獙銆?

