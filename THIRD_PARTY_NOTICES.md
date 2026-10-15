# 第三方來源與授權

## Open-XiaoAI

- 原作者：Del Wang／idootop。
- 原始專案：https://github.com/idootop/open-xiaoai
- 固定 commit：`bc3396c64e2a435f354eb5cb12a203981f1fe422`。
- 本次匯入：2026-10-15；103 個 Git 追蹤檔，497,737 bytes。
- 放置位置：[vendor/open-xiaoai](vendor/open-xiaoai/)，保留原始路徑與原始碼，未作 HD 修改。
- 授權全文：[上游 MIT LICENSE](vendor/open-xiaoai/LICENSE)，含 Copyright (c) 2024 Del Wang。
- 其他聲明：[原始 README](vendor/open-xiaoai/README.md)、[原始 agreement.md](vendor/open-xiaoai/agreement.md)。二者的用途限制與 MIT 的不一致，詳見[授權評估](docs/UPSTREAM_LICENSE_REVIEW.md)。

本倉庫不以自身授權取代上述原作者權利或聲明。原作者未對本專案提供 HD 相容性承諾或背書。

匯入 Client library／binary 原始碼與 MiGPT、Xiaozhi、Gemini Server 範例，連同 manifests／lockfiles／配套程式。原始 README 的部分相對連結指向未匯入的上游文件；查閱時可改到固定 commit 的完整上游樹。

本次沒有匯入 flash-tool、client-patch、runtime sysroot／映像、GitHub Actions、KWS 或 stereo 獨立範例、預編譯 Client 或模型權重。這些內容若日後需要，須另作範圍與授權查核。

## 依賴邊界

Cargo.lock、pnpm-lock.yaml、uv.lock 保留上游解析紀錄；vendor 來源整理階段沒有安裝、建置或重散布其依賴。後續獨立 HD 握手程式在自己的 packages/hd-handshake/Cargo.lock 與 host/requirements.txt 記錄依賴，已於開發主機安裝與測試，未向音箱部署。本文件不是完整依賴 SBOM，也不是宣稱所有傳遞依賴皆為 MIT。

發行二進位、容器或安裝套件前，應對實際解析／打包的 Rust、Python、Node 依賴與系統函式庫產出授權清單，保留必要 notices，並檢查任何額外下載的模型與媒體資產。

## 驗證與後續修改

逐檔來源 blob、SHA-256、大小與原始 Git mode 記錄於 [匯入 manifest](docs/upstream-import-manifest.json)。`tools/verify_upstream_import.py` 可在不存取音箱、不執行上游程式碼的情況下驗證。

將 vendor 視為固定的來源快照。HD 改動另放適配層或明確記錄的 patch，不悄悄覆寫來源。保留原始 shell 腳本是為了來源完整性，不代表可直接在 HD 使用；不要執行其中 init／boot／Docker 流程作為 HD 安裝方式。
