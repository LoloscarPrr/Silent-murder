"""Audit official MakeHuman Community CC0 suit pack before importing anything to Blender."""
import sys,os,zipfile,json,hashlib,collections,re
p=sys.argv[1]
out=sys.argv[2]
assert zipfile.is_zipfile(p),"Descarga no es ZIP válido"
archive=zipfile.ZipFile(p)
names=archive.namelist()
assert 10<len(names)<1500,len(names)
assert any("toigo_male_suit" in n.lower() for n in names), "Archivo inesperado, faltan los trajes masculinos"
candidates=[]
for name in names:
    low=name.lower()
    if not low.endswith(".obj") or "male" not in low or "female" in low or "toigo" not in low:continue
    mn=[float('inf')]*3
    mx=[-float('inf')]*3
    count=faces=0
    groups=set()
    materials=set()
    try:
        with archive.open(name) as f:
            for line in f:
                if line.startswith(b"v "):
                    tokens=line.split()
                    if len(tokens)>=4:
                        vec=[float(v) for v in tokens[1:4]]
                        for k in range(3):
                            mn[k]=min(mn[k],vec[k]);mx[k]=max(mx[k],vec[k])
                        count+=1
                elif line.startswith(b"f "):faces+=1
                elif line.startswith(b"g ") or line.startswith(b"o "):groups.add(line.decode("utf8","replace").strip())
                elif line.startswith(b"usemtl "):materials.add(line.decode("utf8","replace").strip())
    except Exception as e:
        raise RuntimeError("No se pudo analizar OBJ "+name) from e
    if count<200 or faces<200:continue
    candidates.append(dict(path=name,vertices=count,faces=faces,
        bounds_min=[round(v,5) for v in mn],bounds_max=[round(v,5) for v in mx],
        dimensions=[round(mx[k]-mn[k],5) for k in range(3)],
        groups=sorted(groups)[:120],materials=sorted(materials)[:100],
        matching_files=[n for n in names if os.path.dirname(n)==os.path.dirname(name)][:70]))
assert candidates,"Ningún traje masculino OBJ adecuado en paquete"
with open(p,"rb") as f:sha=hashlib.sha256(f.read()).hexdigest()
report=dict(archive_source="https://files2.makehumancommunity.org/asset_packs/suits01/suits01_cc0.zip",
archive_sha256=sha,archive_bytes=os.path.getsize(p),
copyright="Margaret Toigo, CC0 per official MakeHuman suits01 asset pack",
all_files=len(names),obj_candidates=candidates,
candidate_count=len(candidates))
os.makedirs(out,exist_ok=True)
with open(os.path.join(out,"AUDITORIA_PAQUETE_TRAJES.json"),"w",encoding="utf8") as f:
    json.dump(report,f,indent=2,ensure_ascii=False)
print(json.dumps({"count":len(candidates),"files":[{"p":a["path"],"v":a["vertices"],"f":a["faces"],"dimensions":a["dimensions"],"groups":a["groups"],"materials":a["materials"]} for a in candidates]},ensure_ascii=False),flush=True)
