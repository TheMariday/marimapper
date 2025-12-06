// Color array flat format: [r,g,b,r,g,b,...] for pixelCount pixels
export var colors = array(pixelCount * 3)

export function render(index) {
  var baseIdx = index * 3
  var r = colors[baseIdx]
  var g = colors[baseIdx + 1]
  var b = colors[baseIdx + 2]

  if (r || g || b) {
    rgb(r, g, b)
  } else {
    rgb(0, 0, 0)
  }
}
