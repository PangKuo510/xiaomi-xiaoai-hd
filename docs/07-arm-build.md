# 07｜HD ARM32／glibc 2.25 建置與本地驗證

日期：2026-10-15。程式：HD 唯讀握手 Client v0.1.0。

## 結果

| 項目 | 本次驗證結果 |
|---|---|
| Rust target | armv7-unknown-linux-gnueabihf |
| 編譯工具 | 官方 Rust 1.93.1＋ARMv7 std；Cargo 1.93.1 |
| 連結工具 | Zig 0.13.0，明確指定 arm-linux-gnueabihf.2.25 |
| 格式 | ELF32、小端序、ARM、PIE、EABI5 hard-float，已 strip |
| 動態載入器 | /lib/ld-linux-armhf.so.3 |
| 直接依賴 | libm.so.6、libpthread.so.0、libc.so.6、libdl.so.2 |
| 最高 GLIBC 需求 | GLIBC_2.25；未見高於 2.25 的需求 |
| 必要符號 | 與本機 HD 備份執行庫比對，未缺必要動態符號 |
| 二進位大小 | 836,968 bytes，約 817.35 KiB／0.798 MiB |
| SHA-256 | 124537dc946097a99cc8b6784861622508ec35f2b1aa1732b9477e701dc665d4 |
| RPATH／私人建置路徑 | 無 RPATH／RUNPATH；未嵌入本機使用者家目錄或專案絕對路徑 |
| 本地執行 | QEMU ARM＋HD 原有 glibc 2.25 執行庫，7 項握手／負向測試通過 |

詳細機器可讀結果：[arm-build-inspection.json](arm-build-inspection.json)。工具鏈下載 URL／SHA-256 固定於 [arm-toolchain-lock.json](arm-toolchain-lock.json)，Cargo 依賴使用既有 lockfile。建置腳本會驗證官方下載雜湊及已提交 lock。

硬浮點依 ELF header 的 EF_ARM_ABI_FLOAT_HARD 判定；本產物未附選用的 Tag_ABI_VFP_args。原樣記錄的 .ARM.attributes 顯示 v6，不足以據此宣稱整個 Rust 產物只需 ARMv6；本次 Rust target 仍為 ARMv7，並在 QEMU cortex-a7 模型測試。`file` 顯示的 Linux 2.0.0 ABI 註記也不是本程式已驗證的最低 Kernel 版本。

## 測試範圍

沿用七項握手測試，以 QEMU 執行這份實際 ARM release binary：三項查詢往返、無自動事件／串流、拒絕 shell／錄音／播放／開機寫入、非法 payload、錯誤回應 ID／協定、逾時、拒絕 LAN 端點，以及實際 Python Server CLI 的握手／退出。

mock 模式不讀 HD 狀態檔、不呼叫 ubus、不開啟音訊。HD 動態庫僅提供 loader／函式庫相容性驗證；不是在模擬整機、NAND 或音效驅動。

**未驗證**：HD 實機 Kernel 4.9.61 的全部系統呼叫、真實 backend 的 ubus 查詢、實機 RAM／CPU／啟動時間、網路隧道與 ARM 實機穩定性。這次沒有連線或安裝到音箱，沒有刷寫或修改驅動。

## 產物

- [驗證用 ARM 套件](../dist/hd-handshake-armv7-glibc225.tar.gz)：只有 Client、檢查報告、依賴清單與第三方授權 notices。
- [套件 manifest](../dist/manifest.json)：壓縮套件與 Client 的大小／SHA-256。
- 本機原始 binary 在被 Git 忽略的 artifacts/armv7-glibc225/hd-handshake。

壓縮套件不是安裝器，沒有自啟、音訊或刷寫命令。沒有將 HD loader／glibc、原廠韌體、帳號設定或金鑰打包上傳。套件保留本次解析的 47 個 Cargo 套件資訊與授權檔，另附 Rust、Zig 與其 glibc 授權文字；這不變更本專案自有內容尚未選定的公開授權。

## 重現編譯

在 Linux x86_64／WSL 安裝可用的 cargo、curl、xz、Python3、readelf／file 與 QEMU user-mode。工具鏈存入使用者 cache，沒有替換系統 Rust；HD_CROSS_HOME 可改成另一個不含空白的本機路徑。

```bash
sh tools/setup_arm_cross.sh
sh tools/build_arm_glibc225.sh
```

建置使用 glibc 2.25 連結基線，不把私人 rootfs 當 SDK，也不執行上游 runtime Dockerfile。

## 以私人 HD 備份作本地驗證

只從自己的已校驗 rootfs TAR 擷取固定 13 個 runtime library／symlink 項目到 Git 忽略的 .local-cross/hd-runtime。工具拒絕任意路徑、非預期連結與覆寫；不解出 etc、data、host key 或 shadow。

```bash
python3 tools/prepare_hd_runtime.py --rootfs-tar /path/to/private/rootfs.tar.gz
python3 tools/inspect_arm_client.py \
  --binary artifacts/armv7-glibc225/hd-handshake \
  --runtime .local-cross/hd-runtime \
  --output docs/arm-build-inspection.json
sh tools/test_arm_qemu.sh
```

需先依[文件 04](04-read-only-handshake.md)建立 Python 測試 venv。`qemu-arm` 以明確命令啟動，不依賴系統 binfmt 自動註冊；本次 WSL 套件安裝時 binfmt service 重啟失敗，未修改該服務，直接 user-mode 測試已通過。後續實機握手結果見[文件 08](08-hd-live-readonly-test.md)。

## 本地打包

```bash
cargo metadata --locked --format-version 1 \
  --filter-platform armv7-unknown-linux-gnueabihf \
  --manifest-path packages/hd-handshake/Cargo.toml > .local-cross/cargo-metadata.json
python3 tools/package_arm_artifact.py
```

原始 rootfs、工具鏈、runtime libraries 及編譯快取均不提交。重新打包會以固定 uid／gid／mtime 產生壓縮檔，避免把本機帳號／路徑帶進 archive；尚未宣稱不同主機上的整體編譯為 bit-for-bit reproducible。
