#!/usr/bin/env python3
"""Install the pinned Linux x86_64 build tools into an isolated directory."""
import argparse,hashlib,subprocess,shutil
from pathlib import Path
REPOS={
 'a64-rules':('https://github.com/devkitPro/devkitA64-rules.git','b037940200a5a9a87888743fb83d7a87e348c8e7'),
 'libnx':('https://github.com/switchbrew/libnx.git','b156b4774fb2df7b93402169509266da7547fc4c'),
 'switch-tools':('https://github.com/switchbrew/switch-tools.git','22756068dd0ed6ff9734c59cb4f99ebd3f62555b'),
 'lz4':('https://github.com/lz4/lz4.git','ebf8859ddb62cfe1ce2eb1eee4f5bee94a5f21b1')}
URL='https://pkg.devkitpro.org/packages/linux/x86_64/devkitA64-r28-1-x86_64.pkg.tar.zst'
SHA='7d936cb38809c6b70863bbc345f15ed2f26f9186e3f20b9b16c714a122d2697c'
def run(*args):subprocess.run(args,check=True)
def install(root):
 root=root.resolve();root.mkdir(parents=True,exist_ok=True);archive=root/'devkitA64.pkg.tar.zst'
 if not archive.exists():
  partial=archive.with_suffix('.download')
  run('curl','--fail','--location','--retry','3','--connect-timeout','30','--max-time','240',URL,'--output',str(partial))
  partial.replace(archive)
 if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA:raise ValueError('Toolchain archive SHA256 mismatch')
 run('tar','--zstd','-xf',str(archive),'-C',str(root))
 for name,(url,sha) in REPOS.items():
  target=root/name
  if target.exists():raise FileExistsError('Use a fresh isolated toolchain directory: '+str(target))
  run('git','init','-q',str(target));run('git','-C',str(target),'fetch','--depth','1',url,sha)
  run('git','-C',str(target),'checkout','--detach','FETCH_HEAD')
 dk=root/'opt/devkitpro';(dk/'libnx').mkdir(exist_ok=True);(dk/'tools/bin').mkdir(parents=True,exist_ok=True)
 for name in ['base_rules','base_tools']:shutil.copy(root/'a64-rules'/name,dk/'devkitA64'/name)
 shutil.copy(root/'libnx/nx/switch_rules',dk/'libnx/switch_rules')
 st=root/'switch-tools/src';lz=root/'lz4/lib'
 run('cc','-O2','-I'+str(lz),str(st/'elf2nso.c'),str(st/'sha256.c'),str(lz/'lz4.c'),'-o',str(dk/'tools/bin/elf2nso'))
 run('cc','-O2',str(st/'npdmtool.c'),str(st/'cJSON.c'),'-lm','-o',str(dk/'tools/bin/npdmtool'))
 print('DEVKITPRO='+str(dk))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);install(p.parse_args().root)
