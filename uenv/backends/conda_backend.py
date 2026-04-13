import os
import subprocess
from pathlib import Path
from .base import BackendBase

class CondaBackend(BackendBase):
    def create_env(self, name: str, location_type: str, python_version: str = None) -> bool:
        cmd = ["conda", "create", "-y"]
        
        if location_type == "global":
            cmd.extend(["-n", name])
        else:
            # local
            local_path = Path.cwd() / name
            if local_path.exists():
                print(f"Error: Environment {local_path} already exists.")
                return False
            cmd.extend(["-p", str(local_path)])

        if python_version:
            cmd.append(f"python={python_version}")

        try:
            # -y 플래그와 함께 실행하여 비대화형 모드로 생성 시도
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            if "CondaToSNonInteractiveError" in e.stderr:
                print("\n[bold red]✖ Conda 이용 약관(Terms of Service) 동의가 필요합니다.[/bold red]")
                print("아래 명령어를 터미널에 직접 입력하여 약관에 동의한 후 다시 시도해 주세요:")
                print("  conda tos accept --all")
            else:
                print(f"\n[bold red]✖ Conda 환경 생성 중 오류가 발생했습니다.[/bold red]")
                if e.stderr:
                    print(f"상세 정보: {e.stderr.strip()}")
            return False
        except FileNotFoundError:
            print("\n[bold red]✖ 'conda' 명령어를 찾을 수 없습니다.[/bold red] Conda가 설치되어 있고 PATH에 등록되어 있는지 확인해 주세요.")
            return False

    def remove_env(self, name: str, location_type: str) -> bool:
        cmd = ["conda", "env", "remove", "-y"]
        
        if location_type == "global":
            cmd.extend(["-n", name])
        else:
            # local
            local_path = Path.cwd() / name
            cmd.extend(["-p", str(local_path)])

        try:
            subprocess.run(cmd, check=True)
            # Conda doesn't always clean up the directory fully if there are non-conda files.
            # We can optionally remove the directory if it's local.
            if location_type == "local" and local_path.exists() and local_path.is_dir():
                import shutil
                shutil.rmtree(local_path, ignore_errors=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            print("Error: Could not find 'conda' command.")
            return False

    def _get_python_version(self, env_path_str: str) -> str:
        python_bin = Path(env_path_str) / "bin" / "python"
        if python_bin.exists():
            try:
                res = subprocess.run([str(python_bin), "--version"], capture_output=True, text=True)
                if res.returncode == 0:
                    return res.stdout.strip().replace("Python ", "")
            except Exception:
                pass
        return "Unknown"

    def list_envs(self, location_type: str) -> list[dict]:
        envs = []
        try:
            import json
            result = subprocess.run(["conda", "env", "list", "--json"], capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if location_type == "global":
                    for env_path in data.get("envs", []):
                        path_obj = Path(env_path)
                        if path_obj.name and "envs" in path_obj.parts:
                            envs.append({"name": path_obj.name, "version": self._get_python_version(env_path)})
                        elif path_obj.name == "base" or "miniconda" in path_obj.name.lower() or "anaconda" in path_obj.name.lower():
                            # base 추가 전 중복 확인
                            if not any(e["name"] == "base" for e in envs):
                                envs.append({"name": "base", "version": self._get_python_version(env_path)})
                else:
                    cwd = str(Path.cwd())
                    for env_path in data.get("envs", []):
                        if env_path.startswith(cwd) and env_path != cwd:
                            try:
                                rel_path = Path(env_path).relative_to(cwd)
                                if len(rel_path.parts) == 1:
                                    envs.append({"name": rel_path.name, "version": self._get_python_version(env_path)})
                            except ValueError:
                                pass
        except Exception:
            pass
        return envs

    def activate_shell(self, name: str, location_type: str) -> bool:
        try:
            result = subprocess.run(["conda", "info", "--base"], capture_output=True, text=True, check=True)
            conda_base = result.stdout.strip()
            
            target = name if location_type == "global" else str(Path.cwd() / name)
            cmd = f"source {conda_base}/etc/profile.d/conda.sh && conda activate {target}"
            
            return self._spawn_shell(cmd)
        except Exception as e:
            print(f"Error activating conda shell: {e}")
            return False


