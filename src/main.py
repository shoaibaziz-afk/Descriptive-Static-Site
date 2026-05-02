from textnode import TextNode, TextType
from htmlnode import ParentNode, LeafNode
import re
import os
import shutil
import sys


def copy_static_to_public(source_dir, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)

    for item in os.listdir(source_dir):
        src_path = os.path.join(source_dir, item)
        dst_path = os.path.join(dest_dir, item)

        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
        else:
            shutil.copytree(src_path, dst_path)


def extract_title(markdown):
    pattern = r"^#\s+(.+)$"
    match = re.search(pattern, markdown, re.MULTILINE)
    if not match:
        raise ValueError("No h1 header found")
    return match.group(1).strip()


def _apply_inline(text: str) -> str:
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
    return text


def markdown_to_html_node(markdown):
    lines = markdown.split("\n")
    html_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code_block:
                html_lines.append("<code>")
                in_code_block = True
            else:
                html_lines.append("</code>")
                in_code_block = False
            continue

        if in_code_block:
            html_lines.append(stripped)
            continue

        if stripped.startswith("# "):
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
            continue

        if stripped.startswith("## "):
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
            continue

        if stripped.startswith(">"):
            html_lines.append(f"<blockquote>{stripped[1:].strip()}</blockquote>")
            continue

        if stripped.startswith("- "):
            html_lines.append(f"<li>{_apply_inline(stripped[2:])}</li>")
            continue

        if re.match(r"\d+\.\s", stripped):
            html_lines.append(f"<li>{_apply_inline(stripped.split('.', 1)[1].strip())}</li>")
            continue

        if stripped:
            html_lines.append(f"<p>{_apply_inline(stripped)}</p>")

    html = "\n".join(html_lines)
    return ParentNode("div", [LeafNode(None, html)])


def generate_page(from_path, template_path, dest_path, basepath):
    print(f"Generating page from {from_path} to {dest_path}")

    with open(from_path, "r", encoding="utf-8") as f:
        markdown = f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    html_node = markdown_to_html_node(markdown)
    content = html_node.to_html()
    title = extract_title(markdown)

    result = template.replace("{{ Title }}", title)\
                     .replace("{{ Content }}", content)

    # 🔥 IMPORTANT: fix paths for GitHub Pages
    result = result.replace('href="/', f'href="{basepath}')
    result = result.replace('src="/', f'src="{basepath}')

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(result)


def generate_pages_recursive(dir_path_content, template_path, dest_dir_path, basepath):
    for item in os.listdir(dir_path_content):
        src_path = os.path.join(dir_path_content, item)
        dest_path = os.path.join(dest_dir_path, item)

        if os.path.isfile(src_path):
            if src_path.endswith(".md"):
                html_path = dest_path.replace(".md", ".html")
                generate_page(src_path, template_path, html_path, basepath)
        else:
            os.makedirs(dest_path, exist_ok=True)
            generate_pages_recursive(src_path, template_path, dest_path, basepath)


def main():
    # default basepath for local dev
    basepath = "/"

    if len(sys.argv) > 1:
        basepath = sys.argv[1]

    # 🔥 GitHub Pages uses /docs
    output_dir = "docs"

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    copy_static_to_public("static", output_dir)

    generate_pages_recursive(
        "content",
        "template.html",
        output_dir,
        basepath
    )


if __name__ == "__main__":
    main()