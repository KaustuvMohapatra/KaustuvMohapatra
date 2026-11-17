-- Assemble staged layer PNGs (written by build.py) into one layered, animated .aseprite file.
-- Staged files: <dir>/<layer index 00>-<frame index 00>.png, plus manifest.txt.
local dir, out = app.params.dir, app.params.out
local m = { layers = {} }
for line in io.lines(dir .. "/manifest.txt") do
  local k, v = line:match("^(%w+)=(.*)$")
  if k == "layer" then table.insert(m.layers, v) else m[k] = v end
end
local w, h, frames, dur = tonumber(m.w), tonumber(m.h), tonumber(m.frames), tonumber(m.duration)

local spr = Sprite(w, h, ColorMode.RGB)
for f = 2, frames do spr:newEmptyFrame() end
for f = 1, frames do spr.frames[f].duration = dur end

for li, name in ipairs(m.layers) do
  local layer = (li == 1) and spr.layers[1] or spr:newLayer()
  layer.name = name
  for f = 1, frames do
    local path = string.format("%s/%02d-%02d.png", dir, li - 1, f - 1)
    local img = Image{ fromFile = path }
    if not img:isEmpty() then spr:newCel(layer, f, img, Point(0, 0)) end
  end
end
spr:saveAs(out)
