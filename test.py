# the following functions are used to parse entries such as 192.168.[1-5,6,7].[8-9]
# 检查括号
def _check_bracket(entry):
    in_bracket = False
    for c in entry:
        if c == '[' and in_bracket:
            return False
        if c == '[':
            in_bracket = True
        elif c == ']' and not in_bracket:
            return False
        elif c == ']':
            in_bracket = False
    return not in_bracket


# 根据逗号分隔
def _split_by_comma(entry):
    result = []
    left = 0
    in_bracket = False
    for i, c in enumerate(entry):
        if c == '[':
            in_bracket = True
        elif c == ']':
            in_bracket = False
        elif c == ',' and not in_bracket:
            result.append(entry[left:i])
            left = i + 1
    result.append(entry[left:])
    return result


# 序列
class _Sequence:
    def __init__(self, start, end, base_len, stride=1):
        self.start = start
        self.end = end
        self.base_len = base_len
        self.stride = stride


# 模式
class _Pattern:
    def __init__(self, seqs, begin, end):
        self.seqs = seqs
        self.begin = begin
        self.end = end


# 转换模式
def _convert_pattern(matched):
    if matched is None:
        return None
    groups = matched.groups()
    start = int(groups[0])
    end = start if groups[1] is None else int(groups[1])
    base_len = len(groups[0])
    len0 = len(groups[0])
    len1 = len(groups[1]) if groups[1] else None
    if groups[1] and (len0 > len1 or (len0 < len1 and groups[1][0] == '0')):
        raise ValueError("invalid pattern")
    if start > end:
        raise ValueError("{} is larger than {} in pattern".format(start, end))
    return _Sequence(start, end, base_len)


# 解析模式
def _parse_pattern(pattern, begin, end):
    whole_re = re.compile(r'^(([0-9]+)(?:-([0-9]+))?,)*([0-9]+)(?:-([0-9]+))?$')
    if whole_re.match(pattern) is None:
        raise ValueError("{} is not valid pattern".format(pattern))
    r = re.compile(r',?([0-9]+)(?:-([0-9]+))?')
    seqs = [_convert_pattern(i) for i in r.finditer(pattern)]
    return _Pattern(seqs, begin, end)


# 生成啥？
def _generate(patterns, entry, prefix, entry_offset):
    pattern = patterns[0]
    result = []
    prefix += entry[entry_offset:patterns[0].begin]
    if len(patterns) == 1:
        for seq in pattern.seqs:
            for i in range(seq.start, seq.end + 1, seq.stride):
                s = "{}{:0{w}}{}".format(prefix, i, entry[pattern.end:], w=seq.base_len)
                result.append(s)
    else:
        for seq in pattern.seqs:
            for i in range(seq.start, seq.end + 1, seq.stride):
                s = "{}{:0{w}}".format(prefix, i, w=seq.base_len)
                result.extend(_generate(patterns[1:], entry, s, pattern.end))
    return result


# 解析 段 条目
def _parse_segment_entry(entry):
    entry = "".join(entry.split())
    if not _check_bracket(entry):
        return []
    r = re.compile(r'\[([^\]]*)\]')
    result = []
    entries = _split_by_comma(entry)
    for entry in entries:
        all_match = r.finditer(entry)
        try:
            patterns = [_parse_pattern(matched.groups()[0], matched.start(), matched.end())
                        for matched in all_match]
        except ValueError:
            return []
        if len(patterns) == 0 and len(entry) != 0:
            result.append(entry)
        else:
            result.extend(_generate(patterns, entry, "", 0))
    return result
