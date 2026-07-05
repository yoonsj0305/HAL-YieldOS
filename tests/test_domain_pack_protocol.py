"""
Tests for DomainPack Protocol and DomainRegistry (v2.2.0)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDomainPackProtocol:
    def test_protocol_importable(self):
        from yieldos.core.domain_pack import DomainPack
        assert DomainPack is not None

    def test_protocol_is_runtime_checkable(self):
        from yieldos.core.domain_pack import DomainPack
        # A dict does NOT satisfy the protocol
        assert not isinstance({}, DomainPack)

    def test_conforming_class_satisfies_protocol(self):
        from yieldos.core.domain_pack import DomainPack

        class MockPack:
            @property
            def domain(self) -> str:
                return "robot"

            def domain_name(self) -> str:
                return "robot"

            def analyze(self, **kwargs):
                return {}

        assert isinstance(MockPack(), DomainPack)


class TestDomainRegistry:
    def setup_method(self):
        from yieldos.core import domain_registry
        domain_registry.clear()

    def teardown_method(self):
        from yieldos.core import domain_registry
        domain_registry.clear()

    def test_register_and_get(self):
        from yieldos.core import domain_registry

        class FakePack:
            @property
            def domain(self):
                return "test_domain"
            def domain_name(self):
                return "test_domain"
            def analyze(self, **kwargs):
                return {}

        pack = FakePack()
        domain_registry.register("test_domain", pack)
        assert domain_registry.get("test_domain") is pack

    def test_get_unknown_returns_none(self):
        from yieldos.core import domain_registry
        assert domain_registry.get("nonexistent") is None

    def test_list_domains(self):
        from yieldos.core import domain_registry

        class FakePack:
            @property
            def domain(self):
                return "d"
            def domain_name(self):
                return "d"
            def analyze(self, **kwargs):
                return {}

        domain_registry.register("alpha", FakePack())
        domain_registry.register("beta", FakePack())
        domains = domain_registry.list_domains()
        assert "alpha" in domains
        assert "beta" in domains

    def test_register_empty_name_raises(self):
        import pytest

        from yieldos.core import domain_registry

        class FakePack:
            @property
            def domain(self):
                return ""
            def domain_name(self):
                return ""
            def analyze(self, **kwargs):
                return {}

        with pytest.raises(ValueError):
            domain_registry.register("", FakePack())
