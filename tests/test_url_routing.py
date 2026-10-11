import importlib
import unittest
from unittest.mock import patch


resolver = importlib.import_module("shortlink_bypass.bypass")


class CleanUrlTests(unittest.TestCase):
    def test_adds_https_to_bare_host(self):
        self.assertEqual(
            resolver.clean_url("example.com/path"),
            "https://example.com/path",
        )

    def test_normalizes_scheme_and_host(self):
        self.assertEqual(
            resolver.clean_url("HTTPS://ExAmPlE.com:8443/path?q=1"),
            "https://example.com:8443/path?q=1",
        )

    def test_rejects_non_http_schemes(self):
        self.assertIsNone(resolver.clean_url("javascript://example.com/run"))
        self.assertIsNone(resolver.clean_url("ftp://example.com/file"))

    def test_rejects_credentials_and_invalid_ports(self):
        self.assertIsNone(resolver.clean_url("https://user:pass@example.com/"))
        self.assertIsNone(resolver.clean_url("https://example.com:notaport/"))

    def test_rejects_non_string_empty_and_controlled_input(self):
        self.assertIsNone(resolver.clean_url(None))
        self.assertIsNone(resolver.clean_url("  "))
        self.assertIsNone(resolver.clean_url("https://example.com/\n--data"))


class DomainRoutingTests(unittest.TestCase):
    def test_specific_handlers_match_exact_hosts_and_subdomains(self):
        self.assertIs(
            resolver.get_handler("https://ay.live/key")[0],
            resolver.bypass_aylink,
        )
        self.assertIs(
            resolver.get_handler("https://sub.ay.live/key")[0],
            resolver.bypass_aylink,
        )

    def test_lookalike_hosts_and_url_paths_do_not_match_specific_handler(self):
        lookalikes = (
            "https://notay.live/key",
            "https://ay.live.attacker.example/key",
            "https://example.com/ay.live/key",
        )
        for url in lookalikes:
            with self.subTest(url=url):
                self.assertIsNot(
                    resolver.get_handler(url)[0],
                    resolver.bypass_aylink,
                )

    def test_form_handlers_match_host_suffix_not_url_text(self):
        self.assertIs(
            resolver.get_handler("https://sub.rocklinks.net/key")[0],
            resolver.bypass_type_form,
        )
        self.assertIsNot(
            resolver.get_handler("https://example.com/rocklinks.net/key")[0],
            resolver.bypass_type_form,
        )

    def test_known_shortener_matching_respects_domain_boundaries(self):
        with patch.object(resolver, "KNOWN_SHORTENERS", {"bit.ly"}):
            self.assertTrue(resolver.is_known_shortener("bit.ly"))
            self.assertTrue(resolver.is_known_shortener("sub.bit.ly"))
            self.assertFalse(resolver.is_known_shortener("notbit.ly"))
            self.assertFalse(resolver.is_known_shortener("bit.ly.attacker.example"))

    def test_invalid_input_is_not_dispatched(self):
        with patch.object(resolver, "get_handler") as get_handler:
            self.assertIsNone(resolver.bypass("javascript://example.com/run"))
            get_handler.assert_not_called()

    def test_invalid_handler_destination_is_rejected(self):
        with patch.object(
            resolver,
            "get_handler",
            return_value=(lambda _url: "javascript://example.com/run", "test"),
        ):
            self.assertIsNone(resolver.bypass("https://example.com/"))


if __name__ == "__main__":
    unittest.main()
