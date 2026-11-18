"""Run with python -m tpc_editor --workspace <user-workspace>."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description='TPC 本机域壁路径编辑器')
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--ready-file', type=Path)
    args = parser.parse_args()
    try:
        from .server import create_server
        server = create_server(args.workspace, args.port)
    except ImportError as exc:
        parser.exit(2, f'编辑器缺少离线依赖：{exc}。请在运行环境安装 tpc-topology[geometry] 或准备插件 geometry extra。\n')
    status = {'url': f'http://127.0.0.1:{server.server_port}/',
              'workspace': str(server.session.workspace), 'pid': __import__('os').getpid()}
    if args.ready_file:
        args.ready_file.parent.mkdir(parents=True, exist_ok=True)
        args.ready_file.write_text(json.dumps(status, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(status, ensure_ascii=False), flush=True)
    if not args.no_browser:
        import webbrowser
        webbrowser.open(status['url'])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
