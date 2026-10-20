# Provera rešenja o biračkim odborima (Žabari, izbori 25.10.2026).
#   python3 odbori_check.py <known.json|->   -> /tmp/oc/all.json (svi dokumenti), /tmp/oc/new.json (novi), PDF i PNG strane u /tmp/oc/new/
import json,subprocess,time,sys,os,re,urllib.parse,hashlib
W="/tmp/oc"; os.makedirs(W+"/new",exist_ok=True)
R="https://www.rik.parlament.gov.rs"
def page(p,dt):
    for a in range(6):
        r=subprocess.run(["curl","-sS","--http1.1","--max-time","90","-G",R+"/get-additional-documents",
            "--data-urlencode",f"page={p}","--data-urlencode",f"filters[document-type]={dt}",
            "--data-urlencode","filters[election-round]=680072","--data-urlencode","filters[municipality-id]=84",
            "--data-urlencode","filters[election_station]=0","--data-urlencode","filters[additional-document]=0",
            "--data-urlencode","order=0","--data-urlencode","sort=0","--data-urlencode","election_type=-1"],capture_output=True,text=True)
        try:
            d=json.loads(r.stdout); assert "records" in d; return d
        except Exception: time.sleep(3+a*4)
    raise RuntimeError("RIK nedostupan")
docs=[]
for dt in (4,1):
    p=1
    while True:
        d=page(p,dt); recs=d["records"]
        for x in recs:
            for l in re.findall(r'href="([^"]+)"'," ".join(x.get("extfiles_link") or [])):
                st=x.get("election_station_title") or ""
                m=re.match(r"\s*(\d+)",st)
                docs.append(dict(id=hashlib.md5(l.encode()).hexdigest()[:12],type=dt,link=R+l,bm=int(m.group(1)) if m else None,
                    name=re.sub(r"\s+"," ",x.get("document_name") or "").strip(),
                    kind=re.sub(r"<[^>]+>","",x.get("election_board_decision") or x.get("decision_type") or "").strip(),ts=x.get("datetime")))
        if len(recs)<10 or p>=60: break
        p+=1
known=set()
if sys.argv[1]!="-" and os.path.exists(sys.argv[1]):
    k=json.load(open(sys.argv[1])); known=set(k.get("known") or [])
new=[d for d in docs if d["id"] not in known]
for d in new:
    fn=f"{W}/new/{d['id']}.pdf"
    subprocess.run(["curl","-sS","--http1.1","--max-time","120","--retry","4","--retry-all-errors","-o",fn,R+urllib.parse.quote(d["link"][len(R):])])
    subprocess.run(["pdftoppm","-r","120","-gray","-png","-f","1","-l","3",fn,f"{W}/new/{d['id']}"])
    d["pdf"]=fn; d["pages"]=sorted(f"{W}/new/"+f for f in os.listdir(W+"/new") if f.startswith(d["id"]) and f.endswith(".png"))
json.dump(docs,open(W+"/all.json","w"),ensure_ascii=False,indent=1)
json.dump(new,open(W+"/new.json","w"),ensure_ascii=False,indent=1)
print("ukupno dokumenata:",len(docs),"| novih:",len(new))
for d in new: print(" -",d["id"],"BM",d["bm"],"|",d["name"][:120],"|",d["kind"][:80])
