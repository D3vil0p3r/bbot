from .base import ModuleTestBase, tempwordlist


class TestDnsbrute(ModuleTestBase):
    subdomain_wordlist = tempwordlist(["www", "asdf"])
    blacklist = ["api.asdf.blacklanternsecurity.com"]
    config_overrides = {"modules": {"dnsbrute": {"wordlist": str(subdomain_wordlist), "max_depth": 3}}}

    async def setup_after_prep(self, module_test):

        old_run_live = module_test.scan.helpers.run_live

        async def new_run_live(*command, check=False, text=True, **kwargs):
            if "massdns" in command[:2]:
                _input = [l async for l in kwargs["input"]]
                if "asdf.blacklanternsecurity.com" in _input:
                    yield """{"name": "asdf.blacklanternsecurity.com.", "type": "A", "class": "IN", "status": "NOERROR", "rx_ts": 1713974911725326170, "data": {"answers": [{"ttl": 86400, "type": "A", "class": "IN", "name": "asdf.blacklanternsecurity.com.", "data": "1.2.3.4."}]}, "flags": ["rd", "ra"], "resolver": "195.226.187.130:53", "proto": "UDP"}"""
            else:
                async for _ in old_run_live(*command, check=False, text=True, **kwargs):
                    yield _

        module_test.monkeypatch.setattr(module_test.scan.helpers, "run_live", new_run_live)

        await module_test.mock_dns(
            {
                "blacklanternsecurity.com": {"A": ["4.3.2.1"]},
                "asdf.blacklanternsecurity.com": {"A": ["1.2.3.4"]},
            }
        )

        module = module_test.module
        scan = module_test.scan

        # test query logic
        event = scan.make_event("blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "blacklanternsecurity.com"
        event = scan.make_event("asdf.blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "blacklanternsecurity.com"
        event = scan.make_event("api.asdf.blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "asdf.blacklanternsecurity.com"
        event = scan.make_event("test.api.asdf.blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "asdf.blacklanternsecurity.com"

        assert module.dedup_strategy == "lowest_parent"
        module.dedup_strategy = "highest_parent"
        event = scan.make_event("blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "blacklanternsecurity.com"
        event = scan.make_event("asdf.blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "blacklanternsecurity.com"
        event = scan.make_event("api.asdf.blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "blacklanternsecurity.com"
        event = scan.make_event("test.api.asdf.blacklanternsecurity.com", "DNS_NAME", dummy=True)
        assert module.make_query(event) == "blacklanternsecurity.com"
        module.dedup_strategy = "lowest_parent"

        # test recursive brute-force event filtering
        event = module_test.scan.make_event("blacklanternsecurity.com", "DNS_NAME", parent=module_test.scan.root_event)
        event.scope_distance = 0
        result, reason = await module_test.module.filter_event(event)
        assert result == True
        event = module_test.scan.make_event(
            "www.blacklanternsecurity.com", "DNS_NAME", parent=module_test.scan.root_event
        )
        event.scope_distance = 0
        result, reason = await module_test.module.filter_event(event)
        assert result == True
        event = module_test.scan.make_event(
            "test.www.blacklanternsecurity.com", "DNS_NAME", parent=module_test.scan.root_event
        )
        event.scope_distance = 0
        result, reason = await module_test.module.filter_event(event)
        assert result == True
        event = module_test.scan.make_event(
            "asdf.test.www.blacklanternsecurity.com", "DNS_NAME", parent=module_test.scan.root_event
        )
        event.scope_distance = 0
        result, reason = await module_test.module.filter_event(event)
        assert result == True
        event = module_test.scan.make_event(
            "wat.asdf.test.www.blacklanternsecurity.com", "DNS_NAME", parent=module_test.scan.root_event
        )
        event.scope_distance = 0
        result, reason = await module_test.module.filter_event(event)
        assert result == False
        assert reason == f"subdomain depth of *.asdf.test.www.blacklanternsecurity.com (4) > max_depth (3)"
        event = module_test.scan.make_event(
            "hmmm.ptr1234.blacklanternsecurity.com", "DNS_NAME", parent=module_test.scan.root_event
        )
        event.scope_distance = 0
        result, reason = await module_test.module.filter_event(event)
        assert result == False
        assert reason == f'"ptr1234.blacklanternsecurity.com" looks like an autogenerated PTR'

    def check(self, module_test, events):
        assert len(events) == 4
        assert 1 == len(
            [e for e in events if e.data == "asdf.blacklanternsecurity.com" and str(e.module) == "dnsbrute"]
        )
