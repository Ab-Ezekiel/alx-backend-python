#!/usr/bin/env python3
"""Unit tests for client.GithubOrgClient"""
import unittest
from parameterized import parameterized
from unittest.mock import patch

from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """Tests for the GithubOrgClient.org property."""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("client.get_json")
    def test_org(self, org_name, mock_get_json):
        """Test that org property returns value from get_json."""
        expected = {"repos_url": f"https://api.github.com/orgs/{org_name}/repos"}
        mock_get_json.return_value = expected

        gh = GithubOrgClient(org_name)
        # Access property (memoized) — should return mock value
        result = gh.org
        self.assertEqual(result, expected)

        # Ensure get_json was called exactly once with the ORG_URL
        mock_get_json.assert_called_once_with(
            GithubOrgClient.ORG_URL.format(org=org_name)
        )


if __name__ == "__main__":
    unittest.main()
