# macOS Parsers
__Notice__: _yk_bmdata.py and yk_alias.py will no longer be maintained. Please use alternatives such as 
[plistutils](https://github.com/strozfriedberg/plistutils) instead._

Scripts that parse macOS data objects
* yk_ipp.py - Internet Printing Protocol files
* ~~yk_alias.py - Alias v2 and Alias v3 data~~
* ~~yk_bmdata.py - Bookmark data~~

# Installation
Requires Python > 2.7 or > 3.4

# Usage
`python yk_ipp.py TestFiles/ipp/ipp_s1`

`python yk_alias.py TestFiles/alias/alias_s1`

`python yk_bmdata.py TestFiles/bookmark/bm_s1`

Or Import as library and call `parse(<data object>)`
