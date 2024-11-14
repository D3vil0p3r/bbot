from bbot.modules.templates.subdomain_enum import subdomain_enum_apikey


class leakix(subdomain_enum_apikey):
    watched_events = ["DNS_NAME"]
    produced_events = ["DNS_NAME"]
    flags = ["subdomain-enum", "passive", "safe"]
    options = {"api_key": ""}
    # NOTE: API key is not required (but having one will get you more results)
    options_desc = {"api_key": "LeakIX API Key"}
    meta = {
        "description": "Query leakix.net for subdomains",
        "created_date": "2022-07-11",
        "author": "@TheTechromancer",
    }

    base_url = "https://leakix.net"
    ping_url = f"{base_url}/host/1.1.1.1"

    def prepare_api_request(self, url, kwargs):
        if self.api_key:
            kwargs["headers"]["api-key"] = self.api_key
            kwargs["headers"]["Accept"] = "application/json"
        return url, kwargs

    async def request_url(self, query):
        url = f"{self.base_url}/api/subdomains/{self.helpers.quote(query)}"
        response = await self.api_request(url)
        return response

    def parse_results(self, r, query=None):
        json = r.json()
        if json:
            for entry in json:
                subdomain = entry.get("subdomain", "")
                if subdomain:
                    yield subdomain
