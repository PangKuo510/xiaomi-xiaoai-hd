# 已提交資料的隱私與金鑰檢查

日期：2026-10-15。範圍：本倉庫追蹤檔案、程式碼、文件及所有可達 Git 歷史 blob；不把 GitHub 私人可見性當成避免洩漏的唯一措施。

## 本輪結果

未發現使用者的裝置序號、實機 MAC／SSID／內網端點、私人主機目錄、SSH 私鑰、真實 API key／GitHub token／AWS access key 或密碼雜湊被提交。

除了規則掃描，另從本機私人實機證據在記憶體中取得 9 個序號／MAC／SSID／位址類字串，逐一比對目前追蹤內容及可達歷史，沒有命中。這些字串與證據路徑沒有存入倉庫或報告；檢查器只回報類別與檔案位置，不印出匹配值。

## 已辨識的公開上游範例

上游原樣快照內有四處私網 IP 範例、一處 MAC 格式範例，以及 MiGPT 的 x 字元 API key 佔位符。這些不是使用者的實機資訊或可用金鑰，對應檔案完整 SHA-256 與固定上游一致。

- vendor/open-xiaoai/packages/client-rust/README.md：三處區網位址示例。
- vendor/open-xiaoai/examples/migpt/README.md：一處區網位址示例與假 API key。
- vendor/open-xiaoai/examples/migpt/config.ts：假 API key。
- vendor/open-xiaoai/examples/xiaozhi/xiaozhi/utils/config.py：MAC 格式註解示例。

為保留上游來源完整性，本次沒有改寫這些範例；它們不是可照填的 HD 連線設定。新握手程式只使用 loopback，不包含使用者端點，狀態回應也不傳送 URL、序號或網路識別資料。

GitHub 帳號、原作者署名／網站、公開來源 commit 與套件雜湊是刻意保留的公開歸屬資訊，不是內部裝置識別碼。提交作者使用 GitHub noreply 身分；本報告不宣稱倉庫是匿名的。

## 可重跑的檢查

```powershell
python tools/audit_private_data.py
python tools/audit_private_data.py --history
```

可選 `--reference-file` 指定本機私有證據以做額外字串比對；不將證據檔加入 Git。不要在命令列直接傳入密碼或金鑰。

## 限制與維護

規則掃描與已知字串比對不是數學上的無洩漏證明，不涵蓋所有加密／編碼格式、未知型態的密鑰或 GitHub 站外附件。此輪沒有找到需要清除歷史或輪換的使用者秘密，因此沒有重寫 Git 歷史。

往後不要上傳原始備份、shadow、host key、連線資訊、私人環境檔或未遮蔽日誌。任何新部署憑證只留本機或受控服務端；發布前重跑掃描與人工檢查。
