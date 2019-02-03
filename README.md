# SBRscraper
Script to scrape SBR's betting-odds. Can be tailored for other sports and other books.
Practical application of this is to accumulate lines of all games (currently for MLB) over time and have yourself an odds database.


Note: you must either have Tor open when running this code or you must comment out that section of code prior to running.
## Tips for using Tor
1) install tor
2) assuming OS is Ubuntu, these instructions worked for getting geckodriver installed: https://askubuntu.com/questions/851401/where-to-find-geckodriver-needed-by-selenium-python-package/863211#863211

# Future TODO's:
* use the new API to parse out info rather than parsing HTML
** sample link is https://www.sportsbookreview.com/ms-odds-v2/odds-v2-service?query=%7B+eventsByDate(+mtid:+83,+providerAcountOpener:+3,+hoursRange:+25,+showEmptyEvents:+true,+marketTypeLayout:+%22PARTICIPANTS%22,+lid:+3,+spid:+3,+ic:+false,+startDate:+1533772800000,+timezoneOffset:+-4,+nof:+true,+hl:+true,+sort:+%7Bby:+[%22lid%22,+%22dt%22,+%22des%22],+order:+ASC%7D+)+%7B+events+%7B+eid+lid+spid+des+dt+es+rid+ic+ven+tvs+cit+cou+st+sta+hl+seid+consensus+%7B+eid+mtid+bb+boid+partid+sbid+paid+lineid+wag+perc+vol+tvol+wb+%7D+plays(pgid:+2,+limitLastSeq:+3)+%7B+eid+sqid+siid+gid+nam+val+tim+%7D+scores+%7B+partid+val+eid+pn+sequence+%7D+participants+%7B+eid+partid+psid+ih+rot+tr+sppil+startingPitcher+%7B+fn+lnam+%7D+source+%7B+...+on+Player+%7B+pid+fn+lnam+%7D+...+on+Team+%7B+tmid+lid+nam+nn+sn+abbr+cit+%7D+...+on+ParticipantGroup+%7B+partgid+nam+lid+participants+%7B+eid+partid+psid+ih+rot+source+%7B+...+on+Player+%7B+pid+fn+lnam+%7D+...+on+Team+%7B+tmid+lid+nam+nn+sn+abbr+cit+%7D+%7D+%7D+%7D+%7D+%7D+marketTypes+%7B+mtid+spid+nam+des+settings+%7B+sitid+did+alias+layout+format+template+sort+url+%7D+%7D+bettingOptions+%7B+boid+nam+mtid+spid+partid+%7D+currentLines+openingLines+eventGroup+%7B+egid+nam+%7D+statistics(sgid:+3)+%7B+val+eid+nam+partid+pid+typ+siid+sequence+%7D+league+%7B+lid+nam+rid+spid+sn+settings+%7B+alias+rotation+ord+shortnamebreakpoint+%7D+%7D+%7D+maxSequences+%7B+events:+eventsMaxSequence+scores:+scoresMaxSequence+currentLines:+linesMaxSequence+statistics:+statisticsMaxSequence+plays:+playsMaxSequence+%7D+%7D+%7D where "1533772800" needs to be replaced with new dates (in epoch time). API labels are not good, but with time can be translated to human readable (sample: of API response https://imgur.com/a/YKmBKyY)
