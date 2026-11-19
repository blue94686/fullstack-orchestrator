#!/usr/bin/env python3
"""Create the root-relative shared exchange folders for one active project.

This helper only creates the project-local exchange structure. It does not
copy source code, grant application permissions, start a service, or replace
an existing README.
"""
import argparse
import json
from pathlib import Path


DIRECTORIES = (
    "inputs",
    "contracts",
    "tasks",
    "artifacts/stitch",
    "artifacts/gemini",
    "artifacts/codex",
    "acceptance",
)

README = """# 软件公共文件交换目录

这是当前项目实例的交换目录。Codex Main 发布输入、契约和验收记录；外部执行者只写分配的任务产物目录。目录存在不代表软件已获得访问授权。

Codex 与 Gemini 已使用同一获准工作根时直接复用，核对产品相对位置与实际输入访问；不要为每个 task/attempt 重选目录。产物子目录不是必须选中的软件工作目录。仅在访问缺失、目录指错或确需隔离时调整；目录约定不构成系统沙箱。

每个任务使用 `inputs/<task-id>/<revision>/`、`contracts/<contract-id>/<revision>/`、`tasks/<task-id>/<attempt-id>/` 和对应的 `artifacts/`、`acceptance/` 子目录。长任务优先复用项目原生索引；没有等效记录时由 Main 在 `tasks/<task-id>/INDEX.md` 记录当前尝试、状态观察时间、候选/契约身份、已接受产物与哈希、被替代原因和下一步。索引不证明运行状态，不自动清理历史。保留输入哈希、任务定位、实际返回文件和独立验收；不要放入令牌、Cookie、密钥或无关私人数据。

需要持久交接时优先复用项目原生记录，无等效格式才使用协调 Skill 的任务模板。调用辅助脚本使用本次实际加载的 Skill 位置，不假定 Skill 已复制到本产品根目录。既有 README 保持项目所有，不由初始化器覆盖。
"""


def initialize(project_root: Path) -> dict:
    root = project_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"project root must be an existing directory: {root}")
    # Refuse a dangerous filesystem root while allowing ordinary project paths.
    if root.parent == root:
        raise ValueError("refusing to create a shared exchange at filesystem root")
    shared = root / "shared"
    # Preflight all managed paths before creating anything. Do not follow
    # existing links, including dangling links, into another location.
    managed_directories = [shared, shared / "artifacts"]
    managed_directories.extend(shared / relative for relative in DIRECTORIES)
    readme = shared / "README.md"
    for path in [*managed_directories, readme]:
        if path.is_symlink():
            raise ValueError(f"refusing linked exchange path: {path}")
        if path.exists():
            valid = path.is_file() if path == readme else path.is_dir()
            if not valid:
                raise ValueError(f"unexpected file type at exchange path: {path}")
    created = []
    for relative in DIRECTORIES:
        directory = shared / relative
        if not directory.exists():
            try:
                directory.mkdir(parents=True)
            except FileExistsError:
                # Another legitimate initializer may have created this path
                # since preflight. Reuse only a real directory.
                if directory.is_symlink() or not directory.is_dir():
                    raise ValueError(f"unexpected exchange path after creation: {directory}")
            else:
                created.append(relative)
        elif not directory.is_dir():
            raise ValueError(f"expected directory but found a file: {directory}")
    readme_created = False
    if not readme.exists():
        try:
            with readme.open("x", encoding="utf-8") as handle:
                handle.write(README)
        except FileExistsError:
            if readme.is_symlink() or not readme.is_file():
                raise ValueError(f"unexpected README path after creation: {readme}")
        else:
            readme_created = True
    elif not readme.is_file():
        raise ValueError(f"expected README file but found a directory: {readme}")
    return {
        "result": "CREATED_OR_REUSED",
        "project_root": str(root),
        "shared_root": str(shared),
        "created_directories": created,
        "readme_created": readme_created,
        "existing_content_preserved": not readme_created,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path,
                        help="explicit active product root resolved by Main; never inferred from shell cwd")
    args = parser.parse_args()
    try:
        result = initialize(args.project_root)
    except (OSError, ValueError) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
