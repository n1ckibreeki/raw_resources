-- // nickibreeki's HitboxService For Game Development
local RunService = game:GetService("RunService")
local Utilities = script.Parent.Parent:WaitForChild("Utilities")
local Signal = require(Utilities:WaitForChild("Signal"))

local Hitbox = {}
Hitbox.__index = Hitbox

function Hitbox.new(options)
	local self = setmetatable({}, Hitbox)

	self.Options = options or {
		["DebugVisual"] = false,
		["Size"] = Vector3.new(5, 5, 5),
		["CFrame"] = CFrame.new(0, 0, 0),
		["UpdateReference"] = nil,
		["ReferenceCFrame"] = CFrame.new(0, 0, 0),
		["IgnoreList"] = {},
	}
	
	self.CurrentCFrame = self.Options and self.Options.CFrame or CFrame.new(0, 0, 0)
	self.OnHit = Signal.new()

	if self.Options.DebugVisual then
		local box = Instance.new("Part")
		box.Color = Color3.fromRGB(255, 100, 100)
		box.Size = self.Options.Size
		box.CFrame = self.Options.CFrame or CFrame.identity
		box.Anchored = true
		box.CastShadow = false
		box.CanCollide = false
		box.Transparency = 0.25
		box.Material = Enum.Material.ForceField
		box.Parent = workspace
		self.BoxVisual = box
	end

	return self
end

function Hitbox.Cast(self)
	local overlapParams = OverlapParams.new()
	overlapParams.FilterType = Enum.RaycastFilterType.Exclude
	overlapParams.FilterDescendantsInstances = self.Options.IgnoreList or {}

	local hitParts = workspace:GetPartBoundsInBox(self.CurrentCFrame, self.Options.Size or Vector3.new(5, 5, 5), overlapParams)
	if #hitParts >= 1 and self.OnHit then
		for _, hitPart in pairs(hitParts) do
			self.OnHit:Fire(hitPart)
		end
	end

	return hitParts
end

function Hitbox.CastOnce(self)
	return self:Cast(), self:Destroy()
end

function Hitbox.Start(self)
	local activeKey = {}
	self.ActiveKey = activeKey
	self.Active = true
	if self.BoxVisual then
		self.BoxVisual.Parent = workspace
	end
	coroutine.wrap(function()
		while true do
			if self.ActiveKey ~= activeKey or not self.Active then
				break
			end

			if self.Options.UpdateReference and self.Options.UpdateReference:IsA("BasePart") and self.Options.UpdateReference.Parent then
				self.CurrentCFrame = self.Options.UpdateReference.CFrame * (self.Options.ReferenceCFrame or CFrame.new(0, 0, 0))
				if self.BoxVisual then
					self.BoxVisual.CFrame = self.CurrentCFrame
				end	
			end

			self:Cast()
			
			if RunService:IsServer() then
				RunService.Heartbeat:Wait()
			else
				task.wait()
			end
		end
	end)()

	return self, activeKey
end

function Hitbox.Stop(self)
	if self.Active then
		self.Active = false
		self.ActiveKey = nil
		if self.BoxVisual then
			self.BoxVisual.Parent = nil
		end
		
		return self
	end
end

function Hitbox.ChangeOption(self, optionName, newValue)
	if self.Options and self.Options[optionName] then
		self.Options[optionName] = newValue
		return true
	end
end

function Hitbox.Destroy(self)
	self:Stop()
	
	if self.BoxVisual then
		self.BoxVisual:Destroy()
	end
	if self.OnHit then
		self.OnHit:Destroy()
	end
	
	setmetatable(self, nil)
end

return Hitbox
