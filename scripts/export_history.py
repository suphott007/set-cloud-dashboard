from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

EMA_PERIODS=[20,50,75,89,200]

def normalize(df):
    need=['Date','Open','High','Low','Close','Volume']
    if not all(c in df.columns for c in need):
        raise ValueError(f'missing required columns {need}')
    out=df[need].copy()
    out['Date']=pd.to_datetime(out['Date'],errors='coerce')
    try:
        if getattr(out['Date'].dt,'tz',None) is not None:
            out['Date']=out['Date'].dt.tz_localize(None)
    except Exception:
        out['Date']=out['Date'].map(lambda x: x.tz_localize(None) if getattr(x,'tzinfo',None) else x)
    for c in need[1:]: out[c]=pd.to_numeric(out[c],errors='coerce')
    return out.dropna(subset=['Date','Close']).sort_values('Date').drop_duplicates('Date',keep='last')

def payload(df):
    rows=[]
    for _,r in df.iterrows():
        rows.append({'time':r.Date.strftime('%Y-%m-%d'),'open':float(r.Open),'high':float(r.High),'low':float(r.Low),'close':float(r.Close),'volume':None if pd.isna(r.Volume) else float(r.Volume)})
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    ap.add_argument('--out',default='docs/data/history')
    ap.add_argument('--symbols-file',default='config/symbols.txt')
    ap.add_argument('--years',type=int,default=10)
    a=ap.parse_args()
    root=Path(a.root); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    symbols=[x.strip().upper() for x in Path(a.symbols_file).read_text().splitlines() if x.strip() and not x.startswith('#')]
    ok=[]
    for sym in symbols:
        p=root/f'{sym}.csv'
        if not p.exists():
            print('MISS',sym,p); continue
        df=normalize(pd.read_csv(p))
        if a.years:
            cutoff=df.Date.max()-pd.DateOffset(years=a.years)
            df=df[df.Date>=cutoff]
        obj={'symbol':sym,'source':'local archive','rows':payload(df)}
        (out/f'{sym}.json').write_text(json.dumps(obj,separators=(',',':')),encoding='utf-8')
        print('OK',sym,len(df),df.Date.min().date(),df.Date.max().date()); ok.append(sym)
    Path('docs/data/symbols.json').write_text(json.dumps({'symbols':ok}),encoding='utf-8')

if __name__=='__main__': main()
