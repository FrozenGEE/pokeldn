import pytest

from pokeldn.app import github_mirror


@pytest.fixture(autouse=True)
def reset():
    github_mirror.select("")
    yield
    github_mirror.select("")


def test_the_mirror_list_is_unique_https_prefixes():
    prefixes = [prefix for prefix, _ in github_mirror.MIRRORS]
    assert prefixes[0] == "" and len(prefixes) == len(set(prefixes))
    assert all(prefix.startswith("https://") and prefix.endswith("/") for prefix in prefixes if prefix)
    assert len(github_mirror.MIRRORS) >= 6


def test_select_takes_a_listed_mirror_only():
    for prefix, _ in github_mirror.MIRRORS:
        github_mirror.select(prefix)
        assert github_mirror.current() == prefix
    github_mirror.select("https://not-in-the-list.example/")
    assert github_mirror.current() == ""


def test_apply_rewrites_github_hosts_and_leaves_others_alone():
    github_mirror.select("https://ghfast.top/")
    assert github_mirror.apply("https://github.com/a/b") == "https://ghfast.top/https://github.com/a/b"
    assert github_mirror.apply("https://raw.githubusercontent.com/a/b") == (
        "https://ghfast.top/https://raw.githubusercontent.com/a/b")
    assert github_mirror.apply("https://example.com/a") == "https://example.com/a"
    assert github_mirror.apply("https://github.com/a", prefix="") == "https://github.com/a"
