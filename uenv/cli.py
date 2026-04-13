import sys
import argparse
import questionary
from rich.console import Console
from rich.panel import Panel

# UTF-8 출력 보장 (한글 깨짐 방지)
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from uenv.backends.venv_backend import VenvBackend
from uenv.backends.uv_backend import UvBackend
from uenv.backends.conda_backend import CondaBackend

console = Console()

BACKENDS = {
    "venv": VenvBackend(),
    "uv": UvBackend(),
    "conda": CondaBackend(),
}

# --- 터미널 테마 호환성 커스텀 스타일 ---
custom_style = questionary.Style([
    ('qmark', 'fg:ansicyan bold'),       
    ('question', 'bold'),               
    ('answer', 'fg:ansigreen bold'),      
    ('pointer', 'fg:ansicyan bold'),     
    ('highlighted', 'fg:ansicyan bold'), 
    ('selected', 'fg:ansicyan bold'),         
    ('separator', ''),
    ('instruction', ''),  # 어두운 회색 스타일 완전 제거 (테마 기본 글자색 사용)
    ('text', ''),
    ('disabled', '')
])

def create_flow():
    console.print(Panel.fit("🌿 [bold green]uenv[/bold green] - Create Environment"))
    
    step = 0
    name = ".venv"
    location = None
    backend_name = None
    python_version = ""
    
    while step < 4:
        if step == 0:
            res = questionary.text(
                "환경의 이름을 입력하세요 [로컬 .venv 권장 / 취소 및 이전: Ctrl+C]:", 
                default=name,
                style=custom_style
            ).ask()
            if res is None:
                return False
            if not res:
                res = name
            name = res
            step += 1
        elif step == 1:
            location = questionary.select(
                "어디에 저장할까요? [취소 및 이전: Ctrl+C]",
                choices=[
                    questionary.Choice("로컬 프로젝트 폴더 (현재 디렉토리)", value="local"),
                    questionary.Choice("글로벌 중앙 폴더 (~/.uenv/envs/)", value="global"),
                    questionary.Choice("⬅️  이전 단계로", value="back")
                ],
                style=custom_style
            ).ask()
            if location == "back" or location is None:
                step -= 1
            else:
                step += 1
        elif step == 2:
            backend_name = questionary.select(
                "사용할 백엔드를 선택하세요: [취소 및 이전: Ctrl+C]",
                choices=[
                    questionary.Choice("uv", value="uv"),
                    questionary.Choice("conda", value="conda"),
                    questionary.Choice("venv", value="venv"),
                    questionary.Choice("⬅️  이전 단계로", value="back")
                ],
                style=custom_style
            ).ask()
            if backend_name == "back" or backend_name is None:
                step -= 1
            else:
                step += 1
        elif step == 3:
            if backend_name in ["uv", "conda"]:
                res = questionary.text(
                    "파이썬 버전을 입력하세요 [예: 3.10 / 기본 엔터 / 취소: Ctrl+C]:",
                    style=custom_style
                ).ask()
                if res is None:
                    step -= 1
                else:
                    python_version = res
                    step += 1
            else:
                step += 1

    console.print(f"\n[bold cyan]⏳ {backend_name} 백엔드를 사용하여 '{name}' 환경을 생성 중입니다...[/bold cyan]")
    backend = BACKENDS[backend_name]
    success = backend.create_env(name, location, python_version if python_version else None)
    
    if success:
        console.print("[bold green]✔ 성공적으로 가상환경이 생성되었습니다![/bold green]")
        enter_now = questionary.confirm(
            "방금 생성한 가상환경으로 바로 진입하시겠습니까?", 
            style=custom_style
        ).ask()
        if enter_now:
            console.print(f"\n[bold green]🚀 가상환경 '{name}' 내부로 진입합니다... (다 쓰면 `exit` 입력)[/bold green]")
            backend.activate_shell(name, location)
            console.print("[yellow]원래 터미널로 성공적으로 복귀했습니다.[/yellow]")
    else:
        console.print("[bold red]✖ 가상환경 생성에 실패했습니다.[/bold red]")
    return True

def get_all_envs():
    envs = []
    for loc in ["local", "global"]:
        for backend_name, backend_obj in BACKENDS.items():
            found_list = backend_obj.list_envs(loc)
            for e_dict in found_list:
                e_name = e_dict["name"]
                if not any(x["name"] == e_name and x["location"] == loc for x in envs):
                    envs.append({
                        "name": e_name, 
                        "location": loc, 
                        "backend": backend_name,
                        "version": e_dict.get("version", "Unknown")
                    })
    return envs

def delete_flow():
    console.print(Panel.fit("🗑️  [bold red]uenv[/bold red] - Delete Environment"))
    
    envs = get_all_envs()
    if not envs:
        console.print("[yellow]삭제할 수 있는 가상환경이 없습니다.[/yellow]")
        return False
        
    choices = []
    for item in envs:
        loc_str = "로컬" if item["location"] == "local" else "글로벌"
        version_str = item["version"]
        display = f"{item['name']} │ [{loc_str}] (기반: {item['backend']}) [Python: {version_str}]"
        choices.append(questionary.Choice(display, value=item))
    choices.append(questionary.Choice("⬅️  이전 단계로", value="back"))
        
    selected = questionary.select(
        "삭제할 가상환경을 선택하세요: [취소 및 이전: Ctrl+C]",
        choices=choices,
        style=custom_style
    ).ask()
    
    if not selected or selected == "back":
        return False

    name = selected["name"]
    backend_name = selected["backend"]
    location = selected["location"]

    confirm = questionary.confirm(
        f"정말로 '{name}' ({backend_name} 환경)을 삭제하시겠습니까?", 
        style=custom_style
    ).ask()
    if not confirm:
        console.print("취소되었습니다.")
        return False

    console.print(f"\n[bold yellow]⏳ {backend_name} 백엔드를 사용하여 '{name}' 환경을 삭제 중입니다...[/bold yellow]")
    backend = BACKENDS[backend_name]
    success = backend.remove_env(name, location)
    
    if success:
        console.print("[bold green]✔ 성공적으로 가상환경이 삭제되었습니다![/bold green]")
    else:
        console.print("[bold red]✖ 가상환경 삭제에 실패했습니다.[/bold red]")
    return True

def activate_flow():
    console.print(Panel.fit("🚀 [bold blue]uenv[/bold blue] - Activate Environment"))
    
    envs = get_all_envs()
                    
    if not envs:
        console.print("[yellow]사용 가능한 가상환경을 찾지 못했습니다.[/yellow]")
        return False

    choices = []
    for item in envs:
        loc_str = "로컬" if item["location"] == "local" else "글로벌"
        version_str = item["version"]
        display = f"{item['name']} │ [{loc_str}] (기반: {item['backend']}) [Python: {version_str}]"
        choices.append(questionary.Choice(display, value=item))
    choices.append(questionary.Choice("⬅️  이전 단계로", value="back"))
        
    selected = questionary.select(
        "활성화할 가상환경을 선택하세요: [취소 및 이전: Ctrl+C]",
        choices=choices,
        style=custom_style
    ).ask()
    
    if not selected or selected == "back":
        return False
        
    backend = BACKENDS[selected["backend"]]
    console.print(f"\n[bold green]🚀 가상환경 '{selected['name']}' 내부로 진입합니다... (다 쓰면 `exit` 입력)[/bold green]")
    
    backend.activate_shell(selected["name"], selected["location"])
    
    console.print("[yellow]원래 터미널로 성공적으로 복귀했습니다.[/yellow]")
    return True

def main():
    parser = argparse.ArgumentParser(description="Unified Python Environment Manager")
    parser.add_argument("command", nargs="?", choices=["create", "delete", "list", "activate"], help="명령어 (입력하지 않으면 대화형 메뉴 실행)")
    
    args = parser.parse_args()

    if not args.command:
        print("") 
        console.print(Panel.fit("✨ [bold cyan]uenv[/bold cyan] ✨\nUnified Python Environment Manager\n[dim]방향키로 메뉴를 선택하고 Enter를 누르세요.[/dim]"))
        try:
            while True:
                command = questionary.select(
                    "무엇을 하시겠습니까? [종료: Ctrl+C]",
                    choices=[
                        questionary.Choice("🌱 가상환경 생성 (create)", value="create"),
                        questionary.Choice("🚀 가상환경 사용 (activate / shell 진입)", value="activate"),
                        questionary.Choice("🗑️ 가상환경 삭제 (delete)", value="delete"),
                        questionary.Choice("❌ 종료", value="exit")
                    ],
                    style=custom_style
                ).ask()
                
                if not command or command == "exit":
                    console.print("종료합니다.")
                    sys.exit(0)
                elif command == "create":
                    if create_flow(): break
                elif command == "delete":
                    if delete_flow(): break
                elif command == "activate":
                    if activate_flow(): break
                
                print("") # 루프 시 줄 띄우기
        except KeyboardInterrupt:
            console.print("\n[red]사용자에 의해 강제 종료되었습니다.[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]대화형 메뉴를 불러오는 도중 오류가 발생했습니다: {e}[/red]")
            console.print("[yellow]대신 `uenv create` 나 `uenv activate` 처럼 명령어를 직접 입력하여 시도해 보세요.[/yellow]")
            sys.exit(1)
    else:
        if args.command == "create":
            create_flow()
        elif args.command == "delete":
            delete_flow()
        elif args.command == "activate":
            activate_flow()
        elif args.command == "list":
            console.print("[yellow]list 명령어 대신 activate 또는 delete 명령어를 치면 목록을 볼 수 있습니다![/yellow]")

if __name__ == "__main__":
    main()

