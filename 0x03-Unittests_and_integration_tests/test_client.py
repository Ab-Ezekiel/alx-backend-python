#!/usr/bin/env python3
"""Unit tests for client.GithubOrgClient"""
import unittest
from parameterized import parameterized
from unittest.mock import patch, PropertyMock  # add PropertyMock here

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
        result = gh.org
        self.assertEqual(result, expected)
        mock_get_json.assert_called_once_with(
            GithubOrgClient.ORG_URL.format(org=org_name)
        )


class TestPublicRepos(unittest.TestCase):
    """Tests for the GithubOrgClient._public_repos_url property."""

    def test_public_repos_url(self):
        """Test that _public_repos_url returns the mocked repos_url."""
        client = GithubOrgClient("test")
        with patch.object(
            GithubOrgClient, "org", new_callable=PropertyMock
        ) as mock_org:
            mock_org.return_value = {
                "repos_url": "https://api.github.com/orgs/test/repos"
            }
            self.assertEqual(
                client._public_repos_url,
                "https://api.github.com/orgs/test/repos"
            )


if __name__ == "__main__":
    unittest.main()
