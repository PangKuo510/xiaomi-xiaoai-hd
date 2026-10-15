# 上游來源匯入驗證

日期：2026-10-15。

## 已完成

- 從固定 commit 的 Git blobs 選取 103 檔，共 497,737 bytes；沒有複製上游工作目錄的本地未追蹤 patch。
- 103 檔的檔案集合、大小、SHA-256、Git blob ID 與 Git 索引 mode 均相符，錯誤 0。
- 三個 Server Cargo manifests 的本地路徑依賴都仍指向匯入的 packages/client-rust，檢查 3 項通過。
- Python AST 靜態解析 29 檔通過（含本專案兩個匯入／驗證工具）；沒有 import 或執行這些上游 Python 程式。
- JSON 4 檔與 TOML 6 檔靜態解析通過。
- 本專案新增文件／工具的 Git whitespace check 通過；上游快照保留原始空白與行尾，不為了格式檢查而改寫。

## 尚未驗證

- Rust／Node／Python 依賴安裝、Cargo 建置與跨平台 ABI。
- Client／Server 實際啟動、WebSocket 互通、音訊串流。
- NAS 部署、HD 安裝、錄音／播放、驅動或 DSP 相容性。
- 依賴完整授權 SBOM 與發布產物的授權清單。

來源匯入階段沒有使用 Cargo，以上結果仍不等於上游完整程式建置或端到端成功。後續已確認 WSL 有可用 Rust 工具鏈，並完成獨立 HD 握手程式的本地建置／mock 測試，見 [HANDSHAKE_VALIDATION.md](HANDSHAKE_VALIDATION.md)；未建置或執行 vendor 的完整 Client／Server。

## 重現

在本倉庫根目錄執行：

```powershell
python tools/verify_upstream_import.py
```

重新從已存在的上游 Git checkout 取得同一份來源（不抓取網路、不執行上游程式）：

```powershell
python tools/import_open_xiaoai.py --source <上游 checkout 路徑>
```

匯入工具拒絕覆寫已修改的 vendor 檔；Git mode 另記錄於 manifest，Windows 重新匯入後以驗證工具確認索引狀態。Vendor 的 `.gitattributes` 禁止自動換行轉換，以維持與上游 blob 完全一致。
