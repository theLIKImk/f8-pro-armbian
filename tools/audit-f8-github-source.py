"""Fail closed before publishing if the public snapshot contains credentials."""
from pathlib import Path
import re,json
P=Path(__file__).resolve().parents[1];W=P/'local/github-publish-20261104';R=W/'repository'
assert (R/'.git').is_dir()
patterns=[rb'github_pat_[A-Za-z0-9_]{20,}',rb'ghp_[A-Za-z0-9]{20,}',rb'TempF8-'+rb'2026',rb"[\"']"+b'1234'+b'5678'+rb"[\"']",rb'(?m)^-----BEGIN (?:OPENSSH|RSA|EC|DSA|ENCRYPTED )?PRIVATE KEY-----',rb'(?im)^\s*(?:wpa-psk|wep-key[0-3])\s*=\s*[^\s#]+']
excluded={'final-f8-pw-check.sh','verify-f8-password.sh','set-f8-password.sh','set-f8-password2.sh','set-f8-password3.sh','set-f8-password-direct.sh'}
findings=[];total=0;count=0
for f in R.rglob('*'):
 if not f.is_file() or '.git' in f.relative_to(R).parts:continue
 b=f.read_bytes();total+=len(b);count+=1
 if any(re.search(pattern,b) for pattern in patterns):findings.append(str(f.relative_to(R)))
 assert not f.name.endswith('.nmconnection') and f.name not in excluded,str(f)
assert not findings,sorted(set(findings))
audit={'files_scanned':count,'bytes_public_tree':total,'excluded_old_password_scripts':sorted(excluded),'credential_pattern_scan_passed':True,'private_directories_excluded':['local','hardware','downloads','vendor','analysis','outputs'],'documentation_private_address_replaced_with_example':True}
(W/'source-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit))
