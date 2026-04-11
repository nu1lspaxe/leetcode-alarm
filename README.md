# LeetCode Alarm

LeetCode Alarm 是一個用於監控 LeetCode 每日解題狀態並透過 LINE 發送提醒的自動化腳本。它可以幫助你維持 LeetCode 的解題連續天數（Streak）。

關於本專案的介紹文章請見[這篇](https://nu1lspaxe.github.io/posts/20260318_20/20260318_20/)。

## 功能介紹

- **自動檢查解題狀態**：透過 LeetCode 的 GraphQL API 檢查今天是否已經完成挑戰。
- **LINE 推播通知**：
  - 如果已經完成：發送鼓勵訊息並報告目前的 Streak。
  - 如果尚未完成：發送緊急提醒，並附上今日挑戰題目的名稱、難度與連結。
- **自動化執行**：透過 GitHub Actions 每天定時執行（預設為台灣時間 18:00、20:00、21:00），確保你不會忘記今天的題目。

## 系統需求

- Python 3.9 或以上
- 一個有效的 LINE Messaging API 機器人（需取得 Channel Access Token 及接收者的 User ID）
- GitHub 帳號

## 在本機執行

1. **安裝依賴套件**
   首先複製此專案，並安裝所需的套件：
   ```bash
   pip install -r requirements.txt
   ```

2. **設定環境變數**
   你需要設定以下環境變數才能讓腳本正常運作：
   - `LEETCODE_USERNAME`：你的 LeetCode 帳號名稱。
   - `LINE_CHANNEL_ACCESS_TOKEN`：LINE Developer Console 中取得的 Channel Access Token。
   - `LINE_USER_ID`：你的 LINE 使用者 ID。

   *在 Windows / Linux / macOS 中可以透過環境變數設定，或者在本地執行時取消註解 `# from dotenv import load_dotenv` 搭配 `.env` 檔案使用。*

3. **執行腳本**
   ```bash
   python streak.py
   ```

## 自動化部署 (GitHub Actions)

此專案內建了 GitHub Actions 工作流程（位於 `.github/workflows/alarm.yaml`）。

要啟用自動化推播，請在你的 GitHub 儲存庫中進行以下設定：
1. 進入儲存庫的 **Settings** > **Secrets and variables** > **Actions**。
2. 新增以下三個 **Repository secrets**：
   - `LEETCODE_USERNAME`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`
3. 儲存後，GitHub Actions 將會依據 `cron` 排程自動執行程式。

### 排程說明

預設的 `cron: '0 10,12,13 * * *'` 對應的是 UTC 時間。轉換為台灣時間（UTC+8）後，腳本將會在每天的以下時間進行檢查與發送通知：
- 18:00
- 20:00
- 21:00

若需更改時間，可直接修改 `.github/workflows/alarm.yaml` 裡的排程設定。

## 依賴套件

- `requests`
- `pytz`

（詳見 `requirements.txt`）
