#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 组件获取脚本
从开发流程规则仓库的 components/ 目录复制 UI 组件到目标项目。
读取 components/manifest.json 组件清单，按组件名、类型或全部复制到目标项目。

用法:
  python fetch-ui-component.py --list
  python fetch-ui-component.py --name fly-arrow-button --dest D:/MyProject/src/components
  python fetch-ui-component.py --category buttons --dest D:/MyProject/src/components
  python fetch-ui-component.py --all --dest D:/MyProject/src/components
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ANSI 颜色码（Windows 10+ 支持）
CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
DARK_YELLOW = '\033[90m'
WHITE = '\033[97m'
RESET = '\033[0m'


def enable_color():
    """Windows 下启用 ANSI 颜色支持"""
    if sys.platform == 'win32':
        os.system('')


def locate_components():
    """定位组件目录与清单文件"""
    script_dir = Path(__file__).resolve().parent
    components_dir = (script_dir / '..' / 'components').resolve()
    manifest_path = components_dir / 'manifest.json'
    if not manifest_path.exists():
        print(f'错误: 找不到组件清单文件: {manifest_path}', file=sys.stderr)
        sys.exit(1)
    return components_dir, manifest_path


def load_manifest(manifest_path):
    """读取清单并返回扁平组件列表"""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    all_components = []
    for cat in manifest.get('categories', []):
        for comp in cat.get('components', []):
            all_components.append({
                'name': comp['name'],
                'title': comp['title'],
                'author': comp['author'],
                'category': cat['name'],
                'cat_label': cat['label'],
                'file': comp['file'],
                'deps': ', '.join(comp.get('dependencies', [])),
                'views': comp.get('views', ''),
                'description': comp.get('description', ''),
            })
    return manifest, all_components


def show_list(manifest, all_components):
    """模式 1：列表展示所有组件"""
    print()
    print(f'{CYAN}可用 UI 组件清单（来源: {manifest.get("source", "uiverse.io")} / {manifest.get("license", "MIT")} License）{RESET}')
    print(f'共 {len(all_components)} 个组件，{len(manifest["categories"])} 个分类')
    print()

    for cat in manifest['categories']:
        print(f'{YELLOW}[{cat["label"]}]{RESET}')
        for c in [x for x in all_components if x['category'] == cat['name']]:
            dep_tag = f' [依赖: {c["deps"]}]' if c['deps'] else ''
            name_padded = c['name'].ljust(24)
            title_padded = c['title'].ljust(24)
            views_padded = c['views'].rjust(8)
            print(f'  {WHITE}{name_padded} {title_padded} {views_padded} views{dep_tag}{RESET}')
        print()

    print(f'{GREEN}用法:{RESET}')
    print('  复制单个: python fetch-ui-component.py --name <组件名> --dest <目标目录>')
    print('  复制分类: python fetch-ui-component.py --category <类型> --dest <目标目录>')
    print('  复制全部: python fetch-ui-component.py --all --dest <目标目录>')
    print()


def select_components(all_components, name=None, category=None, all_flag=False):
    """根据参数筛选要复制的组件"""
    if all_flag:
        return all_components
    if category:
        selected = [c for c in all_components if c['category'] == category.lower()]
        if not selected:
            available = ', '.join(set(c['category'] for c in all_components))
            print(f'错误: 未找到类型 "{category}"。可用类型: {available}', file=sys.stderr)
            sys.exit(1)
        return selected
    if name:
        selected = [c for c in all_components if c['name'] == name.lower()]
        if not selected:
            print(f'错误: 未找到组件 "{name}"。使用 --list 查看可用组件。', file=sys.stderr)
            sys.exit(1)
        return selected
    return []


def copy_components(selected, components_dir, dest):
    """执行复制操作"""
    dest_path = Path(dest).resolve()
    dest_path.mkdir(parents=True, exist_ok=True)

    print()
    print(f'{CYAN}正在复制 {len(selected)} 个组件到: {dest_path}{RESET}')
    print()

    copied = 0
    deps_warn = []

    for comp in selected:
        src_file = components_dir / comp['file']
        rel_dir = os.path.dirname(comp['file'])
        dst_dir = dest_path / rel_dir
        dst_file = dst_dir / os.path.basename(comp['file'])

        if not src_file.exists():
            print(f'  警告: 源文件缺失，跳过: {comp["file"]}', file=sys.stderr)
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_file), str(dst_file))
        copied += 1

        dep_tag = f' [依赖: {comp["deps"]}]' if comp['deps'] else ''
        rel_path = os.path.join(rel_dir, os.path.basename(comp['file']))
        print(f'  {GREEN}[OK]{RESET} {comp["name"]} -> {rel_path}{dep_tag}')

        if comp['deps']:
            deps_warn.append(comp)

    print()
    print(f'{CYAN}完成: 已复制 {copied}/{len(selected)} 个组件{RESET}')

    # 依赖提示
    if deps_warn:
        print()
        print(f'{YELLOW}依赖提示:{RESET}')
        for d in deps_warn:
            print(f'  {YELLOW}{d["name"]} 需要: {d["deps"]}{RESET}')
            print(f'  {DARK_YELLOW}  请确保目标项目已引入对应依赖（CDN 或 npm 安装）{RESET}')

    # 使用提示
    print()
    print(f'{GREEN}使用方式:{RESET}')
    print('  1. 直接在 HTML 中引用: <iframe src="components/buttons/xxx.html"></iframe>')
    print('  2. 或提取 CSS/HTML 片段嵌入页面（注意作用域隔离）')
    print('  3. 展示页参考: uiverse-components.html（iframe 网格布局）')
    print()


def main():
    enable_color()
    components_dir, manifest_path = locate_components()
    manifest, all_components = load_manifest(manifest_path)

    parser = argparse.ArgumentParser(
        description='从开发流程规则仓库复制 UI 组件到目标项目',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python fetch-ui-component.py --list
  python fetch-ui-component.py --name fly-arrow-button --dest D:/MyProject/src/components
  python fetch-ui-component.py --category buttons --dest D:/MyProject/src/components
  python fetch-ui-component.py --all --dest D:/MyProject/src/components
'''
    )
    parser.add_argument('--name', help='按组件名复制单个组件')
    parser.add_argument('--category', help='按类型复制整类组件')
    parser.add_argument('--dest', help='目标目录路径')
    parser.add_argument('--all', action='store_true', help='复制全部组件')
    parser.add_argument('--list', action='store_true', help='列出所有可用组件')

    args = parser.parse_args()

    # 列表模式
    if args.list or (not args.name and not args.category and not args.all):
        show_list(manifest, all_components)
        return

    # 校验目标目录
    if not args.dest:
        print('错误: 必须指定目标目录: --dest <路径>', file=sys.stderr)
        sys.exit(1)

    selected = select_components(all_components, name=args.name, category=args.category, all_flag=args.all)
    copy_components(selected, components_dir, args.dest)


if __name__ == '__main__':
    main()
