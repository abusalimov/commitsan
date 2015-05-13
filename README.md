# Commitsan: the commit sanitizer
Every time a branch is pushed Commitsan checks _all_ new commits for possible
whitespace errors (`git diff --check`) or commit log message violations
([The Seven Rules](http://chris.beams.io/posts/git-commit/#seven-rules)), and
updates the commit [status](https://github.com/blog/1227-commit-status-api)
on GitHub.
