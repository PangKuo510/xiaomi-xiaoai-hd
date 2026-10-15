# Xiaomi XiaoAI HD Lab

專門研究小愛音箱 HD（XMYX01JY／M01）的系統、可恢復改造、音訊調校與 NAS 整合。這是獨立的個人研究專案，非小米或 Open-XiaoAI 官方專案。

## 目標

- 保留原廠聲學系統，研究音源、擺位、EQ 與原廠 DSP 的改善空間。
- 沿用原生播放器，逐步驗證 NAS 音樂與家庭語音播報。
- 建立 HD 專用 Client／事件／收音適配的證據。
- 維護可追溯的變更、驗證結果與恢復限制。

## 已知狀態

以下是 2026-10-09 的實機與備份快照，並非持續監控結果：

- HD 自身的 system0 rootfs 已完成 SSH-only 修改；重啟、組裝後 SSH 仍可用。
- 未修改 Kernel、DTB、Boot image、Driver、Bootloader 二進位及 Audio／ALSA 設定。啟動環境曾調整 bootdelay／boot_part。
- 原生 mediaplayer 的狀態查詢成功；URL 播放方法存在，但 NAS 音檔播放尚未驗收。
- 原始 system1 保留；備援槽啟動與整機刷回尚未驗證。
- Bootloader 的完整 2 MiB 備份仍有缺口。
- 尚未安裝或驗證 Open-XiaoAI Client。

本倉庫包含上游來源快照，以及已完成本地 mock 測試的獨立 HD 唯讀握手 v0.1。後者只提供版本、機型、唯讀狀態三項查詢；尚無經 HD ARM32 編譯與實機驗證的可安裝版本。不要把 LX06／OH2P 的分區、映像或錄音設定直接套用到 HD。

## 文件

- [硬體與相容性](docs/HD_STATUS.md)
- [Open-XiaoAI 授權與重用評估](docs/UPSTREAM_LICENSE_REVIEW.md)
- [開發路線與驗收條件](docs/ROADMAP.md)
- [Client／Server 共用範圍與 HD 適配清單](docs/HD_ADAPTATION.md)
- [第三方來源與授權](THIRD_PARTY_NOTICES.md)
- [逐檔匯入 manifest](docs/upstream-import-manifest.json)
- [HD 唯讀握手版本與本地重現](docs/HD_HANDSHAKE.md)
- [握手測試結果](docs/HANDSHAKE_VALIDATION.md)
- [HD 與 Pro 差異化改機指南](docs/HD_MODDING_GUIDE.md)
- [隱私與金鑰檢查](docs/PRIVACY_REVIEW.md)

## 參考專案

[idootop/open-xiaoai](https://github.com/idootop/open-xiaoai) 提供 Client／Server 架構及開源實作參考。上游已於 2026-04-04 歸檔，原教學限 LX06／OH2P，不構成 HD 相容性承諾。

已將固定 commit `bc3396c64e2a435f354eb5cb12a203981f1fe422` 的 Client、MiGPT／小智／Gemini Server 範例及原始授權文件存入 [vendor/open-xiaoai](vendor/open-xiaoai/)。共 103 檔、497,737 bytes，逐檔保留來源 blob、SHA-256 與原始 Git mode，未修改上游內容，也未安裝依賴或執行。

上游不是 HD 可直接執行的版本：Server 連線測試會啟動裝置功能，init／boot 腳本也會下載與執行程式。先閱讀適配清單，勿直接執行這些範例。

本地完整性檢查：`python tools/verify_upstream_import.py`。此命令只驗證檔案與 Git 索引，不連線音箱。

## 資料與授權邊界

不收錄原廠完整韌體、NAND 備份、裝置金鑰、憑證、帳號設定、私人網路資訊或未遮蔽日誌。硬體／韌體相關權利不因上游 MIT 授權而自動授予。

本倉庫自有內容的公開再散布授權尚未選定；上游程式碼的 MIT 與第三方條款須分別處理，不能以本專案名稱取代原作者署名。
