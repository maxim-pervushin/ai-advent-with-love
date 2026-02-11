#!/usr/bin/env python3
"""
AI Coder - Command-line utility for programming assistance using Ollama
"""

import json
import subprocess
import readline
from pathlib import Path


from const import (
    MAKE_FILES_SYSTEM_PROMPT,
    HELP_WITH_CODE_SYSTEM_PROMPT,
    GIT_COMMIT_SYSTEM_PROMPT,
    CODE_REVIEW_SYSTEM_PROMPT,
)
# from providers.ollama_provider import OllamaProvider
from providers.yandex_provider import YandexProvider


class AICoder:
    def __init__(self):
        self.allowed_root = None
        self.current_dir = None
        # self.provider = OllamaProvider()
        self.provider = YandexProvider()

    def is_safe_path(self, path: Path) -> bool:
        """Check if path is within allowed directory"""
        if not self.allowed_root:
            return False
        try:
            resolved = path.resolve()
            return resolved.is_relative_to(self.allowed_root.resolve())
        except (ValueError, OSError):
            return False

    def open_folder(self, path: str) -> str:
        """Open and set working directory"""
        folder = Path(path).expanduser().resolve()
        if not folder.exists():
            return f"Error: Directory '{path}' does not exist"
        if not folder.is_dir():
            return f"Error: '{path}' is not a directory"

        self.allowed_root = folder
        self.current_dir = folder
        return f"Working directory set to: {folder}\nAll file operations restricted to this directory."

    def read_file(self, path: Path) -> str:
        """Safely read file content"""
        if not self.is_safe_path(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def write_file(self, path: Path, content: str) -> bool:
        """Safely write file content"""
        if not self.is_safe_path(path):
            return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def delete_file(self, path: Path) -> bool:
        """Safely delete file"""
        if not self.is_safe_path(path):
            return False
        try:
            if path.is_file():
                path.unlink()
                return True
            elif path.is_dir():
                import shutil

                shutil.rmtree(path)
                return True
            return False
        except Exception:
            return False

    def list_files(self) -> str:
        """List files in current directory"""
        if not self.current_dir:
            return "No folder selected. Use /open PATH first."
        try:
            items = []
            for item in sorted(self.current_dir.iterdir()):
                if item.is_dir():
                    items.append(f"[DIR]  {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"[FILE] {item.name} ({size} bytes)")
            return "\n".join(items) if items else "Directory is empty"
        except Exception as e:
            return f"Error listing files: {e}"

    def read_all_files(self) -> str:
        """Read all files in directory for AI context"""
        if not self.current_dir:
            return ""

        files_content = []
        for path in sorted(self.current_dir.rglob("*")):
            if path.is_file():
                if self.is_safe_path(path):
                    content = self.read_file(path)
                    rel_path = path.relative_to(self.current_dir)
                    files_content.append(f"\n=== {rel_path} ===\n{content}")
        return "\n".join(files_content)

    def make_files(self, prompt: str) -> str:
        """Create/update files based on user request"""
        if not self.current_dir:
            return "No folder selected. Use /open PATH first."

        all_files = self.read_all_files()

        user_prompt = f"""Project structure and existing files:
{all_files if all_files else "(empty directory)"}

User request: {prompt}

Create or modify the necessary files to fulfill this request. Consider the existing files and their relationships."""

        response = self.provider.generate(user_prompt, MAKE_FILES_SYSTEM_PROMPT)

        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response = "\n".join(lines)

            data = json.loads(response)
        except json.JSONDecodeError:
            return f"Error: AI response was not valid JSON:\n{response}"

        results = []

        for f in data.get("files", []):
            path = f.get("path", "")
            content = f.get("content", "")

            if not path:
                continue

            file_path = self.current_dir / path
            if not self.is_safe_path(file_path):
                results.append(
                    f"BLOCKED: Attempted to write outside allowed directory: {path}"
                )
                continue

            if self.write_file(file_path, content):
                results.append(f"Created/updated: {path}")
            else:
                results.append(f"Failed to write: {path}")

        for path in data.get("delete", []):
            file_path = self.current_dir / path
            if not self.is_safe_path(file_path):
                results.append(
                    f"BLOCKED: Attempted to delete outside allowed directory: {path}"
                )
                continue

            if self.delete_file(file_path):
                results.append(f"Deleted: {path}")
            else:
                results.append(f"Failed to delete: {path}")

        if not results:
            return "No files were modified."

        return "\n".join(results)

    def help_with_code(self, question: str) -> str:
        """Answer questions about the code"""
        if not self.current_dir:
            return "No folder selected. Use /open PATH first."

        all_files = self.read_all_files()
        if not all_files:
            return "No files found in the project."

        user_prompt = f"""Project files:
{all_files}

Question: {question}

Provide a comprehensive answer based on the code above."""

        return self.provider.generate(user_prompt, HELP_WITH_CODE_SYSTEM_PROMPT)

    def git_commit_message(self) -> str:
        """Generate git commit message from staged/unstaged changes"""
        try:
            diff_output = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            )
            staged_diff = subprocess.run(
                ["git", "diff", "--cached", "--stat"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            )

            diff_stat = diff_output.stdout or staged_diff.stdout

            if not diff_stat.strip():
                unstaged_content = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    cwd=self.current_dir or ".",
                )
                if not unstaged_content.stdout.strip():
                    return "No changes detected for commit."
                diff_stat = unstaged_content.stdout

            diff_content = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            ).stdout

            staged_content = subprocess.run(
                ["git", "diff", "--cached"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            ).stdout

            full_diff = staged_content or diff_content

            user_prompt = f"""Generate a commit message for these changes:

{full_diff if full_diff else diff_stat}

Summary of changed files:
{diff_stat}"""

            return self.provider.generate(user_prompt, GIT_COMMIT_SYSTEM_PROMPT)

        except subprocess.SubprocessError as e:
            return f"Git error: {str(e)}"
        except FileNotFoundError:
            return "Error: git is not installed or not found in PATH"

    def git_info(self) -> str:
        """Show current branch and recent commits"""
        try:
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            )
            current_branch = branch_result.stdout.strip()

            log_result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            )
            commits = log_result.stdout.strip().split("\n")

            result = []
            if current_branch:
                result.append(f"Current branch: {current_branch}")
            else:
                result.append("Current branch: (detached HEAD)")

            result.append("\nRecent commits:")
            for i, commit in enumerate(commits[:3], 1):
                if commit:
                    result.append(f"  {i}. {commit}")

            return "\n".join(result)

        except subprocess.SubprocessError as e:
            return f"Git error: {str(e)}"
        except FileNotFoundError:
            return "Error: git is not installed or not found in PATH"

    def git_review(self) -> str:
        """Review changes between last two commits"""
        try:
            # Get the diff between the last two commits
            diff_result = subprocess.run(
                ["git", "diff", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            )
            
            if diff_result.returncode != 0:
                return f"Git error: {diff_result.stderr}"
                
            diff_content = diff_result.stdout
            
            if not diff_content.strip():
                return "No changes found between the last two commits."

            # Get commit messages for context
            log_result = subprocess.run(
                ["git", "log", "--oneline", "-2"],
                capture_output=True,
                text=True,
                cwd=self.current_dir or ".",
            )
            
            commit_messages = log_result.stdout.strip()
            
            user_prompt = f"""Review the following code changes between the last two commits:

Recent commits:
{commit_messages}

Code changes:
{diff_content}

Please provide a detailed code review based on these changes."""

            return self.provider.generate(user_prompt, CODE_REVIEW_SYSTEM_PROMPT)

        except subprocess.SubprocessError as e:
            return f"Git error: {str(e)}"
        except FileNotFoundError:
            return "Error: git is not installed or not found in PATH"
        except Exception as e:
            return f"Error during review: {str(e)}"


def main():
    coder = AICoder()
    print("AI Coder - Programming Assistant with Ollama")
    print("=" * 45)
    print("Commands:")
    print("  /open PATH    - Select working directory")
    print("  /ls           - List files in current directory")
    print("  /make PROMPT  - Create/update files based on request")
    print("  /help QUESTION - Ask about code in current directory")
    print("  /commit       - Generate git commit message")
    print("  /git          - Show current branch and recent commits")
    print("  /review       - Review changes between last two commits")
    print("  /exit         - Exit the program")
    print("=" * 45)

    while True:
        try:
            user_input = input("\nAI Coder> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.startswith("/open "):
            path = user_input[6:].strip()
            print(coder.open_folder(path))

        elif user_input == "/ls" or user_input == "/list":
            print(coder.list_files())

        elif user_input.startswith("/make "):
            prompt = user_input[6:].strip()
            print("\nAnalyzing and creating files...")
            print(coder.make_files(prompt))

        elif user_input.startswith("/help "):
            question = user_input[6:].strip()
            print("\nAnalyzing code...")
            print(coder.help_with_code(question))

        elif user_input == "/commit":
            print("\nAnalyzing changes...")
            print(coder.git_commit_message())

        elif user_input == "/git":
            print(coder.git_info())

        elif user_input == "/review":
            print("\nAnalyzing code changes...")
            print(coder.git_review())

        elif user_input in ["/exit", "/quit", "exit", "quit"]:
            print("Goodbye!")
            break

        else:
            print("Unknown command. Use /open, /make, /help, /commit, /git, /review, or /exit")


if __name__ == "__main__":
    main()
