# Original Sol Ultra — recovered experiment handoff

Verbatim final reply from session `01a086b4-d6d8-7b21-ae43-54d8999ed130`, timestamp `2026-09-12T05:17:04.830Z`. Retrieved read-only and saved by the current controller. Historical source/results below are not fresh reproduced evidence.

I recovered the original experiment from the local Codex transcript database. The `/tmp` scripts and generated artifacts no longer exist, so the transcript is the only durable primary evidence. I did not execute or modify anything.

The source below is **verbatim**, recovered from:

- Thread: `01a086b4-d6d8-7b21-ae43-54d8999ed130`
- Command event: `exec-7d73f20a-427c-46ac-bafc-65905691d5eb`
- Time: 2026-09-10 14:45:40 UTC
- Original path: `/tmp/probe_auth_orthogonal.py`
- Original invocation: `PYTHONPATH=prototypes/nishan_pq .venv/bin/python /tmp/probe_auth_orthogonal.py <strength>`

```python
from pathlib import Path
import hashlib,hmac,math,sys
import numpy as np
import pymupdf as fitz
from PIL import Image
from nishan import tardos,tardos_carrier,watermark,layout_tag,registration
DPI=144;BS=6;M=52500;TAGN=126;REPS=200;STR=float(sys.argv[1] if len(sys.argv)>1 else 2.0)
src=Path('artifacts/nishan/synthetic-source.pdf');out=Path(f'/tmp/nishan-auth-ortho-{STR}');out.mkdir(exist_ok=True)
tsec=hashlib.sha3_256(b'NISHAN Tardos carrier public fixture v1').digest();tctx='synthetic-source/full-tardos-profile-v1'
cfg=tardos.parameters(1000,5,1e-6);bias,code=tardos.generate_keyed(cfg,tsec,'public-benchmark-codebook/v1')
refs,_=watermark.load_pages(src,dpi=DPI);shapes=[p.shape[:2] for p in refs];caps=[(h//BS)*(w//BS) for h,w in shapes];cap=sum(caps)
torder,tori,tpol=tardos_carrier._plan(tsec,tctx,cap,M);tm=tardos_carrier._templates(BS)
def plan(sec,ctx):
 raw=np.unpackbits(np.frombuffer(hmac.new(sec,b'NISHAN-RECIPIENT-AUTH/v1|'+ctx.encode(),hashlib.sha3_256).digest()[:9],dtype=np.uint8));enc=layout_tag.hamming74_encode(raw)
 keys=np.frombuffer(tardos_carrier._prf_bytes(sec,ctx,b'auth-symbol-order',M*8),dtype='<u8');si=np.argsort(keys,kind='stable')[:TAGN*REPS];pos=torder[si];ori=1-tori[si]
 polbits=np.unpackbits(np.frombuffer(tardos_carrier._prf_bytes(sec,ctx,b'auth-polarities',math.ceil(TAGN*REPS/8)),dtype=np.uint8))[:TAGN*REPS];pol=2*polbits.astype(np.int8)-1
 return raw,enc,pos,ori,pol
def add_auth(base,dst,pl):
 raw,enc,pos,ori,pol=pl;payload=np.tile(enc,REPS);blocks=np.zeros((cap,BS,BS),np.float32);blocks[pos]=(2*payload.astype(np.int8)-1)[:,None,None]*pol[:,None,None]*tm[ori]
 pats=[];off=0
 for (h,w),c in zip(shapes,caps):
  rows=h//BS;cols=w//BS;pb=blocks[off:off+c];crop=pb.reshape(rows,cols,BS,BS).transpose(0,2,1,3).reshape(rows*BS,cols*BS);pat=np.zeros((h,w),np.float32);pat[:crop.shape[0],:crop.shape[1]]=crop;pats.append(pat);off+=c
 d=fitz.open(base)
 for p,pat in zip(d,pats):p.insert_image(p.rect,stream=tardos_carrier._transparent_overlay(pat,STR),overlay=True,keep_proportion=False)
 d.save(dst,garbage=0,clean=False,deflate=True);d.close()
def blocks_from(sus):
 sups,_=watermark.load_pages(sus,dpi=DPI);allb=[]
 for ref,sup,(h,w) in zip(refs,sups,shapes):
  sup,_=registration.align_page(ref,sup);res=watermark._luma(sup)-watermark._luma(ref);rows=h//BS;cols=w//BS;allb.append(res[:rows*BS,:cols*BS].reshape(rows,BS,cols,BS).transpose(0,2,1,3).reshape(rows*cols,BS,BS))
 return np.concatenate(allb)
def decode(bb,pl):
 raw,enc,pos,ori,pol=pl;cor=np.sum(bb[pos]*tm[ori]*pol[:,None,None],axis=(1,2)).reshape(REPS,TAGN);maj=(cor.sum(0)>0).astype(np.uint8);dec=layout_tag.hamming74_decode(maj);return np.array_equal(dec.bits,raw),int(np.count_nonzero(maj!=enc)),dec.corrected_blocks,float(np.median(abs(cor.sum(0))))
plans=[];copies=[]
for i in range(5):
 sec=hashlib.sha3_256(f'recipient-secret-{i}'.encode()).digest();ctx=f'doc:session-{i}:row-{i}';pl=plan(sec,ctx);plans.append(pl)
 base=out/f'base-{i}.pdf';dst=out/f'marked-{i}.pdf';tardos_carrier.embed_pdf(src,base,code[i],tsec,tctx,strength=4.0);add_auth(base,dst,pl);copies.append(dst)
print('psnr',[tardos_carrier.measure_pdf_pair(src,x).psnr_db for x in copies])
for count in [1,2,3,5]:
 avg=out/f'avg-{count}.png'; (Image.fromarray(watermark.load_pages(copies[0],dpi=DPI)[0][0]).save(avg) if count==1 else watermark.average_collusion(copies[:count],avg));bb=blocks_from(avg);print('average',count,[decode(bb,plans[i])[:3] for i in range(5)])
 jpg=out/f'avg-{count}-q55.jpg';Image.fromarray(watermark.load_pages(avg,dpi=DPI)[0][0]).save(jpg,'JPEG',quality=55,optimize=True);bb=blocks_from(jpg);print('average-jpeg',count,[decode(bb,plans[i])[:3] for i in range(5)])
# provider knows Tardos row only
print('provider-only',[decode(blocks_from(out/'base-0.pdf'),plans[i])[:3] for i in range(5)])
```

### Exact construction

- Source: `artifacts/nishan/synthetic-source.pdf`
- Rendering: 144 DPI
- Carrier block: 6×6 pixels
- Tardos length: 52,500 symbols
- Tardos parameters: `n=1000`, `c=5`, `ε=10⁻⁶`
- Tardos embedding strength: 4.0
- Recipient-authenticator strengths explored: 2.0, 3.0, 4.0
- Authenticator payload:
  - HMAC-SHA3-256
  - First 9 digest bytes = 72 bits
  - Hamming(7,4) expansion: 72 → 126 encoded bits
  - 200 repetitions
  - 25,200 placements
- Positions were selected from Tardos carrier positions using a recipient-secret PRF.
- Each authenticator used the template orientation orthogonal to the Tardos orientation at that position.
- Extraction was non-blind: it required the original document rendering for image registration and subtraction.

The document context was only:

```python
ctx = f"doc:session-{i}:row-{i}"
```

It did **not** bind a real document hash, ledger record, release hash, recipient public key, actual session UUID or adjudicator identity.

### Secret ownership and verifier inputs

The experiment did not have recipient-controlled secrets:

```python
sec = sha3_256(f"recipient-secret-{i}".encode()).digest()
```

The same script generated and retained:

- The authority Tardos secret
- Every recipient secret
- Every recipient context
- The complete codebook
- The original reference document
- Every marked copy

The verifier needed the original document, authority carrier plan, candidate recipient secret and candidate context. There was no escrow, enrollment protocol, separate adjudicator, public verification or independent key custody.

The carrier was inserted as a full-page transparent image using `page.insert_image(...)`. It was a separate removable PDF image object. Therefore, the experiment did not solve the malicious-distributor or buyer–seller watermarking problem. The September 10 audit was correct on all four points. See [the independent audit](/home/user_end4/MySpace/SIH/research/INDEPENDENT_GOAL_AUDIT_2026-09-10.md:61), [the prior-art boundary](/home/user_end4/MySpace/SIH/research/NISHAN_NOVELTY_AND_PRIOR_ART.md:40), and [the current README limitation](/home/user_end4/MySpace/SIH/prototypes/nishan_pq/README.md:254).

### Exact decision rule

The original decision had two thresholds:

1. Each repeated encoded symbol was decided by whether its summed correlation was greater than zero.
2. After Hamming decoding, all 72 decoded bits had to equal the expected HMAC bits exactly.

There was no decoded-distance tolerance in the original script.

A radius of six was evaluated afterwards from the outputs. It was never implemented or tested as a preregistered acceptance rule. The nominal uniform-tag calculation was:

| Radius | Per-candidate random-match probability | Union bound for 1,000 candidates |
|---:|---:|---:|
| 4 | 2.31×10⁻¹⁶ | 2.31×10⁻¹³ |
| 5 | 3.19×10⁻¹⁵ | 3.19×10⁻¹² |
| 6 | 3.63×10⁻¹⁴ | 3.63×10⁻¹¹ |
| 8 | 2.88×10⁻¹² | 2.88×10⁻⁹ |
| 10 | 1.34×10⁻¹⁰ | 1.34×10⁻⁷ |

Those are ideal Hamming-sphere probabilities. They are not a measured false-accusation bound for this correlated carrier.

### Original transforms

Digital averaging:

```python
watermark.average_collusion(copies[:count], avg)
```

for coalition sizes 2, 3 and 5. A single copy was rendered directly to PNG.

JPEG attack:

```python
Image.fromarray(
    watermark.load_pages(avg, dpi=144)[0][0]
).save(jpg, "JPEG", quality=55, optimize=True)
```

The separate geometry probe used the existing benchmark helpers:

```python
b._synthetic_perspective_photo(src, dst)
b._rotation_attack(src, dst, 2.0)
b._raster_attack(src, dst, scale=.5)
b._raster_attack(src, dst, crop_fraction=.10)
b._raster_attack(src, dst, crop_fraction=.20)
b._raster_attack(src, dst, crop_fraction=.30)
```

Its transcript event is `exec-ae6e29d7-0ce2-4705-819d-823c9ead160f`.

### Exact recovered results

At recipient strength 3.0:

- PSNR: 39.675–39.680 dB.
- Digital average of 1, 2, 3 or 5 copies: every participating recipient passed exact 72-bit matching.
- JPEG Q55 after 1, 2 or 3-copy averaging: participating recipients passed exactly.
- JPEG Q55 after 5-copy averaging:
  - Rows 0, 2 and 4 passed exactly.
  - Rows 1 and 3 failed exact equality.
  - Their decoded 72-bit distances were respectively `0, 1, 0, 4, 0`.

Therefore, “5/5 survived JPEG-Q55” at strength 3 was a post hoc radius-six interpretation. The original exact verifier recovered 3/5.

At strength 4.0:

- PSNR: about 38.579–38.584 dB.
- All five recipients passed exact matching after 5-copy averaging and JPEG Q55.

At strength 2.0:

- PSNR: about 40.771–40.775 dB.
- Five-copy JPEG decoded distances were `12, 7, 10, 8, 6`; none passed exact matching.

Geometry at strength 3:

| Transform | Exact result | Decoded 72-bit distance |
|---|---:|---:|
| Perspective simulation | Fail | 6 |
| Rotation 2° | Pass | 0 |
| Half-scale raster | Pass | 0 |
| Crop 10% | Fail | 1 |
| Crop 20% | Fail | 32 |
| Crop 30% | Fail | 36 |

Earlier descriptions that perspective and 10% crop “survived” relied on the post hoc radius-six interpretation.

### Negative controls actually run

- Five candidate recipient secrets were checked; recipients outside each coalition did not match exactly.
- An authority-only Tardos copy without the recipient overlay was evaluated against all five authenticator plans. None matched exactly. At strength 3, the decoded distances were `46, 39, 34, 36, 32`.
- Strengths 2, 3 and 4 were explored adaptively.
- Rotation, resizing, cropping and simulated perspective were tried after initial results.

These controls were **not** performed:

- A large independently generated innocent roster
- Fresh unseen keys or documents
- Recipient keys generated outside the distributor process
- Independent enrollment or adjudication
- Wrong adjudicator key
- Actual document-hash or ledger-context substitution
- Replay between documents or sessions
- Copying an observed recipient overlay to another document
- Malicious-distributor forgery
- Physical print, scan or camera capture

The “provider-only” test only showed that a PDF carrying the Tardos layer alone did not accidentally decode under five chosen authenticator secrets. It did not show that the provider could not forge the authenticator, because the provider script knew or could regenerate every secret.

### Provenance events

| Event | Evidence |
|---|---|
| `exec-7d73f20a-427c-46ac-bafc-65905691d5eb` | Canonical orthogonal source, initial strength 2 run |
| `exec-47fe7cb2-2fa1-4314-8438-f83f69c51071` | Strength 4 results |
| `exec-3c948227-e87b-4433-9de3-df925437c9a0` | Strength 3 results |
| `exec-6ee4f795-9877-485e-84b8-30faf3ba34e2` | Added decoded-distance reporting |
| `exec-9fcbdaa6-a5da-4da3-89f4-c1c799f3e8db` | Detailed strength 3 results |
| `exec-ae6e29d7-0ce2-4705-819d-823c9ead160f` | Geometry probe and results |
| `exec-103a473f-05f8-4aa5-9ef1-e8d602fc923c` | Nominal Hamming-radius calculations |
| `exec-6babdf98-2026-4a75-b25d-0346ce1e1c4d` | Detailed strength 2 results |
| `exec-a31df399-8354-4ecf-950d-054aec846056` | Later transcript dump of scratch sources |

### What cannot be recovered

The generated PDFs, PNGs, JPEGs and `/tmp` scripts are gone. There are no artifact hashes, raw correlation arrays, JSON result bundles or probe-specific environment lock. The current repository may not contain exactly the module revisions used on September 10, so rerunning this source against today’s frozen release would not constitute exact reproduction without first recovering the matching source snapshot.

No actual recipient enrollment, escrow ciphertext, adjudicator key, recipient signature or independent adjudication ever existed in this experiment.

### Smallest honest isolated reproduction gate

Run this only as a **recipient-contributed corroboration experiment**:

1. Freeze the September 10 implementation and record all code and input hashes.
2. Have two recipient processes independently generate secrets. Bind each tag to the source-document hash, actual release/session ID, Tardos row and recipient public key. Give only encrypted recovery material to a separate adjudicator.
3. Predeclare strength and the exact acceptance rule before observing results. If radius six is chosen, evaluate it against a substantial independently generated innocent roster.
4. Test clean, JPEG-Q55, two-copy averaging, authority-only forgery, wrong context and copied-overlay substitution.
5. Preserve outputs and hashes in a machine-readable evidence bundle.

Passing that gate would demonstrate an independently reproduced orthogonal corroboration channel under those cases. It would not demonstrate a complete asymmetric fingerprinting or malicious-distributor-resistant protocol.

