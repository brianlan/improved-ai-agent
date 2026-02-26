on run argv
	if (count of argv) < 2 then error "Usage: osascript capture_books_png.scpt <epubPath> <outputDir> [startIndex maxPages duplicateStopThreshold minDelay pollInterval timeout minTotalWait stablePolls postChangeSettle]"

	set epubPath to item 1 of argv
	set outputDir to item 2 of argv

	set startIndex to 1
	set maxPagesSafety to 5000
	set duplicateStopThreshold to 2

	set minDelayAfterTurn to 0.35
	set pollIntervalSeconds to 0.30
	set changeTimeoutSeconds to 9.0
	set minTotalWaitAfterTurn to 1.2
	set stablePollsRequired to 4
	set postChangeSettleSeconds to 0.40

	if (count of argv) >= 3 then set startIndex to (item 3 of argv) as integer
	if (count of argv) >= 4 then set maxPagesSafety to (item 4 of argv) as integer
	if (count of argv) >= 5 then set duplicateStopThreshold to (item 5 of argv) as integer
	if (count of argv) >= 6 then set minDelayAfterTurn to (item 6 of argv) as real
	if (count of argv) >= 7 then set pollIntervalSeconds to (item 7 of argv) as real
	if (count of argv) >= 8 then set changeTimeoutSeconds to (item 8 of argv) as real
	if (count of argv) >= 9 then set minTotalWaitAfterTurn to (item 9 of argv) as real
	if (count of argv) >= 10 then set stablePollsRequired to (item 10 of argv) as integer
	if (count of argv) >= 11 then set postChangeSettleSeconds to (item 11 of argv) as real

	set imageFormat to "png"
	set probePath to "/tmp/books_probe_capture.png"

	do shell script "/bin/mkdir -p " & quoted form of outputDir
	do shell script "/usr/bin/open -a Books " & quoted form of epubPath
	delay 4

	tell application "Books" to activate
	delay 1

	my goToBeginning()
	delay 1

	set prevHash to ""
	set sameCount to 0
	set savedCount to 0
	set firstDim to ""
	set mismatchDimCount to 0

	repeat with i from startIndex to maxPagesSafety
		set pageId to my pad3(i)
		set outPath to outputDir & "/" & pageId & "." & imageFormat

		set {xPos, yPos, w, h} to my getBooksWindowRect()
		do shell script "/usr/sbin/screencapture -x -o -t " & imageFormat & " -R" & xPos & "," & yPos & "," & w & "," & h & " " & quoted form of outPath

		set {ok, dimText} to my verifyImage(outPath)
		if ok is false then error "Capture failed for " & outPath

		if firstDim is "" then
			set firstDim to dimText
		else if dimText is not firstDim then
			set mismatchDimCount to mismatchDimCount + 1
		end if

		set thisHash to do shell script "/sbin/md5 -q " & quoted form of outPath

		if thisHash is prevHash then
			set sameCount to sameCount + 1
		else
			set sameCount to 0
		end if

		if sameCount >= duplicateStopThreshold then
			do shell script "/bin/rm -f " & quoted form of outPath
			exit repeat
		end if

		set prevHash to thisHash
		set savedCount to savedCount + 1

		my nextPage()
		delay minDelayAfterTurn
		my waitForPageChange(prevHash, changeTimeoutSeconds, pollIntervalSeconds, minTotalWaitAfterTurn, stablePollsRequired, postChangeSettleSeconds, probePath)
	end repeat

	do shell script "/bin/rm -f " & quoted form of probePath

	return "Saved images: " & savedCount & " | Output dir: " & outputDir & " | Base dimensions: " & firstDim & " | Dimension mismatches: " & mismatchDimCount
end run

on goToBeginning()
	tell application "System Events"
		tell process "Books"
			set frontmost to true
			key code 115
		end tell
	end tell
end goToBeginning

on nextPage()
	tell application "System Events"
		tell process "Books"
			set frontmost to true
			key code 124
		end tell
	end tell
end nextPage

on getBooksWindowRect()
	tell application "System Events"
		tell process "Books"
			if (count of windows) is 0 then error "No Books window found."
			set win to window 1
			set {xPos, yPos} to position of win
			set {w, h} to size of win
			return {xPos, yPos, w, h}
		end tell
	end tell
end getBooksWindowRect

on waitForPageChange(prevHash, changeTimeoutSeconds, pollIntervalSeconds, minTotalWaitAfterTurn, stablePollsRequired, postChangeSettleSeconds, probePath)
	set t0 to (current date)
	set seenDifferent to false
	set lastProbeHash to ""
	set stableCount to 0

	repeat
		set elapsed to ((current date) - t0)
		if elapsed >= changeTimeoutSeconds then
			delay 0.8
			exit repeat
		end if

		set {xPos, yPos, w, h} to my getBooksWindowRect()
		do shell script "/usr/sbin/screencapture -x -o -t png -R" & xPos & "," & yPos & "," & w & "," & h & " " & quoted form of probePath
		set probeHash to do shell script "/sbin/md5 -q " & quoted form of probePath

		if seenDifferent is false then
			if probeHash is not prevHash then
				set seenDifferent to true
				set lastProbeHash to probeHash
				set stableCount to 1
			end if
		else
			if probeHash is lastProbeHash then
				set stableCount to stableCount + 1
			else
				set lastProbeHash to probeHash
				set stableCount to 1
			end if

			if stableCount >= stablePollsRequired and elapsed >= minTotalWaitAfterTurn then
				delay postChangeSettleSeconds
				exit repeat
			end if
		end if

		delay pollIntervalSeconds
	end repeat
end waitForPageChange

on verifyImage(imgPath)
	try
		set fileSize to do shell script "/usr/bin/stat -f%z " & quoted form of imgPath
		if (fileSize as integer) <= 0 then return {false, "0x0"}

		set dimText to do shell script "/usr/bin/sips -g pixelWidth -g pixelHeight " & quoted form of imgPath & " | /usr/bin/awk '/pixelWidth:/{w=$2} /pixelHeight:/{h=$2} END{if(w>0&&h>0) print w\"x\"h; else print \"0x0\"}'"
		if dimText is "0x0" then return {false, "0x0"}

		return {true, dimText}
	on error
		return {false, "0x0"}
	end try
end verifyImage

on pad3(n)
	set s to "000" & (n as string)
	return text -3 thru -1 of s
end pad3
