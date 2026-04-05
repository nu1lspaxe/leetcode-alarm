import urllib.request
import json
query = """
query {
    matchedUser(username: "nu1lspaxe") {
        userCalendar {
            streak
        }
    }
}
"""
url = "https://leetcode.com/graphql"
req = urllib.request.Request(url, data=json.dumps({"query": query}).encode('utf-8'), headers={'Content-Type': 'application/json'})
response = urllib.request.urlopen(req)
print(json.loads(response.read().decode('utf-8')))
