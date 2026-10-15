# Xiaomi XiaoAI HD Lab

這個專案記錄小愛音箱 HD 的系統盤點、可恢復改造與音訊研究。它由使用者維護，與小米及 Open-XiaoAI 無官方關係。

目前已在 HD 實機完成一次唯讀握手：Client 回報版本、機型與狀態後正常退出。測試使用暫存檔和 SSH 隧道；結束後已確認 Client、暫存資料與隧道均清除。沒有播放、錄音或設定自動啟動。下一步先整理原生 URL 短音檔測試方案，尚未執行播放。

韌體資料、裝置憑證與完整備份留在私人本機資料夾，不放進此倉庫。HD 與 LX06／OH2P 的平台和 rootfs 不同，請勿直接套用對方分區、映像或音訊設定。

## 文件索引

文件以數字排序；`00` 是現況，`01–07` 說明來源、設計與建置，`08–09` 記錄實機結果及下一項測試，`10–11` 收錄隱私與匯入檢查。

| 編號 | 文件 | 用途 |
|---|---|---|
| 00 | [硬體與系統現況](docs/00-hardware-status.md) | HD 規格、系統快照、已知限制 |
| 01 | [Open-XiaoAI 授權與來源](docs/01-upstream-license.md) | 上游授權文字與重用判斷 |
| 02 | [開發路線](docs/02-roadmap.md) | 階段目標與驗收條件 |
| 03 | [Client／Server 適配](docs/03-client-server-adaptation.md) | 上游程式可用範圍及 HD 差異 |
| 04 | [唯讀握手設計](docs/04-read-only-handshake.md) | 三項查詢、邊界與本地重現方式 |
| 05 | [本地驗證](docs/05-local-validation.md) | Rust、Python、QEMU 與 mock 測試 |
| 06 | [HD 與 Pro 改機差異](docs/06-hd-vs-pro-modding.md) | HD／LX06 的系統差異與改造界線 |
| 07 | [ARM32 建置](docs/07-arm-build.md) | glibc 2.25 交叉編譯及產物檢查 |
| 08 | [HD 實機唯讀握手紀錄](docs/08-hd-live-readonly-test.md) | 去識別化實機結果與清理確認 |
| 09 | [原生 URL 短音檔測試方案](docs/09-native-url-playback-plan.md) | 尚待執行的單次、可停止播放測試 |
| 10 | [隱私檢查](docs/10-privacy-review.md) | 追蹤檔案與 Git 歷史檢查 |
| 11 | [上游匯入檢查](docs/11-upstream-import-validation.md) | vendor 檔案完整性與來源核對 |

另見 [第三方授權與來源](THIRD_PARTY_NOTICES.md)、[上游匯入 manifest](docs/upstream-import-manifest.json)、[ARM 工具鏈鎖定資料](docs/arm-toolchain-lock.json) 與 [建置檢查結果](docs/arm-build-inspection.json)。

## 專案內容

`vendor/open-xiaoai/` 保存固定上游版本的 Client、MiGPT／小智／Gemini 範例和原始授權文件。匯入內容保留來源與雜湊；它們是參考資料，不是 HD 可直接執行的版本。請先讀文件 01、03，再執行任何上游程式。

`packages/hd-handshake/` 是獨立的唯讀握手 Client，僅接受 `get_version`、`get_model`、`get_status`。實機測試已證明 ARM32 產物能在這台 HD 上完成三項查詢並退出；結果與限制見文件 08。測試不代表錄音、播放、自動啟動或其他機型已驗證。

## 授權與資料

上游程式依其原始授權及來源文件標示。本倉庫自有內容的公開再散布授權尚未選定。倉庫不收錄原廠韌體、NAND 備份、裝置憑證、帳號設定或私人連線資訊。
