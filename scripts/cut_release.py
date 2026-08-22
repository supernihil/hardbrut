#!/usr/bin/env python3
"""
Cut a HARDBRUT release. Run from the repo root on every push to main:

  1. Reads the current version from the src/hardbrut.css banner.
  2. Tags HEAD as that version (vX.Y), if not already tagged.
  3. Archives it into index.html's "Previous versions" lists (CSS side:
     hardbrut.css/.min.css, plus .nofont.css/.nofont.min.css if those
     exist at this tag; Android side: Hardbrut.kt) — but only if that
     artifact's content actually changed since the last archived entry,
     so an unrelated doc/CI-only merge doesn't spam a redundant entry
     pointing at byte-identical files.
  4. Bumps the banner to the next version (vX.(Y+1)), rebuilds every CSS
     variant via ./build.sh, and updates every place the version number
     or a download size is displayed: index.html (hero badge, footer,
     download sizes) and README.md.
  5. Commits everything and leaves the new tag ready to push.

Idempotent: safe to re-run (won't double-tag, won't double-archive).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "supernihil/hardbrut"
PREV_VERSIONS_MARKER = '<summary>Previous versions</summary>\n        <div class="stack">'


def run(*args, check=True):
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=True)


def read(path):
    return (ROOT / path).read_text()


def write(path, content):
    (ROOT / path).write_text(content)


def file_bytes_at_tag(tag, path):
    r = run("git", "show", f"{tag}:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


def kb(path):
    size = (ROOT / path).stat().st_size
    return (size + 1023) // 1024


def replace_exactly_one(text, pattern, repl, label):
    new_text, n = re.subn(pattern, repl, text, flags=re.MULTILINE)
    if n != 1:
        sys.exit(f"error: expected exactly 1 match for {label!r}, found {n}")
    return new_text


def find_prev_versions_block(html, start=0):
    """Locate the next 'Previous versions' <div class="stack">...</details> block
    starting the search at `start`. Returns (marker_start, marker_end, block_end)."""
    marker_at = html.find(PREV_VERSIONS_MARKER, start)
    if marker_at == -1:
        sys.exit(f"error: could not find a 'Previous versions' block after offset {start}")
    marker_end = marker_at + len(PREV_VERSIONS_MARKER)
    block_end = html.find("</details>", marker_end)
    return marker_at, marker_end, block_end


def most_recent_archived_version(html, marker_end, block_end):
    block = html[marker_end:block_end]
    versions = [tuple(map(int, v.split("."))) for v in re.findall(r'class="badge">v(\d+\.\d+)<', block)]
    return max(versions) if versions else None


def main():
    css_src = read("src/hardbrut.css")
    m = re.search(r"HARDBRUT v(\d+)\.(\d+)", css_src)
    if not m:
        sys.exit("error: no 'HARDBRUT vX.Y' banner found in src/hardbrut.css")
    major, minor = int(m.group(1)), int(m.group(2))
    current = f"{major}.{minor}"
    next_ver = f"{major}.{minor + 1}"
    tag = f"v{current}"
    print(f"current version: {current}  ->  next: {next_ver}")

    existing_tags = set(run("git", "tag", "-l").stdout.split())
    if tag not in existing_tags:
        run("git", "tag", "-a", tag, "-m", f"HARDBRUT {tag}")
        print(f"tagged {tag}")
    else:
        print(f"{tag} already tagged, skipping (points at whatever commit first reached v{current})")

    html = read("index.html")

    # ---- locate the two "Previous versions" blocks (CSS first, then Android) ----
    _, css_marker_end, css_block_end = find_prev_versions_block(html, 0)
    _, android_marker_end, android_block_end = find_prev_versions_block(html, css_block_end)

    css_last = most_recent_archived_version(html, css_marker_end, css_block_end)
    android_last = most_recent_archived_version(html, android_marker_end, android_block_end)

    def changed_since(last_version, path):
        if last_version is None:
            return True
        last_tag = f"v{last_version[0]}.{last_version[1]}"
        return file_bytes_at_tag(last_tag, path) != file_bytes_at_tag(tag, path)

    already_archived_css = css_last == (major, minor)
    already_archived_android = android_last == (major, minor)
    archive_css = not already_archived_css and changed_since(css_last, "hardbrut.css")
    archive_android = not already_archived_android and changed_since(android_last, "Hardbrut.kt")

    def raw(path):
        return f"https://raw.githubusercontent.com/{REPO}/{tag}/{path}"

    # Android goes first: inserting into it doesn't shift the CSS block's offsets.
    if archive_android:
        entry = (
            f'          <div class="cluster">\n'
            f'            <span class="badge">{tag}</span>\n'
            f'            <a href="{raw("Hardbrut.kt")}" download>Hardbrut.kt</a>\n'
            f'          </div>\n'
        )
        insert_at = android_marker_end + 1
        html = html[:insert_at] + entry + html[insert_at:]
        print(f"archived Android {tag}")
    else:
        print("Hardbrut.kt unchanged (or already archived), skipping")

    if archive_css:
        variants = [("hardbrut.css", "hardbrut.css"), ("hardbrut.min.css", "hardbrut.min.css")]
        if file_bytes_at_tag(tag, "hardbrut.nofont.css") is not None:
            variants.append(("hardbrut.nofont.css", "hardbrut.nofont.css"))
        if file_bytes_at_tag(tag, "hardbrut.nofont.min.css") is not None:
            variants.append(("hardbrut.nofont.min.css", "hardbrut.nofont.min.css"))
        links = "\n            ".join(f'<a href="{raw(path)}" download>{label}</a>' for path, label in variants)
        entry = (
            f'          <div class="cluster">\n'
            f'            <span class="badge">{tag}</span>\n'
            f'            {links}\n'
            f'          </div>\n'
        )
        insert_at = css_marker_end + 1
        html = html[:insert_at] + entry + html[insert_at:]
        print(f"archived CSS {tag} ({len(variants)} variant(s))")
    else:
        print("CSS unchanged (or already archived), skipping")

    # ---- bump version banner, rebuild ----
    css_src = css_src.replace(f"HARDBRUT v{current}", f"HARDBRUT v{next_ver}")
    write("src/hardbrut.css", css_src)
    run("./build.sh")

    sizes = {"css": kb("hardbrut.css"), "min": kb("hardbrut.min.css"), "nofont": kb("hardbrut.nofont.css")}

    # ---- update every current-version reference ----
    html = replace_exactly_one(
        html,
        rf'href="https://github\.com/{re.escape(REPO)}/tree/v{re.escape(current)}" class="badge">v{re.escape(current)}<',
        f'href="https://github.com/{REPO}/tree/v{next_ver}" class="badge">v{next_ver}<',
        "hero badge",
    )
    html = replace_exactly_one(
        html,
        rf'href="https://github\.com/{re.escape(REPO)}/tree/v{re.escape(current)}">v{re.escape(current)}<',
        f'href="https://github.com/{REPO}/tree/v{next_ver}">v{next_ver}<',
        "footer badge",
    )
    html = re.sub(r"hardbrut\.css \(\d+KB, with font\)", f'hardbrut.css ({sizes["css"]}KB, with font)', html)
    html = re.sub(r"hardbrut\.min\.css \(\d+KB, minified\)", f'hardbrut.min.css ({sizes["min"]}KB, minified)', html)
    html = re.sub(r"hardbrut\.nofont\.css \(\d+KB\)", f'hardbrut.nofont.css ({sizes["nofont"]}KB)', html)
    write("index.html", html)

    readme = read("README.md")
    readme = re.sub(r"Current version: \*\*v[\d.]+\*\*", f"Current version: **v{next_ver}**", readme)
    write("README.md", readme)

    # ---- commit ----
    run("git", "add", "-A")
    diff = run("git", "diff", "--cached", "--stat", check=False)
    if not diff.stdout.strip():
        print("nothing to commit")
        return
    run("git", "commit", "-m", f"Release v{current}, bump to v{next_ver}\n\nAutomated by scripts/cut_release.py.")
    print(f"committed bump to v{next_ver}")


if __name__ == "__main__":
    main()
