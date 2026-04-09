import requests
import datetime
import os
import json
import pytz
import uuid
# from dotenv import load_dotenv

# load_dotenv()

LEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME") 
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
}

def calculate_streak_from_calendar(submission_calendar, tw_tz):
    """從 submissionCalendar 依台灣時區計算連續天數。"""
    if not submission_calendar:
        return 0

    try:
        calendar_data = json.loads(submission_calendar)
    except (TypeError, ValueError):
        return 0

    solved_dates = set()
    for timestamp_str, count in calendar_data.items():
        if int(count) <= 0:
            continue

        solved_time_utc = datetime.datetime.fromtimestamp(int(timestamp_str), pytz.utc)
        solved_date_tw = solved_time_utc.astimezone(tw_tz).date()
        solved_dates.add(solved_date_tw)

    if not solved_dates:
        return 0

    today_tw = datetime.datetime.now(tw_tz).date()
    current_day = today_tw if today_tw in solved_dates else (today_tw - datetime.timedelta(days=1))

    streak = 0
    while current_day in solved_dates:
        streak += 1
        current_day -= datetime.timedelta(days=1)

    return streak

def post_graphql(query, variables=None):
    """發送 GraphQL 請求的共用函式"""
    url = "https://leetcode.com/graphql"
    csrftoken = uuid.uuid4().hex
    
    headers = HEADERS.copy()
    headers["Referer"] = "https://leetcode.com/"
    headers["X-CSRFToken"] = csrftoken
    headers["Cookie"] = f"csrftoken={csrftoken};"
    
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"GraphQL Error: {e}")
    return None

def get_submission_status():
    """檢查是否今天有提交 & 從原始資料計算 Streak"""
    query = """
    query getUserProfile($username: String!) {
        recentAcSubmissionList(username: $username, limit: 1) {
            timestamp
        }
        streakCounter(username: $username) {
            streakCount
            currentDayCompleted
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
        return None, 0, False

    last_timestamp = 0
    submissions = data["data"].get("recentAcSubmissionList", [])
    if submissions:
        last_timestamp = int(submissions[0]["timestamp"])

    streak_counter = data["data"].get("streakCounter") or {}
    counter_streak = int(streak_counter.get("streakCount", 0) or 0)
    current_day_completed = bool(streak_counter.get("currentDayCompleted", False))
    
    api_streak = 0
    computed_streak = 0
    matched_user = data["data"].get("matchedUser")
    if matched_user and matched_user.get("userCalendar"):
        user_calendar = matched_user["userCalendar"]

        api_streak = user_calendar.get("streak", 0)
        tw_tz = pytz.timezone('Asia/Taipei')
        computed_streak = calculate_streak_from_calendar(user_calendar.get("submissionCalendar"), tw_tz)

    streak = max(counter_streak, api_streak, computed_streak)

    return last_timestamp, streak, current_day_completed

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
    
    last_timestamp, streak, current_day_completed = get_submission_status()
    
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.datetime.now(tw_tz)
    
    has_submitted_today = current_day_completed
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