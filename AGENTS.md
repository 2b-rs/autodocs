
# Working Rules for Automation and AI Agents

YOU are the AGENT. Therefore YOU should respect the following instructions while working with me.

Remark:
This file is intended for automated tools and AI agents (like you are) working on the project.
It is not a guide for using or publishing the API reference.

## MCP / sandbox information
- avoid the write/execute tool. Instead, use the local runner as described below, first and foremost for find and grep operations.

- prefer to call grep inside run.sh over direct file reads.

- Only `/tmp` and the project directory (including `_src/`) are writable.
  Write access to all other files of the local machine and network access
  are blocked by the MCP sandbox.
- By default, the environment's `TMPDIR` points to `/var/folders/…`, which
  is outside the allowed locations. Any use of `tempfile` will therefore fail.
- The sandbox checks the **entire** command in advance: a single disallowed
  path aborts the complete call, even if everything else would be permitted.

- Solutions:
-- use`python3 -m py_compile`. This write `__pycache__` next to the source file.
-- prefix every command with:

```bash
export TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1
```

-- use `ast.parse()` or explicitly set the destination:
  `py_compile.compile(src, cfile="/tmp/x.pyc", doraise=True)`.

- NEVER attempt to install software, download anything, write to the user's home
  directory, or run a headless browser directly through MCP execute. Internet access, writes
  outside `/tmp`, and anything that causes high CPU usage will be BLOCKED.
  All operations MUST use `run.sh` mechanism explained above.

-- prefer to use the local runner whenever possible. See below.

-- If you tried to use MCP and it failed due to a limitation, report the failure reason and YIELD IMMEDIATELY.

## local runner

- The preferred way of executing code in this project is:

  create a zsh script named `run.sh` in the project's root directory and YIELD IMMEDIATELY.
  The script will be executed on your behalf in a sandbox with extended privileges as compared to the local MCP. You will be informed about the exit code and get access to its output.

- At the beginning of `run.sh`, DESCRIBE THE PURPOSE. Print the following to
  stdout:
  1. A one-line title stating the purpose, such as CPU OFFLOADING, DOWNLOAD, or
     SW INSTALLATION.
  2. A short summary of `run.sh`'s structure.
  3. A detailed explanation of your goal hierarchy.
  4. An estimate of the data traffic, CPU load, number of workers, or wall-clock
     time required for completion.

- Combine as much work as possible into each single call of `run.sh`.

- Use job-level parallelism whereever possible. You have 12 CPUs, try to saturate them.

- Have `run.sh` print progress information regularly, at least once every 5
  seconds.


## Collaboration
- The list of open Tasks for AGENTS can be found in TODO.md. This is your backlog.
- ALWAYS KEEP GOING on a task until it is complete or has clearly become unreachable.
- If the intention is not completely clear, make a best guess assumption and document your decisions.
- Be THOROUGH, FACTUAL, PRECISE, CONCISE, and HONEST.
- Whenever you complete a piece of work:
  1. Check the corresponding box in `TODO.md`.
  2. Commit your changes to the local Git repository, using the user's email
     address as the author.
  3. Select the next best piece of work from `TODO.md` and KEEP GOING.

Further project information is available in [`README.md`](README.md) and
[`_src/WARTUNG.md`](_src/WARTUNG.md).
