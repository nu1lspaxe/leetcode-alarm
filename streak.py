import requests
import datetime
import os
import json
import pytz
# from dotenv import load_dotenv

# load_dotenv()

LEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME") 
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
}

def post_graphql(query, variables=None):
    """發送 GraphQL 請求的共用函式"""
    url = "https://leetcode.com/graphql"
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"GraphQL Error: {e}")
    return None

def calculate_streak(submission_calendar_str):
    if not submission_calendar_str:
        return 0

    calendar_data = json.loads(submission_calendar_str)
    submitted_dates = set()
    
    for ts in calendar_data.keys():
        date_obj = datetime.datetime.fromtimestamp(int(ts)).date()
        submitted_dates.add(date_obj)

    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)

    streak = 0
    current_check_date = today

    if today in submitted_dates:
        current_check_date = today
    elif yesterday in submitted_dates:
        current_check_date = yesterday
    else:
        return 0

    while current_check_date in submitted_dates:
        streak += 1
        current_check_date -= datetime.timedelta(days=1)

    return streak

def get_submission_status():
    """檢查是否今天有提交 & 從原始資料計算 Streak"""
    query = """
    query getUserProfile($username: String!) {
        recentAcSubmissionList(username: $username, limit: 1) {
            timestamp
        }
        matchedUser(username: $username) {
            userCalendar {
                streak
                submissionCalendar 
            }
        }
    }
    """
    
    data = post_graphql(query, variables={"username": LEETCODE_USERNAME})
    
    if not data or "data" not in data:
        return None, 0

    last_timestamp = 0
    submissions = data["data"].get("recentAcSubmissionList", [])
    if submissions:
        last_timestamp = int(submissions[0]["timestamp"])
    
    streak = 0
    matched_user = data["data"].get("matchedUser")
    if matched_user and matched_user.get("userCalendar"):
        cal_str = matched_user["userCalendar"].get("submissionCalendar", "{}")
        
        streak = calculate_streak(cal_str)


    return last_timestamp, streak

def get_daily_question():
    """獲取今天的每日挑戰題目"""
    query = """
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            date
            link
            question {
                title
                difficulty
                titleSlug
            }
        }
    }
    """
    data = post_graphql(query)
    
    if data and "data" in data:
        daily = data["data"].get("activeDailyCodingChallengeQuestion", {})
        if daily:
            title = daily["question"]["title"]
            difficulty = daily["question"]["difficulty"]
            link = "https://leetcode.com" + daily["link"]
            return title, difficulty, link
    
    return "Unknown", "Unknown", "https://leetcode.com/problemset/all/"

def notify_line(message):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("缺少 LINE 設定，無法發送通知")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    
    try:
        requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        print("LINE 通知發送成功！")
    except Exception as e:
        print(f"LINE 發送失敗: {e}")

def main():
    if not LEETCODE_USERNAME:
        print("請設定 LEETCODE_USERNAME")
        return

    print(f"正在檢查使用者: {LEETCODE_USERNAME} ...")
    
    last_timestamp, streak = get_submission_status()
    
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.datetime.now(tw_tz)
    
    has_submitted_today = False
    if last_timestamp:
        submission_time_utc = datetime.datetime.fromtimestamp(last_timestamp, pytz.utc)
        submission_time_tw = submission_time_utc.astimezone(tw_tz)
        
        print(f"最後提交: {submission_time_tw.strftime('%Y-%m-%d %H:%M')}")
        if submission_time_tw.date() == now_tw.date():
            has_submitted_today = True
    
    if has_submitted_today:
        print("✅ 今天已完成")
        msg = (
            f"✅今日任務已完成！\n"
            f"@{LEETCODE_USERNAME} 太棒了！\n"
            f"目前連續天數 (Streak): 🔥 {streak} 天\n"
            f"繼續保持這個節奏！"
        )
        notify_line(msg)
        
    else:
        print("❌ 今天還沒寫")
        title, difficulty, link = get_daily_question()
        
        msg = (
            f"🚨 Streak 警報！還沒寫！\n"
            f"@{LEETCODE_USERNAME} 你的 Streak ({streak} 天) 快斷了！\n\n"
            f"📅 今日挑戰: {title}\n"
            f"💀 難度: {difficulty}\n"
            f"🔗 傳送門: {link}\n\n"
            f"快點去寫，不要偷懶！"
        )
        notify_line(msg)

if __name__ == "__main__":
    main()