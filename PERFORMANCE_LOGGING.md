Performance logging:

run.sh script invocations shall be evaluated clustered by purpose. For each purpose, create a distinct subdirectory and keep the logs from each actual invocations there.

`run.sh` scripts with a common purpose that are used frequently must be factored into re-usable scripts in _src/ or _src/tools, so that run.sh merely acts as a wrapper.

Here's a list of common purposes for run.sh scripts. You may extend it if you find it doesn't fit:

- re-generate html
- validate db contents
- perform a scraping run
- update the ai knowledge base
- create ASPICE assessment report
