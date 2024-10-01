import httpx

from .base import ModuleTestBase


class TestC99(ModuleTestBase):
    module_name = "c99"
    config_overrides = {"modules": {"c99": {"api_key": "asdf"}}}

    async def setup_before_prep(self, module_test):
        module_test.httpx_mock.add_response(
            url="https://api.c99.nl/randomnumber?key=asdf&between=1,100&json",
            json={"success": True, "output": 65},
        )
        module_test.httpx_mock.add_response(
            url="https://api.c99.nl/subdomainfinder?key=asdf&domain=blacklanternsecurity.com&json",
            json={
                "success": True,
                "subdomains": [
                    {"subdomain": "asdf.blacklanternsecurity.com", "ip": "1.2.3.4", "cloudflare": True},
                ],
                "cached": True,
                "cache_time": "2023-05-19 03:13:05",
            },
        )

    def check(self, module_test, events):
        assert any(e.data == "asdf.blacklanternsecurity.com" for e in events), "Failed to detect subdomain"


class TestC99AbortThreshold(TestC99):
    config_overrides = {"modules": {"c99": {"api_key": ["6789", "fdsa", "1234", "4321"]}}}

    async def setup_before_prep(self, module_test):
        module_test.httpx_mock.add_response(
            url="https://api.c99.nl/randomnumber?key=fdsa&between=1,100&json",
            json={"success": True, "output": 65},
        )

        self.url_count = {}

        async def custom_callback(request):
            url = str(request.url)
            try:
                self.url_count[url] += 1
            except KeyError:
                self.url_count[url] = 1
            raise httpx.TimeoutException("timeout")

        module_test.httpx_mock.add_callback(custom_callback)

    def check(self, module_test, events):
        assert module_test.module.failed_request_abort_threshold == 8
        assert module_test.module.errored == True
        assert [e.data for e in events if e.type == "DNS_NAME"] == ["blacklanternsecurity.com"]
        assert self.url_count == {
            "https://api.c99.nl/randomnumber?key=6789&between=1,100&json": 1,
            "https://api.c99.nl/randomnumber?key=4321&between=1,100&json": 1,
            "https://api.c99.nl/randomnumber?key=1234&between=1,100&json": 1,
            "https://api.c99.nl/subdomainfinder?key=fdsa&domain=blacklanternsecurity.com&json": 2,
            "https://api.c99.nl/subdomainfinder?key=6789&domain=blacklanternsecurity.com&json": 2,
            "https://api.c99.nl/subdomainfinder?key=4321&domain=blacklanternsecurity.com&json": 2,
            "https://api.c99.nl/subdomainfinder?key=1234&domain=blacklanternsecurity.com&json": 2,
        }
