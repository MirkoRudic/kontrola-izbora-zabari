# Zabari 2026 – RIK rezultati + zapisnici. Faze:
#   python3 zabari_job.py fetch <prev.json|-> [round] [limit]  -> /tmp/zj/new.json, /tmp/zj/upload/*.pdf, /tmp/zj/upload.txt
#   python3 zabari_job.py attach <map.json> [status.json]       -> /tmp/zj/doc.json (spreman za upis)
import json,subprocess,time,sys,datetime,re,os,hashlib,urllib.parse
from zoneinfo import ZoneInfo
W="/tmp/zj"; os.makedirs(W+"/upload",exist_ok=True)
R="https://www.rik.parlament.gov.rs"; CK=W+"/ck"
now=lambda:datetime.datetime.now(ZoneInfo("Europe/Belgrade")).strftime("%d.%m. %H:%M")
def curl(args): return subprocess.run(["curl","-sS","--http1.1","--max-time","90"]+args,capture_output=True)
def post(path,data):
    args=["-b",CK,"-X","POST","-H","X-Requested-With: XMLHttpRequest","-H","Referer: "+R+"/542645/rezultati/"]
    for k,v in data.items(): args+=["--data-urlencode",f"{k}={v}"]
    for a in range(6):
        o=curl(args+[R+path]).stdout
        try: return json.loads(o)
        except Exception: time.sleep(3+a*4)
    raise RuntimeError("RIK nedostupan: "+path)
def pdf(url):
    for a in range(4):
        r=curl(["-o",W+"/tmp.pdf",R+urllib.parse.quote(url)])
        if r.returncode==0 and open(W+"/tmp.pdf","rb").read(5)==b"%PDF-": return open(W+"/tmp.pdf","rb").read()
        time.sleep(3+a*4)
    return None
num=lambda x:int(str(x).replace('.','') or 0)

def fetch(prevf,ROUND,limit):
    prev={}
    if prevf!="-" and os.path.exists(prevf):
        p=json.load(open(prevf)); prev=p.get("data",p).get("bm",{}) if isinstance(p,dict) else {}
    curl(["--retry","5","--retry-all-errors","-c",CK,"-o","/dev/null",R+"/542645/rezultati/"])
    st=post("/get-election-stations/",dict(election_type=2,election_round=ROUND,election_region=4,election_municipality=84))["election_stations"]
    if len(st)!=37: raise RuntimeError("ocekivano 37 BM, dobijeno %d"%len(st))
    bm={}; uploads=[]; t=now()
    for sid,name in list(st.items())[:limit]:
        n=int(name.split(' - ')[0]); k="bm%02d"%n; old=prev.get(k) or {}
        d=post("/get_results/",dict(should_update_pies=1,type=2,election_round=ROUND,region=4,municipality=84,election_station=sid))
        s=d.get("stat_sum_numbers") or {}
        rec=dict(processed=num(s.get("processed_stations",0))>0,voters=num(s.get("total_voters",0)),out=num(s.get("available",0)),outside=old.get("outside"))
        try: rec["valid"],rec["invalid"]=[int(v) for v in d["sum_config"]["data"]["datasets"][0]["data"][:2]]
        except Exception: rec["valid"]=rec["invalid"]=None
        lists=[0]*18
        for l in d.get("table_data") or []:
            i=int(l["count_number"])-1
            if 0<=i<18: lists[i]=num(l["won_number"])
        rec["lists"]=lists
        alerts=list(old.get("alerts") or []); zh=list(old.get("zap_history") or [])
        if old.get("processed") and not rec["processed"]:
            rec.update({x:old.get(x) for x in ("processed","voters","out","valid","invalid","lists")})
        elif old.get("processed") and rec["processed"]:
            ch=[x for x in ("voters","out","valid","invalid","lists") if old.get(x)!=rec.get(x)]
            if ch: alerts.append(dict(type="rezultat",at=t,detail="RIK promenio: "+", ".join(ch),before={x:old.get(x) for x in ch}))
        m=re.search(r"href='([^']+)'",d.get("minute_from_election_station") or "")
        if m:
            link=m.group(1); b=pdf(link)
            if b:
                sha=hashlib.sha256(b).hexdigest()
                last=zh[-1] if zh else None
                if not last or last["sha"]!=sha:
                    fn="bm%02d_%s.pdf"%(n,sha[:10]); open(W+"/upload/"+fn,"wb").write(b)
                    os.makedirs(W+"/img",exist_ok=True); subprocess.run(["pdftoppm","-r","110","-gray","-png","-f","1","-l","2",W+"/upload/"+fn,W+"/img/"+fn[:-4]])
                    zh.append(dict(link=R+link,sha=sha,file=fn,asset=None,at=t)); uploads.append(fn)
                    if last: alerts.append(dict(type="zapisnik",at=t,detail="Zapisnik na RIK-u je zamenjen novim fajlom"))
        rec["at"]=old.get("at") or (t if rec.get("processed") else None)
        rec["zap_history"]=zh; rec["alerts"]=alerts; rec["status"]=old.get("status")
        bm[k]=rec
    meta=dict(checked=t,processed=sum(1 for v in bm.values() if v["processed"]),stations=len(st))
    json.dump(dict(meta=meta,bm=bm),open(W+"/new.json","w"),ensure_ascii=False)
    open(W+"/upload.txt","w").write("\n".join(W+"/upload/"+f for f in uploads))
    open(W+"/read.txt","w").write("\n".join(sorted(W+"/img/"+f for f in os.listdir(W+"/img")) if os.path.isdir(W+"/img") else ""))
    print(json.dumps(meta),"| za upload:",len(uploads),"fajlova (spisak u /tmp/zj/upload.txt)")

def attach(mapf,statf="-"):
    doc=json.load(open(W+"/new.json")); mp=json.load(open(mapf)) if mapf!="-" else {}
    stt=json.load(open(statf)) if statf!="-" and os.path.exists(statf) else {}
    t=doc["meta"]["checked"]
    for k,st in stt.items():
        v=doc["bm"].get(k)
        if not v or not isinstance(st,dict): continue
        v["status"]=dict(oboreno=bool(st.get("oboreno")),primedbe=st.get("primedbe") or None,napomena=st.get("napomena") or None,at=t)
        if st.get("oboreno"): v["alerts"].append(dict(type="oboreno",at=t,detail=st.get("napomena") or "Prema zapisniku glasanje na BM nije regularno / poništeno"))
        elif st.get("primedbe"): v["alerts"].append(dict(type="primedbe",at=t,detail=st.get("primedbe")))
    mp={os.path.basename(k):v for k,v in mp.items()}
    for v in doc["bm"].values():
        for z in v["zap_history"]:
            if not z.get("asset") and z["file"] in mp: z["asset"]=mp[z["file"]]
    json.dump(doc,open(W+"/doc.json","w"),ensure_ascii=False)
    miss=[z["file"] for v in doc["bm"].values() for z in v["zap_history"] if not z.get("asset")]
    print("doc spreman: /tmp/zj/doc.json; bez sacuvane kopije:",len(miss))

if sys.argv[1]=="fetch": fetch(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else "680072",int(sys.argv[4]) if len(sys.argv)>4 else 99)
else: attach(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else "-")
