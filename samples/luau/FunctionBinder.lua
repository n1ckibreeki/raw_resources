-- // nickibreeki's FunctionBinder For Game Development
local Types = ...
local FuncBinderTypes = Types.FunctionBinder

local FunctionBinder = {}

function FunctionBinder.Bind(root: typeof(FuncBinderTypes.Root), data: typeof(FuncBinderTypes.BindData)): ()
	assert(root, "Root table cannot be nil")
	assert(data.Function, "Function/Connection cannot be nil")

	if data.Name then
		root[data.Name] = data.Function
	else
		table.insert(root, data.Function)
	end
end

function FunctionBinder.Unbind(root: typeof(FuncBinderTypes.Root), bindName: string | {string}): ()
	assert(root, "Root table cannot be nil")

	local function unbindSingle(name: string)
		local bound = root[name]
		if not bound then
			return
		end

		local boundType = typeof(bound)

		if boundType == "thread" then
			local success = pcall(function()
				task.cancel(bound)
			end)
			if not success then
				warn(('Failed to cancel: %s'):format(name))
			end
		elseif boundType == "RBXScriptConnection" or (boundType == "table" and bound.Disconnect) then
			local success = pcall(function()
				bound:Disconnect()
			end)
			if not success then
				warn(('Failed to disconnect: %s'):format(name))
			end
		end

		root[name] = nil
	end

	if typeof(bindName) == "table" then
		for _, name in ipairs(bindName) do
			unbindSingle(name)
		end
	else
		unbindSingle(bindName)
	end
end

function FunctionBinder.UnbindAll(root: typeof(FuncBinderTypes.Root)): ()
	assert(root, "Root table cannot be nil")

	for key, value in pairs(root) do
		local valueType = typeof(value)

		if valueType == "thread" then
			pcall(task.cancel, value)
		elseif valueType == "RBXScriptConnection" or (valueType == "table" and value.Disconnect) then
			pcall(function()
				value:Disconnect()
			end)
		end

		root[key] = nil
	end
end

return table.isfrozen(FunctionBinder) and FunctionBinder or table.freeze(FunctionBinder)
