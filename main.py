import re

content = []
rules = []


class Content:

    def __init__(self, name):
        self.name = name
        self.tags = []


class Rule:

    def __init__(self, regexes, tag_output_template):
        self.regexes = regexes
        self.tag_output_template = tag_output_template

    def apply(self, content):
        print("Applying rule to %s" % content.name)
        matches = []
        for ind, regex_set in enumerate(self.regexes):
            for regex in regex_set:
                print("applying %s on %s" % (regex, matches))
                if ind == 0:
                    cur_matches = list(re.finditer(regex, content.name, re.IGNORECASE))
                else:
                    cur_matches = list(re.finditer(regex, matches[0], re.IGNORECASE))

                if cur_matches:
                    groups = cur_matches[0].groups()
                    if not groups:
                        match = cur_matches[0].group()
                    else:
                        match = cur_matches[0].groups()[0]
                    matches = [match]

            if not matches:
                break

        if matches:
            self.generate_tags(content, matches)

    def generate_tags(self, content, matches):
        content.tags.append(self.tag_output_template % int(matches[0]))


content.append(Content("Torrent.Name.S02E01.Something.PROPER.HDTV.x264.mkv"))

# Create a rule that generates a season tag
season_regexes = [[
    '\\ss?(\\d{1,2})\\s\\-\\s\\d{1,2}\\s',
    '\\b(?:Complete[\\.\\s\\-\\+_\\/(),]*)?[\\.\\s\\-\\+_\\/(),]*(?:s(?:easons?)?)[\\.\\s\\-\\+_\\/(),]*(?:s?[0-9]{1,2}[\\s]*(?:(?:\\-|(?:\\s*to\\s*))[\\s]*s?[0-9]{1,2})+)(?:[\\.\\s\\-\\+_\\/(),]*Complete)?\\b',
    '(?:s\\d{1,2}[.+\\s]*){2,}\\b',
    '\\b(?:Complete[\\.\\s\\-\\+_\\/(),])?s([0-9]{1,2})(?:(?<![a-z])(?:e|ep)(?:[0-9]{1,2}(?:-?(?:e|ep)?(?:[0-9]{1,2}))?)(?![0-9])|\\s\\-\\s\\d{1,3}\\s|\\b[0-9]{1,2}x([0-9]{2})\\b|\\bepisod(?:e|io)[\\.\\s\\-\\+_\\/(),]\\d{1,2}\\b)?\\b',
    '\\b([0-9]{1,2})x[0-9]{2}\\b', '[0-9]{1,2}(?:st|nd|rd|th)[\\.\\s\\-\\+_\\/(),]season',
    'Series[\\.\\s\\-\\+_\\/(),]\\d{1,2}',
    '\\b(?:Complete[\\.\\s\\-\\+_\\/(),])?Season[\\. -][0-9]{1,2}\\b'], [
    r"[0-9]+"
]]
rules.append(Rule(season_regexes, "Season %s"))

episode_regexes = [[
    "(?<![a-z])(?:e|ep)(?:[0-9]{1,2}(?:-?(?:e|ep)?(?:[0-9]{1,2}))?)(?![0-9])",
    "\s\-\s\d{1,3}\s",
    r"\b[0-9]{1,2}x([0-9]{2})\b",
    r"\bepisod(?:e|io)[\.\s\-\+_\/(),]\d{1,2}\b"], [
    r"[0-9]+"
]]
rules.append(Rule(episode_regexes, "Episode %s"))

for content in content:
    for rule in rules:
        rule.apply(content)

    print("Tags: %s" % content.tags)
