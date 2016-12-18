# macOS Parsers
Scripts that parse macOS data objects
* yk_alias.py - Alias v2 and Alias v3 data
* yk_bmdata.py - Bookmark data
* yk_ipp.py - Internet Printing Protocol files

# Installation
Requires Python > 2.7 or > 3.4

# Usage
`python yk_alias.py TestFiles/alias/alias_s1`

`python yk_bmdata.py TestFiles/bookmark/bm_s1`

`python yk_ipp.py TestFiles/ipp/ipp_s1`

Or Import as library and call `parse(<data object>)`
