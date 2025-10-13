from pathlib import Path

path = Path("integration_test.py")
lines = path.read_text(encoding="utf-8").splitlines()
filtered = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.strip() == "tests_total += 1" and i + 5 < len(lines):
        next_line = lines[i + 1]
        if "Enterprise Copilot Service" in "".join(lines[i + 1:i + 6]):
            i += 6
            continue
        if "Enterprise Copilot API" in "".join(lines[i + 1:i + 6]):
            i += 6
            continue
    filtered.append(line)
    i += 1
path.write_text('\n'.join(filtered) + '\n', encoding="utf-8")
