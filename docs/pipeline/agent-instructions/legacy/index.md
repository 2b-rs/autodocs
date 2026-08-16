# legacy authority instruction bundle

Read root `agent-workflow.json`, validate its digest and schema, enforce its selected authority epoch, and use only declared runner actions. On any mismatch: stop mutation and run `issuectl bootstrap --refresh`.
