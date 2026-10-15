# HD 與 Pro（LX06）的差異化改機指南

整理：2026-10-15。對象僅為 XMYX01JY／M01；裝置狀態引用 2026-10-09 的實機與備份快照。此文件不對其他 HD 硬體版本、Pro 新版或 OH2P 作相容性承諾。

這是一份 HD 專用的流程與差異指南，不是下載映像後可直接刷寫的教學。本倉庫沒有原廠完整韌體、預刷映像、實機憑證或自動刷機入口。當前音箱已具持久 SSH，新增唯讀能力 Client 不需要重新刷 rootfs。

## 1. 不能直接照搬 Pro 的地方

| 項目 | HD／M01 | Pro／LX06（已分析版本） | HD 處理方式 |
|---|---|---|---|
| rootfs | UBI 容器內的 UBIFS，活動根掛載 rw | system0 為 SquashFS、根掛載 ro | 不能把 Pro 的 root_patched.squashfs 或 mksquashfs 流程套到 HD |
| 韌體快照 | system0 1.66.87、system1 1.66.88 | 分析基線 1.94.13 | 從 HD 對應槽位自己的基線製作；不跨槽整包覆蓋 |
| system 分區 | 實機 system0／system1 各 44 MiB | 已有 system0 備份為 40 MiB | 尺寸不是通用常數，不把此表當作其他裝置的寫入參數 |
| SSH gate | Dropbear 腳本依 UCI CHANNEL 判斷，release 會提前退出 | 原版涉及 micocfg_channel 與 ssh_en 類旗標 | HD 需要修改自己的判斷；只 touch /data/ssh_en 不足以證明開啟 SSH |
| 身分工具 | UCI／matool_*；基線未見 micocfg_* | 有 micocfg_* | HD 使用自己的版本檔讀取，避免執行不存在的工具 |
| 認證 | Dropbear 連 libcrypt，未見 PAM 依賴 | 有 libpam／common-auth／廠商認證 | 不往 HD 新增 Pro 的 PAM 檔案或認證庫 |
| UART inittab | 已有 askfirst login shell | 上游有針對 Pro 的改動 | SSH-only 不需修改 HD inittab |
| 語音前端 | SoundAI／mipns-sai | 上游依賴 mico_aivs_lab 的事件／控制 | Client 必須用 HD adapter；不能重啟錯誤服務或偽造日誌入口 |
| 收音／播放 | HD 沒有已驗證 noop；PDM stream 曾觀察為八聲道 S32_LE／16 kHz | 上游預設 noop、單聲道 | 先能力查詢；不直接開音訊、改 ALSA 或套 Pro 的通道配置 |

這些差異來自專案原始基線與既有實機觀察，不代表兩機完整硬體、DSP 或驗證開機機制都已分析。

## 2. 原始 SSH-only 改造應有的準備順序

1. 核對底部型號與韌體內部 M01 身分；建立私人、獨立的原始備份與雜湊清單。
2. 唯讀取得 /proc/mtd、cmdline、掛載、UBI 對應、NAND 幾何與啟動環境。確認正在使用哪個 boot／system 槽，而非僅相信環境變數名稱。
3. 從 HD 自己的 rootfs 製作工作副本；保留 Linux UID／GID、mode、symlink、device nodes 等 metadata，不能只拿 Windows 解包目錄重新打包。
4. 只修改必要的 HD rootfs 項目，離線比較應只有預期差異。
5. 驗證 UBIFS／UBI 結構、大小、幾何、CRC、解包後內容與 metadata，再規劃寫入與復原。傳輸成功或 SHA-256 一致都不是開機能力的充分證明。
6. 只有具體映像、目標槽位、讀回校驗與恢復流程均可審查後，才安排單槽寫入。保留另一槽不等於完整恢復能力；data 與啟動環境可能共用。

本專案現有 HD 備份的 bootloader 尚未完整覆蓋 2 MiB，整機刷回與備援槽開機未驗證，因此不提供一鍵刷寫命令。這不妨礙在現有正常 SSH 系統上設計可移除的唯讀程式。

## 3. HD SSH-only 的最小 rootfs 變更範圍

| 路徑 | HD 專用處理 |
|---|---|
| /etc/init.d/dropbear | 修改 HD release gate／啟用流程；保留 UCI validation、procd 與設定選項；處理 data 掛載時序及 host key |
| /etc/config/dropbear | 明確設定 SSH 啟用與認證方式；正式部署由使用者設定私密憑證，不寫入公開預設密碼 |
| /etc/shadow | 如採密碼登入，只調整 root 認證欄位；不公開原雜湊，不清空密碼，不覆寫其他帳號 |
| /etc/rc.local | 僅預留 /data/init.sh 的背景 hook；腳本不存在時不啟動任何新增功能 |
| /bin/ota | 在停止原廠服務之前拒絕已知更新入口；保留所需成功通知流程 |
| /bin/flash.sh | 在 source／刪除輸入檔等副作用前攔截入口 |

Kernel、DTB、Boot image、Driver、Bootloader 二進位、Audio／ALSA、wireless、inittab 與 PAM 均不屬於這個最小方案。OTA 入口修改不代表能阻擋任意直接寫入 NAND 的其他程式。

HD 曾使用的幾何為 eraseblock 131072、page 2048、OOB 64 bytes；相應 UBI LEB 為 126976 bytes。這是已觀察個體的資訊，不是鼓勵直接重建或刷入的通用參數。Boot／system 映像的角色與容器格式不同，不能交換使用。

## 4. 已有 SSH 的 HD：本次應走的路線

1. 保持現有 boot／system／data 配置；不重做 SSH patch，也不修改 bootdelay／boot_part。
2. 先在本地執行 [唯讀握手版本](HD_HANDSHAKE.md) 的 mock 測試。
3. 此版本只允許 get_version／get_model／get_status；不存在音訊、任意 shell、OTA、分區寫入或前端控制 RPC。
4. ARM32／glibc 2.25 交叉編譯、二進位格式／依賴／大小與 QEMU mock 驗證已完成，見 [ARM_CROSS_BUILD.md](ARM_CROSS_BUILD.md)；受控實機連線、Kernel／ubus 及資源相容仍未驗證。
5. 後續即使部署，也應先暫存、手動執行並可退出，驗證後才討論 /data/init.sh。此次不部署，也不提供自啟安裝器。

## 5. 本文件涵蓋與未涵蓋

已涵蓋 HD／Pro 差異、SSH-only 六檔範圍、打包／分區確認原則，以及已有 SSH 後的演進方式。尚未提供完整 Bootloader 恢復、可直接刷寫的映像、板級 UART／USB 接線圖、實測音質調整參數或 HD 音訊 Client。

Client／Server 的逐模組差異見 [HD_ADAPTATION.md](HD_ADAPTATION.md)；來源與授權見 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。
