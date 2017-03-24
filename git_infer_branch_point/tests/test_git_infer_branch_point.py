import os
import pytest
import shutil
import subprocess
import tempfile

from ..git_infer_branch_point import git_infer_branch_point

test_repo_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              "temporary_repository_for_testing")
git_err_msg = """Git command exited with status %i

Output:
%s
"""

@pytest.fixture()
def tmp_dir(request):
    name = tempfile.mkdtemp()
    request.addfinalizer(lambda: shutil.rmtree(name, ignore_errors=True))
    return name

# Create a directory containing a git repository, initialize it with a simple
# commit history, and return a function for issuing git commands within it.
# Arrange for the directory to be removed at the completion of the test,
# regardless of test status.
@pytest.fixture
def git(tmp_dir):
    def git(cmd, *args):
        full_cmd = ["git", cmd] + list(args)
        try:
            output = subprocess.check_output(full_cmd, cwd=tmp_dir,
                                             stderr=subprocess.STDOUT)
            return output.decode().strip()
        except subprocess.CalledProcessError as e:
            raise Exception(git_err_msg % (e.returncode, e.output))

    git("init")
    git("config", "user.email", "wpt-tools-test-runner@example.com")
    git("config", "user.name", "wpt-tools-test-runner")
    git("commit", "--allow-empty", "--message", "initial commit")
    git("tag", "initial")
    git("commit", "--allow-empty", "--message", "second commit")
    # Simulate a remote that is in sync with the local repository
    git("branch", "origin/master")

    return git

def test_one_ahead_of_master(git, tmp_dir):
    git("checkout", "--detach")
    git("commit", "--allow-empty", "-m", "tmp")

    assert git_infer_branch_point(tmp_dir) == git("rev-parse", "master")

def test_two_ahead_of_master(git, tmp_dir):
    git("checkout", "--detach")
    git("commit", "--allow-empty", "-m", "tmp")
    git("commit", "--allow-empty", "-m", "tmp")

    assert git_infer_branch_point(tmp_dir) == git("rev-parse", "master")

def test_one_ahead_one_behind_master(git, tmp_dir):
    git("checkout", "master~")
    git("commit", "--allow-empty", "-m", "tmp")

    assert git_infer_branch_point(tmp_dir) == git("rev-parse", "master~")

def test_one_new_on_master(git, tmp_dir):
    git("commit", "--allow-empty", "-m", "tmp")
    git("branch", "--force", "origin/master")

    assert git_infer_branch_point(tmp_dir) == git("rev-parse", "HEAD")

def test_two_new_on_master(git, tmp_dir):
    git("commit", "--allow-empty", "-m", "tmp")
    git("commit", "--allow-empty", "-m", "tmp")
    git("branch", "--force", "origin/master")

    assert git_infer_branch_point(tmp_dir) == git("rev-parse", "HEAD")
