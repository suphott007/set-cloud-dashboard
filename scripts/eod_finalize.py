from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BKK=ZoneInfo('Asia/Bangkok')

def main():
    lp=Path('docs/data/live.json')
    if not lp.exists():
        print('No live.json'); return
    live=json.loads(lp.read_text()).get('quotes',{})
    for sym,q in live.items():
        hp=Path('docs/data/history')/f'{sym}.json'
        if not hp.exists(): continue
        obj=json.loads(hp.read_text()); rows=obj.get('rows',[])
        row={'time':q['Date'],'open':q['Open'],'high':q['High'],'low':q['Low'],'close':q['Close'],'volume':q['Volume']}
        rows=[r for r in rows if r.get('time')!=q['Date']]+[row]
        rows.sort(key=lambda r:r['time']); obj['rows']=rows; obj['finalizedAt']=datetime.now(BKK).isoformat(timespec='seconds')
        hp.write_text(json.dumps(obj,separators=(',',':')),encoding='utf-8'); print('FINAL',sym,q['Date'],q['Close'])

if __name__=='__main__':main()
