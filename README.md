# Commitsan: the commit sanitizer
Every time a branch is pushed Commitsan checks _all_ new commits for possible
whitespace errors (`git diff --check`) or commit log message violations
([The Seven Rules](http://chris.beams.io/posts/git-commit/#seven-rules)), and
updates the commit [status](https://github.com/blog/1227-commit-status-api)
on GitHub.

## Available checks

Check / status code | Description
------------------- | -----------------------------------------------
`diff`              | Some lines introduce whitespace errors
`msg`               | Must provide log message
`msg/subj`          | Put subject on the first line
`msg/subj-list`     | Do not put bullets on the subject line
`msg/subj-period`   | Do not end the subject line with a period
`msg/subj-line`     | Separate subject from body with a blank line
`msg/subj-limit`    | Keep the subject concise: 50 characters or less
`msg/wrap`          | Wrap the body at 72 characters
`msg/case`          | Capitalize the sentence
`msg/mood`          | Use the imperative mood
`msg/topic`         | Missing topic / subsystem
`msg/brackets`      | Use colons inside the topic
`msg/labels`        | Put labels after the topic
