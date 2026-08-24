#!/usr/bin/osascript

on run argv
	if (count of argv) is 0 then
		error "Usage: perplexity-echo.as <text>"
	end if

	set AppleScript's text item delimiters to " "
	set promptText to argv as text
	set AppleScript's text item delimiters to ""

	tell application "Perplexity" to activate
	delay 0.2

	tell application "System Events"
		tell process "Perplexity"
			keystroke "k" using command down
			delay 0.5
			keystroke "a" using command down
			keystroke promptText
			key code 36 -- Return
		end tell
	end tell
end run
