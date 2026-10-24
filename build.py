#!/usr/bin/env python3
"""Free Art Prints site generator.
  python3 build.py fetch <slug>   # fetch real Met Open Access data for a topic -> data/<slug>.json
  python3 build.py next           # fetch the next topic in topics.json that has no data yet
  python3 build.py build          # render all fetched topics + static pages into site/
  python3 build.py payload [msg]  # write push_payload.json (all site/ files) for GitHub push_files
"""
import json, sys, os, re, io, time, urllib.request, urllib.parse, html, datetime
from PIL import ImageFile
ROOT=os.path.dirname(os.path.abspath(__file__)); SITE=os.path.join(ROOT,"site")
BASE="https://yoloboydelis.github.io"; NAME="Free Art Prints"
API="https://collectionapi.metmuseum.org/public/collection/v1"
UA={"User-Agent":"free-art-prints-site/1.0 (+%s)"%BASE}
def get(url,headers=None,raw=False):
    for i in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={**UA,**(headers or {})}),timeout=30); d=r.read()
            return d if raw else json.loads(d)
        except Exception as e:
            err=e; time.sleep(2)
    raise err
def img_size(url):
    p=ImageFile.Parser(); off=0
    while off<4_000_000:
        try: d=get(url,{"Range":"bytes=%d-%d"%(off,off+65535)},raw=True)
        except Exception: return None
        if not d: return None
        p.feed(d)
        if p.image: return p.image.size
        if len(d)<65536: return None
        off+=len(d)
    return None
def topics(): return json.load(open(os.path.join(ROOT,"topics.json")))
def matches(o,rule):
    if not rule: return True
    for part in rule.split("|"):
        k,v=part.split("~"); 
        if v in (o.get(k) or ""): return True
    return False
def fetch(slug,limit=24):
    t=[x for x in topics() if x["slug"]==slug][0]
    q={"isPublicDomain":"true","hasImages":"true","limit":"120",**t["params"]}
    ids=get(API+".1/search?"+urllib.parse.urlencode(q)).get("objectIDs") or []
    out=[]
    for oid in ids:
        if len(out)>=limit: break
        try: o=get("%s/objects/%d"%(API,oid))
        except Exception: continue
        if not o.get("isPublicDomain") or not o.get("primaryImage") or not matches(o,t.get("match")) or (t.get("exclude") and matches(o,t["exclude"])): continue
        sz=img_size(o["primaryImage"])
        if not sz: continue
        out.append({k:o.get(k) for k in ["objectID","title","artistDisplayName","objectDate","medium","department","primaryImage","primaryImageSmall","objectURL","creditLine"]}|{"w":sz[0],"h":sz[1]})
        print(" ",oid,o["title"][:50],sz,flush=True); time.sleep(0.2)
    json.dump({"slug":slug,"fetched":datetime.date.today().isoformat(),"source":"The Metropolitan Museum of Art Open Access API","works":out},open(os.path.join(ROOT,"data",slug+".json"),"w"),indent=1)
    print(slug,len(out),"works")
e=html.escape
def inch(px,dpi): return px/dpi
def size_str(w,h,dpi): return "%.0f × %.0f cm (%.1f × %.1f in)"%(w/dpi*2.54,h/dpi*2.54,w/dpi,h/dpi)
def biggest_paper(w,h,dpi):
    papers=[("A0",841,1189),("A1",594,841),("A2",420,594),("A3",297,420),("A4",210,297),("A5",148,210)]
    a,b=sorted([w/dpi*25.4,h/dpi*25.4])
    for n,x,y in papers:
        if a>=x and b>=y: return n
    return "smaller than A5"
CSS="""*{box-sizing:border-box}body{margin:0;font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#222;background:#faf8f4}a{color:#7a3e12}header,footer{background:#222;color:#eee}header a,footer a{color:#f5d7a1;text-decoration:none;margin-right:1em}.wrap{max-width:1100px;margin:auto;padding:1em}h1{line-height:1.2}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1.2em}.card{background:#fff;border:1px solid #e6e0d6;border-radius:8px;overflow:hidden}.card img{width:100%;height:260px;object-fit:contain;background:#f0ece4}.card div{padding:.8em;font-size:.92em}.card h3{font-size:1em;margin:.2em 0}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:.4em;text-align:left}.note{background:#fff7e6;border-left:4px solid #e0a040;padding:.8em 1em}input{padding:.5em;font-size:1em;width:9em}.out{font-size:1.1em;font-weight:600}.shops{margin:1.2em 0}.shop-ctas{display:flex;flex-wrap:wrap;gap:.6em;margin:1em 0}.cta{display:inline-block;background:#7a3e12;color:#fff!important;padding:.55em 1em;border-radius:6px;text-decoration:none;font-weight:600}.cta:hover{background:#5c2e0c}.disc{font-size:.9em;opacity:.9}"""
def page(path,title,desc,body):
    url=BASE+"/"+path.replace("index.html","")
    nav='<a href="/">Home</a><a href="/print-size-calculator/">Print size calculator</a><a href="/licensing/">Licensing</a><a href="/about/">About</a>'
    doc=f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><link rel="stylesheet" href="/style.css"></head><body><header><div class="wrap"><strong><a href="/">{NAME}</a></strong> {nav}</div></header><main class="wrap">{body}</main><footer><div class="wrap"><p>Images are public domain (CC0) and hotlinked from the museums that hold them. {NAME} is an independent site, not affiliated with any museum. <a href="/licensing/">Sources &amp; licensing</a> · <a href="/about/#disclosure">Affiliate disclosure</a> · <a href="/sitemap.xml">Sitemap</a></p></div></footer></body></html>"""
    fp=os.path.join(SITE,path); os.makedirs(os.path.dirname(fp),exist_ok=True); open(fp,"w").write(doc); return url
WHERE="""<h2>Where to print</h2>
<p>Download the full-resolution file from the museum link, then upload it to a print shop. Pick a size at or below the <b>150 DPI</b> figure for posters viewed from a metre away; use the <b>300 DPI</b> size for sharp close viewing.</p>
<div class="shops note">
<p><b>Recommended print path (Belgium / Netherlands)</b></p>
<ol>
<li>Download the museum file (link on each card).</li>
<li>Upload it to a poster printer at or below the max size shown above.</li>
<li>Order a matching frame if you want it wall-ready.</li>
</ol>
<p class="shop-ctas">
<a class="cta" href="https://www.bol.com/nl/nl/l/posters/" rel="noopener sponsored">Browse posters on bol.com</a>
<a class="cta" href="https://www.bol.com/nl/nl/l/fotolijsten/" rel="noopener sponsored">Browse frames on bol.com</a>
<a class="cta" href="https://desenio.com/" rel="noopener sponsored">Ready-made prints at Desenio</a>
<a class="cta" href="https://www.etsy.com/search?q=custom%20poster%20print" rel="noopener sponsored">Custom poster print on Etsy</a>
</p>
<p class="disc">Disclosure: some shop links above may become affiliate links once programmes approve this site. Today they go straight to the shops with no tracking ID. We may earn a commission if you buy through an approved affiliate link — at no extra cost to you. See <a href="/about/#disclosure">About · Disclosure</a>.</p>
<!-- AFFILIATE_PLACEHOLDERS
  Replace the hrefs above after approval:
  BOL_POSTERS= partner.bol.com click URL for posters category
  BOL_FRAMES= partner.bol.com click URL for frames/lijsten
  DESENIO= CJ deep link
  ETSY= Rakuten / Etsy Affiliates deep link
-->
</div>"""
def build():
    import shutil; shutil.rmtree(SITE,ignore_errors=True); os.makedirs(SITE)
    open(os.path.join(SITE,"style.css"),"w").write(CSS); open(os.path.join(SITE,".nojekyll"),"w").write("")
    urls=[]; hubs=[]
    for t in topics():
        f=os.path.join(ROOT,"data",t["slug"]+".json")
        if not os.path.exists(f): continue
        d=json.load(open(f)); W=d["works"]
        if not W: continue
        cards="".join(f"""<article class="card"><a href="{e(w['objectURL'])}" rel="noopener"><img src="{e(w['primaryImageSmall'] or w['primaryImage'])}" alt="{e(w['title'])}{' by '+e(w['artistDisplayName']) if w['artistDisplayName'] else ''}{', '+e(w['objectDate']) if w['objectDate'] else ''}" loading="lazy"></a><div><h3>{e(w['title'])}</h3><p>{e(w['artistDisplayName'] or 'Unknown artist')}{', '+e(w['objectDate']) if w['objectDate'] else ''}<br>{e(w['medium'] or '')}</p><p><b>File:</b> {w['w']:,} × {w['h']:,} px<br><b>300 DPI:</b> {size_str(w['w'],w['h'],300)} (fits {biggest_paper(w['w'],w['h'],300)})<br><b>150 DPI:</b> {size_str(w['w'],w['h'],150)} (fits {biggest_paper(w['w'],w['h'],150)})</p><p><a href="{e(w['primaryImage'])}" rel="noopener">Full-resolution file</a> · <a href="{e(w['objectURL'])}" rel="noopener">Museum page</a></p></div></article>""" for w in W)
        big=max(W,key=lambda w:w['w']*w['h'])
        body=f"""<h1>{e(t['h1'])}</h1><p>{e(t['intro'])}</p><p class="note">{len(W)} works listed. Pixel sizes were measured from the museum's full-resolution files on {d['fetched']}. Largest file here: <i>{e(big['title'])}</i> at {big['w']:,} × {big['h']:,} px. Print sizes: 300 DPI = gallery-sharp, 150 DPI = fine for posters viewed from a metre away. <a href="/print-size-calculator/">Check any image</a>.</p><div class="grid">{cards}</div>{WHERE}<p>Source: {e(d['source'])}, <a href="https://www.metmuseum.org/policies/image-resources">Open Access (CC0)</a>.</p>"""
        desc=f"{len(W)} public-domain {t['title'].replace('Free ','').lower()} from The Met, free to download and print, with real file sizes and maximum print sizes."
        urls.append(page(t["slug"]+"/index.html",f"{t['title']}: {len(W)} Public-Domain Works to Download & Print",desc[:158],body)); hubs.append((t,len(W),W[0]))
    hl="".join(f'<article class="card"><a href="/{t["slug"]}/"><img src="{e(w["primaryImageSmall"])}" alt="{e(w["title"])}" loading="lazy"></a><div><h3><a href="/{t["slug"]}/">{e(t["title"])}</a></h3><p>{n} works with print sizes</p></div></article>' for t,n,w in hubs)
    urls.insert(0,page("index.html",f"{NAME}: Free Public-Domain Museum Art to Download and Print","Free, high-resolution public-domain art from museum open-access collections, with the real maximum print size of every file.",f"""<h1>Free museum art you can actually print</h1><p>Museums like The Met, the Art Institute of Chicago and the Rijksmuseum have released hundreds of thousands of public-domain images for anyone to use. The hard part is knowing which files are big enough to print well. Every work listed here shows the true pixel size of the museum's file and the largest print you can make from it.</p><div class="grid">{hl}</div><p><a href="/print-size-calculator/">Print size calculator</a> · <a href="/licensing/">Is it really free to use?</a></p>"""))
    urls.append(page("print-size-calculator/index.html","Print Size Calculator: Pixels to Max Print Size (300 & 150 DPI)","Enter an image's width and height in pixels to see the largest print size at 300 and 150 DPI, in cm and inches, plus the biggest A-paper size it fits.","""<h1>Print size calculator</h1><p>Enter the image size in pixels.</p><p><label>Width (px) <input id="w" type="number" value="4000"></label> <label>Height (px) <input id="h" type="number" value="5000"></label></p><table><tr><th>Quality</th><th>Max print size</th><th>Fits paper</th></tr><tr><td>300 DPI (sharp, close viewing)</td><td class="out" id="o300"></td><td id="p300"></td></tr><tr><td>200 DPI (good)</td><td class="out" id="o200"></td><td id="p200"></td></tr><tr><td>150 DPI (posters)</td><td class="out" id="o150"></td><td id="p150"></td></tr></table><p>Formula: print size in inches = pixels ÷ DPI; × 2.54 for cm.</p><script>const P=[["A0",841,1189],["A1",594,841],["A2",420,594],["A3",297,420],["A4",210,297],["A5",148,210]];function c(){const w=+document.getElementById('w').value,h=+document.getElementById('h').value;for(const d of[300,200,150]){const a=w/d,b=h/d;document.getElementById('o'+d).textContent=(a*2.54).toFixed(0)+' × '+(b*2.54).toFixed(0)+' cm ('+a.toFixed(1)+' × '+b.toFixed(1)+' in)';const[s,l]=[a,b].map(x=>x*25.4).sort((x,y)=>x-y);const f=P.find(p=>s>=p[1]&&l>=p[2]);document.getElementById('p'+d).textContent=f?f[0]:'smaller than A5'}}document.querySelectorAll('input').forEach(i=>i.oninput=c);c()</script>"""+WHERE))
    urls.append(page("licensing/index.html","Licensing & Sources: Is Public-Domain Museum Art Free to Print?","Where the images on Free Art Prints come from and how The Met, Art Institute of Chicago and Rijksmuseum open-access licences (CC0 / public domain) work.","""<h1>Licensing and sources</h1><p>Every image on this site is hotlinked from a museum that released it as public domain. We do not host or alter the files.</p><h2>The Metropolitan Museum of Art</h2><p>Images marked public domain in The Met's <a href="https://www.metmuseum.org/policies/image-resources">Open Access</a> programme are released under <a href="https://creativecommons.org/publicdomain/zero/1.0/">Creative Commons Zero (CC0)</a>: you may copy, modify and use them, including commercially, without permission. Data comes from the <a href="https://metmuseum.github.io/">Met Collection API</a>.</p><h2>Art Institute of Chicago</h2><p>Public-domain works in the <a href="https://www.artic.edu/open-access/open-access-images">Art Institute of Chicago's open access</a> collection are published under CC0.</p><h2>Rijksmuseum</h2><p>The <a href="https://www.rijksmuseum.nl/en/research/conduct-research/data">Rijksmuseum</a> makes public-domain images in its collection freely available for reuse.</p><h2>Things to check</h2><ul><li>Only works flagged public domain by the museum are listed.</li><li>Museum names and logos are trademarks; don't imply endorsement.</li><li>Laws vary by country; check the museum's own page before commercial use.</li></ul><h2 id="disclosure">Affiliate disclosure</h2><p>Links to print shops and framing retailers may be affiliate links. See the full note on the <a href="/about/#disclosure">About</a> page.</p>"""))
    urls.append(page("about/index.html","About Free Art Prints","Free Art Prints lists public-domain museum art with real file sizes and print sizes so you can decorate your walls for the cost of printing.","""<h1>About</h1><p>Free Art Prints is an independent guide to public-domain art from museum open-access collections. For each work we measure the museum's full-resolution file and calculate how large you can print it, so you don't pay for a blurry poster.</p><p>All data comes directly from museum APIs; nothing is invented. Images stay on the museums' servers.</p><h2 id="disclosure">Affiliate disclosure</h2><p>This site may earn a commission when you buy frames, posters or print services through links marked as affiliate or sponsored. That does not change the price you pay. We only recommend print paths that match the file sizes we publish.</p><p>Until programmes approve this site, shop buttons may link directly to retailers with no tracking. When tracking links are live, they will stay labelled and this disclosure will remain.</p><p>Free Art Prints is not affiliated with The Met, the Rijksmuseum, the Art Institute of Chicago, bol.com, Desenio, Etsy or any other retailer.</p>"""))
    today=datetime.date.today().isoformat()
    open(os.path.join(SITE,"sitemap.xml"),"w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)+"</urlset>\n")
    open(os.path.join(SITE,"robots.txt"),"w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    print("built",len(urls),"pages")
def payload(msg):
    files=[]
    for dp,_,fs in os.walk(SITE):
        for f in fs:
            p=os.path.join(dp,f); files.append({"path":os.path.relpath(p,SITE),"content":open(p).read()})
    json.dump({"owner":"yoloboydelis","repo":"yoloboydelis.github.io","branch":"main","message":msg,"files":files},open(os.path.join(ROOT,"push_payload.json"),"w"))
    print("payload",len(files),"files")
if __name__=="__main__":
    c=sys.argv[1]
    if c=="fetch": fetch(sys.argv[2])
    elif c=="next":
        n=[t for t in topics() if not os.path.exists(os.path.join(ROOT,"data",t["slug"]+".json"))]
        if not n: print("no topics left; add one to topics.json"); sys.exit(1)
        fetch(n[0]["slug"]); print("NEW",n[0]["slug"])
    elif c=="build": build()
    elif c=="payload": payload(" ".join(sys.argv[2:]) or "Update site")
