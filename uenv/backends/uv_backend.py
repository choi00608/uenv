import os
import shutil
import subprocess
from pathlib import Path
from .base import BackendBase
from ..config import GLOBAL_ENVS_DIR, ensure_global_dir

class UvBackend(BackendBase):
    def _get_path(self, name: str, location_type: str) -> Path:
        if location_type == "global":
            ensure_global_dir()
            return GLOBAL_ENVS_DIR / name
        else:
            return Path.cwd() / name

    def create_env(self, name: str, location_type: str, python_version: str = None) -> bool:
        env_path = self._get_path(name, location_type)
        if env_path.exists():
            print(f"Error: Environment {env_path} already exists.")
            return False

        cmd = ["uv", "venv", "--seed", str(env_path)]
        if python_version:
            cmd.extend(["--python", python_version])
            
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            print("Error: Could not find 'uv' command. Please install uv first.")
            return False

    def remove_env(self, name: str, location_type: str) -> bool:
        env_path = self._get_path(name, location_type)
        if not env_path.exists():
            print(f"Error: Environment {env_path} does not exist.")
            return False
            
        try:
            shutil.rmtree(env_path)
            return True
        except Exception as e:
            print(f"Error deleting environment: {e}")
            return False

    def _get_python_version(self, env_dir: Path) -> str:
        cfg = env_dir / "pyvenv.cfg"
        if cfg.exists():
            try:
                for line in cfg.read_text().splitlines():
                    if line.startswith("version") and "=" in line:
                        return line.split("=")[1].strip()
            except Exception:
                pass
        
        python_bin = env_dir / "bin" / "python"
        if python_bin.exists():
            try:
                res = subprocess.run([str(python_bin), "--version"], capture_output=True, text=True)
                if res.returncode == 0:
                    return res.stdout.strip().replace("Python ", "")
            except Exception:
                pass
        return "Unknown"

    def _is_uv_env(self, env_dir: Path) -> bool:
        cfg = env_dir / "pyvenv.cfg"
        if cfg.exists():
            try:
                lines = cfg.read_text().lower().splitlines()
                for line in lines:
                    if line.strip().startswith("uv =") or line.strip().startswith("uv="):
                        return True
            except Exception:
                pass
        return False

    def list_envs(self, location_type: str) -> list[dict]:
        envs = []
        if location_type == "global":
            if GLOBAL_ENVS_DIR.exists():
                for d in GLOBAL_ENVS_DIR.iterdir():
                    if d.is_dir() and (d / "bin" / "activate").exists() and self._is_uv_env(d):
                        envs.append({"name": d.name, "version": self._get_python_version(d)})
        else:
            for d in Path.cwd().iterdir():
                if d.is_dir() and (d / "bin" / "activate").exists() and self._is_uv_env(d):
                    envs.append({"name": d.name, "version": self._get_python_version(d)})
        return envs

    def activate_shell(self, name: str, location_type: str) -> bool:
        env_path = self._get_path(name, location_type)
        activate_script = env_path / "bin" / "activate"
        if not activate_script.exists():
            print(f"Error: Could not find activate script at {activate_script}")
            return False

        # _spawn_shell을 사용하여 원래의 프롬프트(.bashrc, .zshrc) 로드 후 
        # 가상환경 프롬프트를 덮어씌웁니다.
        cmd = f"source {activate_script}"
        return self._spawn_shell(cmd, disable_conda=True)


