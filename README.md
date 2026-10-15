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

目前本倉庫只包含整理後的研究文件，沒有可直接執行的刷寫或安裝方案。不要把 LX06／OH2P 的分區、映像或錄音設定直接套用到 HD。

## 文件

- [硬體與相容性](docs/HD_STATUS.md)
- [Open-XiaoAI 授權與重用評估](docs/UPSTREAM_LICENSE_REVIEW.md)
- [開發路線與驗收條件](docs/ROADMAP.md)

## 參考專案

[idootop/open-xiaoai](https://github.com/idootop/open-xiaoai) 提供 Client／Server 架構及開源實作參考。上游已於 2026-04-04 歸檔，原教學限 LX06／OH2P，不構成 HD 相容性承諾。

本專案目前沒有匯入上游原始碼；不宣稱已完成 HD 移植。後續每次匯入都必須記錄來源 commit、保留版權／授權文字，並列出 HD 差異。

## 資料與授權邊界

不收錄原廠完整韌體、NAND 備份、裝置金鑰、憑證、帳號設定、私人網路資訊或未遮蔽日誌。硬體／韌體相關權利不因上游 MIT 授權而自動授予。

本倉庫自有內容的公開再散布授權尚未選定；上游程式碼的 MIT 與第三方條款須分別處理，不能以本專案名稱取代原作者署名。
