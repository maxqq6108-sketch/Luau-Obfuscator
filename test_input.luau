local Players = game:GetService("Players")
local function hello(value)
    local message = "Hello " .. value
    print(message, 12345)
end
local player = Players.LocalPlayer
if player then
    hello(player.Name)
end
