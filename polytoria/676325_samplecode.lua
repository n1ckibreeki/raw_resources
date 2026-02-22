----------------------------------------------------------------------

-- // SAMPLE SCRIPT

-- // COMMON VARIABLES
local Camera = game["Environment"]["Camera"]

-- // FORCED FIRSTPERSON
Input.CursorLocked = true
Camera.MaxDistance = 0
Camera.MinDistance = 0
Camera.Distance = 0
--

-- // FUNCTIONS
local function EulerRotation(vec, rot)
    local cx = math.cos(math.rad(rot.x))
    local sx = math.sin(math.rad(rot.x))

    local cy = math.cos(math.rad(rot.y))
    local sy = math.sin(math.rad(rot.y))
    
    local cz = math.cos(math.rad(rot.z))
    local sz = math.sin(math.rad(rot.z))

    local x1 = vec.x
    local y1 = vec.y * cx - vec.z * sx
    local z1 = vec.y * sx + vec.z * cx

    local x2 = x1 * cy + z1 * sy
    local y2 = y1
    local z2 = -x1 * sy + z1 * cy

    local x3 = x2 * cz - y2 * sz
    local y3 = x2 * sz + y2 * cz
    local z3 = z2

    return Vector3.New(x3, y3, z3)
end

--// INIT
local TestingBrick = Instance.New("Part")
TestingBrick.Size = Vector3.New(1,1,1)
TestingBrick.Parent = game["Environment"]
TestingBrick.CanCollide = false

local offset = Vector3.New(1, -1, 3)

game.Rendered:Connect(function(dt)
    local rotatedOffset = EulerRotation(offset, Camera.Rotation)
    TestingBrick.Position = Camera.Position + rotatedOffset
    TestingBrick.Rotation = Camera.Rotation
end)
