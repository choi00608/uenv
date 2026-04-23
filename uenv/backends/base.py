import abc

class BackendBase(abc.ABC):
    @abc.abstractmethod
    def create_env(self, name: str, location_type: str, python_version: str = None) -> bool:
        """가상환경을 생성합니다.
        
        Args:
            name: 환경 이름
            location_type: "local" 또는 "global"
            python_version: 파이썬 버전 (선택적)
        
        Returns:
            성공 여부
        """
        pass

    @abc.abstractmethod
    def remove_env(self, name: str, location_type: str) -> bool:
        """가상환경을 삭제합니다.
        
        Args:
            name: 환경 이름
            location_type: "local" 또는 "global"
            
        Returns:
            성공 여부
        """
        pass

    def _spawn_shell(self, activate_cmd: str, disable_conda: bool = False) -> bool:
        """가상환경 프롬프트를 유지하면서 서브쉘을 띄우는 공통 로직입니다."""
        import os
        import subprocess
        import tempfile
        from pathlib import Path
        
        shell = os.environ.get("SHELL", "bash")
        shell_name = Path(shell).name
        
        try:
            # 임시 디렉토리를 생성하여 초기화 스크립트 작성 (종료 시 자동 삭제)
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                if shell_name == "zsh":
                    zshrc_path = temp_path / ".zshrc"
                    user_zshrc = Path.home() / ".zshrc"
                    with open(zshrc_path, "w") as f:
                        if user_zshrc.exists():
                            f.write(f"source {user_zshrc}\n")
                        if disable_conda:
                            f.write('while [ -n "$CONDA_DEFAULT_ENV" ]; do conda deactivate 2>/dev/null || break; done\n')
                        f.write(f"{activate_cmd}\n")
                    
                    env = os.environ.copy()
                    env["ZDOTDIR"] = temp_dir
                    subprocess.run([shell, "-i"], env=env)
                    
                else: # 기본적으로 bash 작동 방식 지원
                    bashrc_path = temp_path / "bashrc"
                    user_bashrc = Path.home() / ".bashrc"
                    with open(bashrc_path, "w") as f:
                        if user_bashrc.exists():
                            f.write(f"source {user_bashrc}\n")
                        if disable_conda:
                            f.write('while [ -n "$CONDA_DEFAULT_ENV" ]; do conda deactivate 2>/dev/null || break; done\n')
                        f.write(f"{activate_cmd}\n")
                        
                    subprocess.run([shell, "--rcfile", str(bashrc_path), "-i"])
            return True
        except Exception as e:
            print(f"Error activating shell: {e}")
            return False

    @abc.abstractmethod
    def list_envs(self, location_type: str) -> list[dict]:
        """해당 백엔드가 관리하는 가상환경 목록 반환.
        
        Args:
            location_type: "local" 또는 "global"
            
        Returns:
            사전 리스트: [{"name": "이름", "version": "파이썬버전"}]
        """
        pass

    @abc.abstractmethod
    def activate_shell(self, name: str, location_type: str) -> bool:
        """서브쉘(Subshell)을 통해 가상환경을 활성화합니다.
        
        Args:
            name: 환경 이름
            location_type: "local" 또는 "global"
            
        Returns:
            서브쉘 종료 후 True/False (성공/에러)
        """
        pass
