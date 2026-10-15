# HD 硬體與相容性快照

整理日期：2026-10-15。實機觀察日期：2026-10-09；本文件不包含新的裝置連線測試。

| 項目 | 已知結果 |
|---|---|
| 機型 | 小愛音箱 HD，XMYX01JY／M01 |
| CPU | Amlogic AXG，四核心 Cortex-A53，最高 1.2 GHz |
| RAM／NAND | 256 MiB RAM／128 MiB SLC NAND |
| 系統 | Linux 4.9.61 aarch64；ARM32 hard-float 使用者空間，glibc 2.25 |
| 活動 rootfs | M01 1.66.87 為底的 SSH-only 修改版；UBI／UBIFS |
| 保留槽 | system1 1.66.88，未刷寫；未測切換開機 |
| data | UBIFS 可寫；觀察時剩約 4.1 MiB |
| 音訊 | ALSA AML-AXGSOUND，TDM／PDM；TDM-C-tas5707 路徑 |
| 預設播放設定 | 48 kHz／S32_LE／兩聲道，經軟體音量與 dmix |
| 實際收音 stream | 16 kHz／S32_LE／八聲道；八聲道不等於八顆麥克風 |
| 語音前端 | SoundAI／mipns-sai；不能直接假設與 LX06 事件路徑相同 |

## 證據與限制

原生播放器兩個 ubus 狀態查詢成功。URL 播放、DLNA 與 TTS 介面存在，但實際聲音、內容服務、音訊格式與播放恢復尚未完成本專案驗收。

韌體含 libDiracAPI_SHARED.so，ALSA 有 TAS5707 路徑；這不證明當前 DSP 處理、係數或功放型號的全部細節。改善音質先測音源／擺位／上游 EQ，尚無需要修改驅動的證據。

原廠標示六顆麥克風與 4×2.25 吋加 1×4 吋喇叭；多顆單體不代表可獨立控制的多聲道輸出。[官方規格](https://www.mi.com/aispeaker-hd/specs)。

## 上游 Client 的 HD 缺口

- 尚未完成 HD Client 上傳、執行與端到端驗證。
- 未建立上游使用的 noop PCM 與 HD 相容證據。
- HD 語音事件／TTS 路徑不同，需要專用適配。
- 原廠前端已開啟收音 stream，須先研究共享／事件出口，不能直接搶占裝置。
- 預設服務端位址、啟動等待、日誌與重試策略須重新設計，不硬編碼私人端點。

## 恢復材料

私人專案資料中保留原始分析基線、完整的 tpl／boot0／boot1／system0／system1／data 讀回與檔案封存。這些材料不放進此 Git 倉庫。

Bootloader 仍沒有完整覆蓋 2 MiB；線上備份不等同原子離線快照，未涵蓋完整 OOB／保留區，也未完成整機刷回。當前可用與完整可恢復是不同的驗收條件。
