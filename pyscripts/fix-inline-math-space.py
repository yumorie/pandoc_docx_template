from pathlib import Path
import re
import sys


# 匹配单行内的 $...$
# 避开 $$...$$ 和转义的 \$
INLINE_MATH = re.compile(
    r'(?<!\\)(?<!\$)\$(?!\$)(.*?)(?<!\\)(?<!\$)\$(?!\$)'
)


def read_text(path: Path) -> str:
    data = path.read_bytes()

    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass

    raise UnicodeDecodeError("unknown", data, 0, 1, "无法识别文件编码")


def split_inline_code(line: str):
    """
    将一行拆成普通文本和行内代码片段。
    返回列表：
    [
        (False, "普通文本"),
        (True, "`代码`"),
        ...
    ]

    这样可以避免误处理 `...` 里的 $...$。
    """
    result = []
    i = 0
    n = len(line)

    while i < n:
        if line[i] != "`":
            start = i
            while i < n and line[i] != "`":
                i += 1
            result.append((False, line[start:i]))
            continue

        # 遇到反引号，统计连续反引号数量
        start = i
        while i < n and line[i] == "`":
            i += 1

        tick_count = i - start
        ticks = "`" * tick_count

        # 查找对应的结束反引号
        end = line.find(ticks, i)

        if end == -1:
            # 没找到结束，剩余部分按普通文本处理
            result.append((False, line[start:]))
            break

        # 包含结束反引号
        code_part = line[start:end + tick_count]
        result.append((True, code_part))
        i = end + tick_count

    return result


def fix_math_segment(text: str) -> str:
    """
    修复普通文本片段中的 $...$：
    - 去掉开头 $ 后面的空格或 tab
    - 去掉结尾 $ 前面的空格或 tab
    """

    def repl(match):
        inner = match.group(1)
        return "$" + inner.strip(" \t") + "$"

    return INLINE_MATH.sub(repl, text)


def fix_line(line: str) -> str:
    parts = split_inline_code(line)
    fixed_parts = []

    for is_code, part in parts:
        if is_code:
            fixed_parts.append(part)
        else:
            fixed_parts.append(fix_math_segment(part))

    return "".join(fixed_parts)


def fix_markdown(text: str) -> str:
    lines = text.splitlines(keepends=True)
    new_lines = []

    in_code_block = False

    for line in lines:
        stripped = line.lstrip()

        # 跳过 fenced code block，避免误伤 ```...``` 或 ~~~...~~~
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue

        if in_code_block:
            new_lines.append(line)
        else:
            new_lines.append(fix_line(line))

    return "".join(new_lines)


def main():
    if len(sys.argv) != 3:
        print("用法: python fix-inline-math-space.py input.md output.md", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = read_text(input_path)
    fixed = fix_markdown(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        f.write(fixed)

    print(f"已完成 Markdown 预处理: {output_path}")


if __name__ == "__main__":
    main()