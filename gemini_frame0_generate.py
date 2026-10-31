"""Generate one real Frame 0 from canonical L5 with Gemini Image API.

Fail closed: do not overwrite source, no video render, no sheet writes.
"""
import argparse,base64,hashlib,json,os,sys,urllib.request
from pathlib import Path
from gemini_idea_review import api,write

L5_ID="1NHaUGJYqbZFsA6lQ2_9Y7QEAa7hUR1ly"
L5_URL="https://drive.google.com/uc?export=download&id="+L5_ID
PROMPT="""Create a single vertical 9:16 opening keyframe for a delightful cinematic
3D-animated family comedy short. USE THE ATTACHED IMAGE AS THE UNIQUE CANONICAL
REFERENCE FOR ALL THREE CHARACTER IDENTITIES. Preserve their exact 3D character
design, faces, proportions, hair, wardrobes and colors from the reference:
mother LEFT (terracotta/cream), father RIGHT (sage top/jeans),
two-year-old daughter CENTER (peach dress, two pigtails).
Comfortable cozy home entry/living-room environment, warm morning daylight,
child seated on a low sofa/bench with her feet forward, mother gently
offering to help put on shoes, father responding attentively to toddler.
A SINGLE pair of child shoes: no shoe duplicates, no floating shoelaces,
no extra limbs, no extra people. Full waist-to-feet framing with all
three faces visible, natural expressive posing and charming comedic tension.
No text, captions, watermark, signage, or logo. High quality clean image.
Do NOT copy clothing or identity from any source video. This is the static
first frame BEFORE dialogue starts, not a collage, not a storyboard sheet."""
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--output-dir",required=True)
 p.add_argument("--model",default=os.environ.get("WL_GEMINI_IMAGE_MODEL","gemini-3.1-flash-image-preview"))
 a=p.parse_args()
 if not a.model.startswith("gemini-") or "/" in a.model:raise ValueError("Invalid model")
 root=Path(a.output_dir);root.mkdir(parents=True,exist_ok=True)
 original=root/"L5_canonical.png"
 if not original.exists():
  with urllib.request.urlopen(urllib.request.Request(L5_URL,headers={"User-Agent":"Mozilla/5.0"}),timeout=40) as r:
   data=r.read(12_000_000)
  if not data.startswith(b"\x89PNG\r\n\x1a\n"):raise ValueError("L5 is not PNG")
  original.write_bytes(data)
 image=original.read_bytes()
 if not image.startswith(b"\x89PNG\r\n\x1a\n"):raise ValueError("L5 invalid")
 digest=hashlib.sha256(image).hexdigest()
 target=root/"frame0.png";pending=root/"frame0.pending.json";response=root/"frame0.response.json"
 if target.exists():print(json.dumps({"status":"exists","file":str(target)}));return
 if pending.exists() or response.exists():raise ValueError("Pending or response exists: reconcile before retry")
 write(pending,{"model":a.model,"l5_sha256":digest,"reference_row":5})
 raw=api("models/"+a.model+":generateContent",
  {"contents":[{"role":"user","parts":[{"text":PROMPT},{"inlineData":{"mimeType":"image/png","data":base64.b64encode(image).decode("ascii")}}]}],
   "generationConfig":{"responseModalities":["TEXT","IMAGE"],"imageConfig":{"aspectRatio":"9:16"}}},
  error_log=root/"frame0.errors.json")
 # Preserve response evidence before inspecting output. Raw inline images are
 # stored in a local ignored runtime file; never print or push their base64.
 write(response,raw)
 images=[x["inlineData"] for c in raw.get("candidates",[]) for x in c.get("content",{}).get("parts",[]) if "inlineData" in x]
 if len(images)!=1:raise ValueError("Expected one image in provider response")
 data=base64.b64decode(images[0]["data"],validate=True)
 if not data.startswith(b"\x89PNG\r\n\x1a\n"):raise ValueError("Generated image is not PNG")
 target.write_bytes(data)
 write(root/"frame0.evidence.json",{"provider":"Gemini","model":a.model,"response_id":raw.get("responseId"),
  "canonical_reference":"L5","identity_row":5,"reference_sha256":digest,
  "generated_sha256":hashlib.sha256(data).hexdigest(),"qc_status":"pending_visual_review"})
 pending.unlink(missing_ok=True)
 print(json.dumps({"status":"generated","file":str(target),"bytes":len(data),"qc":"pending_visual_review"}))
if __name__=="__main__":
 try:main()
 except Exception as e:print("Frame 0 BLOCKED: "+type(e).__name__+" "+str(e)[:300],file=sys.stderr);sys.exit(2)
