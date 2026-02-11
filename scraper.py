async def list_media(username: str):
    jar = json.loads(r.get("privacy_cookies") or "{}")
    async with httpx.AsyncClient(cookies=jar) as cli:
        r = await cli.post("https://privacy.com.br/graphql",
            json={"query": f'{{profile(username: "{username}") {{media {{id, url, type}}}}}}'})
        return r.json()["data"]["profile"]["media"]   # [{id,url,type}, …]
