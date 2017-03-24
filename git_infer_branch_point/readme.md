# `git_infer_branch_point.py`

A utility for [the git version control system](https://git-scm.com/), written
in Python.

Given a git repository that is checked out to an arbitrary commit containing
a unique history, this module determines the most commit where the history
diverged and returns its SHA.
