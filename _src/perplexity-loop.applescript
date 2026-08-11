#!/usr/bin/osascript

on run argv
	set waitInterval to 5
	if (count of argv) > 0 then
		try
			set waitInterval to (item 1 of argv) as integer
		on error
			error "Invalid interval argument: " & (item 1 of argv)
		end try
	end if

	repeat 65535 times
		set promptRoll to random number from 1 to 100

		if promptRoll is less than or equal to 80 then
			set promptText to "go on with your task. Check in occasionally. When you're finished with one task, pick another from NEXTSTEPS.md and start working on that. If you're completely stuck or nothing is left to do, write \"He's dead, Jim!\" into run.sh."
		else if promptRoll is less than or equal to 100 then
			set promptText to "Read AGENTS.md and keep going."
		else if promptRoll is less than or equal to 30 then
			set promptText to "What's the next step?"
		else if promptRoll is less than or equal to 60 then
			set promptText to "Go ahead."
		else if promptRoll is less than or equal to 68 then
			set promptText to "Do you have any other ideas on how to improve things? Add them to NEXTSTEPS.md and start immediately."
		else
			set promptText to "If you're stuck or finished, write \"He's dead, Jim!\" into run.sh. Otherwise, keep going."
		end if

		tell application "System Events"
			set previousFrontmostProcess to first process whose frontmost is true
			set previousFrontmostName to name of previousFrontmostProcess
		end tell

		set perplexityIsReady to false
		repeat with retryDelay in {0.1, 0.2, 0.4, 0.8}
			tell application "Perplexity" to activate
			delay retryDelay
			tell application "System Events"
				if exists process "Perplexity" then
					if frontmost of process "Perplexity" then
						set perplexityIsReady to true
					end if
				end if
			end tell
			if perplexityIsReady then exit repeat
		end repeat

		if not perplexityIsReady then error "Perplexity did not become frontmost."

		tell application "System Events"
			tell process "Perplexity"
				key code 36 -- Return
				delay 0.2
				keystroke "k" using command down
				delay 0.1
				keystroke "a" using command down
				keystroke promptText
				key code 36 -- Return
			end tell
		end tell

		if previousFrontmostName is not "Perplexity" then
			tell application "System Events"
				if exists process previousFrontmostName then
					set frontmost of process previousFrontmostName to true
				end if
			end tell
		end if

		repeat waitInterval times
			delay 1
		end repeat
	end repeat
end run
