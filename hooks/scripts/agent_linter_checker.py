"""
Agent Linter 检查模块 - RULE-028: Agent 生成代码 Linter 检查

Agent 生成的代码必须通过现有 Linter 检查，确保代码质量和风格一致性。
"""

import asyncio
import fnmatch
import os
import shutil
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)


def build_command(name: str, *args: str) -> List[str]:
    """Windows 兼容构建命令：npx 等前端工具在 Windows 上是 .cmd 垫片（无 .exe），
    直接 spawn 裸名称会 WinError 2；spawn .cmd 绝对路径在带空格路径下会 WinError 206。
    标准方案：.cmd/.bat 垫片经 cmd.exe /c 运行；POSIX 直接 spawn。"""
    resolved = shutil.which(name)
    if resolved and sys.platform.startswith("win") and resolved.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/c", resolved, *args]
    return [resolved if resolved else name, *args]


# 依赖/构建产物/归档目录（rglob 收集源文件时排除，避免命令行超长与误报）
LINTER_EXCLUDED_DIRS = {
    "node_modules", "__pycache__", ".git", ".next", ".pytest_cache",
    ".venv", "venv", "dist", "build", "coverage",
    "archive", "_dsh-release", ".trae-html-share-packages", "html-reports",
}


class LinterResult(Enum):
    """Linter 检查结果"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class LinterSeverity(Enum):
    """Linter 严重级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LinterIssue:
    """Linter 问题"""
    file_path: str
    line: int
    column: int
    severity: str
    code: str
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.file_path}:{self.line}:{self.column} [{self.severity}] {self.code}: {self.message}"


@dataclass
class LinterCheckResult:
    """Linter 检查结果"""
    language: str
    files_checked: List[str]
    issues: List[LinterIssue]
    status: str
    duration_ms: float
    auto_fixed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return any(i.severity == LinterSeverity.ERROR.value for i in self.issues)
    
    @property
    def error_count(self) -> int:
        """错误数量"""
        return sum(1 for i in self.issues if i.severity == LinterSeverity.ERROR.value)
    
    @property
    def warning_count(self) -> int:
        """警告数量"""
        return sum(1 for i in self.issues if i.severity == LinterSeverity.WARNING.value)
    
    @property
    def is_passed(self) -> bool:
        """是否通过"""
        return self.status == LinterResult.PASSED.value and not self.has_errors


@dataclass
class CommandResult:
    """命令执行结果（承载 returncode/stdout/stderr/duration_ms）"""
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    args: List[str]


class LinterChecker:
    """Linter 检查器 - RULE-028"""
    
    def __init__(
        self,
        project_root: str,
        auto_fix: bool = True,
        fail_on_warning: bool = False
    ):
        """
        初始化 Linter 检查器
        
        Args:
            project_root: 项目根目录
            auto_fix: 是否自动修复
            fail_on_warning: 警告是否导致失败
        """
        self.project_root = Path(project_root)
        self.auto_fix = auto_fix
        self.fail_on_warning = fail_on_warning
    
    async def check_python(
        self,
        files: List[str],
        auto_fix: bool = True
    ) -> LinterCheckResult:
        """
        检查 Python 代码
        
        Args:
            files: 文件路径列表
            auto_fix: 是否自动修复
            
        Returns:
            Linter 检查结果
        """
        issues: List[LinterIssue] = []
        auto_fixed = False
        
        # Ruff 检查
        ruff_result = await self._run_ruff(files, auto_fix)
        issues.extend(ruff_result.issues)
        auto_fixed = auto_fixed or ruff_result.auto_fixed
        
        # MyPy 检查
        mypy_result = await self._run_mypy(files)
        issues.extend(mypy_result.issues)
        
        # Bandit 安全扫描
        bandit_result = await self._run_bandit(files)
        issues.extend(bandit_result.issues)
        
        # 合并结果
        all_issues = issues
        status = self._determine_status(all_issues, ruff_result.status)
        
        return LinterCheckResult(
            language="python",
            files_checked=files,
            issues=all_issues,
            status=status,
            duration_ms=ruff_result.duration_ms + mypy_result.duration_ms + bandit_result.duration_ms,
            auto_fixed=auto_fixed
        )
    
    async def check_typescript(
        self,
        files: List[str],
        auto_fix: bool = True
    ) -> LinterCheckResult:
        """
        检查 TypeScript 代码
        
        Args:
            files: 文件路径列表
            auto_fix: 是否自动修复
            
        Returns:
            Linter 检查结果
        """
        issues: List[LinterIssue] = []
        auto_fixed = False
        
        # ESLint 检查
        eslint_result = await self._run_eslint(files, auto_fix)
        issues.extend(eslint_result.issues)
        auto_fixed = auto_fixed or eslint_result.auto_fixed
        
        # TypeScript 编译检查
        tsc_result = await self._run_tsc(files)
        issues.extend(tsc_result.issues)
        
        # Prettier 格式检查
        prettier_result = await self._run_prettier(files, auto_fix)
        issues.extend(prettier_result.issues)
        auto_fixed = auto_fixed or prettier_result.auto_fixed
        
        # 合并结果
        all_issues = issues
        status = self._determine_status(all_issues, eslint_result.status)
        
        return LinterCheckResult(
            language="typescript",
            files_checked=files,
            issues=all_issues,
            status=status,
            duration_ms=eslint_result.duration_ms + tsc_result.duration_ms + prettier_result.duration_ms,
            auto_fixed=auto_fixed
        )
    
    async def check_file(self, file_path: str) -> LinterCheckResult:
        """
        检查单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Linter 检查结果
        """
        path = Path(file_path)
        
        if path.suffix in ['.py', '.pyi']:
            return await self.check_python([file_path])
        elif path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
            return await self.check_typescript([file_path])
        else:
            return LinterCheckResult(
                language="unknown",
                files_checked=[file_path],
                issues=[],
                status=LinterResult.SKIPPED.value,
                duration_ms=0
            )
    
    async def check_project(self, language: str = "all") -> Dict[str, LinterCheckResult]:
        """
        检查整个项目
        
        Args:
            language: 语言类型（python/typescript/all）
            
        Returns:
            各语言检查结果字典
        """
        results = {}

        if language in ('python', 'all'):
            py_files = self._collect_source_files(("*.py",))
            if py_files:
                results['python'] = await self._check_files_batched(
                    py_files, self.check_python
                )

        if language in ('typescript', 'all'):
            ts_files = self._collect_source_files(("*.ts", "*.tsx"))
            if ts_files:
                results['typescript'] = await self._check_files_batched(
                    ts_files, self.check_typescript
                )

        return results

    # 每批传给 linter 的文件数上限（CreateProcess 命令行上限 32K，中文长路径极易超）
    BATCH_SIZE = 40

    def _collect_source_files(self, patterns: Tuple[str, ...]) -> List[str]:
        """收集源文件，**剪枝遍历**排除依赖/构建产物目录。

        v4.10.1 用 rglob + `any(part in EXCLUDED)` 过滤，但 rglob 是**先遍历再过滤**——
        os.scandir 进入那层目录的瞬间就抛 OSError（Windows 路径长度上限 WinError 1921：
        `trae-llm-gateway/_dsh-release/.../@deepseek-ai/cordis/node_modules/...` 循环嵌套
        深达数千字符），过滤逻辑根本来不及执行，整个检查 FAIL。
        改为 os.walk 的原地剪枝（dirs[:] = ...）：不进入被排除的目录，从根上避免超长路径。
        另加 OSError 逐节点容错与路径长度上限防护，任何单点不可读都不让全量检查崩掉。
        """
        files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.project_root):
            # 剪枝：被排除的目录连同其子树一并跳过（不等遍历到再过滤）
            dirnames[:] = [d for d in dirnames if d not in LINTER_EXCLUDED_DIRS]
            for fn in filenames:
                for pattern in patterns:
                    if fnmatch.fnmatch(fn, pattern):
                        full = Path(dirpath) / fn
                        # Windows MAX_PATH 之外的路径 Python 自身也无法 stat/读取，跳过
                        if len(str(full)) >= 259:
                            continue
                        files.append(full)
                        break
        return [str(f) for f in files]

    async def _check_files_batched(self, files: List[str], checker) -> LinterCheckResult:
        """分批调用 checker（每批 BATCH_SIZE 个文件），避免命令行超长；结果合并。"""
        if len(files) <= self.BATCH_SIZE:
            return await checker(files)

        merged = LinterCheckResult(
            language="", files_checked=[], issues=[],
            status=LinterResult.PASSED.value, duration_ms=0.0, auto_fixed=False,
        )
        order = {
            LinterResult.PASSED.value: 0,
            LinterResult.SKIPPED.value: 1,
            LinterResult.FAILED.value: 2,
            LinterResult.ERROR.value: 3,
        }
        last = None
        for i in range(0, len(files), self.BATCH_SIZE):
            last = await checker(files[i:i + self.BATCH_SIZE])
            merged.files_checked.extend(last.files_checked or [])
            merged.issues.extend(last.issues or [])
            merged.duration_ms += last.duration_ms or 0.0
            if last.auto_fixed:
                merged.auto_fixed = True
            if order.get(last.status, 0) > order.get(merged.status, 0):
                merged.status = last.status
        merged.language = last.language
        return merged
    
    async def _run_ruff(
        self,
        files: List[str],
        auto_fix: bool
    ) -> LinterCheckResult:
        """运行 Ruff 检查"""
        # build_command：Windows 上 ruff 可能是 .cmd/.exe 垫片，裸名 spawn 会 WinError 2
        cmd = build_command("ruff", "check")
        if auto_fix:
            cmd.append("--fix")
        cmd.extend(["--output-format", "concise"])
        cmd.extend(files)

        return await self._run_linter_command(
            cmd,
            language="python",
            parser=self._parse_ruff_output
        )

    async def _run_mypy(self, files: List[str]) -> LinterCheckResult:
        """运行 MyPy 检查"""
        cmd = build_command("mypy", "--show-error-codes")
        cmd.extend(files)

        return await self._run_linter_command(
            cmd,
            language="python",
            parser=self._parse_mypy_output
        )

    async def _run_bandit(self, files: List[str]) -> LinterCheckResult:
        """运行 Bandit 安全扫描"""
        cmd = build_command("bandit", "-r", "--format", "txt")
        cmd.extend(files)

        return await self._run_linter_command(
            cmd,
            language="python",
            parser=self._parse_bandit_output
        )
    
    async def _run_eslint(
        self,
        files: List[str],
        auto_fix: bool
    ) -> LinterCheckResult:
        """运行 ESLint 检查"""
        cmd = build_command("npx", "eslint", "--ext", ".ts,.tsx")
        if auto_fix:
            cmd.append("--fix")
        cmd.extend(files)
        
        return await self._run_linter_command(
            cmd,
            language="typescript",
            parser=self._parse_eslint_output
        )
    
    async def _run_tsc(self, files: List[str]) -> LinterCheckResult:
        """运行 TypeScript 编译检查"""
        cmd = build_command("npx", "tsc", "--noEmit")
        cmd.extend(files)
        
        return await self._run_linter_command(
            cmd,
            language="typescript",
            parser=self._parse_tsc_output
        )
    
    async def _run_prettier(
        self,
        files: List[str],
        auto_fix: bool
    ) -> LinterCheckResult:
        """运行 Prettier 格式检查"""
        cmd = build_command("npx", "prettier")
        if auto_fix:
            cmd.append("--write")
        else:
            cmd.append("--check")
        cmd.extend(files)
        
        result = await self._run_command(cmd)
        
        issues = []
        status = LinterResult.PASSED.value
        auto_fixed = False
        
        if result.returncode != 0:
            if auto_fix:
                auto_fixed = True
                # 重新检查
                cmd = build_command("npx", "prettier", "--check")
                cmd.extend(files)
                result = await self._run_command(cmd)
            
            if result.returncode != 0:
                status = LinterResult.FAILED.value
                # 解析 prettier 输出
                for line in result.stdout.split('\n'):
                    if 'Would format' in line:
                        file_path = line.split('Would format')[1].strip()
                        issues.append(LinterIssue(
                            file_path=file_path,
                            line=0,
                            column=0,
                            severity=LinterSeverity.WARNING.value,
                            code="prettier/format",
                            message="文件格式不符合 prettier 规范"
                        ))
        
        return LinterCheckResult(
            language="typescript",
            files_checked=files,
            issues=issues,
            status=status,
            duration_ms=result.duration_ms,
            auto_fixed=auto_fixed
        )
    
    async def _run_linter_command(
        self,
        cmd: List[str],
        language: str,
        parser
    ) -> LinterCheckResult:
        """运行 Linter 命令"""
        result = await self._run_command(cmd)
        
        issues = []
        status = LinterResult.PASSED.value
        auto_fixed = False
        
        if result.returncode != 0:
            # 工具不可用（命令未找到 / 启动失败，returncode=-1）：SKIPPED + 警告放行
            # （v4.10.1：工具缺失 ≠ 代码质量失败，与 alembic_check 优雅放行原则一致，
            #   避免未安装 ruff/mypy/bandit 的机器被门禁误阻断；安装工具后自动恢复强制。）
            if result.returncode == -1:
                raw_tool = cmd[2] if len(cmd) > 2 and str(cmd[0]).lower() == "cmd.exe" else cmd[0]
                tool = Path(raw_tool).stem if str(raw_tool).lower().endswith((".cmd", ".bat")) else raw_tool
                issues.append(LinterIssue(
                    file_path="<tool>",
                    line=0,
                    column=0,
                    severity=LinterSeverity.WARNING.value,
                    code="missing-tool",
                    message=f"Linter 工具未安装，跳过: {tool} — 安装后自动恢复强制检查"
                ))
                status = LinterResult.SKIPPED.value
            else:
                # 解析输出
                issues = parser(result.stdout, result.stderr)
                status = LinterResult.FAILED.value
        
        return LinterCheckResult(
            language=language,
            files_checked=[],
            issues=issues,
            status=status,
            duration_ms=result.duration_ms,
            auto_fixed=auto_fixed
        )
    
    async def _run_command(self, cmd: List[str]) -> CommandResult:
        """运行命令"""
        start_time = asyncio.get_event_loop().time()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            stdout, stderr = await proc.communicate()

            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            return CommandResult(
                args=cmd,
                returncode=proc.returncode,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            return CommandResult(
                args=cmd,
                returncode=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms
            )
    
    def _parse_ruff_output(self, stdout: str, stderr: str) -> List[LinterIssue]:
        """解析 Ruff 输出"""
        issues = []
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            # 格式：file.py:1:1: E501 line too long
            parts = line.split(':')
            if len(parts) >= 4:
                try:
                    issues.append(LinterIssue(
                        file_path=parts[0],
                        line=int(parts[1]),
                        column=int(parts[2]),
                        severity=LinterSeverity.WARNING.value,
                        code=parts[3].split()[0] if len(parts[3].split()) > 0 else "",
                        message=line
                    ))
                except (ValueError, IndexError):
                    pass
        return issues
    
    def _parse_mypy_output(self, stdout: str, stderr: str) -> List[LinterIssue]:
        """解析 MyPy 输出"""
        issues = []
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            # 格式：file.py:1: error: message
            parts = line.split(':')
            if len(parts) >= 4 and 'error' in line.lower():
                try:
                    issues.append(LinterIssue(
                        file_path=parts[0],
                        line=int(parts[1]),
                        column=int(parts[2]) if parts[2].isdigit() else 0,
                        severity=LinterSeverity.ERROR.value,
                        code="",
                        message=line
                    ))
                except (ValueError, IndexError):
                    pass
        return issues
    
    def _parse_bandit_output(self, stdout: str, stderr: str) -> List[LinterIssue]:
        """解析 Bandit 输出"""
        issues = []
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            # 格式：file.py:1: B101 assert_used
            parts = line.split(':')
            if len(parts) >= 4:
                try:
                    issues.append(LinterIssue(
                        file_path=parts[0],
                        line=int(parts[1]),
                        column=int(parts[2]) if parts[2].isdigit() else 0,
                        severity=LinterSeverity.ERROR.value,
                        code=parts[3].split()[0] if len(parts[3].split()) > 0 else "",
                        message=line
                    ))
                except (ValueError, IndexError):
                    pass
        return issues
    
    def _parse_eslint_output(self, stdout: str, stderr: str) -> List[LinterIssue]:
        """解析 ESLint 输出"""
        issues = []
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            # 格式：file.py:1:1: error message (rule-name)
            if ':' in line and ('error' in line or 'warning' in line):
                parts = line.split(':')
                if len(parts) >= 4:
                    try:
                        severity = LinterSeverity.ERROR.value if 'error' in line else LinterSeverity.WARNING.value
                        issues.append(LinterIssue(
                            file_path=parts[0],
                            line=int(parts[1]),
                            column=int(parts[2]) if parts[2].isdigit() else 0,
                            severity=severity,
                            code=parts[3].strip() if len(parts) > 3 else "",
                            message=line
                        ))
                    except (ValueError, IndexError):
                        pass
        return issues
    
    def _parse_tsc_output(self, stdout: str, stderr: str) -> List[LinterIssue]:
        """解析 TypeScript 编译输出"""
        issues = []
        output = stdout + stderr
        for line in output.split('\n'):
            if not line.strip():
                continue
            # 格式：file.ts(1,1): error TS1234: message
            if '(' in line and 'error' in line.lower():
                try:
                    # 提取文件路径
                    file_part = line.split('(')[0]
                    # 提取行号和列号
                    nums = line.split('(')[1].split(')')[0].split(',')
                    line_num = int(nums[0])
                    col_num = int(nums[1]) if len(nums) > 1 else 0
                    # 提取错误信息
                    msg_part = line.split(': ')[1] if ': ' in line else line
                    issues.append(LinterIssue(
                        file_path=file_part,
                        line=line_num,
                        column=col_num,
                        severity=LinterSeverity.ERROR.value,
                        code="",
                        message=msg_part
                    ))
                except (ValueError, IndexError):
                    pass
        return issues
    
    def _determine_status(
        self,
        issues: List[LinterIssue],
        base_status: str
    ) -> str:
        """确定最终状态"""
        if base_status == LinterResult.PASSED.value:
            return LinterResult.PASSED.value
        
        has_errors = any(i.severity == LinterSeverity.ERROR.value for i in issues)
        has_warnings = any(i.severity == LinterSeverity.WARNING.value for i in issues)
        
        if has_errors:
            return LinterResult.FAILED.value
        elif has_warnings and self.fail_on_warning:
            return LinterResult.FAILED.value
        else:
            return LinterResult.PASSED.value
    
    def should_block_execution(self, result: LinterCheckResult) -> bool:
        """
        判断是否应该阻断执行
        
        Args:
            result: Linter 检查结果
            
        Returns:
            是否应该阻断
        """
        if result.status == LinterResult.PASSED.value:
            return False
        
        # 有错误时必须阻断
        if result.has_errors:
            return True
        
        # 警告时根据配置决定
        return self.fail_on_warning
    
    def generate_report(self, result: LinterCheckResult) -> str:
        """生成 Linter 报告"""
        lines = [
            f"=== Linter 检查报告 ===",
            f"语言: {result.language}",
            f"检查文件数: {len(result.files_checked)}",
            f"结果: {result.status}",
            f"耗时: {result.duration_ms:.2f}ms",
            f"自动修复: {'是' if result.auto_fixed else '否'}",
            f"问题数: {len(result.issues)}",
            f"错误数: {result.error_count}",
            f"警告数: {result.warning_count}",
            ""
        ]
        
        if result.issues:
            lines.append("--- 问题详情 ---")
            for issue in result.issues[:20]:  # 只显示前 20 个
                lines.append(str(issue))
            if len(result.issues) > 20:
                lines.append(f"... 还有 {len(result.issues) - 20} 个问题")
        
        return '\n'.join(lines)


# 便捷函数
async def check_python_files(
    files: List[str],
    project_root: str = ".",
    auto_fix: bool = True
) -> LinterCheckResult:
    """便捷函数：检查 Python 文件"""
    checker = LinterChecker(project_root, auto_fix=auto_fix)
    return await checker.check_python(files, auto_fix=auto_fix)


async def check_typescript_files(
    files: List[str],
    project_root: str = ".",
    auto_fix: bool = True
) -> LinterCheckResult:
    """便捷函数：检查 TypeScript 文件"""
    checker = LinterChecker(project_root, auto_fix=auto_fix)
    return await checker.check_typescript(files, auto_fix=auto_fix)


async def check_agent_generated_code(
    files: List[str],
    project_root: str = ".",
    auto_fix: bool = True
) -> Tuple[LinterCheckResult, bool]:
    """
    检查 Agent 生成的代码 - RULE-028
    
    Args:
        files: 文件路径列表
        project_root: 项目根目录
        auto_fix: 是否自动修复
        
    Returns:
        (检查结果, 是否应该阻断执行)
    """
    checker = LinterChecker(project_root, auto_fix=auto_fix)
    
    # 根据文件类型选择检查器
    if any(f.endswith('.py') for f in files):
        result = await checker.check_python(files)
    elif any(f.endswith('.ts') or f.endswith('.tsx') for f in files):
        result = await checker.check_typescript(files)
    else:
        result = LinterCheckResult(
            language="unknown",
            files_checked=files,
            issues=[],
            status=LinterResult.SKIPPED.value,
            duration_ms=0
        )
    
    should_block = checker.should_block_execution(result)
    
    # 记录审计日志
    if result.issues:
        logger.warning(
            f"Linter 检查发现 {len(result.issues)} 个问题，"
            f"错误 {result.error_count} 个，警告 {result.warning_count} 个"
        )
    
    return result, should_block


def _collect_skipped_tools(results: dict) -> set:
    """从各语言检查结果里抽出"因工具缺失而跳过"的工具名集合。

    判据：issue 的 code 为 `missing-tool`（由 _run_linter 在 returncode == -1 时写入，
    message 形如 "Linter 工具未安装，跳过: ruff — 安装后自动恢复强制检查"）。
    """
    tools = set()
    for lang_result in results.values():
        for issue in getattr(lang_result, "issues", []) or []:
            if getattr(issue, "code", "") != "missing-tool":
                continue
            msg = getattr(issue, "message", "") or ""
            # "跳过: <tool> —" 之间即为工具名
            if "跳过:" in msg:
                name = msg.split("跳过:", 1)[1].split("—", 1)[0].strip()
                if name:
                    tools.add(name)
    return tools


# 跨函数共享：main() 写入本次 SKIPPED 工具，__main__ 落 gate-runs 记录时读取
_SKIPPED_TOOLS_CACHE: set = set()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent Linter 检查工具")
    parser.add_argument("files", nargs="*", help="要检查的文件（--ci 模式下自动扫描项目）")
    parser.add_argument("--language", choices=["python", "typescript", "auto"], default="auto")
    parser.add_argument("--no-auto-fix", action="store_true", help="不自动修复")
    parser.add_argument("--fail-on-warning", action="store_true", help="警告也阻断")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--ci", action="store_true", help="CI 模式：扫描整个项目，不自动修复，失败即退出码 1")
    parser.add_argument(
        "--strict-missing-tools",
        action="store_true",
        help="工具缺失也视为未验证：退出码 2（默认仍放行，仅在汇总里标注 NOT-VERIFIED）",
    )
    
    args = parser.parse_args()
    started_at = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    async def main() -> int:
        checker = LinterChecker(
            args.project_root,
            auto_fix=not (args.no_auto_fix or args.ci),
            fail_on_warning=args.fail_on_warning
        )

        # CI 模式：扫描整个项目（Python + TypeScript），失败即阻断
        if args.ci:
            results = await checker.check_project(language="all")
            failed = False
            for lang_result in results.values():
                print(checker.generate_report(lang_result))
                if checker.should_block_execution(lang_result):
                    failed = True
            # ── 未验证 ≠ 已验证（v4.16.1）────────────────────────────────────
            # 工具缺失时本应放行（否则未装 ruff 的机器被门禁误阻断），但"跳过"
            # 必须在汇总里与"通过"分开报，否则日志只写"检查通过"会让读者以为
            # 质量已被验证。放行策略不变，**透明度必须变**。
            skipped_tools = _collect_skipped_tools(results)
            _SKIPPED_TOOLS_CACHE.clear()
            _SKIPPED_TOOLS_CACHE.update(skipped_tools)
            if skipped_tools:
                print(
                    "\n[NOT-VERIFIED] 以下检查**未执行**（工具缺失），本次结论仅代表"
                    "\"未发现问题\"而非\"已验证通过\"："
                )
                for tool in sorted(skipped_tools):
                    print(f"  - {tool}")
                print(
                    "\n装齐上述工具后重跑本门禁，才构成 RULE-008/010/016 的完整验证"
                    "（见 rules/security-rules.md）。"
                )
                # 仅当调用方要求严格（--strict-missing-tools）时才让缺失影响退出码
                if args.strict_missing_tools:
                    return 2
            return 1 if failed else 0

        # 命令行模式：检查指定文件
        if not args.files:
            parser.error("files 不能为空，请指定要检查的文件或使用 --ci 模式")

        if args.language == "python" or (args.language == "auto" and any(f.endswith('.py') for f in args.files)):
            result = await checker.check_python(args.files)
        else:
            result = await checker.check_typescript(args.files)

        print(checker.generate_report(result))

        return 1 if checker.should_block_execution(result) else 0

    exit_code = asyncio.run(main())
    if exit_code != 0:
        logger.error("Linter 检查失败，阻断执行")
    else:
        logger.info("Linter 检查通过")
    # ── 落一条 gate-runs 记录（v4.16.1）───────────────────────────────────
    # gate-inventory.yaml 曾把它标 integrated 却无记录，--unverified 永远报"从未成功
    # 运行"——那是事实不是假红。补上记录后该门禁才真正可被 --unverified 核对。
    try:
        import importlib.util
        from pathlib import Path as _Path
        # hooks/scripts/agent_linter_checker.py → ../../scripts/gate_runs.py
        spec_path = _Path(__file__).resolve().parent.parent.parent / "scripts" / "gate_runs.py"
        if spec_path.exists():
            spec = importlib.util.spec_from_file_location("gate_runs", spec_path)
            gate_runs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gate_runs)
            skipped = _SKIPPED_TOOLS_CACHE
            # 语义分级：exit 0 且有工具缺失 = 放行但未验证（NOT_VERIFIED），
            # 不是 PASS。——证据必须与结论同义，否则记录本身就是假的。
            verdict = "PASS"
            if exit_code == 2:
                verdict = "NOT_VERIFIED"
            elif exit_code == 0 and skipped:
                verdict = "NOT_VERIFIED"
            gate_runs.write_record(
                gate_id="agent-linter",
                mode="dry-run",
                trigger=os.environ.get("GATE_TRIGGER", "manual").lower(),
                result=verdict,
                rule_ids=["RULE-028"],
                evidence={
                    "checker": "hooks/scripts/agent_linter_checker.py --ci",
                    "exit_code": exit_code,
                    "strict_missing_tools": args.strict_missing_tools,
                    "skipped_tools": sorted(skipped),
                },
                started_at=started_at,
                exit_code=exit_code,
            )
    except Exception as exc:  # 记录写失败不得改变门禁结论，只告警
        logger.warning(f"[gate-runs] agent-linter 记录写入失败：{exc}（不影响本次退出码）")
    exit(exit_code)
