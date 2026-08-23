from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse, json, re, time
import requests
from bs4 import BeautifulSoup

BKK=ZoneInfo('Asia/Bangkok')
HEADERS={'User-Agent':'Mozilla/5.0','Accept-Language':'th-TH,th;q=0.9,en;q=0.7'}
SET_TMPL='https://www.set.or.th/th/market/product/stock/quote/{symbol}/price'
SETTRADE_TMPL='https://www.settrade.com/th/equities/quote/{symbol}/overview'

@dataclass
class Quote:
    symbol:str; Date:str; Open:float; High:float; Low:float; Close:float; Volume:float
    source:str; sourceUrl:str; fetchedAt:str

def num(s):
    if s is None: return None
    try:return float(str(s).replace(',','').replace('+','').strip())
    except:return None

def find_field(text,label):
    # broad, tolerant label matcher; validates values before accepting snapshot
    pats=[rf'{re.escape(label)}\s*[:]?\s*(-?\d[\d,]*(?:\.\d+)?)',rf'\b{re.escape(label)}\b[^0-9-]*(-?\d[\d,]*(?:\.\d+)?)']
    for p in pats:
        m=re.search(p,text,re.I)
        if m:
            v=num(m.group(1))
            if v is not None:return v
    return None

def parse_page(symbol,url,source):
    r=requests.get(url,headers=HEADERS,timeout=15); r.raise_for_status()
    text=' '.join(BeautifulSoup(r.text,'html.parser').stripped_strings)
    aliases={
      'Open':['Open','ราคาเปิด'], 'High':['High','สูงสุด'], 'Low':['Low','ต่ำสุด'],
      'Close':['Last','ล่าสุด'], 'Volume':['Volume (Shares)','Volume (Units)','ปริมาณ (หุ้น)','ปริมาณ']}
    vals={}
    for k,labels in aliases.items():
        vals[k]=next((v for lab in labels if (v:=find_field(text,lab)) is not None),None)
    if any(vals[k] is None for k in vals):
        raise ValueError(f'incomplete {source}: {vals}')
    now=datetime.now(BKK)
    return Quote(symbol,now.date().isoformat(),vals['Open'],vals['High'],vals['Low'],vals['Close'],vals['Volume'],source,url,now.isoformat(timespec='seconds'))

def fetch(symbol):
    urls=[(SET_TMPL.format(symbol=symbol),'SET'),(SETTRADE_TMPL.format(symbol=symbol),'SETTRADE')]
    errors=[]
    for url,src in urls:
        try:return parse_page(symbol,url,src)
        except Exception as e: errors.append(f'{src}: {e}')
    raise RuntimeError(' | '.join(errors))

def in_session(now):
    if now.weekday()>4:return False
    t=now.time()
    return dtime(10,0)<=t<=dtime(12,30) or dtime(14,30)<=t<=dtime(16,30)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--force',action='store_true'); ap.add_argument('--symbols-file',default='config/symbols.txt'); ap.add_argument('--out',default='docs/data/live.json'); ap.add_argument('--delay',type=float,default=1.0)
    a=ap.parse_args(); now=datetime.now(BKK)
    if not a.force and not in_session(now):
        print('Outside SET pilot session:',now.isoformat()); return
    symbols=[x.strip().upper() for x in Path(a.symbols_file).read_text().splitlines() if x.strip() and not x.startswith('#')]
    outp=Path(a.out); old={}
    if outp.exists():
        try: old=json.loads(outp.read_text()).get('quotes',{})
        except: pass
    result=dict(old); ok=fail=0
    for sym in symbols:
        try:
            q=fetch(sym); result[sym]=asdict(q); ok+=1; print('OK',sym,q.Close,q.source)
        except Exception as e:
            fail+=1; print('FAIL',sym,e)
        time.sleep(a.delay)
    outp.parent.mkdir(parents=True,exist_ok=True)
    outp.write_text(json.dumps({'updatedAt':datetime.now(BKK).isoformat(timespec='seconds'),'quotes':result,'ok':ok,'fail':fail},ensure_ascii=False,separators=(',',':')),encoding='utf-8')

if __name__=='__main__': main()
