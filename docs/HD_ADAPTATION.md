# Client／Server 共用範圍與 HD 適配清單

日期：2026-10-15。基礎：固定上游 commit `bc3396c64e2a435f354eb5cb12a203981f1fe422`；HD 資訊仍是 2026-10-09 快照。本輪只有離線整理，沒有連音箱、安裝、錄音或改驅動。

## 目錄與角色

```text
vendor/open-xiaoai/
  LICENSE / README.md / agreement.md    原作者授權與聲明
  packages/client-rust/                 Client 執行檔 + 共用 Rust library
  examples/migpt/                       Node／Neon Server + MiGPT 範例
  examples/xiaozhi/                     Python／PyO3 Server + 小智範例
  examples/gemini/                      Python／PyO3 Server + Gemini 範例
```

上游沒有單一獨立的 packages/server：三個 examples 各自實作 AppServer，並依賴 `../../packages/client-rust` 的共用 library。保留路徑可讓這些相對依賴繼續解析。這不代表三種 Server 都應同時啟動，或已在 NAS 建置成功。

## 可共用部分

| 模組 | 檔案位置（相對 vendor/open-xiaoai） | 判定 |
|---|---|---|
| 事件／請求／回應／串流資料結構 | packages/client-rust/src/services/connect/data.rs | 機型無關的協定基礎，可沿用後測序列化與互通 |
| WebSocket 訊息處理與 RPC | packages/client-rust/src/services/connect/{message,handler,rpc}.rs | 可沿用架構；目前 singleton 狀態不可直接當成多音箱 session 設計 |
| 任務／事件工具 | packages/client-rust/src/utils/{task,event}.rs | 可重用，仍須測 HD 流程的取消、逾時與重連 |
| Node Server 橋接 | examples/migpt/src/、migpt/ | 可作 NAS Server 起點，裝置控制與啟動測試須改 |
| Python Server 橋接 | examples/{xiaozhi,gemini}/src/ 及 Python 程式 | 可作 NAS Server 起點，音訊格式、提示與事件須改 |

「可共用」是來源層判斷，沒有建置或端到端成功的宣稱。Server 範例仍混有裝置相關操作。

## HD 必改／必驗證項目

| 優先 | 上游位置／假設 | HD 差異或問題 | 建議變更與驗收 |
|---|---|---|---|
| P0 | examples/{migpt,xiaozhi,gemini}/src/server.rs 的 init／test | 連線後會自動呼叫原廠 TTS；小智與 Gemini 還會 start_recording／start_play | 新的 HD Server 預設只做版本與能力查詢；音訊測試必須顯式啟用 |
| P0 | packages/client-rust/src/services/audio/config.rs | 預設 noop、16 kHz、單聲道 S16；HD 沒有已驗證的 noop PCM | 分開 capture／playback profile；未確認映射前禁止自動錄音 |
| P0 | packages/client-rust/src/services/audio/play.rs | 雖有 AudioConfig.pcm，但 aplay 參數沒有 -D，實際使用預設裝置 | 明確選擇播放入口，或優先經原生 URL 播放；測音量、混音、停止與恢復 |
| P0 | packages/client-rust/src/services/audio/record.rs | 16-bit 請求會改成 32-bit 擷取，再右移 8；沒有做八聲道→單聲道選取／混音 | 量測 HD 真正取樣排列、位元對齊、符號與通道；不把同晶片註解當作 HD 驗證 |
| P0 | packages/client-rust/src/services/monitor/instruction.rs | 硬編碼 /tmp/mico_aivs_lab/instruction.log；HD 為 SoundAI／mipns-sai | 找 HD 語音事件出口；先可停用 instruction monitor，不更名冒充事件檔 |
| P0 | packages/client-rust/src/services/speaker.rs | TTS 依賴 /usr/sbin/tts_play.sh，abort 重啟 mico_aivs_lab | HD 無上述已驗證路徑；以 NAS TTS→原生播放作第一方案，勿直接重啟原廠前端 |
| P0 | Client run_shell RPC；speaker.rs 的 set_boot | 遠端可執行 shell、修改啟動環境；不是音訊相容性驗證所需 | HD 試驗採能力白名單，預設不暴露原始 shell／set_boot；不要接不可信服務端 |
| P1 | monitor/playing.rs、speaker.rs、examples/migpt/migpt/speaker.ts | mphelper 輸出用 contains 字串判斷，playing monitor 每 10 ms 啟動查詢 | 以 HD 已成功回應的 ubus 結果測狀態語意，結構化解析、放慢輪詢 |
| P1 | speaker.rs 的 micocfg_model／micocfg_sn、mic_on／off、wake_up | 工具與事件編號不保證 HD 相容；查詢識別不應觸發設備變更 | 用 HD 已知韌體資訊做識別；對每個控制命令逐項測，不先啟用 |
| P1 | packages/client-rust/src/services/monitor/kws.rs | 只監看 /tmp/open-xiaoai/kws.log，不會自行產生辨識結果 | 保持可停用；日後加入 HD／NAS KWS producer，再測內容格式與例外處理 |
| P1 | packages/client-rust/boot.sh、init.sh | 無限等 baidu ping、下載未固定二進位、丟棄日誌、kill 舊 client | 不執行；另寫 HD wrapper，固定版本／雜湊、有限等待、保留日誌，最後才設自啟 |
| P1 | 三個 Server 的 0.0.0.0:4399／單連線 loop | 接收連線後 await 處理，MessageManager／RPC 共享單例 | 明確一程序一音箱先驗證；NAS 多音箱須隔離埠／程序或重構 session，另設認證與網路邊界 |
| P1 | speaker.rs、MiGPT speaker.ts 的 shell 字串插值 | 文字／URL 可能含引號或特殊字元；不能直接拼成 shell | 使用結構化命令／參數，測引號、換行、JSON 與返回錯誤 |
| P1 | examples/* 的 API／音訊／模型設定 | 是外部服務範例，不是 HD 本機推論方案；音訊規格依服務而異 | 憑證外置，明確取樣率、通道、重採樣及網路失敗行為 |
| P2 | ARM32 cross 編譯與 /data 預算 | Kernel 是 aarch64，但 userland ARM32／glibc 2.25；data 空間小 | 固定工具鏈，檢查 ELF／loader／GLIBC symbols／大小；本次未建置 |

## 建議適配邊界

下一階段把共用的 WebSocket／RPC 保留為 protocol，把 HD 設備行為抽成 adapter：識別、能力查詢、狀態、URL 播放、TTS、事件、capture profile。Vendor 保持原樣，HD adapter 才加入經驗證的方法。

初始能力應限 `get_version`／識別／唯讀狀態；錄音、原始 PCM 播放、原廠前端控制、任意 shell 與開機環境寫入均不預設開放。這是下一階段設計，不是這次已實作的隔離措施。

## 驗收順序

1. 離線 manifest、路徑與來源完整性（本次完成）。
2. 共用 library／Server 建置、協定測試（本次未做）。
3. 無音訊副作用的 HD 能力握手（未做）。
4. 原生 URL 播放、停止、恢復（未做）。
5. HD 事件與短錄音適配（未做）。
6. 長時間資源測試，最後才處理 /data/init.sh（未做）。

所有 P0 的原始行為仍存在 vendor 快照中。文件標示不是程式防護，也不能把本次來源整理當成安全可執行的 HD 版本。
