import logging
import subprocess
import sys

logger = logging.getLogger("git_branch_point")
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

git_err_msg = """Git command exited with status %i

Output:
%s
"""

def get_git_cmd(repo_path):
    """Create a function for invoking git commands as a subprocess."""
    def git(cmd, *args):
        full_cmd = ["git", cmd] + list(args)
        try:
            logger.debug(" ".join(full_cmd))
            output = subprocess.check_output(full_cmd, cwd=repo_path,
                                           stderr=subprocess.STDOUT)
            return output.decode().strip()
        except subprocess.CalledProcessError as e:
            raise Exception(git_err_msg % (e.returncode, e.output))
    return git

def git_infer_branch_point(directory):
    """Given a git repository that is checked out to an arbitrary commit
    containing a unique history, this module determines the most commit where
    the history diverged and returns its SHA."""
    git = get_git_cmd(directory)

    # Otherwise we aren't on a PR, so we try to find commits that are only in
    # the current branch c.f.
    # http://stackoverflow.com/questions/13460152/find-first-ancestor-commit-in-another-branch
    head = git("rev-parse", "HEAD")
    not_heads = [item for item in git("rev-parse", "--not", "--all").split("\n")
                 if head not in item]
    commits = git("rev-list", "HEAD", *not_heads).split("\n")
    first_commit = commits[-1]
    branch_point = git("rev-parse", first_commit + "^")

    # The above can produce a too-early commit if we are e.g. on master and
    # there are preceding changes that were rebased and so aren't on any other
    # branch. To avoid this issue we check for the later of the above branch
    # point and the merge-base with master
    merge_base = git("merge-base", "HEAD", "origin/master")
    if (branch_point != merge_base and
        not git("log", "--oneline", "%s..%s" % (merge_base, branch_point)).strip()):
        logger.debug("Using merge-base as the branch point")
        branch_point = merge_base
    else:
        logger.debug("Using first commit on another branch as the branch point")

    return branch_point
