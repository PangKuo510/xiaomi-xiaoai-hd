# 05｜唯讀握手本地驗證

日期：2026-10-15。

## 結果

- WSL x86_64 Linux：Rust／Cargo 1.93.1，獨立 hd-handshake `cargo test` 6 項通過，`cargo build --locked` 通過。
- Python 本地 venv、websockets 14.2：7 項測試通過，包含真正的 Rust mock binary 與 Python Server CLI round trip。
- Vendor 103 檔仍與匯入 manifest 一致，未為本次改造覆寫上游來源。

## 測試涵蓋

Rust：拒絕 LX06／未知機型；只輸出允許的機型、記憶體與播放器欄位；濾除 token／URL；播放器數字範圍與錯誤回應；未知／變更命令拒絕於 backend 之前；非 null payload、非法訊息與大小上限；三項 mock 查詢；固定路徑白名單。

Python／WebSocket：三項查詢完整往返；連線前後沒有主動事件／串流；run_shell／錄音／播放／set_boot／mic_on 拒絕；拒絕 payload 後仍能完成查詢；回應 ID 不符；協定不符；Server 等待逾時；Client 拒絕非 loopback 目的地；啟動實際 Server CLI 後與 Rust mock 完成握手及退出。

測試資料皆為程式內合成值，mock 不開啟裝置檔案、不執行 ubus。局部測試以真實 backend 旗標送出非法命令，確認拒絕在任何檔案讀取之前。

## 實務界線

- 未連線、安裝或執行於 HD；未錄音、播放、改音量、設定、Driver 或分區。
- 本文件記錄的是本地 x86_64、ARM QEMU 與 mock 測試；交叉編譯詳見[文件 07](07-arm-build.md)。HD 實機的 RAM 數值和固定 ubus 呼叫後來已由一次受控握手實測，詳見[文件 08](08-hd-live-readonly-test.md)。
- Cargo fmt 在本機工具鏈缺少子命令，因此未完成 formatter 檢查；沒有為此另裝系統元件。建置與功能測試已通過。
- 本地功能測試不取代長時間運行、重新連線、TLS／認證與 NAS 部署驗收。

重現命令見[文件 04](04-read-only-handshake.md)。本地測試不代替實機結果；實機測試也不代表長時間或音訊功能已驗收。
