# HD 唯讀能力握手 v0.1

本次實作為獨立 Rust Client `packages/hd-handshake` 與 Python Server `host/handshake_server.py`。採用上游同型的 JSON Request／Response 外層格式，但不載入 vendor 的 Client、SpeakerManager 或範例 Server，因此不繼承其啟動音訊、任意 shell 與寫入功能。這是縮減能力的新入口，不是整套上游 RPC 的相容替代品。

## 命令與來源

| RPC | 回傳範圍 | 真實 backend 的來源 |
|---|---|---|
| get_version | Client 名稱／版本、協定版本、ROM 版本、模擬標記 | /usr/share/mico/version，只解析 ROM／HARDWARE |
| get_model | XMYX01JY／M01 | 同一版本檔；HARDWARE 不等於 M01 時拒絕，包括 LX06 |
| get_status | uptime、MemTotal／MemAvailable、播放器數字狀態／音量／loop_type、三項能力清單 | /proc/uptime、/proc/meminfo；固定 /bin/ubus 的 player_get_play_status 查詢 |

不讀取序號、MAC、SSID、帳號、token、私鑰、播放 URL 或原始語音內容。播放器回應只取允許的數字欄位，不透傳原始 JSON；查詢失敗只回固定錯誤分類，不傳出 stderr。

每項 RPC 拒絕非 null payload、額外 request 欄位、未知命令與不合法 ID。ubus 僅使用固定絕對路徑與 argv，不經 shell；讀取大小與查詢時間有限制。get_status 失敗時不重啟服務、不修正設定。

## 本地模式與界線

- Client 連線前不執行裝置查詢；只在收到三項白名單 RPC 時讀取。
- Server 僅發三次查詢，完成後關閉 session；不自動錄音、播放或發送事件。
- Server 與 Client v0.1 只允許 loopback，沒有 LAN 模式、探索、持久保存或自動啟動。
- 每 session 最多 16 個 frame 迴圈；大小 8192 bytes，連線／閒置／RPC 有逾時。
- `--mock` 使用程式內明確標示的模擬資料；不讀實機檔案、不呼叫 ubus。
- 真實 backend 尚未安裝／執行於 HD。已另完成 ARM32／glibc 2.25 建置與 QEMU mock 驗證，見 [ARM_CROSS_BUILD.md](ARM_CROSS_BUILD.md)；尚未驗證實機 Kernel、資源或 ubus。

沒有啟用認證／TLS，所以本版刻意不開放 LAN。後續部署需要另外設計受控連線方式，不能直接放寬為所有網路介面。

## 在 Linux／WSL 本地重現

需要 Rust 工具鏈、Python 3 與 host/requirements.txt 的 WebSocket 依賴。下列流程只執行本機 mock，不涉及音箱：

```bash
cargo test --locked --manifest-path packages/hd-handshake/Cargo.toml
cargo build --locked --manifest-path packages/hd-handshake/Cargo.toml
python3 -m venv .venv-handshake
.venv-handshake/bin/python -m pip install -r host/requirements.txt
.venv-handshake/bin/python -m unittest discover -s host -p 'test_*.py' -v
```

手動展示可開兩個本地終端（這是 mock 模式，並非安裝指令）：

```bash
# 終端一
.venv-handshake/bin/python host/handshake_server.py
# 終端二
packages/hd-handshake/target/debug/hd-handshake --mock
```

Server 的 console 只列成功／模擬標記／查詢名稱，不印連線位址或原始裝置狀態。測試只在 loopback 使用臨時埠，模擬 M01，不能當作已完成實機端到端驗收。

驗證結果與隱私檢查見 [HANDSHAKE_VALIDATION.md](HANDSHAKE_VALIDATION.md) 與 [PRIVACY_REVIEW.md](PRIVACY_REVIEW.md)。
