from pathlib import Path
P=Path(__file__).resolve().parents[1]
base=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/clk')
chunks=[]
for p in base.rglob('*.c'):
    try:text=p.read_text()
    except (UnicodeError,OSError):continue
    if 'mclkout_to_io' not in text and 'io-mclk-out' not in text:continue
    lines=text.splitlines();picked=set()
    for i,s in enumerate(lines):
        if any(x in s for x in ['mclkout_to_io','io-mclk-out','clock-cells','of_clk_add','compatible =','clk_register_gate','clk_hw_register_gate']):picked.update(range(max(0,i-6),min(len(lines),i+8)))
    chunks.append('\nFILE '+str(p.relative_to(base))+'\n'+'\n'.join(str(i+1)+': '+lines[i] for i in sorted(picked)))
out=P/'analysis/armbian/audio-mclk-source-context-20261030.txt';out.write_text('\n'.join(chunks)+'\n');print(out.read_text())
