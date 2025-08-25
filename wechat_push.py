import os
import datetime
import requests
# 本地运行时打开,提交代码时关闭
# from dotenv import load_dotenv
# load_dotenv()


# 从环境变量中读取配置（关键！为了安全，敏感信息不写死在代码里）
APPID = os.environ['APPID']
APPSECRET = os.environ['APPSECRET']
# 多个用户的OpenID，可以从文件读取，或直接写在环境变量里用分号隔开
OPENID_LIST = os.environ['OPENID_LIST'].split(';')
TEMPLATE_ID = os.environ['TEMPLATE_ID']

user_database = {
    # "os3j01wDbtP7kLBGIP7v5KIUp-DE": {
    #     "name": "阿毛",
    #     "city": "西安",
    #     "city_code": "101110101",  # 西安
    #     "met_date": "2025-08-15"
    # },
    "os3j01wDbtP7kLBGIP7v5KIUp-DE": {
        "name": "Nana",
        "city": "天津",
        "city_code": "101030600",  # 北晨区
        "met_date": "2025-08-15"
    },
}




def get_access_token():
    """获取微信接口调用凭证 access_token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    response = requests.get(url).json()
    return response.get('access_token')


def get_users(access_token):
    """获取测试号关注用户列表（包含真实OpenID）"""
    url = f"https://api.weixin.qq.com/cgi-bin/user/get?access_token={access_token}"
    response = requests.get(url).json()
    print("User list response:", response)

    if 'data' in response and 'openid' in response['data']:
        return response['data']['openid']
    else:
        print("Failed to get user list:", response)
        return []

def get_weather(city_code):
    # 示例：假设你有一个天气API
    weather_api_url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
    response = requests.get(weather_api_url).json()
    cityInfo = response['cityInfo']
    todayInfo:dict[str,str] = response['data']['forecast'][0]
    print(todayInfo)
    city_weather = {
        "date": f"{todayInfo['ymd']}",
        "week": f"{todayInfo['week']}",
        "city": f"{cityInfo['parent']}·{cityInfo['city']}",
        "type": f"{todayInfo['type']}",
        "high": f"{todayInfo['high'].split(' ')[1]}",
        "low":  f"{todayInfo['low'].split(' ')[1]}",
        "tip": f"{todayInfo['notice']}",
    }
    return city_weather


# 计算相识天数
def get_meet_days(met_date):
    met_date = datetime.datetime.strptime(met_date, '%Y-%m-%d')
    today = datetime.datetime.now()
    delta = today - met_date
    return delta.days


def get_new_years_eve():
    """
    计算当前日期到当年除夕的天数
    返回：剩余天数（整数）
    """
    # 获取当前日期
    today = datetime.date.today()

    # 计算当年除夕日期（假设除夕是农历12月30日，这里简化为公历12月31日）
    # 注意：实际除夕日期需要根据农历计算，这里使用简化版本
    new_years_eve = datetime.date(today.year, 12, 31)

    # 如果今年除夕已过，计算下一年的除夕
    if today > new_years_eve:
        new_years_eve = datetime.date(today.year + 1, 12, 31)

    # 计算天数差
    delta = new_years_eve - today
    return delta.days

def send_message(access_token, openid, city_weather,days,eve):
    """发送模板消息给指定用户"""
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

    user_info = user_database[openid]
    # 构建消息数据体，根据你申请的模板字段来构造
    data = {
        "touser": openid,
        "template_id": TEMPLATE_ID,
        "url": "",
        "data": {
            "date": {
                "value": f"{city_weather['date']}",
            },
            "week": {
                "value": f"{city_weather['week']}",
            },
            "uname": {
                "value": user_info["name"],
            },
            "met": {
                "value": days,
            },
            "city": {
                "value": city_weather["city"],
            },
            "type": {
                "value": f"{city_weather['type']}",
            },
            "high": {
                "value": f"{city_weather['high']}",
            },
            "low": {
                "value": f"{city_weather['low']}",
            },
            "tip": {
                "value": city_weather['tip'],
            },
            "cx": {
                "value": eve,
            }
        }
    }
    # 将数据转为JSON并发送
    response = requests.post(url, json=data).json()
    return response


def main():
    # 1. 获取 access_token
    token = get_access_token()
    if not token:
        print("Failed to get access token!")
        return
    # 2. 遍历所有用户，发送消息
    openids = get_users(token)
    for openid in openids:
        user_info = user_database[openid]
        city_weather = get_weather(user_info['city_code'])
        days = get_meet_days(user_info['met_date'])
        eve = get_new_years_eve()
        result = send_message(token, openid,city_weather,days,eve)
        print(f"Message to {openid} sent. Result: {result}")


if __name__ == '__main__':
    main()



# 今天是{{date.DATA}} {{week.DATA}}
# 早上好呀，{{uname.DATA}} (＾▽＾)／ ～
# 今天是认识的第{{met.DATA}}天(◕‿◕✿) ！
# 又是元气满满的一天呢✧。٩(ˊωˋ)و✧*。～
#
# 🌆城市：{{city.DATA}}
# ☁️天气：{{type.DATA}}
# 🔥最高气温：{{high.DATA}}
# ❄️最低气温：{{low.DATA}}
# 💭{{tip.DATA}}
#
# 🎊距离除夕剩余：{{cx.DATA}}天,(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧~

