#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, random, re
from dataclasses import dataclass

KEYWORDS={"and","break","do","else","elseif","end","false","for","function","if","in","local","nil","not","or","repeat","return","then","true","until","while","continue","type","export","typeof","as"}
PROTECTED=KEYWORDS|{"_G","shared","game","workspace","script","Enum","Instance","Vector2","Vector3","CFrame","Color3","BrickColor","UDim","UDim2","TweenInfo","Players","RunService","ReplicatedStorage","ServerStorage","ServerScriptService","StarterGui","StarterPlayer","Lighting","SoundService","UserInputService","ContextActionService","HttpService","TweenService","CollectionService","ReplicatedFirst","Teams","MarketplaceService","TeleportService","Debris","GuiService","task","LocalPlayer","Character","Humanoid","Parent","Name","Value","Position","Size","Color","Transparency","Visible","Enabled","Text","MouseButton1Click","MouseButton1Down","MouseButton1Up","InputBegan","InputEnded","Connect","WaitForChild","FindFirstChild","FindFirstChildOfClass","FindFirstChildWhichIsA","GetChildren","GetDescendants","GetService","Destroy","Clone","FireServer","InvokeServer","OnClientEvent","OnClientInvoke","OnServerEvent","OnServerInvoke","require","assert","error","pcall","xpcall","print","warn","pairs","ipairs","next","select","unpack","rawget","rawset","rawequal","rawlen","setmetatable","getmetatable","tostring","tonumber","type","typeof","string","table","math","bit32","utf8","coroutine","os","debug"}

@dataclass
class Tok:
    kind:str
    text:str
    pos:int

def tokenize(s):
    out=[]; i=0; n=len(s)
    while i<n:
        c=s[i]
        if c.isspace():
            j=i+1
            while j<n and s[j].isspace(): j+=1
            out.append(Tok("ws",s[i:j],i)); i=j; continue
        if s.startswith("--",i):
            if i+2<n and s[i+2]=="[":
                m=re.match(r"\[(=*)\[",s[i+2:])
                if m:
                    close="]"+m.group(1)+"]"; start=i+2+len(m.group(0)); k=s.find(close,start)
                    j=n if k<0 else k+len(close)
                    out.append(Tok("comment",s[i:j],i)); i=j; continue
            j=s.find("\n",i); j=n if j<0 else j
            out.append(Tok("comment",s[i:j],i)); i=j; continue
        if c in "'\"":
            q=c; j=i+1; esc=False
            while j<n:
                ch=s[j]
                if esc: esc=False
                elif ch=="\\": esc=True
                elif ch==q: j+=1; break
                j+=1
            out.append(Tok("string",s[i:j],i)); i=j; continue
        if c=="[":
            m=re.match(r"\[(=*)\[",s[i:])
            if m:
                close="]"+m.group(1)+"]"; start=i+len(m.group(0)); k=s.find(close,start)
                if k>=0:
                    j=k+len(close); out.append(Tok("longstring",s[i:j],i)); i=j; continue
        if re.match(r"[A-Za-z_]",c):
            j=i+1
            while j<n and re.match(r"[A-Za-z0-9_]",s[j]): j+=1
            out.append(Tok("id",s[i:j],i)); i=j; continue
        if c.isdigit():
            j=i+1
            while j<n and re.match(r"[A-Za-z0-9._]",s[j]): j+=1
            out.append(Tok("number",s[i:j],i)); i=j; continue
        matched=False
        for op in ("...","//","==","~=","<=",">=","::","->","+=","-=","*=","/=","%=","^=",".."):
            if s.startswith(op,i):
                out.append(Tok("sym",op,i)); i+=len(op); matched=True; break
        if not matched:
            out.append(Tok("sym",c,i)); i+=1
    return out

def parse_string(raw):
    if len(raw)<2 or raw[0] not in "'\"" or raw[-1]!=raw[0]: return None
    b=raw[1:-1]; out=[]; i=0
    mp={"a":"\a","b":"\b","f":"\f","n":"\n","r":"\r","t":"\t","v":"\v","\\":"\\","'":"'","\"":"\""}
    while i<len(b):
        if b[i]!="\\": out.append(b[i]); i+=1; continue
        i+=1
        if i>=len(b): out.append("\\"); break
        c=b[i]; i+=1
        if c in mp: out.append(mp[c])
        elif c=="z":
            while i<len(b) and b[i].isspace(): i+=1
        elif c=="x" and i+2<=len(b):
            try: out.append(chr(int(b[i:i+2],16))); i+=2
            except: out.append("\\x")
        elif c.isdigit():
            j=i
            while j<len(b) and j<i+2 and b[j].isdigit(): j+=1
            try: out.append(chr(int(c+b[i:j]))); i=j
            except: out.append("\\"+c)
        else: out.append("\\"+c)
    return "".join(out)

def enc(s):
    return "__L("+repr(base64.b64encode(s.encode()).decode())+")"

def newname(i):
    abc="abcdefghijklmnopqrstuvwxyz"; x=i; out=""
    while True:
        out=abc[x%26]+out; x=x//26-1
        if x<0: break
    return "__"+out+"_"+''.join(random.choice("0123456789abcdef") for _ in range(5))

def prev_sig(t,i):
    i-=1
    while i>=0 and t[i].kind in ("ws","comment"): i-=1
    return t[i] if i>=0 else None

def next_sig(t,i):
    i+=1
    while i<len(t) and t[i].kind in ("ws","comment"): i+=1
    return t[i] if i<len(t) else None

def collect(t):
    targets=[]; i=0
    while i<len(t):
        if t[i].kind=="id" and t[i].text=="local":
            j=i+1
            while j<len(t) and t[j].kind in ("ws","comment"): j+=1
            if j<len(t) and t[j].text=="function":
                j+=1
                while j<len(t) and t[j].kind in ("ws","comment"): j+=1
                if j<len(t) and t[j].kind=="id": targets.append((j,t[j].text))
                while j<len(t) and t[j].text!="(": j+=1
                if j<len(t):
                    depth=0; k=j
                    while k<len(t):
                        if t[k].text=="(": depth+=1
                        elif t[k].text==")":
                            depth-=1
                            if depth==0: break
                        elif depth==1 and t[k].kind=="id":
                            p=prev_sig(t,k); q=next_sig(t,k)
                            if (p is None or p.text in ("(",",")) and (q is None or q.text in (",",")")):
                                targets.append((k,t[k].text))
                        k+=1
                    i=k
            else:
                while j<len(t):
                    if t[j].kind=="id":
                        targets.append((j,t[j].text))
                        q=next_sig(t,j)
                        if q and q.text==",": j=t.index(q,j)+1; continue
                        break
                    if t[j].text in ("=",";"): break
                    j+=1
        i+=1
    return targets

def transform(t):
    t=[x for x in t if x.kind!="comment"]
    mapping={}; c=0
    for _,name in collect(t):
        if name not in PROTECTED and name not in mapping:
            mapping[name]=newname(c); c+=1
    out=[]
    for i,x in enumerate(t):
        if x.kind=="string":
            v=parse_string(x.text)
            out.append(Tok("raw",enc(v) if v is not None else x.text,x.pos)); continue
        if x.kind=="number" and x.text.isdigit() and int(x.text) not in (0,1,2):
            v=int(x.text); k=random.randint(3,17); out.append(Tok("raw",f"({v+k}-{k})",x.pos)); continue
        if x.kind=="id" and x.text in mapping:
            p=prev_sig(t,i)
            if not (p and p.text in (".",":")):
                out.append(Tok("raw",mapping[x.text],x.pos)); continue
        out.append(x)
    return out,mapping

def render(t):
    out=[]
    for x in t:
        if x.kind=="ws":
            if out and out[-1] and out[-1][-1:].isalnum(): out.append(" ")
        else: out.append(x.text)
    return "".join(out)

RUNTIME="""-- Luau-Obfuscator runtime string decoder
local __A="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local function __L(s)
 local o,n,b={},0,0
 for i=1,#s do
  local c=s:sub(i,i)
  if c~="=" then
   local p=__A:find(c,1,true)
   if p then
    n=n*64+p-1;b=b+6
    if b>=8 then b=b-8;o[#o+1]=string.char(math.floor(n/2^b)%256);n=n%2^b end
   end
  end
 end
 return table.concat(o)
end
"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("-o","--output")
    a=ap.parse_args()
    src=open(a.input,encoding="utf-8").read()
    tokens=tokenize(src); out,mapping=transform(tokens)
    result=RUNTIME+"\n"+render(out)+"\n"
    target=a.output or re.sub(r"\.(lua|luau)$","_protected.luau",a.input,flags=re.I)
    open(target,"w",encoding="utf-8").write(result)
    print("SUCCESS"); print("Input:",len(src),"bytes"); print("Output:",len(result),"bytes"); print("Renamed locals:",len(mapping)); print("Output:",target)

if __name__=="__main__": main()
