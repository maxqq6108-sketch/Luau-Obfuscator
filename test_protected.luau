-- Luau-Obfuscator runtime string decoder
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

local Players =game:GetService(__L('UGxheWVycw=='))local function __a_c2379(__b_1dfff)local __c_3b647 =__L('SGVsbG8g')..__b_1dfff print(__c_3b647,(12358-13))end local __d_73da3 =Players.LocalPlayer if __d_73da3 then __a_c2379(__d_73da3.Name)end 
