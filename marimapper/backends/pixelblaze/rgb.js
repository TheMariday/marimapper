// Color array indexed by pixel index: [r, g, b] or null for black
export var colors = []

export function render(index) {
  var color = colors[index]
  if (color) {
    rgb(color[0], color[1], color[2])
  } else {
    rgb(0, 0, 0)
  }
}
