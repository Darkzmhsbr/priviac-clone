import redis, json, httpx
r = redis.from_url(os.getenv("REDIS_URL"))

async def login_privacy(username: str, password: str):
    jar = httpx.Cookies()
    async with httpx.AsyncClient(cookies=jar, timeout=15) as cli:
        await cli.post("https://privacy.com.br/auth", data={"username": username, "password": password})
        r.setex("privacy_cookies", 3600, json.dumps(dict(jar)))   # 1 h
        return jar
