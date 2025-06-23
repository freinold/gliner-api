from logging import Logger

from git import Repo
from git.exc import InvalidGitRepositoryError

from gliner_api.logging import getLogger

logger: Logger = getLogger("gliner-api.version")


def get_version() -> str:
    if version := _get_git_version():
        logger.debug(f"Version {version} (from git)")
        return version
    else:
        logger.warning("No version found")
        return "0.1.0"


def _get_git_version() -> str | None:
    version: str | None = None

    # Try to get the version from the git repository
    try:
        repo = Repo(search_parent_directories=True)
        current_commit_hash = repo.commit("HEAD").hexsha

        # Check if the current commit is tagged
        for tag in repo.tags:
            if tag.commit.hexsha == current_commit_hash:
                return tag.name

        # If the current commit is not tagged, use the commit hash stub
        if version is None:
            return current_commit_hash[:8]

    # Fallback to None if no git repository is found
    except InvalidGitRepositoryError:
        return None
