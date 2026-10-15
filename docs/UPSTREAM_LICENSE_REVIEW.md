# Open-XiaoAI 授權與重用評估

查核日期：2026-10-15。用途：HD 個人研究專案的技術與授權規劃，並非對商業使用權利的確定法律結論。

## 查核對象

- Repository：[idootop/open-xiaoai](https://github.com/idootop/open-xiaoai)
- main commit：`bc3396c64e2a435f354eb5cb12a203981f1fe422`
- [固定版本 LICENSE](https://github.com/idootop/open-xiaoai/blob/bc3396c64e2a435f354eb5cb12a203981f1fe422/LICENSE)
- [固定版本 README](https://github.com/idootop/open-xiaoai/blob/bc3396c64e2a435f354eb5cb12a203981f1fe422/README.md)
- [固定版本 agreement.md](https://github.com/idootop/open-xiaoai/blob/bc3396c64e2a435f354eb5cb12a203981f1fe422/agreement.md)

現有本地參考 checkout 的 HEAD 與本輪 git ls-remote 的 main 一致。該 checkout 含本地未追蹤的 patch 目錄，不能直接當作純淨上游整包匯入。本倉庫本次沒有複製任何上游原始碼或執行上游安裝程式。

## LICENSE：MIT

根目錄 LICENSE 標示 MIT，原始版權人為 Copyright (c) 2024 Del Wang。

按 MIT 授權文字，可以使用、複製、修改、合併、散布、再授權與銷售程式碼；重用全部或實質部分時須保留版權及授權通知，並保留免責文字。MIT 本身沒有要求修改後必須公開原始碼，也沒有「僅限非商業」條款。

這適用於權利人能授權的軟體，不能推導為取得小米完整韌體、商標、私有 DSP、雲端服務或任意第三方依賴的再散布權。

## README／agreement.md 的不一致

README 稱專案停止維護，原教學只適用 LX06／OH2P。其免責聲明與 agreement.md 又寫了學術研究／個人測試用途、禁止商業服務等限制；agreement.md 另有下載／運行視為接受條款及責任免除文字。

這些限制與標準 MIT 所表達的廣泛使用權存在文字不一致。不能直接宣稱整個發行物毫無條件可商用，也不能自行裁定附加文字必然無效或自動取代 MIT。

本專案個人研究的目的符合其聲明用途，但不因此宣稱已釐清所有條款效力。若要商業銷售、代刷服務、發行預載產品或大量分發，應向作者取得針對此用途的書面釐清；必要時再作正式法律審查。

## 建議方式

建立獨立 HD 倉庫，維護 HD 文件、適配程式與測試結果；上游保持唯讀參考。後續選擇性匯入 Client／Server 原始碼時：

1. 固定來源 commit，逐檔記錄原路徑與修改。
2. 隨匯入內容保存上游完整 MIT LICENSE、原作者署名，以及 README／agreement 的來源與適用疑點。
3. 檢查被匯入模組、依賴與下載二進位是否另有授權，生成相應第三方清單。
4. 將 LX06／OH2P 預設與 HD 適配明確分開，不保留可誤執行的刷寫預設。
5. 不匯入原廠韌體、裝置備份、憑證、私鑰或私人連線設定。

## Fork 與獨立 Repository

| 方式 | 適合情況 | 本案取捨 |
|---|---|---|
| GitHub Fork | 延續完整 Client／Server、保留 fork 關係與回送 PR | 可以作為技術起點，但公開上游的 fork 也公開；HD 相容性仍需自行完成 |
| 獨立倉庫＋選擇性移植 | 聚焦 HD、先私人研究、避免混入不適用工具 | 本案優先建議，並保留可追溯來源 |
| 直接複製整包、移除來源 | 不利授權與維護追蹤 | 不採用 |

Fork 不會因上游歸檔而必然失去開發能力，但也不會自動得到維護支援或新機型相容性。公開 fork 不能獨立改成私人；若要私人研究，建立獨立倉庫較合適。[GitHub fork 可見性說明](https://docs.github.com/en/pull-requests/reference/forks)。

## 目前落實狀態

本次只建立 HD 文件骨架及來源／授權評估，不接受或代替使用者作額外協議承諾，不重新下載執行上游 Client，也不發布預刷映像。後續原始碼移植應另有具體範圍、HD 適配與驗證紀錄。
