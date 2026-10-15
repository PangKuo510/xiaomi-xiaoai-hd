# 08｜HD 實機唯讀握手紀錄

日期：2026-10-15（台北時間）。裝置以「HD／M01」稱呼；本紀錄不包含序號、MAC、SSID、IP、帳號、暫存路徑或轉送埠。

## 已驗證

- 使用已知 SSH 主機金鑰連線；確認裝置型號與 `/tmp` 為記憶體檔案系統。
- 將 836,968 bytes 的 ARM32 Client 暫存到權限受限的 `/tmp` 目錄。上傳後讀回校驗，SHA-256 與建置產物相同：`124537dc946097a99cc8b6784861622508ec35f2b1aa1732b9477e701dc665d4`。
- 本地 Server 只綁 loopback；裝置透過 SSH 反向隧道連回。Client 以真實 backend 執行一次，依序查詢 `get_version`、`get_model`、`get_status`，正常退出（exit code 0）。全程約 4 秒。
- 回應識別為 HD／M01、韌體 1.66.87、Client 0.1.0、protocol 1；`simulated=false`。狀態回傳 `read_only=true`、MemTotal 231056 KiB、MemAvailable 110452 KiB、播放器數值欄位 `status=0`、`volume=36`、`loop_type=1`。`status=0` 只照錄回傳值，不推斷其意義。
- 沒有播放、錄音、改音量、改設定、自動啟動、驅動或分區操作。八個設定／啟動相關路徑在前後的內容或不存在狀態一致；比對雜湊未保存。
- Client 與暫存目錄已移除；新 SSH 連線確認程序、暫存路徑及本次建立的反向轉送均不存在。本地 Server、relay 與 SSH 連線已結束。

## 清理細節

舊版 Dropbear 沒有在取消轉送請求時立即關閉 listener。關閉原 SSH 連線後，再以新 SSH 連線檢查，確認本次 listener 已消失。系統原有的 miio loopback listener 保持原狀，沒有停止或修改。

兩次準備階段未啟動 Client：HD 沒有可用 SFTP 子系統；舊 Dropbear 也不接受自動分配反向埠。改用 SSH stream 上傳與明確選取的臨時埠後，才執行成功測試。兩次準備失敗都已清理；這些狀況沒有混入本次成功結果。

## 尚未驗證

這次只驗證單次啟動、三項唯讀查詢與正常退出。尚未測長時間執行、重連、資源峰值、其他 HD 個體或其他機型。URL 播放、停止／恢復、錄音、自動啟動及 NAS 長期服務都未測。

本地完整操作紀錄含清理狀態與前後比對結果，保存在私人工作資料夾，沒有推送到 GitHub。此次公開文件只保留必要的測試結論與可重現的產物雜湊。
